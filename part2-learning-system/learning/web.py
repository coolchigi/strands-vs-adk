"""Fetching pages, and deciding whether what a model says about them is true.

Shared by both frameworks. Pages are fetched here, not through a model's tools, so the
text every quote is checked against is text we fetched ourselves, live.
"""

from __future__ import annotations

import hashlib
import ipaddress
import logging
import re
import socket
import threading
from dataclasses import dataclass, field
from typing import Callable, Protocol
from urllib.parse import urlparse

import httpx

from .model import normalise

log = logging.getLogger("learning")

USER_AGENT = "learning-system/1.0"
DROPPED_TAGS = ("script", "style", "noscript", "template", "svg", "nav", "header", "footer", "form")
INLINE_TAGS = ("a", "code", "strong", "em", "b", "i", "span", "kbd", "sup", "sub")


@dataclass(frozen=True)
class Page:
    url: str
    status: int
    text: str
    content_type: str = ""

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300 and bool(self.text.strip())

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.text.encode()).hexdigest()


class Web(Protocol):
    def get(self, url: str) -> Page: ...


def page_text(html: str) -> str:
    """Visible text, one block per line, code blocks intact.

    Syntax highlighting wraps every token of a code block in its own <span>, so a naive
    get_text("\\n") prints HCL one token per line. Unwrapping inline tags and merging the
    strings they leave keeps code whole and sentences in one piece.
    """
    from bs4 import BeautifulSoup, Comment

    soup = BeautifulSoup(html, "lxml")
    for tag in soup(DROPPED_TAGS):
        tag.decompose()
    # React marks the seams between text it renders with <!-- -->, which would split
    # "(currently 7.0)." into three lines
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()
    for tag in soup.find_all(INLINE_TAGS):
        tag.unwrap()
    soup.smooth()
    root = soup.find("main") or soup.body or soup
    return root.get_text(separator="\n", strip=True)


MAX_BYTES = 5_000_000   # a docs page is far smaller. 199 KB of gzip once became 210 MB of text
MAX_SECONDS = 60        # the whole fetch, redirects and slow headers included
MAX_REDIRECTS = 5


def public_ip(address: str) -> bool:
    ip = ipaddress.ip_address(address.split("%")[0])
    mapped = getattr(ip, "ipv4_mapped", None)
    return (mapped or ip).is_global


def public(host: str, resolve: Callable = socket.getaddrinfo) -> bool:
    """Whether every address a host name points at is on the public internet. The URLs come from
    a model, and this machine's own services and the cloud metadata address were reachable."""
    try:
        addresses = {info[4][0] for info in resolve(host, None)}
        return bool(addresses) and all(public_ip(a) for a in addresses)
    except (OSError, UnicodeError, ValueError):
        return False


class HttpWeb:
    def __init__(self, timeout: float = 30.0, transport: httpx.BaseTransport | None = None,
                 resolve: Callable = socket.getaddrinfo) -> None:
        self._timeout, self._transport = timeout, transport
        self._resolve = resolve
        self._cache: dict[str, Page] = {}

    def _client(self) -> httpx.Client:
        # redirects are followed by hand, so every hop is checked like the first
        return httpx.Client(timeout=self._timeout, follow_redirects=False, transport=self._transport,
                            headers={"user-agent": USER_AGENT})

    def get(self, url: str) -> Page:
        """The page, or status 0 if it isn't a public page or doesn't arrive in MAX_SECONDS.

        The fetch runs on its own thread with a deadline: a server that sent headers a byte at a
        time could otherwise hold a build for as long as it liked.
        """
        if url in self._cache:
            return self._cache[url]
        box: dict[str, Page] = {}
        client = self._client()  # its own, so giving up on it can't break another thread's fetch

        def fetch() -> None:
            try:
                box["page"] = self._fetch(client, url)
            except Exception as e:  # a URL httpx can't parse, a bad redirect: not fetched either way
                log.warning("not fetched, %s: %s", type(e).__name__, url)
            finally:
                client.close()

        worker = threading.Thread(target=fetch, daemon=True)
        worker.start()
        worker.join(MAX_SECONDS)
        if worker.is_alive():
            log.warning("gave up on %s after %d seconds", url, MAX_SECONDS)
            try:
                client.close()
            except Exception:
                pass
            return Page(url=url, status=0, text="")
        page = box.get("page") or Page(url=url, status=0, text="")
        if page.ok:
            self._cache[url] = page
        return page

    @staticmethod
    def _through_proxy(client: httpx.Client, url: httpx.URL) -> bool:
        """Whether httpx sent this through a proxy. Asked of httpx itself, so ALL_PROXY, every
        NO_PROXY form and macOS system proxies count the way httpx counts them."""
        try:
            return client._transport_for_url(url) is not client._transport
        except AttributeError:  # a later httpx without this method: keep the check, refuse if unsure
            return False

    def _fetch(self, client: httpx.Client, url: str) -> Page:
        for _ in range(MAX_REDIRECTS + 1):
            parts = urlparse(url)
            if parts.scheme not in ("http", "https") or not parts.hostname or not public(parts.hostname, self._resolve):
                log.warning("not fetched, not a public web address: %s", url)
                return Page(url=url, status=0, text="")
            with client.stream("GET", url) as r:
                # the name is looked up again to connect, and a second answer can point at this
                # machine. Where it actually connected is what counts
                stream = r.extensions.get("network_stream")
                peer = stream.get_extra_info("server_addr") if stream is not None else None
                if peer and not public_ip(peer[0]) and not self._through_proxy(client, r.request.url):  # a proxy is fine
                    log.warning("not read, %s connected to %s, which isn't public", url, peer[0])
                    return Page(url=url, status=0, text="")
                if r.has_redirect_location:
                    url = str(r.url.join(r.headers["location"]))
                    continue
                if len(r.headers.get_list("content-encoding", split_commas=True)) > 1:
                    log.warning("not read, %s is compressed more than once", url)  # a 658-byte page once became 300 MiB
                    return Page(url=str(r.url), status=0, text="")
                body = bytearray()
                for chunk in r.iter_bytes():  # decompressed, so the cap holds for gzip too
                    body += chunk
                    if len(body) > MAX_BYTES:
                        log.warning("stopped reading %s: over %d bytes", url, MAX_BYTES)
                        return Page(url=str(r.url), status=0, text="")
                kind = r.headers.get("content-type", "")
                raw = bytes(body).decode(r.encoding or "utf-8", errors="replace")  # httpx's own charset fallback
                text = page_text(raw) if "html" in kind.lower() else raw
                return Page(url=str(r.url), status=r.status_code, text=text, content_type=kind)
        log.warning("not fetched, more than %d redirects: %s", MAX_REDIRECTS, url)
        return Page(url=url, status=0, text="")


@dataclass
class FakeWeb:
    pages: dict[str, str] = field(default_factory=dict)
    seen: list[str] = field(default_factory=list)

    def get(self, url: str) -> Page:
        self.seen.append(url)
        if url not in self.pages:
            return Page(url=url, status=404, text="")
        return Page(url=url, status=200, text=self.pages[url], content_type="text/plain")


# -- rules --------------------------------------------------------------------------

def host_of(url: str) -> str:
    return (urlparse(url).hostname or "").lower().removeprefix("www.")


def under(host: str, domains: list[str]) -> bool:
    return any(host == d or host.endswith("." + d) for d in (x.lower().removeprefix("www.") for x in domains))


def quote_on_page(quote: str, text: str) -> bool:
    """The words have to be there. A full stop or comma the model added at the end doesn't count."""
    words = normalise(quote).rstrip(".,;:")
    return bool(words) and words in normalise(text)


# stable releases only: 3.15.0rc2, 3.15.0a1 and 1.14.0-beta1 are previews. 3.14.8 at the end of a
# sentence still counts, and so does 3.14.8 run into the next word, the way minified pages read
_SUFFIX = r"(?i:\.?(?:a|b|rc|alpha|beta|dev|pre|preview|nightly)\d*(?![a-z]))"
_RELEASE = re.compile(r"(?<![\d.])(\d+)\.(\d+)\.(\d+)(?!\.?\d)(?!-)(?!" + _SUFFIX + ")")
_PREVIEW = re.compile(r"\d(?:-|" + _SUFFIX + r")|\b(?:alpha|beta|rc\d*|preview|nightly)\b", re.I)


def newest_release(text: str, version: str) -> str | None:
    """The newest stable release on a page in the same major line as `version`, if newer."""
    want = tuple(int(x) for x in re.findall(r"\d+", version)[:3])
    if len(want) < 2:
        return None
    found = {tuple(int(x) for x in m.groups()) for m in _RELEASE.finditer(text)}
    same_line = [v for v in found if v[0] == want[0]]
    best = max(same_line, default=None)
    return ".".join(map(str, best)) if best and best[:len(want)] > want else None


def check_version(web: Web, version: str | None, url: str | None, quote: str | None,
                  official: list[str]) -> str | None:
    """A version is a claim. None when it checks out, otherwise what is wrong with it.

    For an exam, the version that matters is the one the exam tests, and the guide says
    it. Otherwise it is the current release. Either way it needs a live official page that
    states it, and that page must not list a newer release in the same line.
    """
    version = (version or "").strip()
    if not version:
        return None
    if not url or not quote:
        return f"version {version} is given with no page that states it"
    if not under(host_of(url), official):
        return f"{url} is not an official page, so it cannot vouch for version {version}"
    page = web.get(url)
    if not page.ok:
        return f"{url} returned {page.status}, so version {version} is unchecked"
    if not under(host_of(page.url), official):  # a redirect off the official site once vouched for a version
        return f"{url} leads to {page.url}, which is not an official page, so it cannot vouch for version {version}"
    if not quote_on_page(quote, page.text):
        return f"{url} does not say {quote!r}"
    if normalise(version) not in normalise(quote):
        return f"the quote {quote!r} does not mention version {version}"
    number = re.search(r"\d+(?:\.\d+)+", version)  # a release number: an exam's code has none
    if number:
        if _PREVIEW.search(version):
            return f"version {version} is a preview release. Teach the current stable one"
        # each place the quote names it, as a whole token: 3.14 is stated by "3.14.0", and 3.15.0
        # isn't by "3.15.0a1"
        tokens = re.findall(r"(?<![\d.])" + re.escape(number.group(0)) + r"(?!\d)[\w.+-]*", quote)
        if not tokens:  # 4.8 is inside 3.14.8, and isn't a version of anything there
            return f"the quote {quote!r} has {version} only inside a longer version number"
        if all(_PREVIEW.search(t) for t in tokens):
            return f"the quote {quote!r} names {version} only as a preview, so it isn't a release yet"
    newer = newest_release(page.text, version)
    if newer:
        return f"{url} also lists {newer}, which is newer than {version}"
    return None


# -- the site's own list of its pages --------------------------------------------------------

_MD_LINK = re.compile(r"\[[^\]]*\]\((https?://[^\s)]+)\)")
_LOC = re.compile(r"<loc>\s*(https?://[^<\s]+)\s*</loc>", re.I)


def docs_index(web: Web, url_prefix: str, limit: int = 300) -> list[str]:
    """Official pages under a prefix, from the site's llms.txt or sitemap, shallowest first.

    Only pages the site itself lists, so nothing here is made up, and nothing is stale the
    way a search index can be. A sitemap index is followed one level down.
    """
    host = urlparse(url_prefix).netloc
    llms = web.get(f"https://{host}/llms.txt")
    urls = _MD_LINK.findall(llms.text) if llms.ok and "html" not in llms.content_type.lower() else []
    if not urls:
        top = web.get(f"https://{host}/sitemap.xml")
        found = _LOC.findall(top.text) if top.ok else []
        if "<sitemapindex" in top.text.lower():
            children, found = found[:5], []
            for child in children:
                page = web.get(child)
                found += _LOC.findall(page.text) if page.ok else []
        urls = found
    urls = list(dict.fromkeys(u.rstrip(".,);") for u in urls if u.startswith(url_prefix)))
    return sorted(urls, key=lambda u: (urlparse(u).path.rstrip("/").count("/"), u))[:limit]

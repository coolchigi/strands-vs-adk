"""Fetching pages, and deciding whether what a model says about them is true.

Shared by both frameworks. Pages are fetched here, not through a model's tools, so the
text every quote is checked against is text we fetched ourselves, live.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Protocol
from urllib.parse import urlparse

import httpx

from .model import normalise

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


class HttpWeb:
    def __init__(self, timeout: float = 30.0, transport: httpx.BaseTransport | None = None) -> None:
        self._c = httpx.Client(timeout=timeout, follow_redirects=True, transport=transport,
                               headers={"user-agent": USER_AGENT})
        self._cache: dict[str, Page] = {}

    def get(self, url: str) -> Page:
        if url in self._cache:
            return self._cache[url]
        try:
            r = self._c.get(url)
        except httpx.HTTPError:
            return Page(url=url, status=0, text="")
        kind = r.headers.get("content-type", "")
        text = page_text(r.text) if "html" in kind.lower() else r.text
        page = Page(url=str(r.url), status=r.status_code, text=text, content_type=kind)
        if page.ok:
            self._cache[url] = page
        return page


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


_RELEASE = re.compile(r"(?<![\d.])(\d+)\.(\d+)\.(\d+)(?![\d.])(?!-)")  # stable releases only


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
    if not quote_on_page(quote, page.text):
        return f"{url} does not say {quote!r}"
    if normalise(version) not in normalise(quote):
        return f"the quote {quote!r} does not mention version {version}"
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

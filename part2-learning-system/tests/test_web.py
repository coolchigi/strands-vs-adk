"""Fetching and verifying, against pages recorded from developer.hashicorp.com on 27 Sept 2026."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from learning.web import FakeWeb, HttpWeb, check_version, newest_release, quote_on_page

FIXTURES = Path(__file__).parent / "fixtures"
TUTORIAL = "https://developer.hashicorp.com/terraform/tutorials/aws-get-started/aws-create"


def dns(table: dict[str, str] | None = None):
    """A stand-in for DNS: every name is a public address unless the table says otherwise."""
    def resolve(host, port):
        return [(None, None, None, "", ((table or {}).get(host, "93.184.216.34"), 0))]
    return resolve


def tutorial() -> str:
    html = (FIXTURES / "aws-create.html").read_text()
    web = HttpWeb(transport=httpx.MockTransport(
        lambda r: httpx.Response(200, text=html, headers={"content-type": "text/html; charset=utf-8"})), resolve=dns())
    page = web.get(TUTORIAL)
    assert page.ok
    return page.text


def test_a_page_keeps_its_commands_and_hcl_intact():
    text = tutorial()
    assert "$ terraform init" in text
    assert "required_providers {" in text


def test_a_real_sentence_verifies_and_an_invented_one_does_not():
    text = tutorial()
    assert quote_on_page("As part of initialization, Terraform downloads and installs the providers "
                         "defined in your configuration in your current working directory.", text)
    assert not quote_on_page("As part of initialization, Terraform downloads every provider in the registry.", text)


def test_a_quote_of_what_a_reader_sees_verifies_through_markup():
    # a markdown copy of a page has backticks, links and escapes in the middle of the words
    page = "Run `terraform init` in the [working directory](https://x). Download terraform\\_1.16.4."
    assert quote_on_page("Run terraform init in the working directory", page)
    assert quote_on_page("Download terraform_1.16.4", page)


def test_adks_own_page_loader_throws_away_the_lines_a_terraform_lesson_needs(monkeypatch):
    """Why the fetching here doesn't use google.adk.tools.load_web_page."""
    import requests
    from google.adk.tools import load_web_page as lwp

    response = requests.Response()
    response.status_code = 200
    response._content = (FIXTURES / "aws-create.html").read_bytes()
    monkeypatch.setattr(lwp, "_fetch_response", lambda url: response)
    text = lwp.load_web_page(TUTORIAL)
    assert "As part of initialization" in text
    assert "$ terraform init" not in text
    assert "required_providers {" not in text


INSTALL = "https://developer.hashicorp.com/terraform/install"
RELEASES = "https://releases.hashicorp.com/terraform/"


@pytest.mark.parametrize("version, url, quote, problem", [
    ("1.16.4", INSTALL, "Version: 1.16.4", None),
    ("1.9.x", None, None, "no page that states it"),                 # from memory, as one run did
    ("1.16.3", INSTALL, "Version: 1.16.3", "does not say"),          # quoting a stale copy
    ("1.16.3", RELEASES, "terraform_1.16.3", "also lists 1.16.4"),   # a releases page lists them all
    ("1.16.4", "https://someblog.dev/tf", "Version: 1.16.4", "not an official page"),
    (None, None, None, None),
])
def test_a_version_is_a_claim_like_any_other(version, url, quote, problem):
    web = FakeWeb(pages={INSTALL: "Install Terraform\nVersion: 1.16.4",
                         RELEASES: "terraform_1.17.0-beta1\nterraform_1.16.4\nterraform_1.16.3"})
    found = check_version(web, version, url, quote, ["hashicorp.com"])
    assert (found is None) if problem is None else (problem in found)


def test_a_beta_is_not_a_newer_release():
    assert newest_release("terraform_1.17.0-beta1 terraform_1.16.4", "1.16.4") is None


def test_a_full_stop_the_model_added_is_not_a_different_quote():
    # one run's version check failed on 'Version: 1.16.4.' against a page saying 'Version: 1.16.4'
    assert quote_on_page("Version: 1.16.4.", "Binary download\nVersion: 1.16.4\n[Download]")
    assert not quote_on_page("Version: 1.16.3.", "Binary download\nVersion: 1.16.4\n[Download]")


def test_react_comment_markers_do_not_split_a_sentence():
    # typescriptlang.org, 28 Sept 2026. React puts <!-- --> between text pieces it renders
    html = ('<html><body><main><p>To do this, run <code>npm install -g typescript</code>. This will install '
            'the latest version (currently <!-- -->7.0<!-- -->).</p></main></body></html>')
    from learning.web import page_text
    assert quote_on_page("This will install the latest version (currently 7.0).", page_text(html))


def test_addresses_on_this_machine_or_the_cloud_metadata_service_are_not_fetched():
    # the URLs come from a model, and loopback and 169.254.169.254 were reachable
    asked = []
    web = HttpWeb(transport=httpx.MockTransport(lambda r: asked.append(str(r.url)) or httpx.Response(200, text="x")),
                  resolve=dns({"internal.example": "10.0.0.5", "localhost": "127.0.0.1",
                               "169.254.169.254": "169.254.169.254", "mapped.example": "::ffff:127.0.0.1"}))
    for url in ("http://internal.example/x", "http://localhost:8080/", "http://169.254.169.254/latest/meta-data/",
                "http://mapped.example/", "file:///etc/hosts", "ftp://docs.example/x"):
        assert web.get(url).status == 0, url
    assert asked == []


def test_a_redirect_is_checked_like_the_first_address():
    def answer(r):
        if r.url.host == "docs.example":
            return httpx.Response(302, headers={"location": "http://internal.example/admin"})
        return httpx.Response(200, text="secret")

    web = HttpWeb(transport=httpx.MockTransport(answer), resolve=dns({"internal.example": "10.0.0.5"}))
    assert web.get("https://docs.example/page").status == 0


def test_a_page_too_big_to_be_documentation_is_not_read():
    # 199 KB of gzip once expanded to 210 MB of text
    big = "a" * 6_000_000
    web = HttpWeb(transport=httpx.MockTransport(lambda r: httpx.Response(200, text=big)), resolve=dns())
    assert web.get("https://docs.example/huge").status == 0


def test_a_redirect_off_the_official_site_cannot_vouch_for_a_version():
    class Redirected:
        def get(self, url):
            from learning.web import Page
            return Page(url="https://not-the-vendor.example/current", status=200, text="Terraform 99.0.0 is current")

    problem = check_version(Redirected(), "99.0.0", "https://developer.hashicorp.com/terraform/install",
                            "Terraform 99.0.0 is current", ["hashicorp.com"])
    assert problem and "not an official page" in problem


def test_a_page_with_a_charset_nobody_knows_is_still_read():
    # the strict decode once ended a build on one misconfigured page
    web = HttpWeb(transport=httpx.MockTransport(lambda r: httpx.Response(
        200, content="café".encode(), headers={"content-type": "text/plain; charset=foo-bogus"})), resolve=dns())
    page = web.get("https://docs.example/x")
    assert page.ok and page.text == "café"


def test_a_page_compressed_twice_is_not_read():
    # 658 bytes of gzip inside gzip once became 300 MiB before the size cap could look
    import gzip

    twice = gzip.compress(gzip.compress(b"a" * 100_000))
    web = HttpWeb(transport=httpx.MockTransport(lambda r: httpx.Response(
        200, content=twice, headers={"content-encoding": "gzip, gzip"})), resolve=dns())
    assert web.get("https://docs.example/bomb").status == 0


def test_a_server_that_never_finishes_is_given_up_on(monkeypatch):
    # headers sent a byte at a time could hold a build as long as the server liked
    import time

    from learning import web as webmod

    monkeypatch.setattr(webmod, "MAX_SECONDS", 1)

    def slow(r):
        time.sleep(3)
        return httpx.Response(200, text="late")

    started = time.monotonic()
    page = HttpWeb(transport=httpx.MockTransport(slow), resolve=dns()).get("https://docs.example/slow")
    assert page.status == 0 and time.monotonic() - started < 2.5


def test_where_it_actually_connected_is_what_counts():
    # the name is looked up again to connect, and the second answer can point at this machine
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class Local(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            body = b"only for this machine"
            self.send_response(200)
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Local)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        # the check is told the address is public, as DNS rebinding would tell it
        web = HttpWeb(transport=httpx.HTTPTransport(), resolve=dns({"127.0.0.1": "93.184.216.34"}))  # no proxy
        assert web.get(f"http://127.0.0.1:{server.server_address[1]}/").status == 0
    finally:
        server.shutdown()


def test_each_fetch_has_its_own_client_and_closes_it(monkeypatch):
    # giving up on one fetch once closed the client another thread's fetch was using
    made = []
    real = HttpWeb._client

    def counting(self):
        client = real(self)
        made.append(client)
        return client

    monkeypatch.setattr(HttpWeb, "_client", counting)
    web = HttpWeb(transport=httpx.MockTransport(lambda r: httpx.Response(200, text="ok")), resolve=dns())
    web.get("https://docs.example/a")
    web.get("https://docs.example/b")
    assert len(made) == 2 and all(c.is_closed for c in made)


def test_previews_are_not_releases():
    # 3.15.0rc2 counted as a newer stable release, and a preview could vouch for a version
    from learning.web import check_version, newest_release

    assert newest_release("Python 3.14.8 is the latest. Python 3.15.0rc2 is a release candidate.", "3.14.8") is None
    assert newest_release("Python 3.14.8 is the latest. Python 3.15.0b1 is a beta.", "3.14.8") is None
    assert newest_release("Terraform 1.13.2 is current. Terraform 1.14.0-beta1 is a preview.", "1.13.2") is None
    assert newest_release("We shipped 3.14.9.", "3.14.8") == "3.14.9"            # at the end of a sentence too
    assert newest_release("Release 3.14.8.1 is a patch.", "3.14.8") is None      # four parts isn't x.y.z

    url = "https://www.python.org/downloads/"
    web = FakeWeb(pages={url: "Download Python 3.14.8\nPython 3.15.0a1 is an early developer preview."})
    assert check_version(web, "3.14.8", url, "Download Python 3.14.8", ["python.org"]) is None
    assert "preview" in check_version(web, "3.15.0", url, "Python 3.15.0a1 is an early developer preview",
                                      ["python.org"])
    assert "preview release" in check_version(web, "3.15.0a1", url, "Python 3.15.0a1 is an early developer preview",
                                              ["python.org"])



def test_a_release_is_read_from_glued_text_and_a_short_version_from_its_patch_release():
    from learning.web import check_version, newest_release

    assert newest_release("<span>Python 3.14.8</span><span>Oct. 7</span>Python 3.14.9Oct", "3.14.8") == "3.14.9"
    url = "https://www.python.org/doc/"
    web = FakeWeb(pages={url: "Python 3.14.0 documentation"})
    assert check_version(web, "3.14", url, "Python 3.14.0 documentation", ["python.org"]) is None
    both = "Python 3.14.8rc1 was followed by Python 3.14.8"                       # a preview, then the release
    assert check_version(FakeWeb(pages={url: both}), "3.14.8", url, both, ["python.org"]) is None
    inside = FakeWeb(pages={url: "Python 3.14.8 documentation"})                  # 4.8 is in 3.14.8, and isn't it
    assert "inside a longer version" in check_version(inside, "4.8", url, "Python 3.14.8 documentation", ["python.org"])
    alpha = FakeWeb(pages={url: "Python 3.15.0 alpha 1 is out"})
    assert "preview" in check_version(alpha, "3.15.0 alpha 1", url, "Python 3.15.0 alpha 1 is out", ["python.org"])

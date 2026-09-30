"""Fetching and verifying, against pages recorded from developer.hashicorp.com on 27 Sept 2026."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from learning.web import FakeWeb, HttpWeb, check_version, newest_release, quote_on_page

FIXTURES = Path(__file__).parent / "fixtures"
TUTORIAL = "https://developer.hashicorp.com/terraform/tutorials/aws-get-started/aws-create"


def tutorial() -> str:
    html = (FIXTURES / "aws-create.html").read_text()
    web = HttpWeb(transport=httpx.MockTransport(
        lambda r: httpx.Response(200, text=html, headers={"content-type": "text/html; charset=utf-8"})))
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

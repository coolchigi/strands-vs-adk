import pytest


@pytest.fixture(autouse=True)
def no_editor(monkeypatch):
    """`learn next` opens VS Code in a real terminal. A test that wants an editor brings a stand-in."""
    monkeypatch.setenv("LEARN_EDITOR", "none")
    monkeypatch.setenv("LEARN_NOTIFY", "off")  # and a build never posts a real notification

"""The budget: what a token costs, the switch to a cheaper model, and the cap."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from learning import cli
from learning.budget import Budget, BudgetExceeded, price_for
from learning.model import Claim

SONNET = "global.anthropic.claude-sonnet-4-6"
HAIKU = "global.anthropic.claude-haiku-4-5-20251001-v1:0"


def test_a_us_only_profile_costs_ten_percent_more_than_a_global_one():
    assert price_for(SONNET) == (3.00, 15.00)
    assert price_for("us.anthropic.claude-sonnet-4-6") == (3.30, 16.50)
    assert price_for(HAIKU) == (1.00, 5.00)
    assert price_for("gemini-3.5-flash-lite") == (0.30, 2.50)


def test_partway_to_the_cap_the_course_switches_to_the_cheaper_model_and_says_so_once():
    said = []
    b = Budget(model=SONNET, limit_usd=1.00, cheap_model=HAIKU, switch_at=0.5, say=said.append)
    b.charge("lesson", 100_000, 0)                     # $0.30
    assert b.current_model() == SONNET
    b.charge("lesson", 100_000, 0)                     # $0.60, past half of $1
    assert b.current_model() == HAIKU and b.current_model() == HAIKU
    assert len(said) == 1 and HAIKU in said[0]


def test_tokens_are_priced_at_the_model_that_used_them():
    b = Budget(model=SONNET, limit_usd=10.0, cheap_model=HAIKU)
    b.charge("lesson", 1_000_000, 0, SONNET)
    b.charge("lesson", 1_000_000, 0, HAIKU)
    assert b.spent_usd == pytest.approx(4.00)


def test_the_cap_still_stops_the_course():
    b = Budget(model=SONNET, limit_usd=0.50, cheap_model=HAIKU)
    b.charge("lesson", 200_000, 0)                     # $0.60
    with pytest.raises(BudgetExceeded):
        b.check()


def test_settings_pick_the_cheaper_model_or_turn_the_switch_off(monkeypatch):
    monkeypatch.delenv("LEARN_CHEAP_MODEL", raising=False)
    assert Budget.from_env("us.anthropic.claude-sonnet-4-6").cheap_model == "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    assert Budget.from_env("gemini-3.8-flash").cheap_model == "gemini-3.5-flash-lite"
    monkeypatch.setenv("LEARN_CHEAP_MODEL", "none")
    b = Budget.from_env(SONNET)
    b.charge("lesson", 10_000_000, 0)
    assert b.cheap_model is None and b.current_model() == SONNET


def test_spend_saved_before_dollars_were_saved_is_priced_at_the_main_model(tmp_path):
    f = tmp_path / "spend.json"
    f.write_text(json.dumps({"lesson": [3, 1_000_000, 0], "extract": [1, 0, 0, 0.25]}))
    b = Budget(model=SONNET, limit_usd=10.0)
    cli.load_spend(b, f)
    assert b.spent_usd == pytest.approx(3.25)
    cli.save_spend(b, f)
    assert json.loads(f.read_text())["lesson"] == [3, 1_000_000, 0, 3.0]


def test_the_strands_brain_writes_with_the_cheaper_model_after_the_switch(monkeypatch):
    from impl.strands import brain as strands_brain
    from impl.strands.telemetry import Meter

    used = []

    class Agent:
        def __init__(self, model, **kw):
            used.append(model.config["model_id"])
            self.event_loop_metrics = SimpleNamespace(accumulated_usage={})
            self.hooks = []

        def add_hook(self, hook):
            self.hooks.append(hook)

        def __call__(self, prompt, structured_output_model):
            return SimpleNamespace(structured_output="done")

    monkeypatch.setattr(strands_brain, "Agent", Agent)
    meter = Meter(model=SONNET, limit_usd=1.0, cheap_model=HAIKU)
    b = strands_brain.StrandsBrain(meter, research_tools=[])
    b.ask("lesson", "i", "p", object)
    meter.charge("lesson", 200_000, 0)                 # $0.60
    b.ask("lesson", "i", "p", object)
    assert used == [SONNET, HAIKU]


def test_the_adk_brain_builds_agents_on_the_cheaper_model_after_the_switch():
    from impl.adk.brain import AdkBrain
    from impl.adk.telemetry import Meter

    meter = Meter(model="gemini-3.8-flash", limit_usd=1.0, cheap_model="gemini-3.5-flash-lite")
    b = AdkBrain(meter)
    assert b._agent("lesson", "i", Claim, research=False).model == "gemini-3.8-flash"
    meter.charge("lesson", 1_000_000, 0)               # $0.75
    assert b._agent("lesson", "i", Claim, research=False).model == "gemini-3.5-flash-lite"

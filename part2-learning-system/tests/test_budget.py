"""The budget: what a token costs, the switch to a cheaper model, and the cap."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from learning import cli
from learning.budget import Budget, BudgetExceeded, Usage, price_for
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


def test_the_switch_counts_from_the_first_lesson_so_research_cant_use_it_up():
    # counted from $0, 28 Sep's Strands research alone passed the $5 switch, and every lesson
    # would have come from the cheaper model
    b = Budget(model=SONNET, limit_usd=10.0, cheap_model=HAIKU, switch_at=0.5)
    b.charge("extract", 2_000_000, 0)                  # $6 of research, past half of $10
    assert b.current_model() == SONNET and b.switch_usd is None
    b.charge("lesson", 600_000, 0)                     # $1.80 of lessons, under half of the $4 left
    assert b.switch_usd == pytest.approx(8.00) and b.current_model() == SONNET
    b.charge("review_lesson", 100_000, 0)              # $2.10
    assert b.current_model() == HAIKU

    # worked out from the spend alone, so a resumed build switches at the same point
    again = Budget(model=SONNET, limit_usd=10.0, cheap_model=HAIKU, switch_at=0.5, by_role=dict(b.by_role))
    assert again.switch_usd == pytest.approx(8.00) and again.current_model() == HAIKU


def test_a_switch_at_0_means_the_cheaper_model_from_the_start():
    b = Budget(model=SONNET, limit_usd=10.0, cheap_model=HAIKU, switch_at=0)
    assert b.current_model() == HAIKU


def test_teaching_charges_only_the_roles_the_switch_counts_even_on_a_rewrite(tmp_path):
    # the switch counts lesson spend by role, so a new role in teaching would count as research
    from learning import flow as flows
    from learning import stages
    from learning.budget import LESSON_ROLES
    from learning.model import (
        Claim, Curriculum, KnowledgeBase, LearnerProfile, Lesson, LessonSpec, QuizItem, Spec, Stage, Unit,
    )
    from learning.web import FakeWeb

    claim = Claim(id="0123456789ab", text="t", quote="q", source_id="s")
    profile = LearnerProfile(subject="x", goal="y", subject_is_clear=True)
    passing = Lesson(id="l", title="l", explanation="It is so [c:0123456789ab].", worked_example="e",
                     quiz=[QuizItem(stem="s", options=["a", "b", "c"], answer=0, explanation="why", objective="o")])
    reviews = iter([stages.Review(findings=[stages.Finding(stage=Stage.TEACHING, detail="too thin")]),
                    stages.Review(), stages.Review()])
    asked = []

    class Brain:
        def ask(self, name, instruction, prompt, schema, research=False):
            asked.append(name)
            if name == "lesson":
                return passing
            return next(reviews) if name == "review_lesson" else stages.Review()  # a new role fails the assert by name

    f = flows.start(Brain(), FakeWeb(), profile, tmp_path)
    f.board.knowledge = KnowledgeBase(profile=profile, spec=Spec(kind="derived_from_docs", title="x"), claims=[claim])
    f.board.curriculum = Curriculum(title="x", units=[Unit(id="u1", title="u", lessons=[
        LessonSpec(id="u1-l1", title="a", claim_ids=[claim.id]), LessonSpec(id="u1-l2", title="b", claim_ids=[claim.id])])])
    f.teaching()
    assert asked.count("lesson") == 3                  # the rewrite ran
    assert set(asked) == set(LESSON_ROLES), asked


def test_spend_splits_into_research_plan_and_lessons():
    b = Budget(model=SONNET, limit_usd=10.0, by_role={
        "intake": Usage(1, 0, 0, 0.01), "extract": Usage(1, 0, 0, 1.20), "curriculum": Usage(1, 0, 0, 0.08),
        "review_curriculum": Usage(1, 0, 0, 0.02), "lesson": Usage(1, 0, 0, 0.50), "review_lesson": Usage(1, 0, 0, 0.10)})
    assert [round(x, 2) for x in b.spent_on()] == [1.21, 0.10, 0.60]


def test_the_lessons_left_are_played_forward_at_the_model_each_would_get():
    # $0.45 a lesson on Sonnet, $0.15 on Haiku. The switch falls at 7.05 + 0.5 x 2.95 = $8.525
    b = Budget(model=SONNET, limit_usd=10.0, cheap_model=HAIKU, switch_at=0.5, by_role={
        "extract": Usage(1, 0, 0, 7.05), "lesson": Usage(2, 300_000, 0, 0.90)})
    ahead = b.projection(2, 23)
    # lessons 3 and 4 on Sonnet reach $8.85, then Haiku from lesson 5 until lesson 12 passes $10
    assert ahead.cheap_from == 5 and ahead.stop_at == 12 and ahead.lesson_usd == pytest.approx(0.45)
    # all 21 left on Sonnet, plus the lesson the cap interrupts, which is written twice
    assert ahead.finish_usd == pytest.approx(7.95 + 22 * 0.45)
    # output tokens are averaged per lesson too: 30,000 out is $0.45 on Sonnet, $0.15 on Haiku
    out = Budget(model=SONNET, limit_usd=10.0, cheap_model=HAIKU, switch_at=0.5, by_role={
        "extract": Usage(1, 0, 0, 7.05), "lesson": Usage(2, 0, 60_000, 0.90)})
    assert out.projection(2, 23)[1:3] == (5, 12)

    roomy = Budget(model=SONNET, limit_usd=10.0, cheap_model=HAIKU, by_role={
        "extract": Usage(1, 0, 0, 2.00), "curriculum": Usage(1, 0, 0, 0.20), "lesson": Usage(2, 100_000, 0, 0.30)})
    assert roomy.projection(2, 4) == pytest.approx((2.80, None, None, 0.15, 2.95))  # $2.50 now, 2 more at $0.15


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


def test_an_empty_budget_means_the_default_cap_not_no_cap(monkeypatch):
    # an empty LEARNING_BUDGET_USD once removed the cap altogether
    monkeypatch.setenv("LEARNING_BUDGET_USD", "")
    assert Budget.from_env(SONNET).limit_usd == float(Budget.DEFAULT_LIMIT)
    monkeypatch.setenv("LEARNING_BUDGET_USD", "$7.50")
    assert Budget.from_env(SONNET).limit_usd == 7.5


def test_a_budget_of_infinity_is_not_a_budget():
    from learning.budget import dollars, fraction

    for bad in ("inf", "Infinity", "1e400", "0", "-3", "five"):
        with pytest.raises(ValueError):
            dollars(bad)
    assert fraction("0") == 0  # the cheaper model from the start


def test_a_price_change_applies_from_its_day():
    # the meter would have counted half of what Gemini charges from 2027
    from datetime import date

    assert price_for("gemini-3.8-flash", date(2026, 12, 31)) == (0.75, 3.75)
    assert price_for("gemini-3.8-flash", date(2027, 1, 1)) == (1.50, 7.50)
    assert price_for("gemini-3.5-flash-lite", date(2027, 6, 1)) == (0.30, 2.50)


def test_spend_saved_without_dollars_is_priced_as_of_when_it_was_saved(tmp_path):
    # pricing it at today's rate would have doubled an old Gemini build's spend from 2027
    import json
    import os
    from datetime import datetime

    from learning.cli import load_spend

    f = tmp_path / "spend.json"
    f.write_text(json.dumps({"lesson": [1, 1_000_000, 0]}))
    saved = datetime(2026, 12, 1).timestamp()
    os.utime(f, (saved, saved))
    meter = Budget(model="gemini-3.8-flash")
    load_spend(meter, f)
    assert meter.spent_usd == 0.75

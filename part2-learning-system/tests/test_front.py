"""`learn`, the way a learner uses it: a conversation, a course folder, and commands that work
from anywhere inside it. The brain and the pipeline are stand-ins, and everything else is real.
"""

from __future__ import annotations

import json
import logging
import stat

import pytest

from impl.strands.telemetry import BudgetExceeded, Meter
from learning import course_dir, front
from learning.flow import DONE
from learning.model import LearnerProfile
from test_learner import course

QUESTIONS = ["Where are you starting from?", "What do you want to build?"]


class Brain:
    """Asks two questions the first time, then has what it needs."""

    def __init__(self):
        self.intakes: list[str] = []

    def ask(self, name, instruction, prompt, schema, research=False):
        assert name == "intake", f"only the intake should reach the brain here, not {name}"
        self.intakes.append(prompt)
        first = len(self.intakes) == 1
        return LearnerProfile(subject="TypeScript", goal="build a web app", subject_is_clear=True,
                              questions=QUESTIONS if first else [])


def pipeline(fail_with: Exception | None = None):
    def run(flow):
        flow.say("Writing lesson 1 of 1: Your first resource")
        logging.getLogger("learning").info("u1-l1 attempt 1: exercise_does_not_work")
        if fail_with is not None:
            raise fail_with
        c = course()
        flow.board.knowledge, flow.board.curriculum = c.knowledge, c.curriculum
        flow.board.lessons = {l.id: l for l in c.lessons}
        flow.board.route = DONE
    return run


@pytest.fixture
def learner(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARN_HOME", str(tmp_path / "courses"))
    monkeypatch.setenv("LEARN_CONFIG", str(tmp_path / "config" / "env"))
    brain = Brain()

    def build(request, answers=("I know JavaScript", "a small web app"), fail_with=None):
        said, replies = [], iter(answers)
        engine = front.Engine("adk", "m", lambda meter: brain, Meter(), pipeline(fail_with), BudgetExceeded)
        code = front.build(request, engine, ask=lambda _: next(replies), say=said.append)
        return code, "\n".join(said)

    build.brain, build.home = brain, tmp_path / "courses"
    return build


def test_a_course_is_built_from_a_conversation(learner, capfd):
    code, screen = learner("I want to learn TypeScript")
    terminal = capfd.readouterr()
    assert code == 0
    assert "A few questions first" in screen and QUESTIONS[0] in screen
    assert "They answered: I know JavaScript" in learner.brain.intakes[1]   # asked here, not re-run with a flag
    assert "  Writing lesson 1 of 1" in screen                              # progress, in plain words
    assert (learner.home / "typescript" / "course.json").is_file()
    assert "Your course is ready" in screen and "learn next" in screen
    # the details go to the build's log, and none of it reaches the terminal
    assert "attempt 1" in next(learner.home.glob(".builds/*/build.log")).read_text()
    assert "attempt 1" not in terminal.out + terminal.err + screen


def test_the_same_request_picks_up_where_it_stopped(learner):
    code, _ = learner("I want to learn TypeScript", fail_with=RuntimeError("the network went away"))
    assert code == 1 and not (learner.home / "typescript").exists()
    code, screen = learner("  i want to learn   TypeScript ", answers=())
    assert code == 0
    assert len(learner.brain.intakes) == 2 and "Picking up your TypeScript course" in screen
    assert len(list(learner.home.glob(".builds/*"))) == 1


def test_a_different_request_is_a_new_course_and_names_never_collide(learner):
    learner("I want to learn TypeScript")
    learner.brain.intakes.clear()
    learner("TypeScript for backend work please")
    assert (learner.home / "typescript").is_dir() and (learner.home / "typescript-2").is_dir()


def test_a_run_that_hits_the_cap_says_how_to_carry_on(learner):
    stopped = RuntimeError("wrapped")
    stopped.__cause__ = BudgetExceeded("spent $6.01 of a $6.00 cap")
    code, screen = learner("Rust, please", fail_with=stopped)
    assert code == 2 and "spending cap" in screen and "LEARNING_BUDGET_USD" in screen


def test_course_commands_work_from_anywhere_inside_a_course(tmp_path, monkeypatch, capfd):
    root = course_dir.write(course(), tmp_path / "course")
    monkeypatch.chdir(next((root / "units").glob("*/u1-l1-*")) / "exercise")
    assert front.main(["next"]) == 0
    out = capfd.readouterr().out
    assert "Your first resource" in out and "then: learn check" in out


def test_course_commands_outside_a_course_say_so(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    said = []
    assert front.in_course(["next"], say=said.append) == 1
    assert "not in a course folder" in said[0]


def test_a_key_is_asked_for_once_and_kept_private(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARN_CONFIG", str(tmp_path / "env"))
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("LEARN_ENGINE", raising=False)
    monkeypatch.setattr(front, "aws_credentials", lambda: False)
    said = []
    assert front.pick_engine(None, lambda _: "AIza-test-key", said.append) == "adk"
    saved = tmp_path / "env"
    assert "GOOGLE_API_KEY=AIza-test-key" in saved.read_text()
    assert stat.S_IMODE(saved.stat().st_mode) == 0o600

    monkeypatch.delenv("GOOGLE_API_KEY")
    front.load_config()

    def never(_):
        raise AssertionError("asked for the key again")

    assert front.pick_engine(None, never, said.append) == "adk"


def test_the_engine_follows_the_keys_you_have(monkeypatch):
    monkeypatch.delenv("LEARN_ENGINE", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "k")
    monkeypatch.setattr(front, "aws_credentials", lambda: True)
    assert front.pick_engine(None, input, print) == "adk"
    monkeypatch.delenv("GOOGLE_API_KEY")
    assert front.pick_engine(None, input, print) == "strands"
    monkeypatch.setattr(front, "aws_credentials", lambda: False)
    said = []
    assert front.pick_engine("strands", input, said.append) is None and "AWS credentials" in said[0]


def test_learn_on_its_own_lists_courses_and_how_far_you_are(learner):
    learner("I want to learn TypeScript")
    progress = learner.home / "typescript" / ".learn" / "progress.json"
    progress.write_text(json.dumps({"done": {"u1-l1": {"exercise": 1, "quiz": 1}}, "hints": {},
                                    "solutions": [], "review": {}}))
    learner("Rust, please", fail_with=RuntimeError("stopped"))
    said = []
    front.list_courses(say=said.append)
    screen = "\n".join(said)
    assert "typescript" in screen and "1 of 1 lessons done" in screen
    assert 'learn "Rust, please"' in screen and "still building" in screen


def test_a_course_built_by_an_older_version_gets_todays_learn(tmp_path, monkeypatch, capfd):
    # every course folder carries a copy of learn.py, frozen when it was built
    root = course_dir.write(course(), tmp_path / "course")
    (root / "learn.py").write_text('print("an old learn.py")\n')
    monkeypatch.chdir(root)
    assert front.main(["next"]) == 0
    out = capfd.readouterr().out
    assert "an old learn.py" not in out and "then: learn check" in out


def test_the_learner_is_told_the_cap_and_the_switch_and_when_it_happens(learner, monkeypatch):
    def pipeline_that_spends(flow):
        engine_meter.charge("lesson", 2_000_000, 0)   # $6 of a $10 cap, past the halfway switch
        engine_meter.current_model()
        pipeline()(flow)

    engine_meter = Meter(model="global.anthropic.claude-sonnet-4-6", limit_usd=10.0,
                         cheap_model="global.anthropic.claude-haiku-4-5-20251001-v1:0")
    said = []
    engine = front.Engine("strands", "m", lambda meter: learner.brain, engine_meter, pipeline_that_spends,
                          BudgetExceeded)
    replies = iter(["JavaScript", "a web app"])
    assert front.build("I want to learn TypeScript", engine, ask=lambda _: next(replies), say=said.append) == 0
    screen = "\n".join(said)
    assert "Spending cap: $10.00" in screen and "At $5.00 it switches to a cheaper model" in screen
    assert "the rest of this course is written by a cheaper model" in screen

"""`learn`, the way a learner uses it: a conversation, a course folder, and commands that work
from anywhere inside it. The brain and the pipeline are stand-ins, and everything else is real.
"""

from __future__ import annotations

import json
import logging
import os
import stat
import subprocess
import sys
import time
from pathlib import Path

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

    def build(request, answers=("I know JavaScript", "a small web app"), fail_with=None, fresh=False):
        said, replies = [], iter(answers)
        engine = front.Engine("adk", "m", lambda meter: brain, Meter(), pipeline(fail_with), BudgetExceeded)
        code = front.build(request, engine, ask=lambda _: next(replies), say=said.append, fresh=fresh)
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
    assert "(stopped partway)" in screen and "learn --engine adk 'Rust, please'   to carry on" in screen


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
    # research and the plan set the switch point, so a new build gives the rule, not a number
    assert "Spending cap: $10.00" in screen and "Once lessons have used 50% of what's left after research" in screen
    assert "the rest of this course is written by a cheaper model" in screen


@pytest.mark.parametrize("lessons, shown", [
    (0.5, "Spent so far: $6.50. At $8.00 a cheaper model"),
    (2.5, "Spent so far: $8.50.\n"),  # past the point: the meter says so at the next call
])
def test_once_lessons_have_spent_the_start_line_gives_the_switch_point(learner, lessons, shown):
    from learning.budget import Usage

    meter = Meter(model="global.anthropic.claude-sonnet-4-6", limit_usd=10.0,
                  cheap_model="global.anthropic.claude-haiku-4-5-20251001-v1:0",
                  by_role={"extract": Usage(1, 0, 0, 6.0), "lesson": Usage(1, 0, 0, lessons)})
    said = []
    engine = front.Engine("strands", "m", lambda meter: learner.brain, meter, pipeline(), BudgetExceeded)
    replies = iter(["JavaScript", "a web app"])
    assert front.build("I want to learn TypeScript", engine, ask=lambda _: next(replies), say=said.append) == 0
    screen = "\n".join(said)
    assert shown in screen and screen.count("cheaper model") == (1 if lessons < 2 else 0)


def test_a_spend_file_that_cant_be_read_stops_the_build_and_is_left_alone(learner):
    # starting the count from $0 would let a resumed build spend past its cap
    learner("I want to learn TypeScript", fail_with=RuntimeError("UNAVAILABLE 503"))
    spend = next(learner.home.glob(".builds/*/spend.json"))
    spend.write_text('{"lesson": [1, 2')
    code, screen = learner("I want to learn TypeScript")
    assert code == 1 and "can't read" in screen and "Delete that file" in screen
    assert spend.read_text() == '{"lesson": [1, 2'


def test_a_stop_while_a_build_folder_is_made_doesnt_break_the_next_run(learner, monkeypatch):
    # a stop between the two files new_build writes once made every later run of that request crash
    real, written = Path.write_text, []

    def stop_at_the_second(self, *args, **kwargs):
        if self.name in ("request.txt", "engine.txt"):
            written.append(self.name)
            if len(written) == 2:
                raise KeyboardInterrupt
        return real(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", stop_at_the_second)
    with pytest.raises(KeyboardInterrupt):
        learner("I want to learn TypeScript")
    monkeypatch.setattr(Path, "write_text", real)
    code, screen = learner("I want to learn TypeScript")
    assert code == 0 and "Your course is ready" in screen


def test_running_a_finished_request_again_keeps_the_learners_work(learner):
    # it once wrote the course again over the old one, deleting progress, reports and exercise edits
    learner("I want to learn TypeScript")
    folder = learner.home / "typescript"
    (folder / ".learn" / "progress.json").write_text('{"done": {}}')
    mine = next(p for p in folder.glob("units/*/*/exercise/**/*") if p.is_file())
    mine.write_text("my own work")
    asked = len(learner.brain.intakes)
    code, screen = learner("I want to learn TypeScript")
    assert code == 0 and "already built" in screen and "learn --fresh" in screen
    assert len(learner.brain.intakes) == asked                     # nothing was asked of the model
    assert (folder / ".learn" / "progress.json").read_text() == '{"done": {}}'
    assert mine.read_text() == "my own work"


def test_fresh_builds_a_new_copy_and_leaves_the_old_one_alone(learner):
    learner("I want to learn TypeScript")
    old = learner.home / "typescript"
    (old / ".learn" / "progress.json").write_text('{"done": {}}')
    code, screen = learner("I want to learn TypeScript", fresh=True)
    assert code == 0 and (learner.home / "typescript-2" / "course.json").is_file()
    assert (old / ".learn" / "progress.json").read_text() == '{"done": {}}'
    code, screen = learner("I want to learn TypeScript")             # a plain rerun finds the newest copy
    assert "already built" in screen and "typescript-2" in screen


def test_a_quiz_answer_outside_its_options_leaves_the_question_out(tmp_path):
    # it once crashed the write after the build was paid for, and every rerun crashed the same way
    c = course()
    lesson = c.lessons[0]
    broken = lesson.quiz[0].model_copy(update={"answer": len(lesson.quiz[0].options)})
    c.lessons[0] = lesson.model_copy(update={"quiz": [broken] + lesson.quiz[1:]})
    root = course_dir.write(c, tmp_path / "course")
    quiz = json.loads(next(root.glob(f"units/*/{lesson.id}-*/quiz.json")).read_text())
    assert len(quiz) == len(lesson.quiz) - 1


def test_writing_a_course_again_keeps_what_the_learner_changed(tmp_path):
    root = course_dir.write(course(), tmp_path / "course")
    mine = next(p for p in root.glob("units/*/*/exercise/**/*") if p.is_file())
    mine.write_text("my own work")
    (root / ".learn" / "progress.json").write_text('{"done": {}}')
    course_dir.write(course(), root)
    assert mine.read_text() == "my own work"
    assert (root / ".learn" / "progress.json").read_text() == '{"done": {}}'


def test_a_finished_course_whose_folder_was_deleted_is_written_again_for_free(learner):
    import shutil

    learner("I want to learn TypeScript")
    shutil.rmtree(learner.home / "typescript")
    asked = len(learner.brain.intakes)
    code, screen = learner("I want to learn TypeScript")
    assert code == 0 and (learner.home / "typescript" / "course.json").is_file()
    assert len(learner.brain.intakes) == asked and "writing it again" in screen


def test_a_course_that_cant_be_written_is_explained_and_not_marked_finished(learner, monkeypatch):
    def disk_full(*args, **kwargs):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(course_dir, "write", disk_full)
    code, screen = learner("I want to learn TypeScript")
    assert code == 1 and "No space left on device" in screen and "build.log" in screen
    assert not list(learner.home.glob(".builds/*/finished"))


def test_a_disk_error_while_writing_exercise_files_is_not_hidden(tmp_path, monkeypatch):
    def denied(*args, **kwargs):
        raise PermissionError("denied")

    monkeypatch.setattr(course_dir, "write_atomic", denied)
    with pytest.raises(PermissionError):
        course_dir.write(course(), tmp_path / "course")


def test_clashing_exercise_paths_are_skipped_and_logged_in_either_order(tmp_path, caplog):
    for n, order in enumerate((["src/app.py", "src"], ["src", "src/app.py"])):
        caplog.clear()
        for path in order:
            course_dir.put(tmp_path / str(n) / path, "x", keep=True)
        assert "skipped" in caplog.text


def test_the_writer_never_puts_a_file_outside_the_course(tmp_path):
    from learning.model import CourseFile

    c = course()
    lesson = c.lessons[0]
    outside = tmp_path / "outside.txt"
    bad = [CourseFile(path=str(outside), content="x"), CourseFile(path="../../escaped.txt", content="x")]
    ex = lesson.exercise.model_copy(update={"starter": lesson.exercise.starter + bad})
    c.lessons[0] = lesson.model_copy(update={"exercise": ex})
    course_dir.write(c, tmp_path / "course")
    assert not outside.exists() and not (tmp_path / "escaped.txt").exists()


def test_unit_and_lesson_ids_from_the_model_land_inside_the_course(tmp_path):
    c = course()
    unit = c.curriculum.units[0]
    spec = unit.lessons[0].model_copy(update={"id": "../../../sneaky"})
    c.curriculum.units[0] = unit.model_copy(update={"id": "../../evil", "lessons": [spec] + unit.lessons[1:]})
    c.lessons[0] = c.lessons[0].model_copy(update={"id": "../../../sneaky"})
    root = course_dir.write(c, tmp_path / "course")
    assert not list(tmp_path.glob("evil*")) and not list(tmp_path.glob("sneaky*"))
    assert list(root.glob("units/evil-*/sneaky-*/README.md"))


def test_a_typo_inside_a_course_suggests_the_command_and_builds_nothing(tmp_path, monkeypatch, capfd):
    # `learn chekc` once started a paid build about "chekc"
    root = course_dir.write(course(), tmp_path / "course")
    monkeypatch.chdir(root)
    monkeypatch.setattr(front, "build", lambda *a, **k: pytest.fail("a typo started a build"))
    assert front.main(["chekc"]) == 2
    assert "Did you mean `learn check`" in capfd.readouterr().out
    for word in ("help", "stop"):
        assert front.main([word]) == 0


def test_outside_a_course_a_request_that_starts_with_a_command_word_is_a_request(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LEARN_CONFIG", str(tmp_path / "env"))
    monkeypatch.setenv("GOOGLE_API_KEY", "not-a-real-key")
    asked = []
    monkeypatch.setattr(front, "load_engine", lambda name: name)
    monkeypatch.setattr(front, "build", lambda request, engine, **k: asked.append(request) or 0)
    assert front.main(["next", "js", "app", "router"]) == 0
    assert asked == ["next js app router"]


def test_settings_that_cant_be_used_are_named_before_anything_is_spent(tmp_path, monkeypatch, capfd):
    config = tmp_path / "env"
    config.write_text("LEARNING_BUDGET_USD=five dollars\nLEARNING_BUDGET=3\nLEARN_SWITCH_AT=0.6  # a bit later\n")
    monkeypatch.setenv("LEARN_CONFIG", str(config))
    for name in ("LEARNING_BUDGET_USD", "LEARN_SWITCH_AT", "LEARN_ENGINE", "LEARNING_BUDGET"):
        monkeypatch.setenv(name, "x")  # so the test's teardown removes what load_config sets
        monkeypatch.delenv(name)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(front, "pick_engine", lambda *a: pytest.fail("got as far as picking an engine"))
    assert front.main(["I want to learn Rust"]) == 2
    out = capfd.readouterr().out
    assert "LEARNING_BUDGET_USD=five dollars can't be used" in out
    assert "Did you mean LEARNING_BUDGET_USD" in out
    assert "LEARN_SWITCH_AT" not in out   # the comment after 0.6 is fine


def test_a_missing_key_with_no_terminal_says_where_to_put_it(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARN_CONFIG", str(tmp_path / "env"))
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("LEARN_ENGINE", raising=False)
    monkeypatch.setattr(front, "aws_credentials", lambda: False)

    def no_terminal(prompt):
        raise EOFError

    said = []
    assert front.pick_engine(None, no_terminal, said.append) is None
    assert "GOOGLE_API_KEY=your-key" in said[-1] and "Nothing was built" in said[-1]


def test_outside_a_course_a_lesson_id_or_a_report_is_still_a_course_command(tmp_path, monkeypatch):
    # turning `learn next js app router` into a request once made `learn check u1-l1` a paid build too
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(front, "build", lambda *a, **k: pytest.fail("a course command started a build"))
    for argv in (["check", "u1-l1"], ["check", "U1-L1"], ["report", "question 2 has two right answers"], ["next"]):
        assert front.main(argv) == 1
    monkeypatch.setenv("LEARN_HOME", str(tmp_path / "courses"))
    assert front.main(["  "]) == 0   # an empty request lists courses rather than building one


def test_only_real_slips_count_as_typos():
    for typo in ("chekc", "quizz", "chek", "Next", "reveiw"):
        assert any(front.slip(typo, c) for c in front.COURSE_COMMANDS), typo
    for topic in ("nest", "text", "mint", "quic", "nextjs", "repo", "rest", "chess"):
        assert not any(front.slip(topic, c) for c in front.COURSE_COMMANDS), topic


def test_a_folder_name_with_a_hash_in_it_is_kept_whole(tmp_path, monkeypatch):
    config = tmp_path / "env"
    config.write_text("LEARN_HOME=/Users/me/My Courses #2\n")
    monkeypatch.setenv("LEARN_CONFIG", str(config))
    monkeypatch.setenv("LEARN_HOME", "x")  # so the test's teardown removes what load_config sets
    monkeypatch.delenv("LEARN_HOME")
    front.load_config()
    assert os.environ["LEARN_HOME"] == "/Users/me/My Courses #2"


def test_a_misspelled_budget_stops_the_build_and_another_misspelling_only_warns(tmp_path, monkeypatch, capfd):
    config = tmp_path / "env"
    monkeypatch.setenv("LEARN_CONFIG", str(config))
    for name in ("LEARNING_BUDGET_USD", "LEARNING_BUDGET", "XAI_API_KEY"):
        monkeypatch.setenv(name, "x")
        monkeypatch.delenv(name)
    monkeypatch.chdir(tmp_path)
    config.write_text("LEARNING_BUDGET=3\n")
    monkeypatch.setattr(front, "pick_engine", lambda *a: pytest.fail("a misspelled budget got as far as a build"))
    assert front.main(["I want to learn Rust"]) == 2
    assert "Did you mean LEARNING_BUDGET_USD" in capfd.readouterr().out
    config.write_text("XAI_API_KEY=not-a-real-key\n")
    monkeypatch.setattr(front, "pick_engine", lambda *a: None)  # stops right after the settings check
    assert front.main(["I want to learn Rust"]) == 1


def test_inside_a_course_a_real_topic_builds_and_a_command_after_a_flag_runs(tmp_path, monkeypatch):
    root = course_dir.write(course(), tmp_path / "course")
    monkeypatch.chdir(root)
    monkeypatch.setenv("LEARN_CONFIG", str(tmp_path / "env"))
    built, ran = [], []
    monkeypatch.setattr(front, "pick_engine", lambda *a: "adk")
    monkeypatch.setattr(front, "load_engine", lambda name: name)
    monkeypatch.setattr(front, "build", lambda request, engine, **k: built.append(request) or 0)
    monkeypatch.setattr(front, "in_course", lambda argv, say=print: ran.append(argv) or 0)
    assert front.main(["nest"]) == 0 and built == ["nest"]           # one letter off a command is a topic
    assert front.main(["--fresh", "report", "q2 is wrong"]) == 0 and ran == [["report", "q2 is wrong"]]


def test_a_key_never_reaches_the_build_log_or_the_screen(learner, monkeypatch):
    # an error message carrying a key went to build.log, and a search key rode in on a request URL
    key, search_key = "AIza-not-a-real-key-123456", "exa-not-a-real-key-654321"
    monkeypatch.setenv("GOOGLE_API_KEY", key)

    def run(flow):
        logging.getLogger("httpx2").info("HTTP Request: POST https://mcp.example/?k=" + search_key)
        logging.getLogger("learning").info("calling with " + key)
        raise RuntimeError(f"401 for key {key}")

    said = []
    engine = front.Engine("adk", "m", lambda meter: learner.brain, Meter(), run, BudgetExceeded)
    code = front.build("I want to learn TypeScript", engine, ask=lambda _: "x", say=said.append)
    log = next(learner.home.glob(".builds/*/build.log")).read_text()
    assert code == 1 and key not in "\n".join(said) and key not in log and "[hidden]" in log
    assert search_key not in log   # httpx2's request lines are kept out of the log


def test_build_files_are_for_you_alone(learner):
    learner("I want to learn TypeScript")
    for folder in (learner.home / ".builds", next(learner.home.glob(".builds/*")), learner.home / "typescript"):
        assert stat.S_IMODE(folder.stat().st_mode) == 0o700, folder


def test_builds_from_before_are_made_private_too(learner):
    # .builds was only made private when a new build started, so older builds stayed readable
    learner("I want to learn TypeScript")
    builds, course = learner.home / ".builds", learner.home / "typescript"
    builds.chmod(0o755), course.chmod(0o755)
    learner("I want to learn TypeScript")            # already built: no new build folder is made
    assert stat.S_IMODE(builds.stat().st_mode) == 0o700 and stat.S_IMODE(course.stat().st_mode) == 0o700


def test_the_spending_cap_message_hides_secrets_too(learner, monkeypatch):
    key = "AIza-not-a-real-key-123456"
    monkeypatch.setenv("GOOGLE_API_KEY", key)
    code, screen = learner("I want to learn TypeScript", fail_with=BudgetExceeded(f"over the cap with {key}"))
    assert code == 2 and key not in screen and "[hidden]" in screen


def test_a_symlinked_config_keeps_its_link(tmp_path, monkeypatch):
    real = tmp_path / "dotfiles" / "env"
    real.parent.mkdir()
    real.write_text("LEARN_ENGINE=adk\n")
    link = tmp_path / "config" / "env"
    link.parent.mkdir()
    link.symlink_to(real)
    monkeypatch.setenv("LEARN_CONFIG", str(link))
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    front.save_config("GOOGLE_API_KEY", "AIza-not-a-real-key-123456")
    assert link.is_symlink() and "AIza" in real.read_text()
    assert not list(real.parent.glob(".*.tmp"))


def test_a_key_saved_into_a_readable_file_cant_be_read_through_it(tmp_path, monkeypatch):
    config = tmp_path / "env"
    config.write_text("LEARN_ENGINE=adk\n")
    config.chmod(0o644)
    monkeypatch.setenv("LEARN_CONFIG", str(config))
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    already_open = open(config)
    front.save_config("GOOGLE_API_KEY", "AIza-not-a-real-key-123456")
    assert "AIza" not in already_open.read() and "AIza" in config.read_text()
    assert stat.S_IMODE(config.stat().st_mode) == 0o600
    already_open.close()


SONNET, HAIKU = "global.anthropic.claude-sonnet-4-6", "global.anthropic.claude-haiku-4-5-20251001-v1:0"


def test_spend_shows_when_half_the_lessons_are_written_and_when_all_are():
    from learning.budget import Usage

    # $0.30 a lesson on Sonnet, $0.10 on Haiku. The switch falls at 6 + 0.5 x 4 = $8
    m = Meter(model=SONNET, limit_usd=10.0, cheap_model=HAIKU,
              by_role={"extract": Usage(1, 0, 0, 6.0), "lesson": Usage(5, 500_000, 0, 1.5)})
    # warned, so only the two milestones speak: this spend at lesson 1 would be headed for the cap
    assert [n for n in range(1, 11) if front.spend_line(m, n, 10, warned=True)] == [5, 10]
    assert [n for n in range(1, 14) if front.spend_line(m, n, 13, warned=True)] == [7, 13]  # half of 13 rounds up
    assert front.spend_line(m, 5, 10) == (
        "Halfway: 5 of 10 lessons written. Spent about $7.50 of your $10.00 cap: research $6.00, course plan $0.00, "
        "lessons $1.50 (about $0.30 each). The 5 left should cost about $0.90, so about $8.40 in all. "
        f"From about lesson 8, a cheaper model ({HAIKU}) writes the rest.")
    assert front.spend_line(m, 10, 10).startswith("All 10 lessons written. Spent about $7.50 of your $10.00 cap")
    assert front.spend_line(m, 10, 10).endswith("Nothing more will be spent.")
    assert front.spend_line(m, 1, 1).startswith("The lesson is written.")  # one lesson is all of them
    assert "each" not in front.spend_line(m, 1, 1)
    small = Meter(model=SONNET, limit_usd=10.0, cheap_model=HAIKU, by_role={"lesson": Usage(1, 100_000, 0, 0.3)})
    assert "The last one should cost about $0.30, so about $0.60 in all." in front.spend_line(small, 1, 2)

    # once switched, the switch line has already said so
    switched = Meter(model=SONNET, limit_usd=10.0, cheap_model=HAIKU,
                     by_role={"extract": Usage(1, 0, 0, 7.0), "lesson": Usage(5, 500_000, 0, 1.5)})
    assert "so about $9.00 in all" in front.spend_line(switched, 5, 10)
    assert "cheaper model" not in front.spend_line(switched, 5, 10)


def test_a_build_headed_for_the_cap_is_told_what_cap_would_finish_it(learner):
    from learning.budget import Usage

    m = Meter(model=SONNET, limit_usd=10.0, cheap_model=None,
              by_role={"extract": Usage(1, 0, 0, 7.0), "lesson": Usage(5, 750_000, 0, 2.25)})
    line = front.spend_line(m, 5, 10)
    # $9.25 now, $0.45 a lesson: lesson 7 passes $10. All 5 left on Sonnet and the one the cap
    # interrupts comes to $11.95
    assert "the cap stops the build around lesson 7" in line and "LEARNING_BUDGET_USD=12" in line
    assert "should cost" not in line

    # within one lesson of the cap counts too, and the cap it gives is always above the one there is
    close = Meter(model=SONNET, limit_usd=10.0, cheap_model=None,
                  by_role={"extract": Usage(1, 0, 0, 4.0), "lesson": Usage(4, 1_000_000, 0, 3.0)})
    line = front.spend_line(close, 4, 7)  # $7 now, 3 left at $0.75 ends at $9.25
    assert "may stop it near the end" in line and "LEARNING_BUDGET_USD=11" in line


def test_the_spend_lines_reach_the_screen_during_a_build(learner):
    def two_lessons(flow):
        for done in (1, 2):
            meter.charge("lesson", 100_000, 0)
            flow.on_lesson(done, 2)
        pipeline()(flow)

    meter = Meter(model=SONNET, limit_usd=10.0, cheap_model=HAIKU)
    said = []
    engine = front.Engine("strands", "m", lambda meter: learner.brain, meter, two_lessons, BudgetExceeded)
    replies = iter(["JavaScript", "a web app"])
    assert front.build("I want to learn TypeScript", engine, ask=lambda _: next(replies), say=said.append) == 0
    screen = "\n".join(said)
    assert "  Halfway: 1 of 2 lessons written. Spent about $0.30" in screen
    assert "  All 2 lessons written. Spent about $0.60" in screen


def test_a_build_headed_for_the_cap_is_told_before_halfway_and_only_once_between(learner):
    # a 23-lesson Strands course at $10 reached the cap at lesson 9, before its halfway line
    def lessons(flow):
        meter.charge("extract", 2_000_000, 0)          # $6 of research
        for done in range(1, 7):
            meter.charge("lesson", 300_000, 0)         # $0.90 a lesson, so lesson 5 passes $10
            flow.on_lesson(done, 6)
        pipeline()(flow)

    meter = Meter(model=SONNET, limit_usd=10.0, cheap_model=None)
    said = []
    engine = front.Engine("strands", "m", lambda meter: learner.brain, meter, lessons, BudgetExceeded)
    replies = iter(["JavaScript", "a web app"])
    assert front.build("I want to learn TypeScript", engine, ask=lambda _: next(replies), say=said.append) == 0
    screen = "\n".join(said)
    assert "  1 of 6 lessons written. Spent about $6.90" in screen and "around lesson 5" in screen
    assert "\n  To finish, set LEARNING_BUDGET_USD=13" in screen   # $6.90 + 6 x $0.90, on its own line
    assert "2 of 6 lessons" not in screen                          # told once between the milestones
    assert "Halfway: 3 of 6" in screen and screen.count("To finish") == 2


def test_a_halfway_line_without_advice_still_leaves_room_for_a_later_warning(learner):
    # lessons that grow after halfway can head for the cap, and that's worth hearing
    def lessons(flow):
        meter.charge("extract", 2_000_000, 0)          # $6 of research
        for done in range(1, 11):
            meter.charge("lesson", 100_000 if done <= 5 else 400_000, 0)  # $0.30, then $1.20
            flow.on_lesson(done, 10)
        pipeline()(flow)

    meter = Meter(model=SONNET, limit_usd=12.0, cheap_model=None)
    said = []
    engine = front.Engine("strands", "m", lambda meter: learner.brain, meter, lessons, BudgetExceeded)
    replies = iter(["JavaScript", "a web app"])
    assert front.build("I want to learn TypeScript", engine, ask=lambda _: next(replies), say=said.append) == 0
    before, after = "\n".join(said).split("Halfway: 5 of 10")
    assert "To finish" not in after.split("\n")[0]                  # halfway itself had nothing to warn about
    assert "  7 of 10 lessons written" in after and "To finish, set LEARNING_BUDGET_USD=" in after


def test_a_shared_course_cannot_swap_in_its_own_learn_commands(tmp_path, monkeypatch, capfd):
    # learn ran `python -m learning.learn_cli` from the course folder, so a learning/ folder there won
    root = course_dir.write(course(), tmp_path / "course")
    (root / "learning").mkdir()
    (root / "learning" / "__init__.py").write_text("")
    (root / "learning" / "learn_cli.py").write_text('print("SWAPPED IN")')
    monkeypatch.chdir(root)
    assert front.main(["status"]) == 0
    out = capfd.readouterr().out
    assert "SWAPPED IN" not in out and "u1-l1" in out


def test_the_end_of_a_build_says_to_work_in_the_editor(learner, monkeypatch, tmp_path):
    monkeypatch.setenv("LEARN_EDITOR", "none")
    code, screen = learner("I want to learn TypeScript")
    assert code == 0 and "Work through it in VS Code or Cursor" in screen and "code.visualstudio.com" not in screen

    (tmp_path / "bin").mkdir()
    (tmp_path / "bin" / "code").write_text("#!/bin/sh\n")
    (tmp_path / "bin" / "code").chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path / "bin") + os.pathsep + os.environ["PATH"])
    monkeypatch.delenv("LEARN_EDITOR")
    code, screen = learner("I want to learn TypeScript", fresh=True)
    assert "That opens the first lesson in VS Code" in screen and "VS Code's terminal" in screen


def test_learn_inside_a_course_takes_the_editor_from_the_config_and_nothing_else(tmp_path, monkeypatch):
    # LEARN_EDITOR=none in the config was ignored by learn next, while the build obeyed it
    root = course_dir.write(course(), tmp_path / "course")
    config = tmp_path / "env"
    config.write_text("LEARN_EDITOR=cursor\nGOOGLE_API_KEY=not-for-the-editor\n")
    monkeypatch.setenv("LEARN_CONFIG", str(config))
    monkeypatch.delenv("LEARN_EDITOR")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.chdir(root)
    seen = {}

    class Ran:
        def __init__(self, argv, cwd, env):
            seen.update(env)

        def wait(self):
            return 0

    monkeypatch.setattr(front.subprocess, "Popen", Ran)
    assert front.main(["next"]) == 0
    assert seen["LEARN_EDITOR"] == "cursor" and "GOOGLE_API_KEY" not in seen
    config.write_bytes(b"LEARN_EDITOR=\xff\xfe\n")                      # a config that can't be read stops nothing
    assert front.main(["status"]) == 0


def two_lesson_course():
    c = course()
    c.lessons.append(c.lessons[0].model_copy(update={"id": "u1-l2", "title": "Second"}))
    c.curriculum.units[0].lessons.append(c.curriculum.units[0].lessons[0].model_copy(update={"id": "u1-l2",
                                                                                        "title": "Second"}))
    return c


def test_each_lesson_is_there_to_work_on_as_soon_as_it_is_written(learner, tmp_path, monkeypatch):
    # lesson 1 was ready at minute 36 and sat unused until minute 73, when the folder was written
    seen = {}
    c = two_lesson_course()

    def lessons(flow, stop_after=None):
        seen["flow"] = flow
        note = learner.home / "typescript" / ".learn" / "building.json"
        if note.exists():  # a resumed build says it's running again, as this process, before it writes a lesson
            from learning import learn_cli

            seen["running_at_start"] = json.loads(note.read_text())["running"]
            before = json.loads(note.read_text())["updated"]
            time.sleep(0.01)
            seen["meter"].charge("lesson", 1, 0)                         # a model call is a heartbeat
            after = json.loads(note.read_text())
            seen["beat"] = after["updated"] > before and after["pid"] == os.getpid()
            monkeypatch.setattr(learn_cli, "ROOT", learner.home / "typescript")
            seen["notice"] = learn_cli.still_to_come()
        flow.board.knowledge, flow.board.curriculum = c.knowledge, c.curriculum
        for done, lesson in enumerate(c.lessons, 1):
            flow.board.lessons[lesson.id] = lesson
            flow.on_lesson(done, 2)
            folder = learner.home / "typescript"
            if done == 1:
                seen["lessons"] = json.loads((folder / ".learn" / "lessons.json").read_text())
                seen["note"] = json.loads((folder / ".learn" / "building.json").read_text())
                starter = next(folder.glob("units/*/u1-l1-*/exercise/main.tf"))
                starter.write_text("# my own work")                  # the learner starts while lesson 2 is written
            if done == stop_after:
                raise KeyboardInterrupt
        flow.board.route = DONE

    def build(stop_after=None):
        said = []
        seen["meter"] = Meter()
        engine = front.Engine("adk", "m", lambda meter: learner.brain, seen["meter"], lambda f: lessons(f, stop_after),
                              BudgetExceeded)
        replies = iter(["JavaScript", "a web app"])
        code = front.build("I want to learn TypeScript", engine, ask=lambda _: next(replies, ""), say=said.append)
        return code, "\n".join(said)

    code, screen = build(stop_after=1)
    folder = learner.home / "typescript"
    assert code == 130 and f"Lesson 1 is ready in {folder}: cd there and run learn next" in screen
    assert f"Lesson 1 is ready to start in {folder}" in screen          # said as soon as it was, during the build
    assert [l["id"] for l in seen["lessons"]] == ["u1-l1"] and seen["note"]["total"] == 2
    note = json.loads((folder / ".learn" / "building.json").read_text())
    assert note["running"] is False and note["request"] == "I want to learn TypeScript"

    # its process keeps the build: a worker still finishing after Ctrl-C mustn't share it with a new one
    build_dir = next(learner.home.glob(".builds/*"))
    probe = subprocess.run([sys.executable, "-c", "import fcntl, sys\n"
                            f"f = open({str(build_dir / 'running')!r}, 'a+')\n"
                            "try:\n    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)\nexcept BlockingIOError:\n"
                            "    sys.exit(3)"], timeout=30)
    assert sys.platform == "win32" or probe.returncode == 3

    # a stopped build's worker can still finish a lesson or make a call: neither changes the course
    seen["flow"].board.lessons["u1-l2"] = c.lessons[1]
    seen["flow"].on_lesson(2, 2)
    seen["meter"].charge("lesson", 1, 0)
    assert len(json.loads((folder / ".learn" / "lessons.json").read_text())) == 1
    assert json.loads((folder / ".learn" / "building.json").read_text())["running"] is False

    # the learner finishes what's there, and is told the rest is coming and how to get it
    (folder / ".learn" / "progress.json").write_text(json.dumps(
        {"done": {"u1-l1": {"exercise": 1, "quiz": 1}}, "hints": {}, "solutions": [], "review": {}}))
    told = subprocess.run([sys.executable, "learn.py", "next"], cwd=folder, capture_output=True, text=True)
    assert "Lesson 2 isn't written yet, and the build has stopped. To carry on, run: learn --engine adk " \
        "'I want to learn TypeScript'" in told.stderr
    said = []
    front.list_courses(say=said.append)
    assert "1 of 1 lessons done, 1 still to write" in "\n".join(said)

    note = folder / ".learn" / "building.json"                        # as if the stopped build was another process
    note.write_text(json.dumps({**json.loads(note.read_text()), "pid": 2 ** 22 + 12345}))
    code, screen = build()                                            # carrying on writes the rest
    assert seen["beat"] and "The build is on it now" in seen["notice"]
    assert code == 0 and not (folder / ".learn" / "building.json").exists() and seen["running_at_start"] is True
    assert [l["id"] for l in json.loads((folder / ".learn" / "lessons.json").read_text())] == ["u1-l1", "u1-l2"]
    assert next(folder.glob("units/*/u1-l1-*/exercise/main.tf")).read_text() == "# my own work"


@pytest.mark.skipif(sys.platform == "win32", reason="the stand-in holder uses fcntl")
def test_a_second_build_of_the_same_course_waits_for_the_first(learner):
    # nothing stopped two builds of one request at once, and each paid for the same lessons
    learner("I want to learn TypeScript", fail_with=RuntimeError("the network went away"))
    build = next(learner.home.glob(".builds/*"))
    front._HELD.pop(build / "running").close()                        # as if that build's process had ended
    holder = subprocess.Popen([sys.executable, "-c", "import fcntl, sys, time\n"
                               f"f = open({str(build / 'running')!r}, 'a+')\n"
                               "fcntl.flock(f, fcntl.LOCK_EX)\nprint('held', flush=True)\ntime.sleep(30)"],
                              stdout=subprocess.PIPE, text=True)
    try:
        assert holder.stdout.readline().strip() == "held"            # another build is running
        spend = (build / "spend.json").read_text()
        code, screen = learner("I want to learn TypeScript", answers=())
        assert code == 1 and "being built right now. learn shows how it's going, and learn stop stops it" in screen
        assert (build / "spend.json").read_text() == spend
        (build / "status.json").write_text(json.dumps({"line": "Writing lesson 3 of 14: Traits", "cap": 5.0}))
        (build / "spend.json").write_text(json.dumps({"lesson": [3, 100, 100, 1.25]}))
        said = []
        front.list_courses(say=said.append)
        listed = "\n".join(said)
        assert "(building now)" in listed and "Writing lesson 3 of 14: Traits. $1.25 spent of your $5.00 cap." in listed
    finally:
        holder.kill()
        holder.wait()
    code, screen = learner("I want to learn TypeScript", answers=())   # once it's gone, this one carries on
    assert code == 0


def test_the_writes_learn_reads_mid_build_are_whole_files(tmp_path, monkeypatch):
    written = []
    real = course_dir.write_atomic
    monkeypatch.setattr(course_dir, "write_atomic", lambda path, data: (written.append(Path(path).name), real(path, data)))
    course_dir.write(course(), tmp_path / "course")
    assert {"lessons.json", "quiz.json", "hints.json", "learn.py", "course.json"} <= set(written)


def test_a_file_system_without_locks_still_builds(learner, monkeypatch):
    import fcntl

    def no_locks(f, how):
        raise OSError(77, "No locks available")

    monkeypatch.setattr(fcntl, "flock", no_locks)
    code, _ = learner("I want to learn TypeScript")
    assert code == 0


@pytest.mark.skipif(sys.platform == "win32", reason="a signal to this process is POSIX")
def test_ctrl_c_stops_the_build_at_the_next_model_call(learner):
    # the stages run on worker threads, and Ctrl-C only reached the main one: the build ran on and kept paying
    import signal

    before, calls = signal.getsignal(signal.SIGINT), []

    def pipeline_with_a_ctrl_c(flow):
        os.kill(os.getpid(), signal.SIGINT)                          # the learner presses Ctrl-C mid-build
        time.sleep(0.05)
        for _ in range(3):
            meter.check()                                            # what every model call does first
            calls.append(1)

    meter = Meter()
    engine = front.Engine("adk", "m", lambda m: learner.brain, meter, pipeline_with_a_ctrl_c, BudgetExceeded)
    said, replies = [], iter(["JavaScript", "a web app"])
    code = front.build("I want to learn TypeScript", engine, ask=lambda _: next(replies), say=said.append)
    screen = "\n".join(said)
    assert code == 130 and calls == []
    assert "Stopping before the next model call" in screen and "Stopped. Nothing more will be spent" in screen
    assert signal.getsignal(signal.SIGINT) is before                 # put back once the build is over


CHILD = '''
import asyncio, sys, time
from learning import front
from learning.budget import Budget, BudgetExceeded
from learning.model import LearnerProfile

class Brain:
    def ask(self, *a, **k):
        return LearnerProfile(subject="Go", goal="build a tool", subject_is_clear=True)

meter = Budget(model="m")

def lessons():
    for i in range(20):  # a model call is 1 s: the meter's check, then the charge
        meter.check()
        time.sleep(1)
        meter.charge("lesson", 1000, 0)
        meter.by_role["lesson"].calls += 1  # counted after the charge, as Strands' hook does, so only a save keeps it
        print("charged", flush=True)

def run(flow):  # ADK's layout: asyncio.run, and the stage on a worker thread
    asyncio.run(asyncio.to_thread(lessons))

engine = front.Engine("adk", "m", lambda m: Brain(), meter, run, BudgetExceeded)
sys.exit(front.build("I want to learn Go", engine, ask=lambda _: ""))
'''


@pytest.mark.skipif(sys.platform == "win32", reason="signals to a child are POSIX")
@pytest.mark.parametrize("presses", [1, 2])
def test_ctrl_c_stops_a_build_whose_stages_run_on_a_worker_thread(tmp_path, presses):
    import signal

    script = tmp_path / "child.py"
    script.write_text(CHILD)
    env = {**os.environ, "LEARN_HOME": str(tmp_path / "courses"), "LEARN_CONFIG": str(tmp_path / "env"),
           "LEARN_EDITOR": "none"}
    p = subprocess.Popen([sys.executable, str(script)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                         env=env)
    try:
        time.sleep(2)
        for _ in range(presses):
            p.send_signal(signal.SIGINT)
            time.sleep(0.1)
        out, _ = p.communicate(timeout=30)
    finally:
        p.kill()
    assert p.returncode == 130 and "Traceback" not in out
    assert out.count("charged") < 6                                   # stopped well before the end
    if presses == 1:
        assert "Stopped. Nothing more will be spent" in out
    else:
        assert "The step that was running is lost" in out and "Nothing more will be spent" not in out
        build = next((tmp_path / "courses" / ".builds").glob("*"))
        assert json.loads((build / "spend.json").read_text())["lesson"][0] == out.count("charged")  # saved first


@pytest.mark.skipif(sys.platform == "win32", reason="the second process holds the lock with fcntl")
def test_learn_stop_stops_the_build_that_is_running(learner, capsys):
    # with the build in the background, there's no terminal to press Ctrl-C in
    learner("I want to learn TypeScript", fail_with=RuntimeError("the network went away"))
    build = next(learner.home.glob(".builds/*"))
    front._HELD.pop(build / "running").close()
    holder = subprocess.Popen([sys.executable, "-c", "import fcntl, time\n"
                               f"f = open({str(build / 'running')!r}, 'a+')\n"
                               "fcntl.flock(f, fcntl.LOCK_EX)\nprint('held', flush=True)\ntime.sleep(30)"],
                              stdout=subprocess.PIPE, text=True)
    try:
        assert holder.stdout.readline().strip() == "held"
        assert front.main(["stop"]) == 0
        assert (build / "stop").exists() and "Stopping the build of 'I want to learn TypeScript'" in capsys.readouterr().out
    finally:
        holder.kill()
        holder.wait()
    meter = Meter()
    meter.stop_file = build / "stop"
    with pytest.raises(BudgetExceeded):                                  # the build sees it at its next model call
        meter.check()
    code, screen = learner("I want to learn TypeScript", answers=())    # a stop asked for last time is done
    assert code == 0 and not (build / "stop").exists()
    assert front.main(["stop"]) == 0 and "Nothing is being built right now" in capsys.readouterr().out


SECOND_PRESS = """
import asyncio, sys, time
from learning import front, learn_cli
from learning.budget import Budget, BudgetExceeded
from learning.model import LearnerProfile

class Brain:
    def ask(self, *a, **k):
        return LearnerProfile(subject="Go", goal="build a tool", subject_is_clear=True)

meter = Budget(model="m")

def lessons(flow):
    flow.on_lesson(1, 20)  # a lesson is written, so the course says it's being built
    print("checking", flush=True)
    learn_cli._run([sys.executable, "-c", "import time; time.sleep(60)", sys.argv[1]], ".", {}, 600)  # an exercise

def run(flow):
    asyncio.run(asyncio.to_thread(lessons, flow))

engine = front.Engine("adk", "m", lambda m: Brain(), meter, run, BudgetExceeded)
sys.exit(front.build("I want to learn Go", engine, ask=lambda _: ""))
"""


@pytest.mark.skipif(sys.platform == "win32", reason="signals to a child are POSIX")
def test_a_second_ctrl_c_ends_the_tests_that_are_running_and_saves(tmp_path):
    import signal

    script = tmp_path / "child.py"
    script.write_text(SECOND_PRESS)
    env = {**os.environ, "LEARN_HOME": str(tmp_path / "courses"), "LEARN_CONFIG": str(tmp_path / "env"),
           "LEARN_EDITOR": "none"}
    tag = f"exercise-{os.getpid()}-{time.time_ns()}"                   # this test's own, so no other test's counts
    p = subprocess.Popen([sys.executable, str(script), tag], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, env=env, start_new_session=True)
    try:
        while "checking" not in p.stdout.readline():
            pass
        time.sleep(0.5)
        for _ in range(2):
            os.kill(p.pid, signal.SIGINT)
            time.sleep(0.1)
        out, _ = p.communicate(timeout=30)
    finally:
        p.kill()
    assert p.returncode == 130 and "Traceback" not in out
    assert "The step that was running is lost" in out and "Nothing more will be spent" not in out
    note = json.loads((tmp_path / "courses" / "go" / ".learn" / "building.json").read_text())
    assert note["running"] is False
    deadline = time.time() + 5                                          # killed, it goes in moments. Left, it lasts 60 s
    while subprocess.run(["pgrep", "-f", tag], capture_output=True).returncode == 0:
        assert time.time() < deadline, "the exercise's tests outlived the build"
        time.sleep(0.1)


SCRATCH_PRESS = """
import asyncio, sys, time
from learning import front, learn_cli
from learning.budget import Budget, BudgetExceeded
from learning.model import LearnerProfile

class Brain:
    def ask(self, *a, **k):
        return LearnerProfile(subject="Go", goal="build a tool", subject_is_clear=True)

def lessons(flow):
    with learn_cli.scratch("learn-home-") as d:
        print("folder", d, flush=True)
        learn_cli._run([sys.executable, "-c", "import time; time.sleep(60)"], ".", {}, 600)
        time.sleep(5)  # the build is gone before this check's own cleanup would run

def run(flow):
    asyncio.run(asyncio.to_thread(lessons, flow))

engine = front.Engine("adk", "m", lambda m: Brain(), Budget(model="m"), run, BudgetExceeded)
sys.exit(front.build("I want to learn Go", engine, ask=lambda _: ""))
"""


@pytest.mark.skipif(sys.platform == "win32", reason="signals to a child are POSIX")
def test_a_second_ctrl_c_removes_the_folders_of_the_check_that_was_running(tmp_path):
    import signal

    script = tmp_path / "child.py"
    script.write_text(SCRATCH_PRESS)
    env = {**os.environ, "LEARN_HOME": str(tmp_path / "courses"), "LEARN_CONFIG": str(tmp_path / "env"),
           "LEARN_EDITOR": "none"}
    p = subprocess.Popen([sys.executable, str(script)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                         env=env, start_new_session=True)
    try:
        line = ""
        while not line.startswith("folder"):
            line = p.stdout.readline()
        folder = Path(line.split(" ", 1)[1].strip())
        time.sleep(0.5)
        for _ in range(2):
            os.kill(p.pid, signal.SIGINT)
            time.sleep(0.1)
        out, _ = p.communicate(timeout=30)
    finally:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except OSError:
            pass
    assert p.returncode == 130 and not folder.exists()


@pytest.mark.parametrize("given", ["SIG_IGN", "SIG_DFL"])
def test_the_ctrl_c_handler_there_before_is_respected_and_put_back(tmp_path, monkeypatch, given):
    import signal

    from learning.model import LearnerProfile

    class Brain:
        def ask(self, *a, **k):
            return LearnerProfile(subject="Go", goal="build a tool", subject_is_clear=True)

    monkeypatch.setenv("LEARN_HOME", str(tmp_path / "courses"))
    monkeypatch.setenv("LEARN_CONFIG", str(tmp_path / "env"))
    handler, seen = getattr(signal, given), []

    def pipeline(flow):
        seen.append(signal.getsignal(signal.SIGINT))
        raise RuntimeError("the model went away")

    before = signal.signal(signal.SIGINT, handler)
    try:
        engine = front.Engine("adk", "m", lambda m: Brain(), Meter(), pipeline, BudgetExceeded)
        assert front.build("I want to learn Go", engine, ask=lambda _: "", say=lambda m: None) == 1
        after = signal.getsignal(signal.SIGINT)
    finally:
        signal.signal(signal.SIGINT, before)
    assert after is handler                                           # put back as it was
    if given == "SIG_IGN":
        assert seen == [signal.SIG_IGN]                               # nohup: an ignored Ctrl-C stays ignored


WAKES = """
import asyncio, sys, time
from learning import front, learn_cli
from learning.budget import Budget, BudgetExceeded
from learning.model import LearnerProfile

class Brain:
    def ask(self, *a, **k):
        return LearnerProfile(subject="Go", goal="build a tool", subject_is_clear=True)

real = learn_cli.abandon
def slow_abandon():  # the hard stop takes a moment to save, as a slow disk would make it
    real()
    time.sleep(0.5)
learn_cli.abandon = slow_abandon

def lessons(flow):
    print("checking", flush=True)
    learn_cli._run([sys.executable, "-c", "import time; time.sleep(60)", sys.argv[1]], ".", {}, 600)
    try:  # the next check, the way the checker goes on to it once this one returns
        with learn_cli.scratch("learn-home-") as d:
            print("second folder", d, flush=True)
    except learn_cli.Abandoned:
        print("scratch refused", flush=True)
    try:
        learn_cli._run([sys.executable, "-c", "pass"], ".", {}, 600)
        print("second run", flush=True)
    except learn_cli.Abandoned:
        print("run refused", flush=True)
    time.sleep(5)

def run(flow):
    asyncio.run(asyncio.to_thread(lessons, flow))

engine = front.Engine("adk", "m", lambda m: Brain(), Budget(model="m"), run, BudgetExceeded)
sys.exit(front.build("I want to learn Go", engine, ask=lambda _: ""))
"""

LATE = """
import os, signal, sys, time
from learning import front
from learning.budget import Budget, BudgetExceeded
from learning.model import LearnerProfile

class Brain:
    def ask(self, *a, **k):
        return LearnerProfile(subject="Go", goal="build a tool", subject_is_clear=True)

meter = Budget(model="m")

def pipeline(flow):
    os.kill(os.getpid(), signal.SIGINT)  # the first press
    time.sleep(0.1)
    meter.check()

def say(m):
    print(m, flush=True)
    if "Stopped. Nothing more" in m:
        os.kill(os.getpid(), signal.SIGINT)  # a second press, as the build reports how it ended
        time.sleep(0.2)

engine = front.Engine("adk", "m", lambda m: Brain(), meter, pipeline, BudgetExceeded)
sys.exit(front.build("I want to learn Go", engine, ask=lambda _: "", say=say))
"""


def stoppable_child(tmp_path, code, *args):
    script = tmp_path / "child.py"
    script.write_text(code)
    env = {**os.environ, "LEARN_HOME": str(tmp_path / "courses"), "LEARN_CONFIG": str(tmp_path / "env"),
           "LEARN_EDITOR": "none"}
    return subprocess.Popen([sys.executable, str(script), *args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, env=env, start_new_session=True)


@pytest.mark.skipif(sys.platform == "win32", reason="signals to a child are POSIX")
def test_a_check_that_wakes_after_a_hard_stop_starts_nothing(tmp_path):
    import signal

    p = stoppable_child(tmp_path, WAKES, f"wakes-{os.getpid()}-{time.time_ns()}")
    try:
        while "checking" not in p.stdout.readline():
            pass
        time.sleep(0.5)
        for _ in range(2):
            os.kill(p.pid, signal.SIGINT)
            time.sleep(0.1)
        out, _ = p.communicate(timeout=30)
    finally:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except OSError:
            pass
    assert p.returncode == 130, out
    assert "second folder" not in out and "second run" not in out, out


@pytest.mark.skipif(sys.platform == "win32", reason="signals to a child are POSIX")
def test_a_late_ctrl_c_while_the_build_reports_how_it_ended_does_nothing(tmp_path):
    import signal

    p = stoppable_child(tmp_path, LATE)
    try:
        out, _ = p.communicate(timeout=30)
    finally:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except OSError:
            pass
    assert p.returncode == 130 and "Traceback" not in out, out
    assert out.count("Stopped.") == 1, out


def test_a_build_in_the_background_asks_its_questions_here_then_hands_off(learner, monkeypatch):
    # the build held its terminal for an hour, so lesson 1 could only be used from a second one
    started = []
    monkeypatch.setattr(front, "detach", lambda b, reviewer: started.append((b, reviewer)))
    said, replies = [], iter(["JavaScript", "a web app"])
    engine = front.Engine("adk", "m", lambda meter: learner.brain, Meter(), pipeline(), BudgetExceeded)
    code = front.build("I want to learn TypeScript", engine, ask=lambda _: next(replies), say=said.append,
                       background=True)
    screen = "\n".join(said)
    build = next(learner.home.glob(".builds/*"))
    assert code == 0 and started == [(build, True)]
    assert "building in the background, so you can close this terminal" in screen and "learn stop stops it" in screen
    assert (build / "profile.json").is_file()                          # the answers are kept for the build
    assert build / "running" not in front._HELD                         # and the lock is free for it to take
    assert not (learner.home / "typescript" / ".learn" / "building.json").exists()  # the build itself says it runs


def test_the_build_in_the_background_carries_on_from_the_answers_and_reports(learner, monkeypatch):
    monkeypatch.setattr(front, "detach", lambda b, reviewer: None)
    replies = iter(["JavaScript", "a web app"])
    engine = front.Engine("adk", "m", lambda meter: learner.brain, Meter(), pipeline(), BudgetExceeded)
    front.build("I want to learn TypeScript", engine, ask=lambda _: next(replies), say=lambda m: None,
                background=True)
    build = next(learner.home.glob(".builds/*"))
    told = []
    monkeypatch.setattr(front, "notify", told.append)
    monkeypatch.setattr(front, "load_engine", lambda name: front.Engine(
        name, "m", lambda meter: learner.brain, Meter(), pipeline(), BudgetExceeded))
    assert front.work(build, reviewer=True) == 0                       # no questions asked: the answers were saved
    screen = (build / "screen.log").read_text()
    assert "Writing lesson 1 of 1" in screen and "Your course is ready" in screen
    assert json.loads((build / "status.json").read_text())["line"].startswith("Ready: 1 lessons")
    assert told and told[-1].startswith("Your TypeScript course is ready")


def test_a_notification_never_runs_what_a_lesson_title_says(monkeypatch):
    ran = []
    monkeypatch.setattr(front.sys, "platform", "darwin")
    monkeypatch.setattr(front.shutil, "which", lambda name: "/usr/bin/osascript")
    monkeypatch.setattr(front.subprocess, "run", lambda argv, **k: ran.append(argv))
    monkeypatch.delenv("LEARN_NOTIFY")
    title = 'Types are checked, not run" & (do shell script "touch pwned") & "'
    front.notify(title)
    script = [a for i, a in enumerate(ran[0]) if ran[0][i - 1] == "-e"]
    assert ran[0][-1] == title and not any("touch" in part for part in script)  # an argument, never the script
    monkeypatch.setenv("LEARN_NOTIFY", "off")
    front.notify("anything")
    assert len(ran) == 1


@pytest.mark.parametrize("tty, flags, expected", [(True, [], True), (True, ["--wait"], False), (False, [], False)])
def test_only_a_build_started_in_a_terminal_goes_to_the_background(monkeypatch, tty, flags, expected):
    seen = {}
    monkeypatch.setattr(front.sys.stdin, "isatty", lambda: tty)
    monkeypatch.setattr(front.sys.stdout, "isatty", lambda: tty)
    monkeypatch.setattr(front, "pick_engine", lambda *a: "adk")
    monkeypatch.setattr(front, "load_engine", lambda name: name)
    monkeypatch.setattr(front, "check_settings", lambda: ([], []))
    monkeypatch.setattr(front, "build", lambda request, engine, **k: seen.update(k) or 0)
    assert front.main(flags + ["I want to learn Go"]) == 0
    assert seen["background"] is (expected and front.os.name == "posix")


def test_the_build_process_is_handed_the_lock_and_a_session_of_its_own(tmp_path, monkeypatch):
    # without its own session, closing the terminal ended the build. Without the lock, a `learn stop`
    # in the half second before the build took it went unheard
    seen = {}

    class Popen:
        def __init__(self, argv, **kw):
            seen.update(argv=argv, **kw)

    monkeypatch.setattr(front.subprocess, "Popen", Popen)
    assert front.hold(tmp_path / "running")
    try:
        front.detach(tmp_path, reviewer=False)
        held = front._HELD[tmp_path / "running"].fileno()
    finally:
        front.release(tmp_path / "running")
    assert seen["start_new_session"] is True and seen["stdin"] is subprocess.DEVNULL and seen["cwd"] == tmp_path
    assert seen["argv"][:6] == [sys.executable, "-P", "-m", "learning.front", "--worker", str(tmp_path)]
    assert seen["argv"][-3:] == ["--held-fd", str(held), "--no-review"] and seen["pass_fds"] == (held,)


def test_the_terminal_writes_nothing_after_the_hand_off(learner, monkeypatch):
    # the build's own process writes the spend and the course's note from then on
    learner("I want to learn TypeScript", fail_with=RuntimeError("the network went away"))
    build = next(learner.home.glob(".builds/*"))
    front._HELD.pop(build / "running").close()
    folder = learner.home / "typescript"
    course_dir.note_building(folder, 3, "I want to learn TypeScript", "adk", 1)
    note = (folder / course_dir.BUILDING).read_text()
    written = []
    monkeypatch.setattr(front, "detach", lambda b, reviewer: written.clear())
    real = course_dir.note_running
    monkeypatch.setattr(course_dir, "note_running", lambda *a, **k: (written.append(("note", a)), real(*a, **k)))
    import learning.cli as cli
    real_save = cli.save_spend
    monkeypatch.setattr(cli, "save_spend", lambda *a: (written.append(("spend",)), real_save(*a)))
    engine = front.Engine("adk", "m", lambda meter: learner.brain, Meter(), pipeline(), BudgetExceeded)
    assert front.build("I want to learn TypeScript", engine, ask=lambda _: "", say=lambda m: None, background=True) == 0
    assert written == [] and (folder / course_dir.BUILDING).read_text() == note


def test_the_build_process_never_asks_and_never_interviews_again(learner, monkeypatch):
    monkeypatch.setattr(front, "detach", lambda b, reviewer: None)
    replies = iter(["JavaScript", "a web app"])
    engine = front.Engine("adk", "m", lambda meter: learner.brain, Meter(), pipeline(), BudgetExceeded)
    front.build("I want to learn TypeScript", engine, ask=lambda _: next(replies), say=lambda m: None, background=True)
    build = next(learner.home.glob(".builds/*"))
    intakes = len(learner.brain.intakes)
    monkeypatch.setattr(front, "load_engine", lambda name: front.Engine(
        name, "m", lambda meter: learner.brain, Meter(), pipeline(), BudgetExceeded))
    assert front.work(build, reviewer=True) == 0 and len(learner.brain.intakes) == intakes  # the answers were kept
    other = front.new_build(learner.home, "I want to learn Go", "adk")    # no saved answers: refused, not guessed
    learner.brain.intakes.clear()
    assert front.work(other, reviewer=True) == 1
    assert "can't ask questions" in (other / "screen.log").read_text()


def test_a_background_build_that_hits_the_cap_says_what_to_do_where_it_can_be_seen(learner, monkeypatch):
    # "raise LEARNING_BUDGET_USD" went only to the build's own log, and `learn` showed no way on
    monkeypatch.setattr(front, "detach", lambda b, reviewer: None)
    replies = iter(["JavaScript", "a web app"])
    engine = front.Engine("adk", "m", lambda meter: learner.brain, Meter(), pipeline(), BudgetExceeded)
    front.build("I want to learn TypeScript", engine, ask=lambda _: next(replies), say=lambda m: None, background=True)
    build = next(learner.home.glob(".builds/*"))
    capped = RuntimeError("wrapped")
    capped.__cause__ = BudgetExceeded("spent $5.01 of a $5.00 cap")
    monkeypatch.setattr(front, "load_engine", lambda name: front.Engine(
        name, "m", lambda meter: learner.brain, Meter(), pipeline(fail_with=capped), BudgetExceeded))
    assert front.work(build, reviewer=True) == 2
    said = []
    front.list_courses(say=said.append)
    listed = "\n".join(said)
    assert "Stopped at the spending cap." in listed and "Raise LEARNING_BUDGET_USD in" in listed

    spent = Meter(model="global.anthropic.claude-sonnet-4-6", limit_usd=0.01)  # already at its cap: no hand-off
    spent.charge("lesson", 10_000, 0)
    started = []
    monkeypatch.setattr(front, "detach", lambda b, reviewer: started.append(b))
    said = []
    code = front.build("I want to learn TypeScript", front.Engine("adk", "m", lambda meter: learner.brain, spent,
                       pipeline(), BudgetExceeded), ask=lambda _: "", say=said.append, background=True)
    assert code == 2 and started == [] and "Raise LEARNING_BUDGET_USD" in "\n".join(said)


def test_a_build_that_could_not_start_says_why(learner, monkeypatch, tmp_path):
    build = front.new_build(learner.home, "I want to learn Go", "adk")
    told = []
    monkeypatch.setattr(front, "notify", told.append)

    def broken(name):
        raise ImportError("No module named 'google.adk'")

    monkeypatch.setattr(front, "load_engine", broken)
    assert front.work(build, reviewer=True) == 1 and told
    said = []
    front.list_courses(say=said.append)
    assert "The build couldn't start: No module named 'google.adk'" in "\n".join(said)
    (build / "status.json").unlink()                                     # one that died before it wrote anything
    (build / "worker.out").write_text("Traceback (most recent call last):\nSystemError: it broke\n")
    said = []
    front.list_courses(say=said.append)
    assert "The build stopped unexpectedly: SystemError: it broke" in "\n".join(said)


def handed_off(learner, monkeypatch):
    """A background start whose detach does nothing, then the lock the way the build process inherits it."""
    monkeypatch.setattr(front, "detach", lambda b, reviewer: None)
    replies = iter(["JavaScript", "a web app"])
    engine = front.Engine("adk", "m", lambda meter: learner.brain, Meter(), pipeline(), BudgetExceeded)
    front.build("I want to learn TypeScript", engine, ask=lambda _: next(replies), say=lambda m: None, background=True)
    build = next(learner.home.glob(".builds/*"))
    assert front.hold(build / "running")                              # what the terminal had
    fd = os.dup(front._HELD[build / "running"].fileno())               # what the build process inherits
    os.set_inheritable(fd, True)                                       # as pass_fds leaves it
    front.release(build / "running")                                   # the terminal lets go of its own copy
    lessons, meter = [], Meter()

    def run(flow):
        meter.check()                                                  # as the real meters do before each model call
        lessons.append(1)
        return pipeline()(flow)

    monkeypatch.setattr(front, "load_engine", lambda name: front.Engine(
        name, "m", lambda m: learner.brain, meter, run, BudgetExceeded))
    return build, fd, lessons


@pytest.mark.skipif(sys.platform == "win32", reason="the background build is POSIX")
def test_the_terminal_still_holds_the_lock_when_it_hands_it_over(learner, monkeypatch):
    # released first, the build folder was free for half a second, and a `learn stop` in it went unheard
    seen = {}
    monkeypatch.setattr(front, "detach", lambda b, reviewer: seen.update(held=(b / "running") in front._HELD))
    replies = iter(["JavaScript", "a web app"])
    engine = front.Engine("adk", "m", lambda meter: learner.brain, Meter(), pipeline(), BudgetExceeded)
    assert front.build("I want to learn TypeScript", engine, ask=lambda _: next(replies), say=lambda m: None,
                       background=True) == 0
    build = next(learner.home.glob(".builds/*"))
    assert seen == {"held": True} and build / "running" not in front._HELD


@pytest.mark.skipif(sys.platform == "win32", reason="the background build is POSIX")
def test_the_build_process_takes_on_the_lock_it_is_handed(learner, monkeypatch):
    build, fd, lessons = handed_off(learner, monkeypatch)
    try:
        assert front.work(build, reviewer=True, held_fd=fd) == 0 and lessons == [1]   # its own hold doesn't refuse it
        assert not os.get_inheritable(fd)                              # and nothing it starts gets the lock too
    finally:
        front.release(build / "running")


@pytest.mark.skipif(sys.platform == "win32", reason="the background build is POSIX")
def test_a_stop_asked_while_the_build_process_starts_up_is_kept(learner, monkeypatch):
    build, fd, lessons = handed_off(learner, monkeypatch)
    (build / "stop").write_text("")                                    # `learn stop` before it got going
    try:
        assert front.work(build, reviewer=True, held_fd=fd) != 0 and lessons == []
    finally:
        front.release(build / "running")


def test_a_relative_courses_folder_still_puts_the_course_where_it_says(learner, monkeypatch, tmp_path):
    # the build process runs inside its build folder: a relative LEARN_HOME once built the course in there
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LEARN_HOME", "courses")
    code, screen = learner("I want to learn TypeScript")
    assert code == 0 and (tmp_path / "courses" / "typescript" / "course.json").is_file()
    assert str(tmp_path / "courses" / "typescript") in screen


def test_a_library_warning_is_not_mistaken_for_why_a_build_died(learner):
    build = front.new_build(learner.home, "I want to learn Go", "adk")
    (build / "worker.out").write_text("UserWarning: [EXPERIMENTAL] feature is enabled.\n  check_feature_enabled()\n")
    said = []
    front.list_courses(say=said.append)
    assert "stopped unexpectedly" not in "\n".join(said)


def stand_in(learner, run, meter=None):
    return lambda name: front.Engine(name, "m", lambda m: learner.brain, meter or Meter(), run, BudgetExceeded)


def listing():
    said = []
    front.list_courses(say=said.append)
    return "\n".join(said)


def test_a_crash_after_the_build_says_it_is_starting_is_still_explained(learner, monkeypatch):
    # "Starting the build." stayed up, and the traceback in worker.out was never shown
    build = front.new_build(learner.home, "I want to learn Go", "adk")
    monkeypatch.setattr(front, "load_engine", stand_in(learner, pipeline()))
    told = []
    monkeypatch.setattr(front, "notify", told.append)

    def crash(*a, **k):
        raise PermissionError(13, "Permission denied", str(build / "build.log"))

    monkeypatch.setattr(front, "build", crash)
    with pytest.raises(PermissionError):                              # the interpreter writes it to worker.out
        front.work(build, reviewer=True)
    assert "Permission denied" in listing() and told == ["A course build stopped unexpectedly. learn shows why."]


def test_a_build_refused_at_the_cap_says_why_in_learn_too(learner, monkeypatch):
    # the terminal said why, then `learn` showed the build with no reason
    spent = Meter(model="global.anthropic.claude-sonnet-4-6", limit_usd=0.01)
    spent.charge("lesson", 10_000, 0)
    monkeypatch.setattr(front, "detach", lambda b, reviewer: None)
    code = front.build("I want to learn Go", front.Engine("adk", "m", lambda m: learner.brain, spent, pipeline(),
                       BudgetExceeded), ask=lambda _: "", say=lambda m: None, background=True)
    assert code == 2 and "Stopped at the spending cap." in listing() and "Raise LEARNING_BUDGET_USD" in listing()


def test_the_status_says_starting_before_the_frameworks_load(learner, monkeypatch):
    build = front.new_build(learner.home, "I want to learn Go", "adk")
    seen = {}

    def load(name):
        seen["line"] = json.loads((build / "status.json").read_text())["line"]
        raise ImportError("stop here")

    monkeypatch.setattr(front, "load_engine", load)
    front.work(build, reviewer=True)
    assert seen == {"line": "Starting the build."}


def test_the_newest_crash_is_the_one_shown(learner):
    # worker.out is added to on every run, so an old crash comes first
    build = front.new_build(learner.home, "I want to learn Go", "adk")
    (build / "worker.out").write_text("Traceback (most recent call last):\nOldError: last week\n"
                                      "Traceback (most recent call last):\nNewError: just now\n")
    shown = listing()
    assert "NewError: just now" in shown and "OldError" not in shown


def test_an_old_crash_does_not_hide_what_the_build_is_doing_now(learner):
    # a crash from an earlier run stays in worker.out after the build carries on
    build = front.new_build(learner.home, "I want to learn Go", "adk")
    (build / "worker.out").write_text("Traceback (most recent call last):\nImportError: last week\n")
    (build / "status.json").write_text(json.dumps({"line": "Writing lesson 3 of 14: Traits", "cap": 5.0}))
    shown = listing()
    assert "Writing lesson 3 of 14: Traits." in shown and "ImportError" not in shown


@pytest.mark.parametrize("how", ["ctrl-c", "learn stop"])
def test_a_stop_leaves_no_advice_from_before_it(learner, monkeypatch, how):
    # the halfway spend line was the advice, and stayed under "Stopped."
    monkeypatch.setattr(front, "detach", lambda b, reviewer: None)
    replies = iter(["JavaScript", "a web app"])
    engine = front.Engine("adk", "m", lambda m: learner.brain, Meter(), pipeline(), BudgetExceeded)
    front.build("I want to learn TypeScript", engine, ask=lambda _: next(replies), say=lambda m: None, background=True)
    build = next(learner.home.glob(".builds/*"))
    meter = Meter()

    def run(flow):
        flow.on_lesson(1, 2)                                           # halfway: the spend line becomes the advice
        if how == "ctrl-c":
            raise KeyboardInterrupt
        meter.stop_requested = True                                    # `learn stop` reaches a stage as an error
        raise RuntimeError("stopped")

    monkeypatch.setattr(front, "load_engine", stand_in(learner, run, meter))
    assert front.work(build, reviewer=True) == 130
    status = json.loads((build / "status.json").read_text())
    assert status["line"].startswith("Stopped") and not status.get("advice")


def test_a_refused_carry_on_says_nothing_about_picking_up(learner, monkeypatch):
    monkeypatch.setattr(front, "detach", lambda b, reviewer: None)
    replies = iter(["JavaScript", "a web app"])
    engine = front.Engine("adk", "m", lambda m: learner.brain, Meter(), pipeline(), BudgetExceeded)
    front.build("I want to learn TypeScript", engine, ask=lambda _: next(replies), say=lambda m: None, background=True)
    spent = Meter(model="global.anthropic.claude-sonnet-4-6", limit_usd=0.01)
    spent.charge("lesson", 10_000, 0)
    said = []
    code = front.build("I want to learn TypeScript", front.Engine("adk", "m", lambda m: learner.brain, spent,
                       pipeline(), BudgetExceeded), ask=lambda _: "", say=said.append, background=True)
    assert code == 2 and "Picking up" not in "\n".join(said)


def test_a_build_exactly_at_its_cap_is_not_handed_off(learner, monkeypatch):
    # at the cap the first model call is refused, so a build process would only post a cap notification
    at = Meter(model="global.anthropic.claude-sonnet-4-6")
    at.charge("lesson", 10_000, 0)
    at.limit_usd = at.spent_usd
    started = []
    monkeypatch.setattr(front, "detach", lambda b, reviewer: started.append(b))
    code = front.build("I want to learn Go", front.Engine("adk", "m", lambda m: learner.brain, at, pipeline(),
                       BudgetExceeded), ask=lambda _: "", say=lambda m: None, background=True)
    assert code == 2 and started == []


def test_a_build_process_that_cannot_start_is_not_announced_as_running(learner, monkeypatch):
    # "so you can close this terminal" came first, then the error from starting it
    def no_process(*a, **k):
        raise OSError(11, "Resource temporarily unavailable")

    monkeypatch.setattr(front.subprocess, "Popen", no_process)
    replies = iter(["JavaScript", "a web app"])
    said = []
    engine = front.Engine("adk", "m", lambda m: learner.brain, Meter(), pipeline(), BudgetExceeded)
    code = front.build("I want to learn TypeScript", engine, ask=lambda _: next(replies), say=said.append,
                       background=True)
    screen = "\n".join(said)
    assert code == 1 and "Resource temporarily unavailable" in screen and "you can close this terminal" not in screen


@pytest.mark.parametrize("cut", [KeyboardInterrupt, BrokenPipeError])
def test_this_terminal_says_nothing_about_a_build_it_has_handed_off(learner, monkeypatch, cut):
    # the hand-off line prints after the build process starts: a Ctrl-C there said "Stopped." while it ran on,
    # and a closed terminal would have said "Something went wrong" over the build's own status
    started, said, told = [], [], []
    monkeypatch.setattr(front, "notify", told.append)

    def say(m):
        said.append(m)
        if "so you can close this terminal" in m:                      # as the hand-off line prints
            raise cut

    monkeypatch.setattr(front, "detach", lambda b, reviewer: started.append(b))
    replies = iter(["JavaScript", "a web app"])
    engine = front.Engine("adk", "m", lambda m: learner.brain, Meter(), pipeline(), BudgetExceeded)
    assert front.build("I want to learn TypeScript", engine, ask=lambda _: next(replies), say=say,
                       background=True) == 0
    build = next(learner.home.glob(".builds/*"))
    status = json.loads((build / "status.json").read_text()) if (build / "status.json").exists() else {}
    assert started and not status.get("line", "").startswith(("Stopped", "Something went wrong")) and told == []
    assert not any(m.lstrip().startswith(("Stopped", "Something went wrong")) for m in said)
    if cut is KeyboardInterrupt:                                       # whoever pressed it hears the build goes on
        assert said[-1].strip() == "It's building in the background. learn stop stops it."


def test_a_spend_that_cant_be_saved_after_a_cap_stop_keeps_the_cap_advice(learner, monkeypatch):
    # build()'s finally raised after the cap was explained, and the build process wrote over it
    monkeypatch.setattr(front, "detach", lambda b, reviewer: None)
    replies = iter(["JavaScript", "a web app"])
    engine = front.Engine("adk", "m", lambda m: learner.brain, Meter(), pipeline(), BudgetExceeded)
    front.build("I want to learn TypeScript", engine, ask=lambda _: next(replies), say=lambda m: None, background=True)
    build = next(learner.home.glob(".builds/*"))
    capped = RuntimeError("wrapped")
    capped.__cause__ = BudgetExceeded("spent $5.01 of a $5.00 cap")
    monkeypatch.setattr(front, "load_engine", stand_in(learner, pipeline(fail_with=capped)))
    told = []
    monkeypatch.setattr(front, "notify", told.append)

    def full(meter, path):
        raise OSError(28, "No space left on device")

    import learning.cli as cli
    monkeypatch.setattr(cli, "save_spend", full)
    assert front.work(build, reviewer=True) == 2
    status = json.loads((build / "status.json").read_text())
    assert status["line"] == "Stopped at the spending cap." and "LEARNING_BUDGET_USD" in status.get("advice", "")
    assert len(told) == 1 and "spending cap" in told[0]
    assert "Couldn't save what this build spent" in (build / "screen.log").read_text()


def test_a_crash_is_still_notified_when_its_status_cannot_be_written(learner, monkeypatch):
    # on a full disk the status write raised inside the handler, so the notification never went
    from learning import stages
    build = front.new_build(learner.home, "I want to learn Go", "adk")
    monkeypatch.setattr(front, "load_engine", stand_in(learner, pipeline()))
    told = []
    monkeypatch.setattr(front, "notify", told.append)
    real = stages.write_atomic

    def write(path, data):
        if "stopped unexpectedly" in str(data):
            raise OSError(28, "No space left on device")
        return real(path, data)

    monkeypatch.setattr(stages, "write_atomic", write)

    def crash(*a, **k):
        raise RuntimeError("it broke")

    monkeypatch.setattr(front, "build", crash)
    with pytest.raises(RuntimeError):
        front.work(build, reviewer=True)
    assert told == ["A course build stopped unexpectedly. learn shows why."]


def test_a_build_process_that_cannot_start_leaves_the_course_marked_stopped(learner, monkeypatch):
    # nothing took over, so this terminal still writes the spend and the course's note
    learner("I want to learn TypeScript", fail_with=RuntimeError("the network went away"))
    build = next(learner.home.glob(".builds/*"))
    front._HELD.pop(build / "running").close()
    folder = learner.home / "typescript"
    course_dir.note_building(folder, 3, "I want to learn TypeScript", "adk", os.getpid())  # running, by a live pid
    spend = (build / "spend.json").read_text()

    def no_process(*a, **k):
        raise OSError(11, "Resource temporarily unavailable")

    monkeypatch.setattr(front.subprocess, "Popen", no_process)
    engine = front.Engine("adk", "m", lambda m: learner.brain, Meter(), pipeline(), BudgetExceeded)
    assert front.build("I want to learn TypeScript", engine, ask=lambda _: "", say=lambda m: None, background=True) == 1
    assert json.loads((folder / course_dir.BUILDING).read_text())["running"] is False
    assert json.loads((build / "spend.json").read_text()) == json.loads(spend)


def test_a_crash_report_hides_secrets_and_covers_any_error(learner, monkeypatch):
    monkeypatch.setenv("EXA_API_KEY", "fake-exa-secret-not-real-0002")
    build = front.new_build(learner.home, "I want to learn Go", "adk")
    monkeypatch.setattr(front, "load_engine", stand_in(learner, pipeline()))
    monkeypatch.setattr(front, "notify", lambda text: None)

    def crash(*a, **k):
        raise RuntimeError("upstream said no (key fake-exa-secret-not-real-0002)")

    monkeypatch.setattr(front, "build", crash)
    with pytest.raises(RuntimeError):
        front.work(build, reviewer=True)
    line = json.loads((build / "status.json").read_text())["line"]
    assert line.startswith("The build stopped unexpectedly: upstream said no") and "fake-exa-secret" not in line

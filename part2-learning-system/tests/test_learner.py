"""The course as a learner uses it: a folder, and learn.py.

These write a real course folder and drive learn.py the way a person would, including
running the real terraform binary on the exercise.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

import pytest

from learning import course_dir
from learning.model import (
    Claim, Course, CourseFile, Curriculum, Evidence, Exercise, KnowledgeBase, LearnerProfile, Lesson,
    LessonObjective, LessonSpec, Level, Objective, Problem, QuizItem, Source, Spec, Stage, Tier, Unit,
)

PROVIDER = 'terraform {\n  required_providers {\n    aws = { source = "hashicorp/aws", version = "~> 6.0" }\n  }\n}\nprovider "aws" { region = "us-east-1" }\n'
SOLUTION = PROVIDER + 'resource "aws_vpc" "main" {\n  cidr_block = "10.0.0.0/16"\n}\n'
STARTER = PROVIDER + '# TODO: an aws_vpc named "main" with the CIDR block 10.0.0.0/16\n'
TEST = '''mock_provider "aws" {}

run "vpc" {
  command = apply
  assert {
    condition     = aws_vpc.main.cidr_block == "10.0.0.0/16"
    error_message = "aws_vpc.main should use the CIDR block 10.0.0.0/16"
  }
}
'''


def course() -> Course:
    src = Source.build("https://developer.hashicorp.com/terraform/language/resources",
                       "Resources", "Resources are the most important element in the Terraform language.", Tier.OFFICIAL)
    claim = Claim(id="a" * 12, text="Resources are central", quote="Resources are the most important element",
                  source_id=src.id, objective_ids=["1"])
    profile = LearnerProfile(subject="Terraform", goal="build things", subject_is_clear=True)
    kb = KnowledgeBase(profile=profile, spec=Spec(kind="derived_from_docs", title="Terraform",
                                                  objectives=[Objective(id="1", statement="write a resource")]),
                       sources=[src], claims=[claim])
    spec = LessonSpec(id="u1-l1", title="Your first resource", claim_ids=[claim.id],
                      objectives=[LessonObjective(statement="write an aws_vpc resource", level=Level.APPLY,
                                                  covers=["1"], evidence=Evidence.EXERCISE)])
    lesson = Lesson(id="u1-l1", title="Your first resource", explanation=f"Resources matter [c:{claim.id}].",
                    worked_example="An example.",
                    exercise=Exercise(task="Add the VPC.", starter=[CourseFile(path="main.tf", content=STARTER)],
                                      solution=[CourseFile(path="main.tf", content=SOLUTION)],
                                      checks=[CourseFile(path="tests/vpc.tftest.hcl", content=TEST)],
                                      hints=["Look at the TODO.", "It's an aws_vpc resource."]),
                    quiz=[QuizItem(stem="Which block creates infrastructure?", options=["resource", "variable", "output"],
                                   answer=0, explanation="resource does. variable and output don't.",
                                   objective="write an aws_vpc resource")])
    cur = Curriculum(title="Terraform", units=[Unit(id="u1", title="Basics", lessons=[spec], project="Build it.")])
    return Course(profile=profile, knowledge=kb, curriculum=cur, lessons=[lesson])


def learn(root, *args, stdin=""):
    return subprocess.run([sys.executable, "learn.py", *args], cwd=root, input=stdin,
                          capture_output=True, text=True, timeout=600)


def test_the_answers_are_not_in_what_the_learner_reads(tmp_path):
    root = course_dir.write(course(), tmp_path / "course")
    lesson = next((root / "units").glob("*/u1-l1-*"))
    readme = (lesson / "README.md").read_text()
    questions = json.loads((lesson / "quiz.json").read_text())
    assert "resource does" not in readme
    assert "answer" not in questions[0] and "explanation" not in questions[0]
    assert "aws_vpc\" \"main\"" not in (lesson / "exercise" / "main.tf").read_text()
    assert (lesson / ".answers" / "solution" / "main.tf").exists()


def test_every_fact_links_to_its_source(tmp_path):
    root = course_dir.write(course(), tmp_path / "course")
    readme = next((root / "units").glob("*/u1-l1-*/README.md")).read_text()
    assert "[c:" not in readme
    assert "(https://developer.hashicorp.com/terraform/language/resources)" in readme


def test_a_quiz_shows_the_answer_only_after_the_learner_answers(tmp_path):
    root = course_dir.write(course(), tmp_path / "course")
    lesson = next((root / "units").glob("*/u1-l1-*"))
    right = json.loads((lesson / ".answers" / "quiz.json").read_text())[0]["answer"] + 1
    wrong = next(n for n in (1, 2, 3) if n != right)
    out = learn(root, "quiz", "u1-l1", stdin=f"{wrong}\n").stdout
    asked, told = out.split("Your answer:", 1)
    assert "resource does" not in asked
    assert f"Not quite. It's {right}." in told and "resource does" in told
    assert "u1-l1#0" in json.loads((root / ".learn" / "progress.json").read_text())["review"]


def test_hints_come_one_at_a_time(tmp_path):
    root = course_dir.write(course(), tmp_path / "course")
    assert "Hint 1 of 2: Look at the TODO." in learn(root, "hint").stdout
    assert "Hint 2 of 2" in learn(root, "hint").stdout
    assert "No more hints" in learn(root, "hint").stdout


@pytest.mark.skipif(shutil.which("terraform") is None, reason="needs terraform")
def test_check_fails_the_untouched_starter_and_passes_the_finished_work(tmp_path):
    root = course_dir.write(course(), tmp_path / "course")
    lesson = next((root / "units").glob("*/u1-l1-*"))
    failed = learn(root, "check")
    assert "Not yet" in failed.stdout
    (lesson / "exercise" / "main.tf").write_text(SOLUTION)   # the learner does the work
    passed = learn(root, "check")
    assert "Passed" in passed.stdout, passed.stdout
    assert "built" in learn(root, "status").stdout


def test_a_learner_can_flag_a_bad_question(tmp_path):
    root = course_dir.write(course(), tmp_path / "course")
    assert "Noted against u1-l1" in learn(root, "report", "question 1 has two right answers").stdout
    assert json.loads((root / ".learn" / "reports.json").read_text())[0]["reason"] == "question 1 has two right answers"


def test_a_problem_the_checks_could_not_fix_is_told_to_the_learner_where_they_meet_it(tmp_path):
    c = course()
    c.problems = [Problem(stage=Stage.TEACHING, check="exercise_does_not_work", lesson_id="u1-l1",
                          detail="the solution does not pass its own checks: Error: Failed to install provider")]
    root = course_dir.write(c, tmp_path / "course")
    lesson = next((root / "units").glob("*/u1-l1-*/README.md")).read_text()
    assert lesson.index("Known problems") < lesson.index("## Your turn")
    assert "Failed to install provider" in lesson
    assert "u1-l1: the solution does not pass" in (root / "README.md").read_text()


def test_a_clean_course_claims_no_problems(tmp_path):
    root = course_dir.write(course(), tmp_path / "course")
    assert "Known problems" not in (root / "README.md").read_text()
    assert "Known problems" not in next((root / "units").glob("*/u1-l1-*/README.md")).read_text()


def test_the_right_answer_is_not_always_in_the_same_place(tmp_path):
    # Gemini put the right answer first in 30 of 36 questions. A learner shouldn't be
    # able to pass by position
    c = course()
    item = c.lessons[0].quiz[0]
    c.lessons[0].quiz = [item.model_copy(update={"stem": f"q{i}"}) for i in range(12)]
    root = course_dir.write(c, tmp_path / "course")
    lesson = next((root / "units").glob("*/u1-l1-*"))
    asked = json.loads((lesson / "quiz.json").read_text())
    answers = [a["answer"] for a in json.loads((lesson / ".answers" / "quiz.json").read_text())]
    assert len(set(answers)) > 1
    assert all(q["options"][a] == "resource" for q, a in zip(asked, answers))


def test_a_question_whose_explanation_counts_options_keeps_its_order(tmp_path):
    # a course written before explanations had to name options by what they say
    c = course()
    item = c.lessons[0].quiz[0].model_copy(update={"explanation": "Option 1 is right, resource does."})
    c.lessons[0].quiz = [item.model_copy(update={"stem": f"q{i}"}) for i in range(12)]
    root = course_dir.write(c, tmp_path / "course")
    lesson = next((root / "units").glob("*/u1-l1-*"))
    assert {a["answer"] for a in json.loads((lesson / ".answers" / "quiz.json").read_text())} == {0}


# -- other subjects ------------------------------------------------------------------

def course_with(exercise: Exercise) -> Course:
    c = course()
    c.lessons[0].exercise = exercise
    return c


GREET_TEST = '''import unittest
from greet import greet


class T(unittest.TestCase):
    def test_greet(self):
        self.assertEqual(greet("Ada"), "Hello, Ada!", "greet should say hello by name")
'''
PY_EXERCISE = Exercise(task="Make greet say hello.",
                       starter=[CourseFile(path="greet.py", content='def greet(name):\n    return ""  # TODO\n')],
                       solution=[CourseFile(path="greet.py", content='def greet(name):\n    return f"Hello, {name}!"\n')],
                       checks=[CourseFile(path="test_greet.py", content=GREET_TEST)], hints=["f-strings"])


def test_a_python_exercise_is_checked_with_python_itself(tmp_path):
    root = course_dir.write(course_with(PY_EXERCISE), tmp_path / "course")
    lesson = next((root / "units").glob("*/u1-l1-*"))
    assert "Python's own `unittest`" in (lesson / "README.md").read_text()
    failed = learn(root, "check").stdout
    assert "greet should say hello by name" in failed and "Not yet" in failed
    (lesson / "exercise" / "greet.py").write_text(PY_EXERCISE.solution[0].content)
    assert "Passed" in learn(root, "check").stdout


def test_an_exercise_nothing_can_check_is_left_to_the_learner_and_they_can_move_on(tmp_path):
    essay = Exercise(task="Write 3 sentences in Spanish.", starter=[CourseFile(path="answer.md", content="")],
                     solution=[CourseFile(path="answer.md", content="Hola. Me llamo Ada. Vivo en Lagos.")],
                     hints=["Start with Hola."])
    root = course_dir.write(course_with(essay), tmp_path / "course")
    lesson = next((root / "units").glob("*/u1-l1-*"))
    assert "Nothing can check this exercise automatically" in (lesson / "README.md").read_text()
    assert "you're the judge" in learn(root, "check").stdout
    assert "self-checked" in (root / ".learn" / "progress.json").read_text()


def test_a_missing_tool_says_what_to_install(tmp_path):
    root = course_dir.write(course(), tmp_path / "course")   # the Terraform one
    out = subprocess.run([sys.executable, "learn.py", "check"], cwd=root, capture_output=True, text=True,
                         env={"PATH": str(tmp_path / "nothing-here")}).stdout
    assert "developer.hashicorp.com/terraform/install" in out


def test_several_facts_cited_at_once_become_links_too(tmp_path):
    # one lesson showed "[c:9f728d8072ec, c:a4776625a307, c:b6a00d2f972e]" to the learner
    c = course()
    cid = c.knowledge.claims[0].id
    c.lessons[0].explanation = f"Modules come from many places [c:{cid}, c:{cid}]."
    root = course_dir.write(c, tmp_path / "course")
    readme = next((root / "units").glob("*/u1-l1-*/README.md")).read_text()
    assert "[c:" not in readme
    assert "places ([source](https://developer.hashicorp.com/terraform/language/resources))." in readme


def test_a_mistyped_citation_never_reaches_the_learner(tmp_path):
    c = course()
    c.lessons[0].explanation += " Like this [c:bfaa726bb50]:"
    root = course_dir.write(c, tmp_path / "course")
    assert "[c:" not in next((root / "units").glob("*/u1-l1-*/README.md")).read_text()


SUM_TEST = '''import { test } from "node:test";
import assert from "node:assert/strict";
import { sum } from "./sum.ts";

test("adds two numbers", () => {
  assert.equal(sum(2, 3), 5, "sum(2, 3) should be 5");
});
'''


@pytest.mark.skipif(shutil.which("npm") is None, reason="needs node and npm")
def test_a_failing_typescript_check_says_what_failed_without_the_stack(tmp_path):
    ts = Exercise(task="Make sum add.",
                  starter=[CourseFile(path="sum.ts", content="export function sum(a: number, b: number): number {\n  return 0;\n}\n")],
                  solution=[CourseFile(path="sum.ts", content="export function sum(a: number, b: number): number {\n  return a + b;\n}\n")],
                  checks=[CourseFile(path="sum.test.ts", content=SUM_TEST)], hints=["+"])
    root = course_dir.write(course_with(ts), tmp_path / "course")
    out = learn(root, "check").stdout
    assert "  - adds two numbers: sum(2, 3) should be 5 (0 !== 5)" in out
    assert "node:internal" not in out and "    at " not in out


def test_lessons_name_the_learn_command_and_the_course_says_how_to_do_without_it(tmp_path):
    root = course_dir.write(course(), tmp_path / "course")
    lesson = next((root / "units").glob("*/u1-l1-*/README.md")).read_text()
    assert "learn check" in lesson and "python3 learn.py" not in lesson
    assert "Type `python3 learn.py` wherever it says `learn`" in (root / "README.md").read_text()


def exercise_folder(tmp_path, test_code: str):
    folder = tmp_path / "exercise"
    folder.mkdir()
    (folder / "test_it.py").write_text("import os\nimport unittest\n\n" + test_code)
    return folder


def test_an_exercise_never_sees_the_keys_or_the_real_home(tmp_path, monkeypatch):
    # the tests are written by a model, and once ran with every key and credential in reach
    from pathlib import Path

    from learning.learn_cli import run_exercise

    monkeypatch.setenv("GOOGLE_API_KEY", "AIza-not-a-real-key-123456")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "not-a-real-secret-123456")
    monkeypatch.setenv("TF_TOKEN_app_terraform_io", "not-a-real-token-123456")
    folder = exercise_folder(tmp_path, f"""
class T(unittest.TestCase):
    def test_nothing_secret_is_here(self):
        for name in ("GOOGLE_API_KEY", "AWS_SECRET_ACCESS_KEY", "TF_TOKEN_app_terraform_io"):
            self.assertNotIn(name, os.environ, name + " reached the exercise")
        self.assertNotEqual(os.environ["HOME"], {str(Path.home())!r}, "the real home reached the exercise")
""")
    outcome, output = run_exercise(folder, "python")
    assert outcome == "passed", output


def test_a_secret_a_test_prints_is_hidden_from_the_output(tmp_path, monkeypatch):
    # a test can still read a key from a file, so whatever it prints is checked too
    from learning.learn_cli import run_exercise

    monkeypatch.setenv("GOOGLE_API_KEY", "AIza-not-a-real-key-123456")
    folder = exercise_folder(tmp_path, """
class T(unittest.TestCase):
    def test_leak(self):
        self.fail("the key is AIza-not-a-real-key-123456")
""")
    outcome, output = run_exercise(folder, "python")
    assert outcome == "failed" and "[hidden]" in output and "AIza-not-a-real-key-123456" not in output


@pytest.mark.skipif(sys.platform == "win32", reason="process groups are POSIX")
def test_a_timeout_stops_what_the_exercise_started_too(tmp_path):
    # a timeout once killed only the test runner and left what it started running
    import os
    import time

    from learning.learn_cli import run_exercise

    pid_file = tmp_path / "child.pid"
    folder = exercise_folder(tmp_path, f"""
import subprocess
import time

class T(unittest.TestCase):
    def test_hang(self):
        child = subprocess.Popen(["sleep", "30"])
        open({str(pid_file)!r}, "w").write(str(child.pid))
        time.sleep(30)
""")
    outcome, output = run_exercise(folder, "python", timeout=2)
    assert outcome == "failed" and "took longer" in output
    pid = int(pid_file.read_text())
    time.sleep(0.2)
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)


@pytest.mark.skipif(sys.platform == "win32", reason="process groups are POSIX")
def test_stopping_a_check_stops_what_the_exercise_started(tmp_path, monkeypatch):
    # the check runs in its own process group, which the terminal's Ctrl-C no longer reaches
    import os
    import time

    from learning.learn_cli import run_exercise

    pid_file = tmp_path / "child.pid"
    folder = exercise_folder(tmp_path, f"""
import subprocess
import time

class T(unittest.TestCase):
    def test_hang(self):
        child = subprocess.Popen(["sleep", "30"])
        open({str(pid_file)!r}, "w").write(str(child.pid))
        time.sleep(30)
""")

    real = subprocess.Popen.communicate

    def ctrl_c_once_started(self, *args, **kwargs):
        if "unittest" not in self.args:  # the syntax step runs first, untouched
            return real(self, *args, **kwargs)
        for _ in range(100):
            if pid_file.exists() and pid_file.read_text():
                break
            time.sleep(0.1)
        raise KeyboardInterrupt

    monkeypatch.setattr(subprocess.Popen, "communicate", ctrl_c_once_started)
    with pytest.raises(KeyboardInterrupt):
        run_exercise(folder, "python")
    time.sleep(0.2)
    with pytest.raises(ProcessLookupError):
        os.kill(int(pid_file.read_text()), 0)


@pytest.mark.skipif(sys.platform == "win32", reason="sessions are POSIX")
def test_a_timeout_returns_even_when_something_keeps_the_output_open(tmp_path):
    import os
    import signal
    import time

    from learning.learn_cli import run_exercise

    pid_file = tmp_path / "stray.pid"
    folder = exercise_folder(tmp_path, f"""
import subprocess
import time

class T(unittest.TestCase):
    def test_hang(self):
        stray = subprocess.Popen(["sleep", "8"], start_new_session=True)  # out of reach, holding the output
        open({str(pid_file)!r}, "w").write(str(stray.pid))
        time.sleep(30)
""")
    started = time.monotonic()
    outcome, output = run_exercise(folder, "python", timeout=2)
    took = time.monotonic() - started
    try:
        os.kill(int(pid_file.read_text()), signal.SIGKILL)
    except (ProcessLookupError, ValueError, FileNotFoundError):
        pass
    assert outcome == "failed" and took < 5


def test_the_typescript_compiler_is_fetched_at_exact_versions(tmp_path, monkeypatch):
    # "latest" from npm ran whatever was published that day, install scripts included
    from learning import learn_cli

    monkeypatch.setattr(learn_cli, "TSC_HOME", tmp_path / "tsc")
    monkeypatch.setattr(learn_cli.shutil, "which", lambda name: "/usr/bin/" + name)
    ran = []
    monkeypatch.setattr(learn_cli.subprocess, "run", lambda argv, **k: ran.append(argv) or subprocess.CompletedProcess(argv, 1, "", "offline"))
    learn_cli.typescript_compiler()
    # only these two packages, so one added later without a version fails here
    packages = [a for a in ran[0][2:] if not a.startswith("-") and a != str(tmp_path / "tsc")]
    assert packages == ["typescript@7.0.2", "@types/node@26.6.3"] and "--ignore-scripts" in ran[0]


def test_a_secret_inside_a_longer_one_is_hidden_whole(monkeypatch):
    from learning.learn_cli import hide_secrets

    monkeypatch.setenv("A_KEY", "abcdefgh")
    monkeypatch.setenv("B_TOKEN", "abcdefgh-and-more")
    assert hide_secrets("got abcdefgh-and-more") == "got [hidden]"


def test_commands_act_on_the_lesson_whose_folder_they_are_typed_in(tmp_path, monkeypatch, capfd):
    # `check` in lesson 2's folder ran lesson 1's tests and said Passed. hint and solution did the same
    c = course_with(PY_EXERCISE)                                   # lesson 1's starter fails its check
    done = PY_EXERCISE.model_copy(update={"starter": PY_EXERCISE.solution, "hints": ["the second hint"]})
    c.lessons.append(c.lessons[0].model_copy(update={"id": "u1-l2", "title": "Second", "exercise": done}))
    c.curriculum.units[0].lessons.append(c.curriculum.units[0].lessons[0].model_copy(update={"id": "u1-l2"}))
    root = course_dir.write(c, tmp_path / "course")
    two = next((root / "units").glob("*/u1-l2-*")) / "exercise"

    def typed(*args, stdin=""):  # python3 learn.py, from lesson 2's folder
        return subprocess.run([sys.executable, str(root / "learn.py"), *args], cwd=two, input=stdin,
                              capture_output=True, text=True, timeout=600).stdout

    checked = typed("check")
    assert "u1-l2" in checked and "Passed" in checked
    assert "Hint 1 of 1: the second hint" in typed("hint")
    assert "Noted against u1-l2" in typed("report", "this one")
    # next shows the lesson you're in while it's unfinished, and names an earlier one left behind
    shown = typed("next")
    assert shown.startswith("u1-l2") and "u1-l1 isn't finished yet" in shown
    assert typed("next", "u1-l1").startswith("u1-l1")             # a lesson named still wins
    typed("solution")
    typed("quiz", stdin="1\n")
    progress = json.loads((root / ".learn" / "progress.json").read_text())
    assert progress["solutions"] == ["u1-l2"]
    assert "quiz" in progress["done"]["u1-l2"] and "quiz" not in progress["done"].get("u1-l1", {})
    # lesson 2 is finished, so next moves on, and its commands name the lesson they're for
    shown = typed("next")
    assert shown.startswith("u1-l1") and "check u1-l1" in shown and "quiz u1-l1" in shown

    monkeypatch.chdir(two)                                         # and through `learn`
    from learning import front
    assert front.main(["check"]) == 0
    assert "u1-l2" in capfd.readouterr().out


def test_the_lesson_you_are_in_is_found_through_symlinks_and_similar_names(tmp_path, monkeypatch):
    from learning import learn_cli

    root = tmp_path / "course"
    for name in ("u1-l1", "u1-l10"):
        (root / "units" / "u1" / name / "exercise").mkdir(parents=True)
    (root / ".learn").mkdir()
    (root / ".learn" / "lessons.json").write_text(json.dumps(
        [{"id": n, "title": n, "path": f"units/u1/{n}", "exercise": True} for n in ("u1-l1", "u1-l10")]))
    monkeypatch.setattr(learn_cli, "ROOT", root)
    ten = root / "units" / "u1" / "u1-l10"

    def here(path):
        monkeypatch.setattr(learn_cli, "HERE", str(path))
        return (learn_cli.lesson_here() or {}).get("id")

    assert here(ten / "exercise") == "u1-l10"                     # u1-l1 is a prefix of its name
    (tmp_path / "link").symlink_to(root)
    assert here(tmp_path / "link" / "units" / "u1" / "u1-l10") == "u1-l10"
    moved = tmp_path / "elsewhere"
    ten.rename(moved)
    ten.symlink_to(moved)
    assert here(moved / "exercise") == "u1-l10"
    assert here(root / "units") is None

    gone = tmp_path / "gone"
    gone.mkdir()
    monkeypatch.chdir(gone)
    gone.rmdir()
    monkeypatch.setattr(learn_cli, "HERE", None)
    assert learn_cli.lesson_here() is None                        # a folder deleted under you isn't a crash


def test_check_gives_one_line_per_failing_test_and_keeps_the_first(tmp_path):
    # output was cut to its last 3000 characters, which dropped the first failure, and exit was 0
    many = "\n".join(f"    def test_{i:02}(self):\n        self.assertEqual(greet('x' * 80), 'no', 'check {i} failed')"
                     for i in range(40))
    ex = PY_EXERCISE.model_copy(update={"checks": [CourseFile(
        path="test_greet.py", content=f"import unittest\nfrom greet import greet\n\n\nclass T(unittest.TestCase):\n{many}\n")]})
    root = course_dir.write(course_with(ex), tmp_path / "course")
    run = learn(root, "check")
    assert run.returncode == 1 and "40 checks failed:" in run.stdout
    assert "  - test_00: check 0 failed (" in run.stdout and "  - test_39: check 39 failed (" in run.stdout
    assert "Traceback" not in run.stdout
    (next((root / "units").glob("*/u1-l1-*")) / "exercise" / "greet.py").write_text("def greet(name):\n    return 'no'\n")
    assert learn(root, "check").returncode == 0


def test_failures_are_read_from_each_runner_and_python_3_9_too():
    from learning import learn_cli

    assert learn_cli.failures("terraform", TF_FAILED) == [
        'two_asserts: the VPC must use 10.0.0.0/16 (output.cidr is "10.1.0.0/16")',
        'two_asserts: the name must be ledger (output.name is "1234")',
        'errors_without_assert: Invalid function argument: Invalid value for "v" parameter: cannot convert '
        '"abcd" to number; given string must be a decimal representation of a number. (var.name is "abcd")',
        'bad_variable: Invalid value for variable: name must be longer than 2 characters (var.name is "x")']
    assert learn_cli.failures("python", PY39_FAILED) == [
        "test_total: NotImplementedError: total is not written yet",
        "test_greet: greet should say hello by name ('' != 'Hello, Ada!')",
        "test_greet_plain: '' != 'Hello, Bo!'",
        "test_multiline: lines differ ('a\\nb\\nc' != 'a\\nB\\nc')"]
    assert learn_cli.failures("node", "sum.ts(3,5): error TS2322: Type 'string' is not assignable to type 'number'.") == [
        "sum.ts line 3: Type 'string' is not assignable to type 'number'."]
    long = "start\n" + "x" * 5000 + "\nend"
    assert learn_cli.shorten(long).startswith("start") and learn_cli.shorten(long).endswith("end")


def test_check_watch_checks_again_on_save_and_stops_once_it_passes(tmp_path):
    import threading
    import time

    root = course_dir.write(course_with(PY_EXERCISE), tmp_path / "course")
    greet = next((root / "units").glob("*/u1-l1-*")) / "exercise" / "greet.py"
    # piped, so its output only arrives if it flushes: an editor's task panel reads it this way too
    p = subprocess.Popen([sys.executable, "learn.py", "check", "--watch"], cwd=root, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True)
    lines = []
    threading.Thread(target=lambda: lines.extend(p.stdout), daemon=True).start()
    try:
        deadline = time.time() + 60
        while "Save a file to check again" not in "".join(lines) and time.time() < deadline:
            time.sleep(0.1)
        assert "Not yet" in "".join(lines), "".join(lines)
        greet.write_text(PY_EXERCISE.solution[0].content)
        assert p.wait(timeout=60) == 0
    finally:
        p.kill()
    time.sleep(0.2)
    assert "Passed" in "".join(lines)


def test_check_watch_outside_a_course_is_still_a_course_command():
    from learning import front

    assert front.course_command(["check", "--watch"], None)


# as run_exercise sees it: terraform's errors go to stderr, which comes after stdout
TF_FAILED = 'tests/a.tftest.hcl... in progress\n  run "two_asserts"... fail\n  run "passes"... pass\n  run "errors_without_assert"... fail\ntests/a.tftest.hcl... tearing down\ntests/a.tftest.hcl... fail\ntests/b.tftest.hcl... in progress\n  run "bad_variable"... fail\n  run "in_b_fails"... skip\n  run "expects_failure_that_never_comes"... skip\ntests/b.tftest.hcl... tearing down\ntests/b.tftest.hcl... fail\n\nFailure! 1 passed, 3 failed, 2 skipped.\n\nError: Test assertion failed\n\n  on tests/a.tftest.hcl line 5, in run "two_asserts":\n   5:     condition     = output.cidr == "10.0.0.0/16"\n    ├────────────────\n    │ output.cidr is "10.1.0.0/16"\n\nthe VPC must use 10.0.0.0/16\n\nError: Test assertion failed\n\n  on tests/a.tftest.hcl line 9, in run "two_asserts":\n   9:     condition     = output.name == "ledger"\n    ├────────────────\n    │ output.name is "1234"\n\nthe name must be ledger\n\nError: Invalid function argument\n\n  on main.tf line 16, in output "parsed":\n  16:   value = tonumber(var.name)\n    ├────────────────\n    │ while calling tonumber(v)\n    │ var.name is "abcd"\n\nInvalid value for "v" parameter: cannot convert "abcd" to number; given\nstring must be a decimal representation of a number.\n\nError: Invalid value for variable\n\n  on tests/b.tftest.hcl line 3, in run "bad_variable":\n   3:   variables { name = "x" }\n    ├────────────────\n    │ var.name is "x"\n\nname must be longer than 2 characters\n\nThis was checked by the validation rule at main.tf:8,3-13.'
PY39_FAILED = 'FFF.E\n======================================================================\nERROR: test_total (test_greet.T)\n----------------------------------------------------------------------\nTraceback (most recent call last):\n  File "/course/exercise/test_greet.py", line 13, in test_total\n    self.assertEqual(total([1, 2]), 3)\n  File "/course/exercise/greet.py", line 4, in total\n    raise NotImplementedError("total is not written yet")\nNotImplementedError: total is not written yet\n\n======================================================================\nFAIL: test_greet (test_greet.T)\n----------------------------------------------------------------------\nTraceback (most recent call last):\n  File "/course/exercise/test_greet.py", line 7, in test_greet\n    self.assertEqual(greet("Ada"), "Hello, Ada!", "greet should say hello by name")\nAssertionError: \'\' != \'Hello, Ada!\'\n+ Hello, Ada! : greet should say hello by name\n\n======================================================================\nFAIL: test_greet_plain (test_greet.T)\n----------------------------------------------------------------------\nTraceback (most recent call last):\n  File "/course/exercise/test_greet.py", line 10, in test_greet_plain\n    self.assertEqual(greet("Bo"), "Hello, Bo!")\nAssertionError: \'\' != \'Hello, Bo!\'\n+ Hello, Bo!\n\n======================================================================\nFAIL: test_multiline (test_greet.T)\n----------------------------------------------------------------------\nTraceback (most recent call last):\n  File "/course/exercise/test_greet.py", line 16, in test_multiline\n    self.assertEqual("a\\nb\\nc", "a\\nB\\nc", "lines differ")\nAssertionError: \'a\\nb\\nc\' != \'a\\nB\\nc\'\n  a\n- b\n+ B\n  c : lines differ\n\n----------------------------------------------------------------------\nRan 5 tests in 0.001s\n\nFAILED (failures=3, errors=1)\n'


def run_failing(tmp_path, runner, files):
    from learning import learn_cli

    folder = tmp_path / runner
    for name, text in files.items():
        (folder / name).parent.mkdir(parents=True, exist_ok=True)
        (folder / name).write_text(text)
    outcome, output = learn_cli.run_exercise(folder, runner)
    return outcome, learn_cli.failures(runner, output)


PY_CASES = '''import unittest


class InsufficientFunds(Exception):
    pass


class T(unittest.TestCase):
    def test_chained(self):
        try:
            {}["acct"]
        except KeyError as e:
            raise InsufficientFunds("not enough in acct") from e

    def test_bare_assert(self):
        assert 1 == 2

    def test_colon_in_a_value(self):
        self.assertIn("x", "a : b")

    def test_long_message(self):
        self.assertEqual(1, 2, "first line\\nsecond line")

    def test_sub(self):
        for i in (1, 2):
            with self.subTest(i=i):
                self.assertEqual(i, 0)

    def test_colon_in_the_diff(self):
        self.assertEqual("c", "a : b")

    def test_colon_in_a_repr(self):
        self.assertEqual(Entry(), 1)


class Entry:
    def __repr__(self):
        return "<E debit : 10>"
'''


def test_python_failures_name_the_right_error_and_keep_values_whole(tmp_path):
    outcome, lines = run_failing(tmp_path, "python", {"test_cases.py": PY_CASES})
    assert outcome == "failed"
    assert "test_chained: test_cases.InsufficientFunds: not enough in acct" in lines  # the outer one the test saw
    assert "test_bare_assert: assert 1 == 2 failed" in lines
    assert "test_colon_in_a_value: 'x' not found in 'a : b'" in lines
    assert "test_long_message: first line second line (1 != 2)" in lines
    assert "test_sub (i=1): 1 != 0" in lines and "test_sub (i=2): 2 != 0" in lines
    assert "test_colon_in_the_diff: 'c' != 'a : b'" in lines                   # no message made up from the diff
    assert "test_colon_in_a_repr: <E debit : 10> != 1" in lines
    assert all("\n" not in line for line in lines)


@pytest.mark.skipif(shutil.which("node") is None, reason="needs node")
def test_node_failures_keep_what_differs_and_why_a_file_did_not_load(tmp_path):
    test = '''import { describe, it } from "node:test";
import assert from "node:assert/strict";
it("deep", () => { assert.deepEqual({ id: 1, balance: 10 }, { id: 1, balance: 20 }, "the balance should be 20"); });
describe("ledger", () => { it("balances", () => { assert.equal(0, 10); }); });
describe("transfers", () => { it("balances", () => { assert.equal(0, 2); }); });
'''
    outcome, lines = run_failing(tmp_path, "node", {"sum.test.mjs": test})
    assert outcome == "failed" and len(lines) == 3                         # listed twice by node, once here
    assert "deep: the balance should be 20 (got balance: 10, expected balance: 20)" in lines
    assert [line.split(":")[0] for line in lines[1:]] == ["balances (sum.test.mjs", "balances (sum.test.mjs"]

    # each file that doesn't load gets its own reason, never another file's or a line its code logged
    broken = {"tax.mjs": 'console.log("Error: just the learner logging");\nexport const rate = TAX_RATE * 2;\n',
              "tax.test.mjs": 'import { it } from "node:test";\nimport { rate } from "./tax.mjs";\nit("rate", () => {});\n',
              "fee.test.mjs": 'import { it } from "node:test";\nimport { fee } from "./missing.mjs";\nit("fee", () => {});\n',
              "lines.test.mjs": 'import { it } from "node:test";\nimport assert from "node:assert/strict";\n'
                                'it("lines", () => { assert.equal("a\\nb\\nc", "a\\nB\\nc"); });\n'}
    outcome, lines = run_failing(tmp_path / "broken", "node", broken)
    assert "tax.test.mjs: ReferenceError: TAX_RATE is not defined" in lines
    assert any(l.startswith("fee.test.mjs: Error: Cannot find module") for l in lines)
    assert "lines: Expected values to be strictly equal: got 'a\\nb\\nc', expected 'a\\nB\\nc'" in lines

    # what was thrown has a stack under it. A line logged after it, on the way out, isn't the reason
    from learning import learn_cli
    logged_late = ("ReferenceError: TAX_RATE is not defined\n    at file:///x/tax.mjs:2:21\n\nError: logged on the way out\n"
                   "\u2716 tax.test.mjs (1.0ms)\n  'test failed'\n\n\u2716 failing tests:\n\ntest at tax.test.mjs:1:1\n"
                   "\u2716 tax.test.mjs (1.0ms)\n  'test failed'\n")
    assert learn_cli.failures("node", logged_late) == ["tax.test.mjs: ReferenceError: TAX_RATE is not defined"]


@pytest.mark.skipif(shutil.which("terraform") is None, reason="needs terraform")
def test_terraform_failures_come_out_one_line_each_from_a_real_run(tmp_path, monkeypatch):
    monkeypatch.setenv("TF_CLI_CONFIG_FILE", "/dev/null")
    files = {"main.tf": 'variable "cidr" {\n  default = "10.1.0.0/16"\n}\noutput "cidr" {\n  value = var.cidr\n}\n',
             "tests/cidr.tftest.hcl": 'run "uses_the_right_cidr" {\n  command = plan\n  assert {\n'
             '    condition     = output.cidr == "10.0.0.0/16"\n    error_message = "the VPC must use 10.0.0.0/16"\n  }\n}\n'}
    outcome, lines = run_failing(tmp_path, "terraform", files)  # no providers, so nothing is downloaded
    assert outcome == "failed"
    assert lines == ['uses_the_right_cidr: the VPC must use 10.0.0.0/16 (output.cidr is "10.1.0.0/16")']

    # an error in main.tf names no run. Two of them go to their two runs, in order
    parse = {"main.tf": 'variable "name" {\n  type = string\n}\noutput "parsed" {\n  value = tonumber(var.name)\n}\n'}
    for f, value in (("a", "abc"), ("b", "xyz")):
        parse[f"tests/{f}.tftest.hcl"] = (f'run "{f}_parse" {{\n  command = plan\n  variables {{\n    name = "{value}"\n  }}\n}}\n')
    outcome, lines = run_failing(tmp_path / "parse", "terraform", parse)
    assert [l.split(":")[0] for l in lines] == ["a_parse", "b_parse"] and 'var.name is "xyz"' in lines[1]

    # two errors from one run both belong to it
    both = {"main.tf": parse["main.tf"] + 'output "again" {\n  value = tonumber("${var.name}x")\n}\n',
            "tests/a.tftest.hcl": parse["tests/a.tftest.hcl"].replace("a_parse", "both_parse")}
    outcome, lines = run_failing(tmp_path / "both", "terraform", both)
    assert [l.split(":")[0] for l in lines] == ["both_parse", "both_parse"]


def test_a_failing_check_shows_what_the_code_printed_and_any_output_keeps_its_start(tmp_path, monkeypatch, capsys):
    from learning import learn_cli

    noisy = PY_EXERCISE.model_copy(update={"starter": [CourseFile(
        path="greet.py", content='def greet(name):\n    print("DEBUG greeting", name)\n    return ""\n')]})
    root = course_dir.write(course_with(noisy), tmp_path / "course")
    out = learn(root, "check").stdout
    assert "Your code printed:\n  DEBUG greeting Ada" in out

    monkeypatch.setattr(learn_cli, "ROOT", root)
    monkeypatch.setattr(learn_cli, "STATE", root / ".learn" / "progress.json")
    monkeypatch.setattr(learn_cli, "run_exercise", lambda folder, runner: ("failed", "FIRST\n" + "x\n" * 4000 + "LAST"))
    learn_cli.check_once(learn_cli.state(), learn_cli.lessons()[0])
    shown = capsys.readouterr().out
    assert "FIRST" in shown and "LAST" in shown


def test_watch_looks_only_at_what_a_learner_edits(tmp_path):
    from learning import learn_cli

    for name in ("main.tf", "tests/a.tftest.hcl", ".terraform/modules/modules.json", ".terraform.lock.hcl",
                 ".main.tf.swp", "main.tf~", "report.json", "plan.out", "#main.tf#", "schema.sql"):
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text("x")
    assert sorted(learn_cli.snapshot(tmp_path, "terraform")) == ["main.tf", "tests/a.tftest.hcl"]
    # a file the lesson's answer changes counts whatever its kind: the ledger course has you edit schema.sql
    assert "schema.sql" in learn_cli.snapshot(tmp_path, "python", frozenset({"schema.sql"}))
    assert learn_cli.failures("terraform", 'tests/a.tftest.hcl... in progress\n  run "x"... fail\n'
                              'tests/a.tftest.hcl... fail\n\nFailure! 0 passed, 1 failed.\n') == ["x: failed"]


SLOW_TEST = '''import time
import unittest
from greet import greet


class T(unittest.TestCase):
    def test_greeting_file(self):
        with open("greeting.txt") as f:  # a file that isn't code, which the answer changes
            self.assertEqual(f.read().strip(), "hello", "greeting.txt should say hello")

    def test_greet(self):
        with open("report.json", "w") as f:  # what a check writes is no reason to check again
            f.write("{}")
        time.sleep(1.5)
        self.assertEqual(greet("Ada"), "Hello, Ada!", "greet should say hello by name")
'''


@pytest.mark.skipif(sys.platform == "win32", reason="signals to a process group are POSIX")
def test_watch_checks_a_save_made_during_a_check_and_never_its_own_writes(tmp_path):
    import signal
    import threading
    import time

    slow = PY_EXERCISE.model_copy(update={
        "checks": [CourseFile(path="test_greet.py", content=SLOW_TEST)],
        "starter": PY_EXERCISE.starter + [CourseFile(path="greeting.txt", content="hi\n")],
        "solution": PY_EXERCISE.solution + [CourseFile(path="greeting.txt", content="hello\n")]})
    root = course_dir.write(course_with(slow), tmp_path / "course")
    lesson = next((root / "units").glob("*/u1-l1-*"))

    def watch(argv):
        p = subprocess.Popen(argv, cwd=lesson / "exercise", stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, start_new_session=True)
        heard = []  # (when, line)
        threading.Thread(target=lambda: heard.extend((time.time(), l) for l in p.stdout), daemon=True).start()
        return p, heard

    def when(heard, text, n=1, wait=20):
        end = time.time() + wait
        while time.time() < end:
            hits = [t for t, l in heard if text in l]
            if len(hits) >= n:
                return hits[n - 1]
            time.sleep(0.05)
        raise AssertionError(f"never heard {text!r}: {''.join(l for _, l in heard)}")

    # a save while the first check runs gets a check of its own, which passes
    p, heard = watch([sys.executable, str(root / "learn.py"), "check", "--watch"])
    try:
        started = when(heard, "Checking")
        time.sleep(0.6)  # the check has loaded greet.py by now, and is in its 1.5 s sleep
        (lesson / "exercise" / "greet.py").write_text(PY_EXERCISE.solution[0].content)
        assert when(heard, "Not yet") - started > 1                     # the Checking line came first
        when(heard, "Checking", n=2)                                    # the save during the check counted
        when(heard, "Save a file to check again", n=2)
        (lesson / "exercise" / "greeting.txt").write_text("hello\n")    # and so does a file that isn't code
        assert p.wait(timeout=30) == 0 and when(heard, "Passed")
    finally:
        p.kill()

    # left alone after a failed check, it waits, and Ctrl-C through `learn` stops it cleanly
    (lesson / "exercise" / "greet.py").write_text(PY_EXERCISE.starter[0].content)
    (root / ".learn" / "progress.json").unlink()
    learn_cmd = [sys.executable, "-c", "import sys; from learning.front import main; sys.exit(main())"]
    p, heard = watch(learn_cmd + ["check", "--watch"])
    try:
        when(heard, "Save a file to check again")
        # an editor's short-lived file, gone well before the second look 0.3 s later, even on a busy
        # machine. 0.42 s apart, so across 12 of them some fall where a look (every 0.5 s) sees them
        for _ in range(12):
            (lesson / "exercise" / "tmp_x.py").write_text("x = 1\n")
            time.sleep(0.1)
            (lesson / "exercise" / "tmp_x.py").unlink()
            time.sleep(0.32)
        assert len([l for _, l in heard if "Checking" in l]) == 1
        os.killpg(p.pid, signal.SIGINT)
        assert p.wait(timeout=30) == 1
    finally:
        p.kill()
    assert "Traceback" not in "".join(l for _, l in heard)

    # Ctrl-C during a plain check stops it with 130, as shells report it, and no traceback
    p, heard = watch(learn_cmd + ["check"])
    try:
        when(heard, "Checking")
        time.sleep(0.5)
        os.killpg(p.pid, signal.SIGINT)
        assert p.wait(timeout=30) == 130
    finally:
        p.kill()
    assert "Traceback" not in "".join(l for _, l in heard)


def fake_editor(bin_dir, name="code"):
    """A stand-in for VS Code's command: writes down what it was asked to open."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    script = bin_dir / name
    script.write_text(f'#!/bin/sh\nfor a in "$@"; do echo "$a"; done > "{bin_dir}/opened.txt"\n')
    script.chmod(0o755)
    return bin_dir / "opened.txt"


def opened(record, wait=10):
    import time

    end = time.time() + wait
    while time.time() < end:
        if record.exists() and record.read_text().endswith("\n"):
            return record.read_text().splitlines()
        time.sleep(0.05)
    raise AssertionError("the editor was never opened")


@pytest.mark.skipif(sys.platform == "win32", reason="the stand-in editor is a shell script")
def test_next_opens_the_lesson_and_the_files_to_change_in_the_editor(tmp_path, monkeypatch, capsys):
    # the course was all Markdown in a terminal, and nothing said to open an editor
    from learning import learn_cli

    root = course_dir.write(course_with(PY_EXERCISE), tmp_path / "course")
    lesson = next((root / "units").glob("*/u1-l1-*"))
    record = fake_editor(tmp_path / "bin")
    monkeypatch.setenv("PATH", str(tmp_path / "bin"))
    monkeypatch.delenv("LEARN_EDITOR", raising=False)
    monkeypatch.setattr(learn_cli, "ROOT", root)
    monkeypatch.setattr(learn_cli, "STATE", root / ".learn" / "progress.json")
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)

    learn_cli.cmd_next(learn_cli.state(), None)
    shown = capsys.readouterr().out
    assert "Opened in VS Code" in shown and "run `python3 learn.py check` in VS Code's terminal" in shown
    paths = opened(record)
    assert paths[:2] == [str(root.resolve()), str((lesson / "README.md").resolve())]
    assert str((lesson / "exercise" / "greet.py").resolve()) in paths
    assert not any(p.endswith("test_greet.py") for p in paths) and all(p.startswith("/") for p in paths)
    settings = root / ".vscode" / "settings.json"
    assert json.loads(settings.read_text()) == learn_cli.PREVIEW
    settings.write_text("{}")                                       # someone's own settings stay theirs
    learn_cli.cmd_next(learn_cli.state(), None)
    assert settings.read_text() == "{}"

    monkeypatch.setenv("LEARN_EDITOR", "none")                       # or it only says where things are
    learn_cli.cmd_next(learn_cli.state(), None)
    shown = capsys.readouterr().out
    assert "Work through it in VS Code or Cursor: open this course's folder" in shown
    assert "Install 'code' command" not in shown                     # none was their choice
    monkeypatch.setenv("LEARN_EDITOR", "subl")
    learn_cli.cmd_next(learn_cli.state(), None)
    assert "LEARN_EDITOR is 'subl', and there's no command by that name" in capsys.readouterr().out
    monkeypatch.delenv("LEARN_EDITOR")
    monkeypatch.setenv("PATH", str(tmp_path / "nothing"))
    learn_cli.cmd_next(learn_cli.state(), None)
    assert "https://code.visualstudio.com" in capsys.readouterr().out


@pytest.mark.skipif(sys.platform == "win32", reason="the stand-in editor is a shell script")
def test_a_cmd_editor_is_not_handed_a_path_cmd_exe_would_read_as_a_command(tmp_path, monkeypatch):
    from learning import learn_cli

    root = course_dir.write(course_with(PY_EXERCISE), tmp_path / "a&calc")
    record = fake_editor(tmp_path / "bin", "code.cmd")
    monkeypatch.setattr(learn_cli, "ROOT", root)
    monkeypatch.setattr(learn_cli, "editor", lambda: str(tmp_path / "bin" / "code.cmd"))
    assert learn_cli.open_lesson(learn_cli.lessons()[0]) is None
    assert not record.exists()


def test_nothing_is_opened_when_the_output_is_not_a_terminal(tmp_path):
    root = course_dir.write(course_with(PY_EXERCISE), tmp_path / "course")
    out = learn(root, "next").stdout                                  # piped: tests, scripts, editors' tasks
    assert "Opened in" not in out and "Work through it" not in out and not (root / ".vscode").exists()


@pytest.mark.skipif(sys.platform == "win32", reason="the stand-in editor is a shell script")
def test_the_editor_is_detached_and_none_opens_nothing(tmp_path, monkeypatch):
    import time

    from learning import learn_cli

    root = course_dir.write(course_with(PY_EXERCISE), tmp_path / "course")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    how = bin_dir / "how.txt"
    # its own session, nothing of ours on stdin, stdout or stderr, and none of learn's settings
    probe = ("import os; n = os.stat('/dev/null').st_rdev; "
             f"open({str(how)!r}, 'w').write(str(os.getsid(0) in (os.getpid(), os.getppid())) + ' ' + "
             "str(all(os.fstat(i).st_rdev == n for i in (0, 1, 2))) + ' ' + str('LEARN_HERE' in os.environ))")
    (bin_dir / "code").write_text(f'#!/bin/sh\n"{sys.executable}" -c "{probe}"\n')
    (bin_dir / "none").write_text(f'#!/bin/sh\necho ran > "{bin_dir}/none-ran.txt"\n')
    for n in ("code", "none"):
        (bin_dir / n).chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))
    monkeypatch.setenv("LEARN_HERE", str(root))                        # as `learn` sets it
    monkeypatch.delenv("LEARN_EDITOR")
    monkeypatch.setattr(learn_cli, "ROOT", root)
    monkeypatch.setattr(learn_cli, "STATE", root / ".learn" / "progress.json")
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)

    learn_cli.cmd_next(learn_cli.state(), None)
    end = time.time() + 10
    while time.time() < end and not (how.exists() and how.read_text()):
        time.sleep(0.05)
    assert how.read_text() == "True True False"

    monkeypatch.setenv("LEARN_EDITOR", "none")                         # none means none, even with a `none` about
    learn_cli.cmd_next(learn_cli.state(), None)
    time.sleep(1)
    assert not (bin_dir / "none-ran.txt").exists()


@pytest.mark.skipif(sys.platform == "win32", reason="the stand-in editor is a shell script")
def test_the_files_the_answer_changes_open_first_and_the_lesson_id_carries_through(tmp_path, monkeypatch, capsys):
    from learning import learn_cli

    many = Exercise(task="t", hints=["h"], checks=[CourseFile(path="test_z.py", content="")],
                    starter=[CourseFile(path=n, content="") for n in ("A.py", "b.py", "c.py", "d.py", "e.py", "f.py",
                                                                    "z_last.py")],
                    solution=[CourseFile(path="z_last.py", content="x = 1\n")])
    c = course_with(many)
    c.lessons.append(c.lessons[0].model_copy(update={"id": "u1-l2", "title": "Second", "exercise": None}))
    c.curriculum.units[0].lessons.append(c.curriculum.units[0].lessons[0].model_copy(update={"id": "u1-l2"}))
    root = course_dir.write(c, tmp_path / "course")
    record = fake_editor(tmp_path / "bin")
    monkeypatch.setenv("PATH", str(tmp_path / "bin"))
    monkeypatch.delenv("LEARN_EDITOR")
    monkeypatch.setattr(learn_cli, "ROOT", root)
    monkeypatch.setattr(learn_cli, "STATE", root / ".learn" / "progress.json")
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)

    learn_cli.cmd_next(learn_cli.state(), None)
    assert opened(record)[2].endswith("/exercise/z_last.py")           # the one to change, though it sorts last
    record.unlink()
    learn_cli.cmd_next(learn_cli.state(), "u1-l2")                     # no exercise: no files to change
    shown = capsys.readouterr().out.split("Opened in")[-1]
    assert "Read the lesson there, then run `python3 learn.py quiz u1-l2`" in shown and "files you'll change" not in shown
    learn_cli.cmd_next(learn_cli.state(), "u1-l1")
    assert "`python3 learn.py check --watch`" in capsys.readouterr().out
    c.lessons[1].exercise = many                                       # a lesson named, not the one you're on
    root = course_dir.write(c, tmp_path / "course2")
    monkeypatch.setattr(learn_cli, "ROOT", root)
    monkeypatch.setattr(learn_cli, "STATE", root / ".learn" / "progress.json")
    learn_cli.cmd_next(learn_cli.state(), "u1-l2")
    assert "`python3 learn.py check u1-l2 --watch`" in capsys.readouterr().out


def test_the_lessons_still_to_come_are_described_by_whether_the_build_is_alive(tmp_path, monkeypatch, capsys):
    import os
    import time

    from learning import learn_cli

    root = course_dir.write(course_with(PY_EXERCISE), tmp_path / "course")
    note = root / ".learn" / "building.json"
    monkeypatch.setattr(learn_cli, "ROOT", root)

    def told(**fields):
        note.write_text(json.dumps({"total": 2, "request": "Go, the \"real\" way $(touch pwned)", "engine": "strands",
                                    "running": True, "pid": os.getpid(), "updated": time.time(), **fields}))
        return learn_cli.still_to_come()

    assert told() == "Lesson 2 isn't written yet. The build is on it now, and `python3 learn.py next` shows it once it's ready."
    gone = told(pid=2 ** 22 + 12345)                                    # its process is gone: it stopped
    assert gone.endswith("""To carry on, run: learn --engine strands 'Go, the "real" way $(touch pwned)'""")
    assert "stopped" in told(running="false") and "stopped" in told(updated=time.time() + 3600)
    assert told(total=1e309) is None and told(total=1) is None
    assert "Lessons 2 and 3 aren't" in told(total=3) and "Lessons 2 to 4 aren't" in told(total=4)


def test_a_partial_course_has_no_dead_links_and_keeps_what_the_learner_deleted(tmp_path):
    c = course_with(PY_EXERCISE)
    c.curriculum.units[0].lessons.append(c.curriculum.units[0].lessons[0].model_copy(update={"id": "u1-l2",
                                                                                        "title": "Second"}))
    root = course_dir.write(c, tmp_path / "course")
    assert "Second (still being written)" in (root / "README.md").read_text()
    unit = next((root / "units").glob("*/README.md")).read_text()
    assert "- Second (still being written)" in unit
    starter = next((root / "units").glob("*/u1-l1-*")) / "exercise" / "greet.py"
    starter.unlink()                                                   # the learner deleted it
    course_dir.write(c, root)
    assert not starter.exists()


def test_a_solution_never_shows_a_file_the_build_is_halfway_through(tmp_path):
    root = course_dir.write(course_with(PY_EXERCISE), tmp_path / "course")
    answer = next((root / "units").glob("*/u1-l1-*")) / ".answers" / "solution"
    (answer / ".greet.py.123-456.tmp").write_text("half a file")
    out = learn(root, "solution").stdout
    assert "half a file" not in out and "Hello" in out


def test_a_lesson_not_handed_over_yet_is_filled_in_if_a_write_stopped_partway(tmp_path):
    # the build died after writing the starter and before the test: the test never came, and 3.9 passed it
    root = course_dir.write(course_with(PY_EXERCISE), tmp_path / "course")
    lessons_file = root / ".learn" / "lessons.json"
    lessons_file.write_text("[]")                                     # it never reached the learner
    exercise = next((root / "units").glob("*/u1-l1-*")) / "exercise"
    (exercise / "test_greet.py").unlink()
    course_dir.write(course_with(PY_EXERCISE), root)
    assert (exercise / "test_greet.py").is_file()


def test_the_course_names_a_version_only_when_a_page_states_it_and_says_what_it_numbers(tmp_path):
    # "Written against Ledger Engineering and Double-Entry Bookkeeping 3.14.8": Python's, never checked
    c = course()
    spec = c.knowledge.spec
    unchecked = c.model_copy(update={"knowledge": c.knowledge.model_copy(update={"spec": spec.model_copy(
        update={"version": "3.14.8", "version_of": "Python", "version_checked": False})})})
    assert "Written against" not in (course_dir.write(unchecked, tmp_path / "a") / "README.md").read_text()
    checked = c.model_copy(update={"knowledge": c.knowledge.model_copy(update={"spec": spec.model_copy(
        update={"version": "3.14.8", "version_of": "Python", "version_checked": True})})})
    assert "Written against Python 3.14.8" in (course_dir.write(checked, tmp_path / "b") / "README.md").read_text()

"""The course as a learner uses it: a folder, and learn.py.

These write a real course folder and drive learn.py the way a person would, including
running the real terraform binary on the exercise.
"""

from __future__ import annotations

import json
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
    assert "✖ adds two numbers" in out and "sum(2, 3) should be 5" in out
    assert "node:internal" not in out and "    at " not in out


def test_lessons_name_the_learn_command_and_the_course_says_how_to_do_without_it(tmp_path):
    root = course_dir.write(course(), tmp_path / "course")
    lesson = next((root / "units").glob("*/u1-l1-*/README.md")).read_text()
    assert "learn check" in lesson and "python3 learn.py" not in lesson
    assert "Type `python3 learn.py` wherever it says `learn`" in (root / "README.md").read_text()

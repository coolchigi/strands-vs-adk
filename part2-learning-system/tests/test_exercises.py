"""Running an exercise the way the learner will, with the real terraform binary."""

from __future__ import annotations

import shutil

import pytest

from learning import exercises
from learning.model import CourseFile, Exercise

needs_terraform = pytest.mark.skipif(shutil.which("terraform") is None, reason="needs terraform")

PROVIDER = 'terraform {\n  required_providers {\n    aws = { source = "hashicorp/aws", version = "~> 6.0" }\n  }\n}\n'
NO_PROVIDER = 'terraform {\n  required_providers {\n    # TODO: the aws provider, hashicorp/aws, ~> 6.0\n  }\n}\n'
VPC = 'resource "aws_vpc" "main" {\n  cidr_block = "10.0.0.0/16"\n}\n'
TODO_VPC = '# TODO: the CIDR block is 10.0.0.0/16\nresource "aws_vpc" "main" {\n  cidr_block = "172.16.0.0/16"\n}\n'
CHECK = CourseFile(path="tests/vpc.tftest.hcl", content='''mock_provider "aws" {}

run "vpc" {
  command = apply
  assert {
    condition     = aws_vpc.main.cidr_block == "10.0.0.0/16"
    error_message = "aws_vpc.main should use 10.0.0.0/16"
  }
}
''')


def exercise(starter: str, solution: str) -> Exercise:
    return Exercise(task="t", starter=[CourseFile(path="main.tf", content=starter)],
                    solution=[CourseFile(path="main.tf", content=solution)], checks=[CHECK], hints=["h"])


@needs_terraform
def test_a_gap_the_checks_never_look_at_is_caught():
    # a real lesson: the learner could leave the provider TODO alone and still pass,
    # because Terraform infers hashicorp/aws anyway and nothing tested it
    problems = exercises.verify(exercise(NO_PROVIDER + TODO_VPC, PROVIDER + VPC))
    assert len(problems) == 1 and "main.tf line 3" in problems[0], problems


@needs_terraform
def test_an_exercise_whose_every_gap_is_tested_passes():
    # the TODO comment differs from the solution too, and a comment isn't a gap
    assert exercises.verify(exercise(PROVIDER + TODO_VPC, PROVIDER + VPC)) == []


# -- the other subjects: Python and Node, with their own built-in test tools ---------------

def ex(starter: dict, solution: dict, checks: dict) -> Exercise:
    files = lambda d: [CourseFile(path=p, content=c) for p, c in d.items()]  # noqa: E731
    return Exercise(task="t", starter=files(starter), solution=files(solution), checks=files(checks), hints=["h"])


PY_TEST = '''import unittest
from greet import greet, shout


class T(unittest.TestCase):
    def test_greet(self):
        self.assertEqual(greet("Ada"), "Hello, Ada!", "greet should say hello by name")

    def test_shout(self):
        self.assertEqual(shout("hi"), "HI!", "shout should upper-case and add a !")
'''
PY_DONE = 'def greet(name):\n    return f"Hello, {name}!"\n\n\ndef shout(text):\n    return text.upper() + "!"\n'
PY_TODO_BOTH = 'def greet(name):\n    return ""  # TODO\n\n\ndef shout(text):\n    return ""  # TODO\n'


def test_a_python_exercise_is_proven_like_a_terraform_one():
    assert exercises.verify(ex({"greet.py": PY_TODO_BOTH}, {"greet.py": PY_DONE}, {"test_greet.py": PY_TEST})) == []


def test_a_python_gap_the_tests_skip_is_caught():
    only_greet = PY_TEST.split("    def test_shout")[0]
    problems = exercises.verify(ex({"greet.py": PY_TODO_BOTH}, {"greet.py": PY_DONE}, {"test_greet.py": only_greet}))
    assert len(problems) == 1 and "greet.py line 6" in problems[0], problems


def test_python_a_learner_on_3_9_cant_run_is_caught():
    newer = PY_DONE + "\n\ndef kind(x):\n    match x:\n        case 1:\n            return 'one'\n"
    problems = exercises.verify(ex({"greet.py": PY_TODO_BOTH}, {"greet.py": newer}, {"test_greet.py": PY_TEST}))
    assert any("needs a Python newer than 3.9" in p for p in problems), problems


TS_TEST = '''import { test } from "node:test";
import assert from "node:assert/strict";
import { area } from "./shapes.ts";

test("area of a rectangle", () => {
  assert.equal(area({ width: 3, height: 4 }), 12, "area should multiply width by height");
});
'''
TS_DONE = "export type Rect = { width: number; height: number };\n\nexport function area(r: Rect): number {\n  return r.width * r.height;\n}\n"
TS_TODO = "export type Rect = { width: number; height: number };\n\nexport function area(r: Rect): number {\n  return 0; // TODO\n}\n"


@pytest.mark.skipif(shutil.which("node") is None, reason="needs node")
def test_a_typescript_exercise_runs_on_node_with_nothing_installed():
    assert exercises.verify(ex({"shapes.ts": TS_TODO}, {"shapes.ts": TS_DONE}, {"shapes.test.ts": TS_TEST})) == []


@pytest.mark.skipif(shutil.which("node") is None, reason="needs node")
def test_a_typescript_starter_that_does_not_parse_is_caught():
    broken = TS_TODO.replace("return 0; // TODO", "return r.width *")
    problems = exercises.verify(ex({"shapes.ts": broken}, {"shapes.ts": TS_DONE}, {"shapes.test.ts": TS_TEST}))
    assert len(problems) == 1 and "starter doesn't run" in problems[0], problems


def test_tests_nothing_can_run_are_caught_when_there_is_code():
    problems = exercises.verify(ex({"greet.py": PY_TODO_BOTH}, {"greet.py": PY_DONE}, {"checks.py": PY_TEST}))
    assert len(problems) == 1 and "aren't test files anything can run" in problems[0]


def test_an_exercise_with_no_code_is_left_to_the_learner():
    # a spoken language, say: nothing can run it, and learn.py tells the learner to judge it
    essay = ex({"answer.md": "Write 3 sentences in Spanish."}, {"answer.md": "Hola. Me llamo Ada. Vivo en Lagos."}, {})
    assert exercises.verify(essay) == []


TYPED_TEST = '''import { test } from "node:test";
import assert from "node:assert/strict";
import { formatUsername } from "./utils.ts";

test("null becomes Anonymous", () => {
  assert.equal(formatUsername(null), "Anonymous", "formatUsername(null) should be Anonymous");
});
'''
TYPED = ('export function formatUsername(username: string | null): string {\n'
         '  return username === null ? "Anonymous" : username.trim();\n}\n')
UNTYPED = ('// TODO: annotate username as string | null, returning a string\n'
           'export function formatUsername(username) {\n'
           '  return username === null ? "Anonymous" : username.trim();\n}\n')


@pytest.mark.skipif(shutil.which("npm") is None, reason="needs node and npm")
def test_a_typescript_gap_can_be_the_types_themselves():
    # a real lesson: "annotate username as string | null", and the tests only called the
    # function. Node strips types without checking them, so only the compiler can see this
    assert exercises.verify(ex({"utils.ts": UNTYPED}, {"utils.ts": TYPED}, {"utils.test.ts": TYPED_TEST})) == []
    starter = exercises.run([CourseFile(path="utils.ts", content=UNTYPED),
                             CourseFile(path="utils.test.ts", content=TYPED_TEST)], "node")
    assert starter[0] == "failed" and "implicitly has an 'any' type" in starter[1]


@pytest.mark.skipif(shutil.which("npm") is None, reason="needs node and npm")
def test_an_exercise_with_its_own_tsconfig_is_type_checked_with_it():
    # a lesson on tsconfig.json failed 3 times: TypeScript won't take file names on the
    # command line when a tsconfig.json is there
    config = ('{"compilerOptions": {"strict": true, "module": "nodenext", "target": "esnext", '
              '"noEmit": true, "allowImportingTsExtensions": true}}\n')
    done = ex({"utils.ts": UNTYPED, "tsconfig.json": config}, {"utils.ts": TYPED, "tsconfig.json": config},
              {"utils.test.ts": TYPED_TEST})
    assert exercises.verify(done) == []

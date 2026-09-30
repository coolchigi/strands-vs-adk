"""Proving an exercise is worth doing, by running it.

An exercise passes only if all of these hold:

- the solution, with the checks, passes
- the untouched starter, with the checks, runs and fails
- each gap, left undone on its own in the finished files, makes the checks fail

An exercise whose checks already pass has nothing for the learner to do. A starter that
doesn't run gives the learner an error in the code instead of a test telling them what's
missing. And a gap the checks pass without is one the learner can skip.

The checks run with each subject's own tools, the same way learn.py runs them (see
learn_cli.run_exercise): `terraform test` with a mock provider for Terraform, so no cloud
account is needed, `unittest` for Python, and Node's test runner for JavaScript and
TypeScript. Mocks accept values a real API would reject (an AMI id, a CIDR), so a passing
Terraform check proves the configuration is right, not that AWS would accept it.
"""

from __future__ import annotations

import ast
import difflib
import os
import re
import tempfile
from pathlib import Path

from .learn_cli import CODE, run_exercise, runner_for
from .model import CourseFile, Exercise

TIMEOUT_S = 600
PLUGIN_CACHE = Path(os.environ.get("TF_PLUGIN_CACHE_DIR",
                                   Path.home() / ".cache" / "learning-system" / "terraform-plugins"))


# Terraform writes these itself. A model that writes one invents it: a lock file's
# checksums come from the provider package, so a made-up one stops `terraform init`.
GENERATED = re.compile(r"(^|/)(\.terraform\.lock\.hcl|\.terraform/.*|[^/]*\.tfstate(\.backup)?|[^/]*\.tfplan)$")


def authored(files: list[CourseFile]) -> list[CourseFile]:
    """The files a person writes, without the ones Terraform generates."""
    return [f for f in files if not GENERATED.search(f.path)]


def without_generated(exercise: Exercise | None) -> Exercise | None:
    if exercise is None:
        return None
    return exercise.model_copy(update={"starter": authored(exercise.starter),
                                       "solution": authored(exercise.solution),
                                       "checks": authored(exercise.checks)})


def lay_out(files: list[CourseFile], root: Path) -> str | None:
    root = root.resolve()  # macOS: /var is a symlink to /private/var
    for f in files:
        target = (root / f.path.lstrip("/")).resolve()
        if root not in target.parents:
            return f"{f.path} points outside the exercise folder"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f.content)
    return None


def run(files: list[CourseFile], runner: str | None) -> tuple[str, str]:
    """Lay the files out in a fresh folder and run the checks, the way learn.py will."""
    PLUGIN_CACHE.mkdir(parents=True, exist_ok=True)
    env = {"TF_PLUGIN_CACHE_DIR": str(PLUGIN_CACHE), "TF_IN_AUTOMATION": "1", "CHECKPOINT_DISABLE": "1"}
    with tempfile.TemporaryDirectory() as tmp:
        problem = lay_out(files, Path(tmp))
        if problem:
            return "invalid", problem
        return run_exercise(Path(tmp).resolve(), runner, env=env, timeout=TIMEOUT_S)


_ASSERT = re.compile(r"assert\s*\{(.*?)\n\s*\}", re.S)


def unreadable_asserts(checks: list[CourseFile]) -> list[str]:
    """Terraform assert blocks with no error_message. A learner who fails one learns nothing."""
    out = []
    for f in checks:
        for block in _ASSERT.findall(f.content):
            if "error_message" not in block:
                out.append(f"{f.path} has an assert with no error_message")
    return out


RUNNABLE = (".tf",) + CODE["python"] + CODE["node"]
TEST_NAMES = ("tests/*.tftest.hcl for Terraform, test_*.py for Python, or *.test.ts / *.test.js "
              "for TypeScript and JavaScript")


OLDEST_PYTHON = (3, 9)  # what macOS ships as /usr/bin/python3


def too_new_for_python(files: list[CourseFile]) -> list[str]:
    """Syntax the oldest Python a learner is likely to have can't parse.

    Courses are built on a newer Python than many learners run. ast's feature_version is
    best effort: it rejects match statements, and lets a few smaller things through.
    """
    out = []
    for f in files:
        if f.path.endswith(".py"):
            try:
                ast.parse(f.content, f.path, feature_version=OLDEST_PYTHON)
            except SyntaxError as e:
                out.append(f"{f.path} line {e.lineno} needs a Python newer than "
                           f"{'.'.join(map(str, OLDEST_PYTHON))}: {e.msg}")
    return out


def verify(exercise: Exercise) -> list[str]:
    """What is wrong with this exercise. Empty means a learner can do it and be checked.

    The runner comes from the test files' names, so it's decided by what the teacher wrote,
    and the same runner checks the learner's work in learn.py.
    """
    runner = runner_for([f.path for f in exercise.checks])
    if runner is None:
        if any(f.path.endswith(RUNNABLE) for f in exercise.solution + exercise.starter):
            return [f"the checks aren't test files anything can run. Name them {TEST_NAMES}"]
        return []  # nothing can run this kind of exercise. learn.py tells the learner to judge it
    problems = unreadable_asserts(exercise.checks) if runner == "terraform" else []
    if runner == "python":
        problems += too_new_for_python(exercise.solution + exercise.starter + exercise.checks)
    if problems:
        return problems

    outcome, output = run(exercise.solution + exercise.checks, runner)
    if outcome == "missing":
        return [f"this exercise could not be run here: {output}"]
    if outcome != "passed":
        return [f"the solution does not pass its own checks:\n{output[-1500:]}"]

    outcome, output = run(exercise.starter + exercise.checks, runner)
    if outcome == "invalid":
        return [f"the starter doesn't run, so the learner would see an error in the code instead of "
                f"a failing test:\n{output[-1500:]}"]
    if outcome == "passed":
        return ["the untouched starter already passes the checks, so there is nothing to do"]
    return untested_gaps(exercise, runner)


def _only_comments(lines: list[str]) -> bool:
    return all(not x.strip() or x.strip().startswith(("#", "//")) for x in lines)


def gaps(exercise: Exercise) -> list[tuple[str, list[CourseFile]]]:
    """Each place the learner has to change, as the solution with just that place left undone."""
    starter = {f.path: f.content.splitlines(keepends=True) for f in exercise.starter}
    out = []
    for f in exercise.solution:
        others = [g for g in exercise.solution if g.path != f.path]
        if f.path not in starter:
            out.append((f"{f.path}, which the learner creates", others))
            continue
        before, after = starter[f.path], f.content.splitlines(keepends=True)
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, before, after).get_opcodes():
            if tag == "equal" or _only_comments(before[i1:i2] + after[j1:j2]):
                continue
            undone = "".join(after[:j1] + before[i1:i2] + after[j2:])
            out.append((f"{f.path} line {j1 + 1}", others + [CourseFile(path=f.path, content=undone)]))
    return out


def untested_gaps(exercise: Exercise, runner: str) -> list[str]:
    """A gap the checks pass without is one a learner can skip and still be told they passed.

    The starter failing proves at least one gap is tested, not all of them. So each gap is
    put back on its own into the finished files, and the checks have to fail every time.
    """
    problems = []
    for where, files in gaps(exercise):
        if run(files + exercise.checks, runner)[0] == "passed":
            problems.append(f"the checks don't test the gap at {where}: with just that left as the starter "
                            "has it, the checks still pass. Test it, or fill it in for the learner.")
    return problems


# -- are the provider pins current? ---------------------------------------------------
#
# Validation proves the code runs, not that it teaches today's provider. A model that
# learned Terraform a year ago pins the AWS provider to ~> 5.0, and validate is happy.

import functools  # noqa: E402

import httpx  # noqa: E402

_BLOCK = re.compile(r"\{([^{}]*)\}")
_SOURCE = re.compile(r'source\s*=\s*"([^"]+)"')
_VERSION = re.compile(r'version\s*=\s*"([^"]+)"')


def _parts(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3])


def allows(constraint: str, version: str) -> bool:
    """Does a Terraform version constraint admit this version? Handles = != > >= < <= ~>."""
    have = _parts(version)
    for clause in constraint.split(","):
        m = re.match(r"\s*(~>|>=|<=|!=|=|>|<)?\s*v?([\d.]+)", clause)
        if not m:
            continue
        op, want = m.group(1) or "=", _parts(m.group(2))
        if op == "~>":
            upper = (want[0] + 1,) if len(want) <= 2 else (want[0], want[1] + 1)
            if not (have >= want and have[:len(upper)] < upper):
                return False
            continue
        cut = have[:len(want)]
        if not {"=": cut == want, "!=": cut != want, ">": have > want, ">=": have >= want,
                "<": have < want, "<=": cut <= want}[op]:
            return False
    return True


@functools.lru_cache(maxsize=None)
def latest_version(source: str) -> str | None:
    source = source.removeprefix("registry.terraform.io/")
    if source.count("/") != 1:
        return None
    try:
        return httpx.get(f"https://registry.terraform.io/v1/providers/{source}", timeout=20).json().get("version")
    except (httpx.HTTPError, ValueError):
        return None


def pins(files: list[CourseFile]) -> list[tuple[str, str]]:
    found = []
    for f in files:
        for block in _BLOCK.findall(f.content):
            s, v = _SOURCE.search(block), _VERSION.search(block)
            if s and v:
                found.append((s.group(1), v.group(1)))
    return found


def stale_pins(files: list[CourseFile]) -> list[str]:
    """One sentence per provider pinned behind its current release."""
    out = []
    for source, constraint in pins(files):
        latest = latest_version(source)
        if latest and not allows(constraint, latest):
            out.append(f'{source} is pinned "{constraint}", which rules out the current release '
                       f'{latest}. Pin "~> {latest.split(".")[0]}.0".')
    return list(dict.fromkeys(out))

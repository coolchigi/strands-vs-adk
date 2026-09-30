"""Work through this course.

    python3 learn.py next        where you are, and what's next
    python3 learn.py check       run the current exercise's tests
    python3 learn.py hint        one hint at a time
    python3 learn.py solution    show the solution, and record that you looked
    python3 learn.py quiz        answer the questions, then see the answers
    python3 learn.py review      questions you missed, when they're due again
    python3 learn.py report "…"  flag something wrong in the current lesson
    python3 learn.py status      how far you are

Standard library only, so it runs anywhere the course folder goes. Each exercise's tests
run with its own subject's tools: `terraform test` for Terraform, `unittest` for Python,
and Node's built-in test runner for JavaScript and TypeScript.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

# the course folder: where this file sits, or where `learn` says it is. `learn` runs its own,
# newer copy of this file, so a fix reaches courses built before it
ROOT = Path(os.environ.get("LEARN_ROOT") or Path(__file__).resolve().parent)
CMD = os.environ.get("LEARN_AS", "python3 learn.py")  # `learn` sets this to "learn" when it runs us
STATE = ROOT / ".learn" / "progress.json"
DAY = 86400
INTERVALS = [1 * DAY, 3 * DAY, 7 * DAY, 21 * DAY]  # a missed question comes back, spaced further each time


# -- running an exercise's tests ---------------------------------------------------------
#
# The course builder uses these same functions to prove every exercise before a learner
# sees it, so what passes there is what passes here.

INSTALL = {"terraform": "Terraform: https://developer.hashicorp.com/terraform/install",
           "node": "Node.js: https://nodejs.org/en/download"}
TS = (".ts", ".mts", ".cts")
CODE = {"python": (".py",), "node": (".js", ".mjs", ".cjs") + TS}
_PY_SYNTAX = "import ast, sys\nfor f in sys.argv[1:]:\n    ast.parse(open(f).read(), f)"


def is_test(runner: str, name: str) -> bool:
    if runner == "terraform":
        return name.endswith(".tftest.hcl")
    if runner == "python":
        return bool(re.fullmatch(r"test_.+\.py|.+_test\.py", name))
    return bool(re.fullmatch(r".+\.test\.(?:js|mjs|cjs|ts|mts|cts)", name))


def runner_for(paths: list[str]) -> str | None:
    """Which tools run an exercise, from its test files' names. None if nothing can run it."""
    names = [Path(p).name for p in paths]
    for runner in ("terraform", "python", "node"):
        if any(is_test(runner, n) for n in names):
            return runner
    return None


def node_version() -> tuple[int, ...] | None:
    try:
        out = subprocess.run(["node", "--version"], capture_output=True, text=True).stdout
    except OSError:
        return None
    found = re.findall(r"\d+", out)
    return tuple(int(x) for x in found[:3]) if found else None


def node_flags(uses_typescript: bool) -> list[str] | str:
    """What Node needs to run TypeScript, or why it can't. Node strips types itself from 22.6,
    behind a flag until 22.18 and 23.6."""
    if not uses_typescript:
        return []
    v = node_version()
    if v is None or v < (22, 6):
        return "TypeScript exercises need Node.js 22.6 or newer. " + INSTALL["node"]
    if v >= (23, 6) or (22, 18) <= v < (23, 0):
        return []
    return ["--experimental-strip-types", "--disable-warning=ExperimentalWarning"]


# Node runs TypeScript by stripping the types, without checking them. So TypeScript exercises
# also go through the real compiler in strict mode, fetched once with npm (which comes with
# Node) into a folder of our own, with Node's type definitions for node:test and friends.
TSC_HOME = Path(os.environ.get("LEARN_TSC_HOME") or Path.home() / ".cache" / "learning-system" / "typescript")


def typescript_compiler() -> list[str] | str:
    """The compiler, ready to type-check, or why it isn't available."""
    tsc = TSC_HOME / "node_modules" / ".bin" / "tsc"
    if not tsc.exists():
        if shutil.which("npm") is None:
            return "Checking TypeScript types needs npm, which comes with " + INSTALL["node"]
        print("Fetching the TypeScript compiler. This happens once.", file=sys.stderr)
        p = subprocess.run(["npm", "install", "--prefix", str(TSC_HOME), "typescript", "@types/node",
                            "--no-audit", "--no-fund", "--silent"], capture_output=True, text=True)
        if p.returncode != 0 or not tsc.exists():
            return "Couldn't fetch the TypeScript compiler with npm:\n" + (p.stdout + p.stderr).strip()[-1000:]
    # what every check needs, whatever the exercise's own settings say
    return [str(tsc), "--noEmit", "--allowImportingTsExtensions", "--skipLibCheck", "--typeRoots",
            str(TSC_HOME / "node_modules" / "@types"), "--types", "node", "--pretty", "false"]


def steps(runner: str, folder: Path) -> list[tuple[str, list[str]]] | str:
    """The commands that check an exercise, in order, or what's missing to run them."""
    files = sorted(str(p.relative_to(folder)) for p in folder.rglob("*")
                   if p.is_file() and not any(part.startswith(".") for part in p.relative_to(folder).parts))
    tests = [f for f in files if is_test(runner, Path(f).name)]
    if runner == "terraform":
        if shutil.which("terraform") is None:
            return "This exercise needs " + INSTALL["terraform"]
        return [("setup", ["terraform", "init", "-backend=false", "-input=false", "-no-color"]),
                ("syntax", ["terraform", "validate", "-no-color"]),
                ("test", ["terraform", "test", "-no-color"])]
    if runner == "python":
        code = [f for f in files if f.endswith(CODE["python"])]
        return [("syntax", [sys.executable, "-c", _PY_SYNTAX, *code]),
                ("test", [sys.executable, "-m", "unittest", *tests])]
    if shutil.which("node") is None:
        return "This exercise needs " + INSTALL["node"]
    flags = node_flags(any(f.endswith(TS) for f in files))
    if isinstance(flags, str):
        return flags
    # `node --check` doesn't parse TypeScript (it exits 0 on broken code), so a .ts syntax
    # error shows up when the tests load it instead. See run_exercise.
    js = [f for f in files if f.endswith(CODE["node"]) and not f.endswith(TS)]
    plan = [("syntax", ["node", "--check", f]) for f in js] + \
        [("test", ["node", *flags, "--test", "--test-reporter=spec", *tests])]
    ts = [f for f in files if f.endswith(TS)]
    if ts:
        tsc = typescript_compiler()
        if isinstance(tsc, str):
            return tsc
        # a type error is a failed test: types are what's being taught. An exercise with its own
        # tsconfig.json is checked with it (TypeScript won't take file names alongside one), and
        # without one, strictly
        if "tsconfig.json" in files:
            plan.append(("test", [*tsc, "--project", "tsconfig.json"]))
        else:
            plan.append(("test", [*tsc, "--strict", "--module", "nodenext", "--target", "esnext", *ts]))
    return plan


_NOISE = re.compile(r"^\s+(at |generatedMessage:|code: '|actual:|expected:|operator:|\}$)")


def readable(output: str) -> str:
    """Test output without the stack frames and error internals a learner can't act on."""
    return "\n".join(line for line in output.splitlines() if not _NOISE.match(line))


def run_exercise(folder: Path, runner: str | None, env: dict | None = None,
                 timeout: float | None = None) -> tuple[str, str]:
    """Run an exercise's checks. Returns (outcome, output), where outcome is one of:
    passed, failed (a test failed), invalid (it doesn't parse, so no test ran),
    missing (a tool isn't installed) and unchecked (nothing can run this exercise)."""
    if runner is None:
        return "unchecked", ""
    plan = steps(runner, folder)
    if isinstance(plan, str):
        return "missing", plan
    full_env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **(env or {})}
    output = ""
    for kind, argv in plan:
        try:
            p = subprocess.run(argv, cwd=folder, capture_output=True, text=True, env=full_env, timeout=timeout)
        except subprocess.TimeoutExpired:
            return "failed", f"{argv[0]} took longer than {timeout:.0f}s"
        output = (p.stdout + p.stderr).strip()
        if p.returncode != 0:
            if kind == "test" and runner == "node" and re.search(r"SyntaxError|ERR_INVALID_TYPESCRIPT_SYNTAX", output):
                return "invalid", output
            return ("failed" if kind == "test" else "invalid"), output
    return "passed", output


def lessons() -> list[dict]:
    return json.loads((ROOT / ".learn" / "lessons.json").read_text())


def state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"done": {}, "hints": {}, "solutions": [], "review": {}}


def save(s: dict) -> None:
    STATE.write_text(json.dumps(s, indent=2))


def current(s: dict) -> dict | None:
    """The first lesson whose exercise hasn't passed or whose quiz hasn't been taken."""
    for l in lessons():
        d = s["done"].get(l["id"], {})
        if (l["exercise"] and not d.get("exercise")) or not d.get("quiz"):
            return l
    return None


def pick(s: dict, arg: str | None) -> dict:
    if arg:
        for l in lessons():
            if l["id"] == arg:
                return l
        sys.exit(f"no lesson {arg}. `{CMD} status` lists them.")
    l = current(s)
    if l is None:
        sys.exit(f"You've finished every lesson. `{CMD} review` keeps it fresh.")
    return l


def cmd_next(s: dict, arg: str | None) -> None:
    l = pick(s, arg)
    d = s["done"].get(l["id"], {})
    print(f"{l['id']}  {l['title']}\n\n  read   {l['path']}/README.md")
    if l["exercise"]:
        print(f"  build  {l['path']}/exercise/   {'passed' if d.get('exercise') else f'then: {CMD} check'}")
    print(f"  quiz   {CMD} quiz   {'done' if d.get('quiz') else ''}")


def cmd_check(s: dict, arg: str | None) -> None:
    l = pick(s, arg)
    if not l["exercise"]:
        print(f"{l['id']} has no exercise. Take the quiz: {CMD} quiz")
        return
    folder = ROOT / l["path"] / "exercise"
    runner = l.get("runner") or runner_for([str(p) for p in folder.rglob("*")])
    print(f"Checking {folder.relative_to(ROOT)} ...\n")
    outcome, output = run_exercise(folder, runner)
    if outcome == "unchecked":
        print("Nothing can run this exercise's checks automatically, so you're the judge. When you're\n"
              f"happy with it, compare with the answer: {CMD} solution")
        s["done"].setdefault(l["id"], {})["exercise"] = "self-checked"
        save(s)
        return
    if outcome == "missing":
        print(output)
        return
    print(readable(output)[-3000:])
    if outcome == "invalid":
        print("\nThat's an error in the code itself, so the tests didn't get to run. Fix it and check again.")
        return
    if outcome == "failed":
        print("\nNot yet. Read the messages above, change your files, and check again."
              f"\nStuck? {CMD} hint")
        return
    s["done"].setdefault(l["id"], {})["exercise"] = time.time()
    save(s)
    print(f"\nPassed. Now: {CMD} quiz")


def cmd_hint(s: dict, arg: str | None) -> None:
    l = pick(s, arg)
    hints = json.loads((ROOT / l["path"] / ".answers" / "hints.json").read_text()) if l["exercise"] else []
    n = s["hints"].get(l["id"], 0)
    if n >= len(hints):
        print(f"No more hints. `{CMD} solution` shows the answer.")
        return
    print(f"Hint {n + 1} of {len(hints)}: {hints[n]}")
    s["hints"][l["id"]] = n + 1
    save(s)


def cmd_solution(s: dict, arg: str | None) -> None:
    l = pick(s, arg)
    folder = ROOT / l["path"] / ".answers" / "solution"
    if not folder.exists():
        print("This lesson has no exercise.")
        return
    if l["id"] not in s["solutions"]:
        s["solutions"].append(l["id"])
        save(s)
    for f in sorted(folder.rglob("*")):
        if f.is_file():
            print(f"--- {f.relative_to(folder)} ---\n{f.read_text()}")


def ask(q: dict, a: dict) -> bool:
    print(f"\n{q['stem']}\n")
    for i, o in enumerate(q["options"], 1):
        print(f"  {i}. {o}")
    while True:
        raw = input("\nYour answer: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(q["options"]):
            break
        print(f"Type a number from 1 to {len(q['options'])}.")
    right = int(raw) - 1 == a["answer"]
    print(("Right. " if right else f"Not quite. It's {a['answer'] + 1}. ") + a["explanation"])
    return right


def cmd_quiz(s: dict, arg: str | None) -> None:
    l = pick(s, arg)
    qs = json.loads((ROOT / l["path"] / "quiz.json").read_text())
    ans = json.loads((ROOT / l["path"] / ".answers" / "quiz.json").read_text())
    score = 0
    for i, (q, a) in enumerate(zip(qs, ans)):
        key = f"{l['id']}#{i}"
        if ask(q, a):
            score += 1
        else:
            s["review"][key] = {"due": time.time() + INTERVALS[0], "step": 0}
    s["done"].setdefault(l["id"], {})["quiz"] = time.time()
    save(s)
    print(f"\n{score} of {len(qs)}. " + (f"Missed ones come back in `{CMD} review`." if score < len(qs) else ""))


def cmd_review(s: dict, arg: str | None) -> None:
    now = time.time()
    due = [k for k, v in s["review"].items() if v["due"] <= now]
    if not due:
        upcoming = min((v["due"] for v in s["review"].values()), default=None)
        print("Nothing due." + (f" Next one in {int((upcoming - now) / 3600)} hours." if upcoming else ""))
        return
    paths = {l["id"]: l["path"] for l in lessons()}
    for key in due:
        lesson_id, i = key.split("#")
        qs = json.loads((ROOT / paths[lesson_id] / "quiz.json").read_text())
        ans = json.loads((ROOT / paths[lesson_id] / ".answers" / "quiz.json").read_text())
        item = s["review"][key]
        if ask(qs[int(i)], ans[int(i)]):
            item["step"] += 1
            if item["step"] >= len(INTERVALS):
                del s["review"][key]
                continue
        else:
            item["step"] = 0
        item["due"] = now + INTERVALS[item["step"]]
    save(s)


def cmd_report(s: dict, arg: str | None) -> None:
    if not arg:
        sys.exit(f'Say what is wrong: {CMD} report "question 2 has two right answers"')
    l = current(s) or lessons()[-1]
    reports = ROOT / ".learn" / "reports.json"
    found = json.loads(reports.read_text()) if reports.exists() else []
    found.append({"lesson": l["id"], "reason": arg, "at": time.time()})
    reports.write_text(json.dumps(found, indent=2))
    print(f"Noted against {l['id']}. Thanks. It's kept in .learn/reports.json.")


def cmd_status(s: dict, arg: str | None) -> None:
    for l in lessons():
        d = s["done"].get(l["id"], {})
        marks = ("built " if d.get("exercise") else "      " if l["exercise"] else "  -   ") + \
                ("quizzed" if d.get("quiz") else "")
        print(f"{l['id']:8} {marks:16} {l['title']}")
    print(f"\n{len(s['review'])} questions scheduled for review. "
          f"Solutions looked at: {len(s['solutions'])}.")


COMMANDS = {"next": cmd_next, "check": cmd_check, "hint": cmd_hint, "solution": cmd_solution,
            "quiz": cmd_quiz, "review": cmd_review, "report": cmd_report, "status": cmd_status}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        sys.exit(__doc__)
    s = state()
    COMMANDS[sys.argv[1]](s, sys.argv[2] if len(sys.argv) > 2 else None)

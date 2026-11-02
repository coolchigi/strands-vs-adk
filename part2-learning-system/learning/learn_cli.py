"""Work through this course.

    python3 learn.py next        where you are, and what's next
    python3 learn.py check       run the tests for the lesson you're on
    python3 learn.py check --watch  check again every time you save a file
    python3 learn.py hint        one hint at a time
    python3 learn.py solution    show the solution, and record that you looked
    python3 learn.py quiz        answer the questions, then see the answers
    python3 learn.py review      questions you missed, when they're due again
    python3 learn.py report "…"  flag something wrong in the lesson you're on
    python3 learn.py status      how far you are

`next` opens the lesson and the files you'll change in VS Code or Cursor, when it finds one.
LEARN_EDITOR picks which (code, cursor), or none to only say where they are.

The lesson you're on is the one whose folder you typed the command in, or anywhere else, the
first lesson you haven't finished. `next` moves on once the lesson you're in is finished. Name
a lesson to pick it instead: `python3 learn.py check u1-l2`.

Standard library only, so it runs anywhere the course folder goes. Each exercise's tests
run with its own subject's tools: `terraform test` for Terraform, `unittest` for Python,
and Node's built-in test runner for JavaScript and TypeScript.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

# the course folder: where this file sits, or where `learn` says it is. `learn` runs its own,
# newer copy of this file, so a fix reaches courses built before it
ROOT = Path(os.environ.get("LEARN_ROOT") or Path(__file__).resolve().parent)
CMD = os.environ.get("LEARN_AS", "python3 learn.py")  # `learn` sets this to "learn" when it runs us
STATE = ROOT / ".learn" / "progress.json"
# where the command was typed. `learn` runs this from the course folder, so it passes it on
HERE = os.environ.get("LEARN_HERE")
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
TYPESCRIPT = ("typescript@7.0.2", "@types/node@26.6.3")


def typescript_compiler() -> list[str] | str:
    """The compiler, ready to type-check, or why it isn't available."""
    tsc = TSC_HOME / "node_modules" / ".bin" / "tsc"
    if not tsc.exists():
        if shutil.which("npm") is None:
            return "Checking TypeScript types needs npm, which comes with " + INSTALL["node"]
        print("Fetching the TypeScript compiler. This happens once.", file=sys.stderr)
        # exact versions and no install scripts: "latest" from the registry ran whatever it was that day
        p = subprocess.run(["npm", "install", "--prefix", str(TSC_HOME), *TYPESCRIPT, "--ignore-scripts",
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


def shorten(text: str, keep: int = 1500) -> str:
    """The start and the end of a long output. Keeping only the end once dropped the first failure."""
    if len(text) <= 2 * keep:
        return text
    return text[:keep].rstrip() + "\n\n...\n\n" + text[-keep:].lstrip()


def _first(text: str, limit: int = 120) -> str:
    line = next((l.strip() for l in text.splitlines() if l.strip()), "")
    return line if len(line) <= limit else line[:limit - 3] + "..."


def _one_line(text: str) -> str:
    return " ".join(text.split())


_PY_HEAD = re.compile(r"^(FAIL|ERROR): (\w+) \([^)]*\)(.*)$", re.M)
_PY_RAISED = re.compile(r"^([A-Za-z_][\w.]*)(?:: ?(.*))?$")
_NODE_FAIL = re.compile(r"^\u2716 (.+?) \([\d.]+m?s\)$")
_NODE_ERROR = re.compile(r"^(\w*Error)(?: \[\w+\])?: (.+)$", re.M)
_NODE_RESULT = re.compile(r"^[\u2714\u2716] ", re.M)
_TSC = re.compile(r"^(.+?)\((\d+),\d+\): error TS\d+: (.*)$", re.M)
_TF_RUN = re.compile(r'^\s*run "([^"]+)"\.\.\. fail\s*$', re.M)
_TF_IN_RUN = re.compile(r'in run "([^"]+)"')
_TF_STATUS = re.compile(r'^(\s*run "|\S.*\.tftest\.hcl\.\.\.|Failure!|Success!)')


def failures(runner: str, output: str) -> list[str]:
    """One line per failing test: its name and what it says went wrong. Empty when the output
    isn't in a shape this knows, and then it's shown as it is."""
    if runner == "python":
        return _python_failures(output)
    if runner == "terraform":
        return _terraform_failures(output)
    return _node_failures(output) or [f"{f} line {n}: {m}" for f, n, m in _TSC.findall(output)]


def _balanced(text: str) -> bool:
    plain = text.replace("\\'", "").replace('\\"', "")
    return plain.count("'") % 2 == 0 and plain.count('"') % 2 == 0 and \
        all(plain.count(a) == plain.count(b) for a, b in ("()", "[]", "{}", "<>"))


def _python_message(detail: str) -> tuple[str, str]:
    """(the test author's message, what was compared), from an AssertionError's text.
    unittest writes "<what was compared> : <message>", and only when the test gave a message."""
    lines = detail.splitlines()
    if not lines:
        return "", ""
    own = next((i for i, l in enumerate(lines) if l.startswith(" : ")), None)
    if own is not None:  # after a multi-line diff, newer Pythons put it on a line of its own
        return _one_line(" ".join([lines[own][3:]] + lines[own + 1:])), "\n".join(lines[:own])
    at = lines[0].find(" : ")
    while at != -1:  # 'a : b' inside a compared value isn't where the message starts
        if _balanced(lines[0][:at]):
            return _one_line(" ".join([lines[0][at + 3:]] + lines[1:])), lines[0][:at]
        at = lines[0].find(" : ", at + 1)
    if len(lines) > 1 and " : " in lines[-1] and lines[-1][2:] not in lines[0]:
        # older ones end a diff's last line with it, unless that line is part of the values compared
        left, said = detail.rsplit(" : ", 1)
        return _one_line(said), left
    return "", detail


def _python_failures(output: str) -> list[str]:
    heads = list(_PY_HEAD.finditer(output))
    out = []
    for n, h in enumerate(heads):
        name = h.group(2) + h.group(3).rstrip()  # a subTest adds its values: test_x (i=2)
        end = heads[n + 1].start() if n + 1 < len(heads) else len(output)
        lines = [l for l in output[h.end():end].splitlines() if not re.fullmatch(r"[-=]{20,}", l)]
        lines = lines[:next((i for i, l in enumerate(lines) if l.startswith("Ran ")), len(lines))]
        # what was raised is the first unindented line after the last traceback header, so a
        # chained exception reports the one the test saw
        tb = max((i for i, l in enumerate(lines) if l.startswith("Traceback (most recent call last)")), default=-1)
        at = next((i for i in range(tb + 1, len(lines)) if lines[i] and not lines[i][0].isspace()), None)
        m = _PY_RAISED.match(lines[at]) if at is not None else None
        if m is None:
            out.append(f"{name}: " + next((l.strip() for l in reversed(lines) if l.strip()), h.group(1).lower()))
            continue
        detail = "\n".join([m.group(2) or ""] + lines[at + 1:]).strip()
        if m.group(1) != "AssertionError":  # the learner's code raised: its type is part of the message
            out.append(f"{name}: {m.group(1)}: {_first(detail)}" if detail else f"{name}: {m.group(1)}")
            continue
        said, compared = _python_message(detail)
        if compared.strip() in ("", "None"):  # a bare assert, or self.fail(): show the line that failed
            code = [l.strip() for l in lines[tb + 1:at] if l.strip() and not l.strip().startswith("File ")
                    and not set(l.strip()) <= set("~^")]
            compared = f"{code[-1]} failed" if code else "failed"
        out.append(f"{name}: {said} ({_first(compared)})" if said else f"{name}: {_first(compared)}")
    return out


def _node_load_error(listing: str, name: str) -> str | None:
    """Why a test file didn't load. Node prints it just before that file's line in the listing,
    so only that stretch is searched: an error from elsewhere would name the wrong cause."""
    line = re.search(r"^\u2716 " + re.escape(name) + r" \(", listing, re.M)
    if line is None:
        return None
    before = list(_NODE_RESULT.finditer(listing, 0, line.start()))
    stretch = listing[listing.find("\n", before[-1].end()) + 1 if before else 0:line.start()]
    found = list(_NODE_ERROR.finditer(stretch))
    # what was thrown has its stack under it, and a line the learner's code logged has none
    thrown = [m for m in found if re.match(r"\n\s+at ", stretch[m.end():m.end() + 40])]
    pick = (thrown or found or [None])[-1]
    return f"{pick.group(1)}: {pick.group(2).strip()}" if pick else None


def _node_failures(output: str) -> list[str]:
    # the spec reporter lists every failing test again at the end, under this line
    listing, _, section = output.rpartition("\u2716 failing tests:")
    section = section if listing else output
    lines = section.splitlines()
    found = []  # (name, where, text)
    for i, line in enumerate(lines):
        m = _NODE_FAIL.match(line)
        if not m:
            continue
        where = lines[i - 1][len("test at "):] if i and lines[i - 1].startswith("test at ") else ""
        said = []
        for x in lines[i + 1:]:
            t = x.strip()
            if t.startswith(("at ", "test at ")) or _NODE_FAIL.match(x):
                break
            if t:
                said.append(re.sub(r"^(\w+) \[\w+\]: ", r"\1: ", t))
        if said == ["'test failed'"]:  # the file didn't load
            reason = _node_load_error(listing or output, m.group(1))
            if reason is None:
                return []  # shown as it is, so the reason isn't lost
            said = [reason]
        if not said:
            found.append((m.group(1), where, "failed"))
            continue
        text = said[0][len("AssertionError: "):] if said[0].startswith("AssertionError: ") else said[0]
        header = any(l.startswith("+ actual - expected") for l in said)
        diff = [l for l in said[1:] if re.match(r"[+-] +\S", l) and not l.startswith("+ actual - expected")]
        if header and diff:  # which fields or lines differ
            shown = ", ".join(("got " if d[0] == "+" else "expected ") + _one_line(d[1:]).rstrip(",")
                              for d in diff[:4])
            text += f" {shown}" if text.endswith(":") else f" ({shown})"
        elif len(said) > 1 and not header and not said[1].startswith(("actual:", "expected:", "operator:")):
            text += f" {_first(said[1])}" if text.endswith(":") else f" ({_first(said[1])})"
        found.append((m.group(1), where, text))
    names = [n for n, _, _ in found]
    # tests in different describe blocks can share a name, so say where each one is
    return [f"{n}{f' ({w})' if w and names.count(n) > 1 else ''}: {t}" for n, w, t in found]


def _terraform_failures(output: str) -> list[str]:
    failed = _TF_RUN.findall(output)
    if not failed:
        return []
    errors = []  # (run, line)
    for chunk in re.split(r"^(?=Error: )", output, flags=re.M)[1:]:
        lines = chunk.splitlines()
        lines = lines[:next((i for i, l in enumerate(lines) if i and _TF_STATUS.match(l)), len(lines))]
        title = lines[0][len("Error: "):].strip()
        run = _TF_IN_RUN.search(chunk)
        # the explanation is the first paragraph at the left margin, after the code it points at
        start = next((i for i in range(1, len(lines)) if lines[i].strip() and not lines[i][0].isspace()), None)
        said = []
        for l in lines[start:] if start is not None else []:
            if not l.strip():
                break
            said.append(l.strip())
        values = [l.strip().lstrip("\u2502").strip() for l in lines if l.strip().startswith("\u2502")]
        values = [v for v in values if " is " in v]
        text = " ".join(said) if title == "Test assertion failed" and said else \
            f"{title}: {' '.join(said)}" if said else title
        errors.append((run.group(1) if run else None, text + (f" ({', '.join(values)})" if values else "")))
    # an error inside the configuration names no run: it belongs to a failed run with none of its own
    spare = [r for r in failed if r not in {r for r, _ in errors if r}]
    loose = [i for i, (r, _) in enumerate(errors) if r is None]
    # terraform reports them in run order, so the same count pairs them up
    if len(spare) == len(loose):
        owners = spare
    else:
        owners = [spare[0] if len(spare) == 1 else "terraform test"] * len(loose)
    named = dict(zip(loose, owners))
    out = [f"{run or named[i]}: {text}" for i, (run, text) in enumerate(errors)]
    told = {run or named[i] for i, (run, _) in enumerate(errors)}
    return out + [f"{r}: failed" for r in failed if r not in told]


# What an exercise's tools need from the environment. The tests are written by a model and
# once ran with every API key and cloud credential in reach, so nothing else is passed on.
# Most TF_ settings are left out on purpose: TF_TOKEN_* holds Terraform Cloud tokens.
KEEP_ENV = {"PATH", "LANG", "LANGUAGE", "TERM", "TZ", "TMPDIR", "TEMP", "TMP", "USER", "LOGNAME", "USERNAME",
            "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "http_proxy", "https_proxy", "no_proxy",
            "SSL_CERT_FILE", "SSL_CERT_DIR", "NODE_EXTRA_CA_CERTS", "TF_CLI_CONFIG_FILE", "TF_PLUGIN_CACHE_DIR",
            "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "PATHEXT"}
SECRET_NAME = re.compile(r"KEY|TOKEN|SECRET|PASS|CRED|AUTH(?!OR)|PRIVATE|DSN|_PAT$|_PWD$", re.I)
TIMEOUT_S = 600


def exercise_env(home: str, extra: dict | None = None) -> dict:
    """The environment an exercise runs in: the tools' needs, a throwaway home, and what the caller adds."""
    kept = {k: v for k, v in os.environ.items() if k in KEEP_ENV or k.startswith("LC_")}
    terraformrc = Path.home() / ".terraformrc"  # a mirror or plugin cache set up there still applies
    if "TF_CLI_CONFIG_FILE" not in kept and terraformrc.is_file():
        kept["TF_CLI_CONFIG_FILE"] = str(terraformrc)
    return {**kept, "HOME": home, "USERPROFILE": home, "PYTHONDONTWRITEBYTECODE": "1", **(extra or {})}


def hide_secrets(output: str) -> str:
    """A secret that still reaches the output (a test can read a key file) is blanked out, so it
    never lands in a log, a rewrite prompt or the course."""
    secrets = [v for n, v in os.environ.items() if SECRET_NAME.search(n) and len(v) >= 8]
    for value in sorted(secrets, key=len, reverse=True):  # a key inside a longer one mustn't leave part of it
        output = output.replace(value, "[hidden]")
    return output


# what exercise checks have running right now: a hard stop ends them, where a timeout no longer can
ALIVE: set = set()
SCRATCH: set = set()
ABANDONED = threading.Event()  # set by a hard stop: nothing new starts in the moment before the process ends


class Abandoned(RuntimeError):
    pass


@contextlib.contextmanager
def scratch(prefix: str = "tmp"):
    """A temporary folder that a hard stop removes too."""
    if ABANDONED.is_set():
        raise Abandoned("stopping")
    with tempfile.TemporaryDirectory(prefix=prefix) as d:
        SCRATCH.add(d)
        try:
            yield d
        finally:
            SCRATCH.discard(d)


def abandon() -> None:
    """Before a hard stop: end every check still running, and remove its folders. Exiting at once
    skips the cleanup each one would do, and a test started in a session of its own outlived the build."""
    ABANDONED.set()  # a check that wakes up after this, and would start the next one, can't
    for p in list(ALIVE):
        try:
            os.killpg(p.pid, signal.SIGKILL) if os.name == "posix" else p.kill()
        except OSError:
            pass
    for d in list(SCRATCH):
        shutil.rmtree(d, ignore_errors=True)


def _run(argv: list, cwd: Path, env: dict, timeout: float | None) -> tuple[int, str]:
    """One command, in its own process group, so a timeout stops whatever it started too.

    The group no longer hears the terminal's Ctrl-C, so a Ctrl-C here (or any other way out)
    stops the group itself. It waits for the process, not its output: something the test
    started in a session of its own can hold the output open long after.
    """
    posix = os.name == "posix"
    if ABANDONED.is_set():
        raise Abandoned("stopping")
    p = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, start_new_session=posix)
    ALIVE.add(p)
    try:
        out, err = p.communicate(timeout=timeout)
    except BaseException:
        if posix:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except OSError:  # the group is gone, or (macOS) its leader just exited: EPERM
                pass
        else:
            p.kill()
        p.wait()
        p.stdout.close()
        p.stderr.close()
        raise
    finally:
        ALIVE.discard(p)
    return p.returncode, (out + err).strip()


def run_exercise(folder: Path, runner: str | None, env: dict | None = None,
                 timeout: float | None = TIMEOUT_S) -> tuple[str, str]:
    """Run an exercise's checks. Returns (outcome, output), where outcome is one of:
    passed, failed (a test failed), invalid (it doesn't parse, so no test ran),
    missing (a tool isn't installed) and unchecked (nothing can run this exercise)."""
    if runner is None:
        return "unchecked", ""
    plan = steps(runner, folder)
    if isinstance(plan, str):
        return "missing", plan
    output = ""
    with scratch("learn-home-") as home:
        full_env = exercise_env(home, env)
        for kind, argv in plan:
            try:
                code, output = _run(argv, folder, full_env, timeout)
            except subprocess.TimeoutExpired:
                return "failed", f"{argv[0]} took longer than {timeout:.0f}s"
            output = hide_secrets(output)
            if code != 0:
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


def finished(s: dict, l: dict) -> bool:
    d = s["done"].get(l["id"], {})
    return bool((d.get("exercise") or not l["exercise"]) and d.get("quiz"))


def current(s: dict) -> dict | None:
    """The first lesson whose exercise hasn't passed or whose quiz hasn't been taken."""
    return next((l for l in lessons() if not finished(s, l)), None)


def lesson_here() -> dict | None:
    """The lesson whose folder the command was typed in, if it was typed in one."""
    try:
        here = Path(HERE or os.getcwd()).resolve()
    except (OSError, RuntimeError):  # a folder deleted under you, or a symlink loop on 3.9
        return None
    for l in lessons():
        folder = (ROOT / l["path"]).resolve()
        if here == folder or folder in here.parents:
            return l
    return None


def pick(s: dict, arg: str | None, here: bool = True) -> dict:
    """The lesson named, else the one whose folder you're in, else the first one not finished.
    `check` in lesson 2's folder once ran lesson 1's tests and said Passed."""
    if arg:
        for l in lessons():
            if l["id"] == arg:
                return l
        sys.exit(f"no lesson {arg}. `{CMD} status` lists them.")
    l = (lesson_here() if here else None) or current(s)
    if l is None:
        sys.exit(still_to_come() or f"You've finished every lesson. `{CMD} review` keeps it fresh.")
    return l


def alive(pid: int, since: float) -> bool:
    """Whether the build that last wrote at `since` is still going. On POSIX its process is asked,
    and a note 2 hours old counts as stopped in case the number went to another process. Windows
    has no harmless way to ask, so there the build's heartbeat must be under 30 minutes old."""
    age = time.time() - since
    if age < 0:  # a time in the future says nothing about now
        return False
    if os.name != "posix":
        return age < 30 * 60
    if pid <= 0 or age > 2 * 3600:
        return False
    try:
        os.kill(pid, 0)  # signal 0 asks without sending anything
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def carry_on(request: str, engine: str = "", *flags: str) -> str:
    """The command that carries on a build, quoted so it's safe to paste. A request with $(...)
    or a quote of its own ran the one, or broke the other and started a new paid build."""
    request = "".join(ch if ch.isprintable() else " " for ch in request)  # the same request, read as words
    picked = (f"--engine {engine}",) if engine in ("adk", "strands") else ()
    if os.name == "posix":
        return " ".join(("learn",) + flags + picked + (shlex.quote(request),))
    # cmd.exe and PowerShell each read something inside double quotes: & after a quote, $(...)
    if re.search(r"[\"&|<>^%$`!]", request):
        return " ".join(("learn",) + flags + picked) + " and your request, typed as you typed it the first time"
    return " ".join(("learn",) + flags + picked + (f'"{request}"',))


def still_to_come() -> str | None:
    """What to say about lessons the build hasn't written yet, while it writes them or after it stopped."""
    try:
        note = json.loads((ROOT / ".learn" / "building.json").read_text())
        total = int(note["total"])
        running = note.get("running") is True and alive(int(note.get("pid", 0)), float(note.get("updated", 0)))
        request, engine = str(note.get("request", "")), str(note.get("engine", ""))
    except (OSError, ValueError, KeyError, TypeError, OverflowError, AttributeError):
        return None
    ready = len(lessons())
    if total <= ready:
        return None
    left = total - ready
    rest = f"Lesson {total} isn't" if left == 1 else \
        f"Lessons {ready + 1} and {total} aren't" if left == 2 else f"Lessons {ready + 1} to {total} aren't"
    if running:
        return (f"{rest} written yet. The build is on {'it' if left == 1 else 'them'} now, and `{CMD} next` "
                f"shows {'it' if left == 1 else 'each one'} once it's ready.")
    return f"{rest} written yet, and the build has stopped. To carry on, run: {carry_on(request, engine)}"


def cmd_next(s: dict, arg: str | None) -> None:
    """The lesson you're in while it isn't finished, else the first one that isn't."""
    here = None if arg else lesson_here()
    l = here if here and not finished(s, here) else pick(s, arg, here=False)
    d = s["done"].get(l["id"], {})
    bare = lesson_here() or current(s)  # what `check` and `quiz` act on, typed here with no id
    named = "" if bare and bare["id"] == l["id"] else f" {l['id']}"
    print(f"{l['id']}  {l['title']}\n\n  read   {l['path']}/README.md")
    if l["exercise"]:
        print(f"  build  {l['path']}/exercise/   {'passed' if d.get('exercise') else f'then: {CMD} check{named}'}")
    print(f"  quiz   {CMD} quiz{named}   {'done' if d.get('quiz') else ''}")
    first = current(s)
    order = [x["id"] for x in lessons()]
    if first and order.index(first["id"]) < order.index(l["id"]):
        print(f"\n{first['id']} isn't finished yet: {CMD} next {first['id']}")
    if not sys.stdout.isatty():  # piped or in a test: say where things are, open nothing
        return
    name = open_lesson(l)
    check = f"{CMD} check{named}" if l["exercise"] else f"{CMD} quiz{named}"
    watch = f" `{CMD} check{named} --watch` checks again each time you save." if l["exercise"] else ""
    if name:
        opened = "the lesson's README.md and the files you'll change" if l["exercise"] else "the lesson's README.md"
        then = "Read the lesson there, edit the files, and run" if l["exercise"] else "Read the lesson there, then run"
        print(f"\nOpened in {name}: {opened}. {then} `{check}` in {name}'s terminal (Terminal > New Terminal).{watch}"
              "\nIf the lesson shows as plain text, Shift+Cmd+V (Ctrl+Shift+V on Windows and Linux) formats it.")
    else:
        print(f"\nWork through it in VS Code or Cursor: open this course's folder ({ROOT}) there and read "
              f"{l['path']}/README.md" + (f", change the files in {l['path']}/exercise/," if l["exercise"] else ",")
              + f" and run `{check}` in the editor's terminal (Terminal > New Terminal).{watch}" + why_not_opened())


def why_not_opened() -> str:
    chosen = os.environ.get("LEARN_EDITOR", "").strip()
    if chosen.lower() == "none" or editor() is not None:  # their choice, or the editor wouldn't start
        return ""
    if chosen:
        return f"\nLEARN_EDITOR is {chosen!r}, and there's no command by that name."
    return (f"\nTo have `{CMD} next` open them for you, get VS Code from https://code.visualstudio.com. On macOS, "
            "also run \"Shell Command: Install 'code' command in PATH\" from its Command Palette.")


EDITORS = {"code": "VS Code", "cursor": "Cursor"}
# lessons open as formatted text in the course's own folder. A pattern without a slash is matched
# against the file name (VS Code 1.141's code), so an exercise's answer.md still opens to edit
PREVIEW = {"workbench.editorAssociations": {"README.md": "vscode.markdown.preview.editor"}}
# a .cmd file runs through cmd.exe on Windows, where & or % in a file name could run a command
_PLAIN_PATH = re.compile(r"[\w\-. :\\/]+")


def editor() -> str | None:
    """The editor command lessons open in: LEARN_EDITOR if set, else VS Code, else Cursor."""
    chosen = os.environ.get("LEARN_EDITOR", "").strip()
    if chosen.lower() == "none":
        return None
    return next((p for p in (shutil.which(n) for n in ([chosen] if chosen else list(EDITORS))) if p), None)


def open_lesson(l: dict) -> str | None:
    """Open the lesson and the files to change in the editor. Its name, or None if it didn't."""
    command = editor()
    if command is None:
        return None
    folder, ex = ROOT / l["path"], ROOT / l["path"] / "exercise"
    runner = runner_of(l, ex) if ex.is_dir() else None
    files = sorted(p for p in ex.rglob("*") if p.is_file() and not IGNORED.search(p.relative_to(ex).as_posix())
                   and not (runner and is_test(runner, p.name))) if ex.is_dir() else []
    answer = folder / ".answers" / "solution"
    changed = {p.relative_to(answer).as_posix() for p in answer.rglob("*") if p.is_file()} if answer.is_dir() else set()
    files.sort(key=lambda p: p.relative_to(ex).as_posix() not in changed)  # the files the answer changes first
    # absolute paths: a file the model named "-something" can't become an option
    argv = [command, str(ROOT.resolve()), str((folder / "README.md").resolve())] + [str(p.resolve()) for p in files[:6]]
    if command.lower().endswith((".cmd", ".bat")) and not all(_PLAIN_PATH.fullmatch(a) for a in argv[1:]):
        return None
    vscode = ROOT / ".vscode"
    if not vscode.exists():  # never over settings someone made
        try:
            vscode.mkdir()
            (vscode / "settings.json").write_text(json.dumps(PREVIEW, indent=2) + "\n")
        except OSError:
            pass
    # without the settings `learn` gives this file: in the editor's terminal, LEARN_HERE would pin
    # every command to the lesson `next` was typed in
    env = {k: v for k, v in os.environ.items() if k not in ("LEARN_AS", "LEARN_ROOT", "LEARN_HERE")}
    try:
        subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=os.name != "nt", env=env)
    except OSError:
        return None
    return EDITORS.get(Path(command).stem.lower(), Path(command).stem)


def runner_of(l: dict, folder: Path) -> str | None:
    return l.get("runner") or runner_for([str(p) for p in folder.rglob("*")])


def printed(output: str) -> str:
    """What the learner's own code printed during a Python check. Its output comes first, then
    unittest's report: a line of dots and letters, then a rule of = signs."""
    lines = output.splitlines()
    rule = next((i for i, l in enumerate(lines) if l == "=" * 70), 0)
    return "\n".join(lines[:rule - 1]).strip() if rule > 1 else ""


def check_once(s: dict, l: dict) -> str:
    """Run a lesson's checks and say how it went. Returns the outcome."""
    folder = ROOT / l["path"] / "exercise"
    if not folder.is_dir():  # nothing to run, and nothing to mark as checked
        print(f"{folder.relative_to(ROOT)} isn't there any more, so there's nothing to check.")
        return "missing"
    runner = runner_of(l, folder)
    print(f"Checking {folder.relative_to(ROOT)} ...\n", flush=True)  # before a check that may take a while
    outcome, output = run_exercise(folder, runner)
    if outcome == "unchecked":
        print("Nothing can run this exercise's checks automatically, so you're the judge. When you're\n"
              f"happy with it, compare with the answer: {CMD} solution")
        s["done"].setdefault(l["id"], {})["exercise"] = "self-checked"
        save(s)
        return outcome
    if outcome == "missing":
        print(output)
        return outcome
    found = failures(runner, output) if outcome == "failed" else []
    if found:
        print(f"{len(found)} check{'s' if len(found) != 1 else ''} failed:")
        print("\n".join(f"  - {f}" for f in found))
        own = printed(output).splitlines() if runner == "python" else []
        if own:  # printing values is how most people find a bug
            print("\nYour code printed" + (" (the last 20 lines):" if len(own) > 20 else ":"))
            print("\n".join("  " + line for line in own[-20:]))
    else:
        print(shorten(readable(output)))
    if outcome == "invalid":
        print("\nThat's an error in the code itself, so the tests didn't get to run. Fix it and check again.")
        return outcome
    if outcome == "failed":
        print("\nNot yet. Read the messages above, change your files, and check again."
              f"\nStuck? {CMD} hint")
        return outcome
    s["done"].setdefault(l["id"], {})["exercise"] = time.time()
    save(s)
    print(f"\nPassed. Now: {CMD} quiz")
    return outcome


def cmd_check(s: dict, arg: str | None, watch: bool = False) -> int:
    """0 once the checks pass, 1 while they don't, so scripts and editors can tell."""
    l = pick(s, arg)
    if not l["exercise"]:
        print(f"{l['id']} has no exercise. Take the quiz: {CMD} quiz")
        return 0
    if watch:
        return check_watching(s, l)
    return 0 if check_once(s, l) in ("passed", "unchecked") else 1


# what a learner edits: their code and the tests. What the checks write (a report, a cache)
# would set off another check, and another
WATCHED = {"python": (".py",), "node": CODE["node"] + ("package.json", "tsconfig.json"),
           "terraform": (".tf", ".tfvars", ".hcl")}
# dot files, caches, and editors' swap and backup files
IGNORED = re.compile(r"(^|/)(\.[^/]*|__pycache__|node_modules)(/|$)|(~|\.swp|\.swx|\.tmp)$")


def snapshot(folder: Path, runner: str | None, also: frozenset = frozenset()) -> dict:
    snap = {}
    try:
        for p in folder.rglob("*"):
            rel = p.relative_to(folder).as_posix()
            if (rel in also or rel.endswith(WATCHED.get(runner or "", ()))) and not IGNORED.search(rel) \
                    and p.is_file():
                st = p.stat()
                snap[rel] = (st.st_mtime_ns, st.st_size)
    except OSError:  # a file went while it was being listed: the next look sees the change
        pass
    return snap


def check_watching(s: dict, l: dict) -> int:
    """Check, then check again each time a file in the exercise is saved, until the checks pass.
    It looks twice a second: standard library only, and a few files cost nothing to look at."""
    folder = ROOT / l["path"] / "exercise"
    runner = runner_of(l, folder)
    answer = ROOT / l["path"] / ".answers" / "solution"
    # the files the answer changes are the ones the learner edits, whatever kind they are
    edits = frozenset(p.relative_to(answer).as_posix() for p in answer.rglob("*") if p.is_file())
    seen = None
    try:
        while True:
            snap = snapshot(folder, runner, edits)
            if snap != seen:
                if seen is not None:
                    time.sleep(0.3)  # editors save in more than one write
                    snap = snapshot(folder, runner, edits)
                    if snap == seen:  # a file that came and went
                        continue
                # taken before the check, so a save while it runs is checked too
                seen = snap
                outcome = check_once(s, l)
                if outcome in ("passed", "unchecked"):
                    return 0
                if outcome == "missing":  # saving a file won't install a tool or bring a folder back
                    return 1
                # flushed: piped into an editor's task panel, it would otherwise wait for a full buffer
                print(f"\nWatching {folder.relative_to(ROOT)}. Save a file to check again. Ctrl-C stops.\n", flush=True)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print()
        return 1


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
        if re.fullmatch(r"\..+\.\d+-\d+\.tmp", f.name):  # half of a file the build is writing right now
            continue
        try:
            text = f.read_text() if f.is_file() else None
        except OSError:  # gone while being read
            continue
        if text is not None:
            print(f"--- {f.relative_to(folder)} ---\n{text}")


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
    l = lesson_here() or current(s) or lessons()[-1]
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
    if more := still_to_come():
        print(more)


COMMANDS = {"next": cmd_next, "check": cmd_check, "hint": cmd_hint, "solution": cmd_solution,
            "quiz": cmd_quiz, "review": cmd_review, "report": cmd_report, "status": cmd_status}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        sys.exit(__doc__)
    command, rest = sys.argv[1], sys.argv[2:]
    watch = command == "check" and "--watch" in rest
    rest = [a for a in rest if a != "--watch"] if watch else rest
    s = state()
    try:
        if watch:
            code = cmd_check(s, rest[0] if rest else None, watch=True)
        else:
            code = COMMANDS[command](s, rest[0] if rest else None)
    except KeyboardInterrupt:
        print()
        code = 130
    sys.exit(code or 0)  # 1 when checks fail, so scripts and editors can tell

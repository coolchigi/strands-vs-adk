"""learn: tell it what you want to learn, and work through the course it builds.

    learn "I want to learn TypeScript so I can build a small web app"
    learn                 your courses, and how far you are in each
    learn stop            stop a course that's being built, before its next model call
    learn next            inside a course folder: where you are, and what's next
    learn check           run the tests for the lesson you're on
    learn check --watch   check again every time you save a file
    learn hint            one hint at a time
    learn solution        show the answer, and record that you looked
    learn quiz            answer the questions, then see the answers
    learn review          questions you missed, when they're due again
    learn report "..."    flag something wrong in the lesson you're on
    learn status          every lesson, and what you've done

Courses go in ~/courses, one folder each (LEARN_HOME changes that). Building one takes 30
to 90 minutes, and if it stops, running the same request again picks up where it left off.
Keys and settings live in ~/.config/learning-system/env.
"""

from __future__ import annotations

import argparse
import difflib
import getpass
import json
import logging
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

COURSE_COMMANDS = ("next", "check", "hint", "solution", "quiz", "review", "report", "status")
GEMINI_KEY_URL = "https://aistudio.google.com/apikey"
SUPPORTED = ("Exercises are checked automatically when the subject is Terraform, Python, JavaScript or "
             "TypeScript. For anything else, you judge your own work against the answer.")

Ask = Callable[[str], str]
Say = Callable[[str], None]


def home() -> Path:
    return Path(os.environ.get("LEARN_HOME", Path.home() / "courses")).expanduser()


def config_file() -> Path:
    return Path(os.environ.get("LEARN_CONFIG", Path.home() / ".config" / "learning-system" / "env")).expanduser()


# -- one build at a time -------------------------------------------------------------------

_HELD: dict[Path, object] = {}  # build folders this process holds, kept until it ends


def hold(lock: Path, quiet: bool = False) -> bool:
    """An exclusive hold on a build folder for as long as this process lives, or False if another
    process has it. The system lets go when the process ends, crashes included, so a worker still
    finishing after Ctrl-C keeps it too. A check, then a write, once let two builds in at once."""
    if lock in _HELD:
        return True
    f = open(lock, "a+")
    try:
        if os.name == "posix":
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        else:
            import msvcrt
            f.seek(0)  # it locks bytes from where the file is, and "a+" opens at the end
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
    except (BlockingIOError, PermissionError):  # another process has it
        f.close()
        return False
    except OSError as e:  # a file system with no locks: build anyway, as before there was one
        if not quiet:
            logging.getLogger("learning").warning("couldn't lock %s, so a second build won't be stopped: %s", lock, e)
    f.seek(0)
    f.truncate()
    f.write(str(os.getpid()))
    f.flush()
    _HELD[lock] = f
    return True


def release(lock: Path) -> None:
    f = _HELD.pop(lock, None)
    if f is not None:
        f.close()


def can_notify() -> bool:
    return sys.platform == "darwin" and os.environ.get("LEARN_NOTIFY", "").strip().lower() not in ("off", "none", "0") \
        and shutil.which("osascript") is not None


def notify(text: str) -> None:
    """A macOS notification, for a build running where nobody watches it. The text goes in as
    arguments to the script, so a lesson title a model wrote is never run as AppleScript."""
    if not can_notify():
        return
    try:
        subprocess.run(["osascript", "-e", "on run argv", "-e",
                        "display notification (item 2 of argv) with title (item 1 of argv)", "-e", "end run",
                        "learn", text[:240]], timeout=10, capture_output=True)
    except (OSError, subprocess.SubprocessError):
        pass


def detach(b: Path, reviewer: bool) -> None:
    """The build goes on in a process of its own, in a session of its own, so closing the terminal
    doesn't stop it. What it would have printed goes to screen.log, and a crash to worker.out.

    It's handed the lock this terminal holds, so the build folder is never free in between: a
    `learn stop` in the half second before the build took it once went unheard."""
    held = _HELD.get(b / "running")
    fd = [] if held is None else ["--held-fd", str(held.fileno())]
    with open(b / "worker.out", "a") as out:
        subprocess.Popen([sys.executable, "-P", "-m", "learning.front", "--worker", str(b), *fd]
                         + ([] if reviewer else ["--no-review"]), cwd=b, stdin=subprocess.DEVNULL, stdout=out,
                         stderr=subprocess.STDOUT, start_new_session=True,
                         pass_fds=() if held is None else (held.fileno(),))


def work(b: Path, reviewer: bool, held_fd: int | None = None) -> int:
    """The build itself, in the background, picking up from the answers the terminal saved."""
    from .learn_cli import hide_secrets
    from .stages import write_atomic

    if held_fd is not None:  # the terminal's hold on the build folder, now this process's
        os.set_inheritable(held_fd, False)  # pass_fds made it inheritable: nothing this process starts needs it
        f = os.fdopen(held_fd, "a+")
        f.seek(0)
        f.truncate()
        f.write(str(os.getpid()))
        f.flush()
        _HELD[b / "running"] = f
    # said before the frameworks load: until then, `learn` had only worker.out, where a library's import
    # warning read as the reason the build had died
    write_atomic(b / "status.json", json.dumps({"line": "Starting the build.", "updated": time.time()}))
    try:
        engine = load_engine((b / "engine.txt").read_text())
    except Exception as e:  # nothing else would ever say why the build never started
        why = hide_secrets(str(e)) or type(e).__name__
        write_atomic(b / "status.json", json.dumps({"line": f"The build couldn't start: {why}", "updated": time.time()}))
        notify("A course build couldn't start. learn shows why.")
        return 1

    def no_questions(prompt: str) -> str:
        raise RuntimeError("a build in the background can't ask questions")

    with open(b / "screen.log", "a", buffering=1) as screen:
        def say(m: str) -> None:
            try:
                screen.write(m + "\n")
            except OSError:  # a full disk mustn't stop the build telling `learn` and you how it ended
                pass

        try:
            return build((b / "request.txt").read_text(), engine, ask=no_questions, say=say, reviewer=reviewer,
                         build_dir=b, notify=notify, worker=True)
        except Exception as e:  # build() explains its own failures once under way. This is one before that,
            why = hide_secrets(str(e)) or type(e).__name__  # and "Starting the build." would otherwise stay up
            try:
                write_atomic(b / "status.json", json.dumps({"line": f"The build stopped unexpectedly: {why}",
                                                            "updated": time.time()}))
            except OSError:  # a full disk, say: the notification needs none
                pass
            notify("A course build stopped unexpectedly. learn shows why.")
            raise


def held_elsewhere(lock: Path) -> bool:
    """Whether another process is building in this folder right now."""
    if lock in _HELD or not lock.exists():
        return False
    if not hold(lock, quiet=True):  # a listing has nothing to say about locks
        return True
    _HELD.pop(lock).close()  # nobody had it: let it go again
    return False


def stop_builds(here: Path | None, say: Say = print) -> int:
    """learn stop: ask the builds running now to stop before their next model call. Inside a
    course folder, only the one writing it."""
    from .learn_cli import carry_on

    running = [b for b in unfinished_builds(home()) if held_elsewhere(b / "running")]
    if here is not None:
        running = [b for b in running if (b / "course.txt").is_file()
                   and Path((b / "course.txt").read_text()).resolve() == here]
    if not running:
        say("This course isn't being built right now." if here else "Nothing is being built right now.")
        return 0
    from .stages import write_atomic

    for b in running:
        request = (b / "request.txt").read_text()
        engine = (b / "engine.txt").read_text() if (b / "engine.txt").is_file() else ""
        write_atomic(b / "stop", "")
        say(f"Stopping the build of {request!r} before its next model call, so nothing more is spent. "
            f"To carry on later: {carry_on(request, engine)}")
    return 0


# -- inside a course: hand over to the course's own learn.py -------------------------------

def course_root(start: Path) -> Path | None:
    """The course folder this path is in, from anywhere inside it."""
    for folder in [start, *start.parents]:
        if (folder / "learn.py").is_file() and (folder / ".learn" / "lessons.json").is_file():
            return folder
    return None


def in_course(argv: list[str], say: Say = print) -> int:
    root = course_root(Path.cwd().resolve())
    if root is None:
        say("You're not in a course folder. `learn` on its own lists your courses.")
        return 1
    try:
        load_config(only=("LEARN_EDITOR",))  # the keys stay out: the editor started from here inherits this
    except (OSError, UnicodeDecodeError):  # a config that can't be read shouldn't stop `learn status`
        pass
    env = {**os.environ, "LEARN_AS": "learn", "LEARN_ROOT": str(root), "LEARN_HERE": str(Path.cwd())}
    # -P: a learning/ folder in a course someone shared would otherwise run in place of this one
    p = subprocess.Popen([sys.executable, "-P", "-m", "learning.learn_cli", *argv], cwd=root, env=env)
    while True:
        try:
            code = p.wait()
            return 128 - code if code < 0 else code  # stopped by a signal: 130 for Ctrl-C, as shells say
        except KeyboardInterrupt:  # Ctrl-C reached the command too, and it stops on its own
            continue


def list_courses(say: Say = print) -> int:
    from . import course_dir
    from .learn_cli import carry_on

    root = home()
    courses = sorted(p for p in root.glob("*") if (p / "course.json").is_file()) if root.exists() else []
    builds = [b for b in unfinished_builds(root)]
    if not courses and not builds:
        say('No courses yet. Start one with: learn "what you want to learn, in your own words"')
        return 0
    for c in courses:
        lessons = json.loads((c / ".learn" / "lessons.json").read_text())
        progress = c / ".learn" / "progress.json"
        done = json.loads(progress.read_text())["done"] if progress.exists() else {}
        finished = sum(1 for l in lessons if done.get(l["id"], {}).get("quiz")
                       and (not l["exercise"] or done.get(l["id"], {}).get("exercise")))
        title = json.loads((c / "course.json").read_text())["curriculum"]["title"]
        try:
            total = json.loads((c / course_dir.BUILDING).read_text())["total"]
        except (OSError, ValueError, KeyError, TypeError):
            total = len(lessons)
        more = f", {total - len(lessons)} still to write" if total > len(lessons) else ""
        say(f"{c.name:24} {finished} of {len(lessons)} lessons done{more}   {title}")
    for b in builds:
        request = (b / "request.txt").read_text()
        engine = (b / "engine.txt").read_text() if (b / "engine.txt").is_file() else ""
        try:  # what the build last said, and what it has spent: a build in the background has no screen
            status = json.loads((b / "status.json").read_text())
            line, cap, advice = str(status.get("line", "")), status.get("cap"), str(status.get("advice", ""))
        except (OSError, ValueError, AttributeError):
            line, cap, advice = "", None, ""
        out = (b / "worker.out").read_text(errors="replace") if (b / "worker.out").is_file() else ""
        if not line and "Traceback (most recent call last)" in out:  # it died before it could say anything else
            from .learn_cli import hide_secrets

            crash = [l for l in out.split("Traceback (most recent call last)")[-1].splitlines()
                     if l.strip() and not l.startswith(" ")]
            line = f"The build stopped unexpectedly: {hide_secrets(crash[-1].strip())}" if crash else ""
        if line and line[-1] not in ".!?:":
            line += "."
        try:
            spent = sum(row[3] for row in json.loads((b / "spend.json").read_text()).values() if len(row) > 3)
        except (OSError, ValueError, TypeError, AttributeError):
            spent = None
        money = "" if spent is None else f"${spent:.2f} spent" + (f" of your ${cap:.2f} cap" if cap else "") + ". "
        if held_elsewhere(b / "running"):
            say(f'{"(building now)":24} {carry_on(request)}')
            say(f'{"":24} {line + " " if line else ""}{money}learn stop stops it.')
        else:
            say(f'{"(stopped partway)":24} {carry_on(request, engine)}   to carry on')
            if line:
                say(f'{"":24} {line}')
        if advice:
            say(f'{"":24} {advice}')
    say(f"\nCourses live in {root}. cd into one and type `learn next`.")
    return 0


# -- keys and the engine, set up once -------------------------------------------------------

NUMBERS = ("LEARNING_BUDGET_USD", "LEARN_SWITCH_AT")


def load_config(only: tuple[str, ...] | None = None) -> None:
    """KEY=VALUE lines from the config file, for anything not already set, or just the keys in
    `only`. A number may have a comment after it: `LEARNING_BUDGET_USD=5  # five dollars` once
    crashed the build. Other values are kept whole, since a folder name can have " #" in it."""
    f = config_file()
    if f.is_file():
        for line in f.read_text().splitlines():
            key, sep, value = line.partition("=")
            key = key.strip()
            if sep and key and not key.startswith("#") and (only is None or key in only):
                os.environ.setdefault(key, re.sub(r"\s+#.*$", "", value).strip() if key in NUMBERS else value.strip())


SETTINGS = ("GOOGLE_API_KEY", "LEARNING_BUDGET_USD", "LEARN_SWITCH_AT", "LEARN_CHEAP_MODEL", "LEARN_ENGINE",
            "LEARN_HOME", "LEARN_TSC_HOME", "ADK_MODEL", "STRANDS_MODEL", "AWS_REGION", "AWS_PROFILE",
            "EXA_API_KEY", "TAVILY_API_KEY", "TF_PLUGIN_CACHE_DIR", "LEARN_EDITOR")


def check_settings() -> tuple[list[str], list[str]]:
    """What's wrong with the settings, before anything is spent: (problems, likely typos)."""
    from .budget import dollars, fraction

    problems, typos = [], []
    for name, parse, example in (("LEARNING_BUDGET_USD", dollars, "5"), ("LEARN_SWITCH_AT", fraction, "0.5")):
        value = os.environ.get(name, "").strip()
        if value:
            try:
                parse(value)
            except ValueError:
                problems.append(f"{name}={value} can't be used. Set it to a number like {example}.")
    engine = os.environ.get("LEARN_ENGINE", "").strip()
    if engine and engine not in ("adk", "strands"):
        problems.append(f"LEARN_ENGINE={engine} can't be used. Set it to adk or strands.")
    f = config_file()
    for line in f.read_text().splitlines() if f.is_file() else []:
        key = line.partition("=")[0].strip()
        if key and not key.startswith("#") and key not in SETTINGS and not key.startswith("AWS_"):
            close = difflib.get_close_matches(key, SETTINGS, n=1, cutoff=0.8)
            if close:  # a misspelled budget once fell back to the higher default cap, so that one stops
                (problems if close[0] in NUMBERS else typos).append(
                    f"{key} isn't a setting I read. Did you mean {close[0]}?")
    return problems, typos


def save_config(key: str, value: str) -> None:
    f = config_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    lines = [l for l in (f.read_text().splitlines() if f.exists() else []) if not l.startswith(f"{key}=")]
    # private before the key goes in. It was written first and made private after, and a file
    # opened while it was still readable kept reading, so the new one replaces it whole
    target = f.resolve()  # a config symlinked from a dotfiles folder keeps its link
    tmp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    tmp.unlink(missing_ok=True)
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        try:
            os.fchmod(fd, 0o600)
            os.write(fd, ("\n".join([*lines, f"{key}={value}"]) + "\n").encode())
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(tmp, target)
    except BaseException:
        tmp.unlink(missing_ok=True)  # never a stray copy of the key
        raise
    os.environ[key] = value


def aws_credentials() -> bool:
    try:
        import boto3
        return boto3.Session().get_credentials() is not None
    except Exception:
        return False


def pick_engine(explicit: str | None, ask_secret: Ask, say: Say) -> str | None:
    """ADK on Gemini or Strands on Claude, from what you asked for or the keys you have.

    With nothing set up, it asks for a Gemini key once and saves it.
    """
    name = explicit or os.environ.get("LEARN_ENGINE")
    if name == "strands" or (name is None and not os.environ.get("GOOGLE_API_KEY") and aws_credentials()):
        if not aws_credentials():
            say("Building with Strands runs Claude on Amazon Bedrock, and I can't find AWS credentials. "
                "Set them up with `aws configure` or `aws login`, then try again.")
            return None
        return "strands"
    if not os.environ.get("GOOGLE_API_KEY"):
        say(f"To build courses I need a Gemini API key. You can get one at {GEMINI_KEY_URL}")
        try:
            key = ask_secret("Paste it here (it won't show): ").strip()
        except EOFError:  # no terminal to paste into, as when run from a script
            say(f"There's no terminal here to paste one into. Add a line GOOGLE_API_KEY=your-key to "
                f"{config_file()} and run the same command. Nothing was built and nothing was spent.")
            return None
        if not key:
            say("No key, so I can't build a course yet.")
            return None
        save_config("GOOGLE_API_KEY", key)
        say(f"Saved to {config_file()}, readable only by you. I won't ask again.")
    return "adk"


@dataclass
class Engine:
    name: str
    model: str
    make_brain: Callable
    meter: object
    run_pipeline: Callable
    budget_error: type[Exception]


def load_engine(name: str) -> Engine:
    if name == "strands":
        from impl.strands.brain import MODEL_ID, StrandsBrain
        from impl.strands.pipeline import run
        from impl.strands.telemetry import BudgetExceeded, Meter
        return Engine("strands", MODEL_ID, StrandsBrain, Meter.from_env(MODEL_ID), run, BudgetExceeded)
    from impl.adk.brain import MODEL, AdkBrain
    from impl.adk.pipeline import run
    from impl.adk.telemetry import BudgetExceeded, Meter
    return Engine("adk", MODEL, AdkBrain, Meter.from_env(MODEL), run, BudgetExceeded)


# -- building a course ---------------------------------------------------------------------

def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40].rstrip("-") or "course"


def builds_dir(root: Path) -> Path:
    return root / ".builds"


class Hidden(logging.Formatter):
    """Log lines, tracebacks included, with the value of any secret setting blanked out."""

    def format(self, record: logging.LogRecord) -> str:
        from .learn_cli import hide_secrets
        return hide_secrets(super().format(record))


def same_request(a: str, b: str) -> bool:
    return " ".join(a.split()).lower() == " ".join(b.split()).lower()


def find_build(root: Path, request: str, engine: str) -> Path | None:
    """The newest build of this request on this engine, so after --fresh a rerun finds the new one."""
    for b in sorted(builds_dir(root).glob("*"), reverse=True) if builds_dir(root).exists() else []:
        if (b / "request.txt").is_file() and same_request((b / "request.txt").read_text(), request) \
                and (b / "engine.txt").is_file() and (b / "engine.txt").read_text() == engine:
            return b
    return None


def unfinished_builds(root: Path) -> list[Path]:
    if not builds_dir(root).exists():
        return []
    return [b for b in sorted(builds_dir(root).glob("*"))
            if (b / "request.txt").is_file() and not (b / "finished").exists()]


def new_build(root: Path, request: str, engine: str) -> Path:
    stamp, n = f"{datetime.now():%Y%m%d-%H%M%S}-{engine}", 1
    b = builds_dir(root) / stamp
    while b.exists():  # two builds started in the same second
        n += 1
        b = builds_dir(root) / f"{stamp}-{n}"
    builds_dir(root).mkdir(parents=True, exist_ok=True)
    builds_dir(root).chmod(0o700)  # your profile, spend and logs, for no one else on this machine
    b.mkdir(mode=0o700)
    # engine first: find_build only looks at folders with a request.txt, so a stop in between
    # leaves a folder it skips instead of one it crashes on
    (b / "engine.txt").write_text(engine)
    (b / "request.txt").write_text(request)
    return b


def course_folder(root: Path, build: Path, subject: str) -> Path:
    """~/courses/<subject>, or <subject>-2 and so on if another course has that name."""
    from .stages import write_atomic

    saved = build / "course.txt"
    if saved.is_file():
        return Path(saved.read_text())
    base, n = slug(subject), 1
    taken = {Path(p.read_text()) for p in builds_dir(root).glob("*/course.txt")}
    folder = root / base
    while folder.exists() or folder in taken:
        n += 1
        folder = root / f"{base}-{n}"
    write_atomic(saved, str(folder))
    return folder


def interview(brain, request: str, ask: Ask, say: Say):
    """The intake, as a conversation: its questions asked here, one at a time."""
    from . import stages

    conversation = request
    profile = stages.intake(brain, conversation)
    for _ in range(2):
        if not profile.questions:
            break
        say("\nA few questions first, so I build the right course:")
        answers = []
        for q in profile.questions:
            say(f"  {q}")
            try:
                answers.append((q, ask("> ").strip() or "No preference."))
            except EOFError:
                answers.append((q, "No preference."))
        conversation += "\n\n" + "\n".join(f"You asked: {q}\nThey answered: {a}" for q, a in answers)
        profile = stages.intake(brain, conversation + "\n\nOnly ask again if the subject itself is still unclear.")
    return profile


def cap_advice(meter, done: int, total: int) -> str | None:
    """What to do when the lessons left, played forward, reach the cap. None when they don't."""
    if not meter.limit_usd or done >= total:
        return None
    ahead = meter.projection(done, total)
    if ahead.stop_at is not None:
        where = f"At this rate the cap stops the build around lesson {ahead.stop_at}."
    elif ahead.end_usd + ahead.lesson_usd >= meter.limit_usd:
        # later lessons were bigger than the early ones in both real builds, so close counts too
        where = "At this rate it ends within one lesson of the cap, so the cap may stop it near the end."
    else:
        return None
    need = max(math.ceil(ahead.finish_usd), math.floor(meter.limit_usd) + 1)
    return (f"{where}\nTo finish, set LEARNING_BUDGET_USD={need} in {config_file()} if it stops, then run the same "
            "command. Lessons already written aren't paid for again.")


def spend_line(meter, done: int, total: int, warned: bool = False) -> str | None:
    """What the build has spent, once half the lessons are written and again once all of them are.
    A build headed for the cap is told at the first lesson that shows it: a big course can reach
    the cap before halfway."""
    halfway = done == math.ceil(total / 2)
    advice = cap_advice(meter, done, total)
    if done != total and not halfway and (warned or advice is None):
        return None
    research, plan, lessons = meter.spent_on()
    cap = f" of your ${meter.limit_usd:.2f} cap" if meter.limit_usd else ""
    each = f" (about ${lessons / done:.2f} each)" if done > 1 else ""
    spent = (f"Spent about ${meter.spent_usd:.2f}{cap}: research ${research:.2f}, course plan ${plan:.2f}, "
             f"lessons ${lessons:.2f}{each}.")
    if done == total:
        written = f"All {total} lessons written." if total > 1 else "The lesson is written."
        return f"{written} {spent} Nothing more will be spent."
    line = f"{'Halfway: ' if halfway else ''}{done} of {total} lessons written. {spent}"
    if advice:
        return f"{line} {advice}"
    ahead = meter.projection(done, total)
    left = "The last one" if total - done == 1 else f"The {total - done} left"
    line += f" {left} should cost about ${ahead.end_usd - meter.spent_usd:.2f}, so about ${ahead.end_usd:.2f} in all."
    switched = meter.switch_usd is not None and meter.spent_usd >= meter.switch_usd
    if ahead.cheap_from is not None and not switched:  # once switched, the switch line has said so
        line += f" From about lesson {ahead.cheap_from}, a cheaper model ({meter.cheap_model}) writes the rest."
    return line


def build(request: str, engine: Engine, ask: Ask = input, say: Say = print, reviewer: bool = True,
          fresh: bool = False, background: bool = False, build_dir: Path | None = None,
          notify: Callable[[str], None] = lambda text: None, worker: bool = False) -> int:
    """Build a course. With `background`, this terminal asks the questions and saves the answers,
    then the build goes on by itself (detach), and the terminal is free."""
    from . import course_dir
    from .cli import _caused_by, load_spend, save_spend
    from .flow import open_problems, start
    from .model import LearnerProfile
    from . import learn_cli
    from .learn_cli import carry_on, hide_secrets
    from .stages import clear_stale_temps, write_atomic
    from .web import HttpWeb

    root = home().resolve()  # the build process runs in its build folder, so a relative LEARN_HOME would move
    if builds_dir(root).is_dir():
        builds_dir(root).chmod(0o700)  # builds from before this was set, too
    b = build_dir or (None if fresh else find_build(root, request, engine.name))
    if b is not None and (b / "finished").is_file() and Path((b / "finished").read_text().strip()).is_dir():
        # rebuilding a finished course once wrote over it, and the learner's progress with it.
        # If its folder was moved or deleted there's nothing to lose, so it's written again below
        folder = (b / "finished").read_text().strip()
        Path(folder).chmod(0o700)  # a course written before folders were made private
        say(f"This course is already built: {folder}\nWork on it with: cd {folder} && learn next\n"
            f"To build a new copy from scratch in a new folder: {carry_on(request, engine.name, '--fresh')}")
        return 0
    rewriting = b is not None and (b / "finished").is_file()  # finished, but its folder is gone
    resuming = b is not None
    b = (b or new_build(root, request, engine.name)).resolve()  # the worker starts in it, so no relative path
    clear_stale_temps(b)

    # the details go to a log in the build folder. The screen gets one line per step
    handler = logging.FileHandler(b / "build.log")
    handler.setFormatter(Hidden("%(asctime)s %(name)s %(message)s", "%H:%M:%S"))
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)
    logging.captureWarnings(True)  # library warnings go to the log too, not the learner's screen
    # httpx2 logs every request's full URL, and a search key once went into build.log in one
    for noisy in ("strands", "botocore", "httpx", "httpx2", "mcp", "google_adk", "google_genai"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    logging.getLogger("google_genai._api_client").setLevel(logging.INFO)  # "Retrying ... in 4.2 seconds"

    spend = b / "spend.json"
    try:
        load_spend(engine.meter, spend)
    except ValueError as e:
        # outside the try below on purpose: its finally would overwrite the file with $0
        say(f"\n{e}")
        logging.getLogger().removeHandler(handler)
        return 1
    # one build per folder: a second `learn` of the same request once wrote and paid for the same lessons
    if not hold(b / "running"):
        say("\nThis course is being built right now. learn shows how it's going, and learn stop stops it.")
        logging.getLogger().removeHandler(handler)
        return 1
    folder, stopped, told = None, False, False  # the course folder, whether this build has stopped, and said so
    subject, handed_off = "", False  # what the course is about, and whether a background build took over

    status: dict = {}

    def progress(line: str | None = None, advice: str | None = None) -> None:
        """What the build is doing, and what to do about it, for `learn` to show while nobody
        watches the build itself: the cap's "raise LEARNING_BUDGET_USD" once went only to its log."""
        if line is not None:
            status["line"] = line.strip()
        if advice is not None:
            status["advice"] = " ".join(advice.split())
        status.update(updated=time.time(), cap=engine.meter.limit_usd)
        try:
            write_atomic(b / "status.json", json.dumps(status))
        except OSError:
            pass
    engine.meter.stop_file = b / "stop"  # where `learn stop` asks this build to stop
    if not worker:  # a stop asked for last time is done. The terminal clears it, and a build process
        engine.meter.stop_file.unlink(missing_ok=True)  # starting up keeps one asked for since
    restore = None  # the Ctrl-C handler that was there before this build's

    def beat() -> None:
        """Every model call tells `learn` in the course that the build is alive, and which process it is."""
        save_spend(engine.meter, spend)
        if not stopped and folder is not None:
            course_dir.note_running(folder, True, os.getpid())

    engine.meter.persist = beat
    engine.meter.say = lambda m: say(f"  {m}")  # the switch to a cheaper model is announced
    brain = engine.make_brain(engine.meter)

    def ready(where: str = "") -> str:
        """Which lessons are in the course folder to work on, counted there: on a resume, lessons from
        before are in it too."""
        try:
            n = len(json.loads((folder / ".learn" / "lessons.json").read_text())) if folder else 0
        except (OSError, ValueError):
            n = 0
        if not n:
            return ""
        which = "Lesson 1 is" if n == 1 else f"Lessons 1 to {n} are"
        return f"{which} ready{where} in {folder}: cd there and run learn next."

    try:
        saved = b / "profile.json"
        if saved.is_file():
            profile = LearnerProfile.model_validate_json(saved.read_text())
        else:
            profile = interview(brain, request, ask, say)
            if not profile.subject_is_clear:
                say("\nI still can't tell what to research. Try again and name the subject, "
                    'like: learn "I want to learn Rust"')
                return 1
            write_atomic(saved, profile.model_dump_json(indent=1))
        folder, subject = course_folder(root, b, profile.subject), profile.subject
        background = background and not rewriting  # writing a finished course again is quick, and free
        if background and engine.meter.limit_usd and engine.meter.spent_usd >= engine.meter.limit_usd:
            # it would stop at once, where nobody sees why
            say(f"This build has spent ${engine.meter.spent_usd:.2f} of your ${engine.meter.limit_usd:.2f} cap. "
                f"Raise LEARNING_BUDGET_USD in {config_file()}, then run the same command to carry on.")
            progress("Stopped at the spending cap.",
                     advice=f"Raise LEARNING_BUDGET_USD in {config_file()}, then run {carry_on(request, engine.name)} "
                            "to carry on.")
            return 2
        if not background:
            course_dir.note_running(folder, True, os.getpid())  # a course stopped partway is being written again
        cap = engine.meter.limit_usd
        if rewriting:
            say(f"\nYour {profile.subject} course folder is missing, so I'm writing it again from the finished "
                "build. This costs nothing.")
        elif resuming:
            say(f"\nPicking up your {profile.subject} course where it stopped"
                + (", in the background." if background else "."))
        else:
            say(f"\nGot it. Building your {profile.subject} course in {folder}")
            if not background:
                say("This usually takes 30 to 90 minutes. You can stop it any time, and running the same "
                    "command again picks up where it left off.")
            say(SUPPORTED)
        if cap:
            m = engine.meter
            point = m.switch_usd
            if not m.cheap_model or (point is not None and m.spent_usd >= point):
                switch = ""  # past it, the meter says so at the next call
            elif point is None:  # research and the plan set the point, so it isn't known yet
                switch = (f" Once lessons have used {m.switch_at:.0%} of what's left after research and "
                          f"planning, a cheaper model ({m.cheap_model}) writes the rest.")
            else:
                switch = f" At ${point:.2f} a cheaper model ({m.cheap_model}) takes over."
            say(f"Spending cap: ${cap:.2f}. Spent so far: ${m.spent_usd:.2f}.{switch}"
                f"\nChange these in {config_file()}\n")
        if background:
            if ready():
                when = f"{ready()} " + ("You'll get a notification as the rest are written." if can_notify()
                                        else "learn shows how the rest are coming.")
            else:
                when = ("You'll get a notification when lesson 1 is ready." if can_notify()
                        else "learn shows when lesson 1 is ready.") + \
                    f" Then open {folder} in your editor and run learn next in its terminal."
            detach(b, reviewer)  # handed the lock while this terminal still holds it, so it's never free
            handed_off = True  # if it couldn't start, this terminal still saves the spend and says why
            release(b / "running")  # then this terminal's own copy goes. The build process's keeps it held
            say(f"It's building in the background, so you can close this terminal. {when}\n"
                "Outside the course folder, learn shows how it's going. learn stop stops it.")
            return 0
        warned = False

        def lesson_written(done: int, total: int) -> None:
            nonlocal warned, told
            if stopped:  # a stopped build's worker can still be finishing a lesson: it doesn't count
                return
            try:  # each lesson is there to work on as soon as it's written, not when the last one is
                course_dir.note_building(folder, total, request, engine.name, os.getpid())
                course_dir.write(flow.course(), folder)
                if not told and done < total:
                    say(f"  {ready(' to start')}" + ("" if worker else
                                                      " Keep this one running and open another terminal to work in."))
                    notify(f"{subject}: {ready()}")
                    told = True
            except Exception as e:  # releasing early is a bonus: the write at the end tries again, and says if it fails
                logging.getLogger("learning").warning("couldn't add lesson %d to %s yet: %s", done, folder, e,
                                                      exc_info=True)
            if line := spend_line(engine.meter, done, total, warned):
                say("  " + line.replace("\n", "\n  "))
                progress(advice=line)  # the spend so far, and what to do if the cap is coming
                warned = warned or cap_advice(engine.meter, done, total) is not None

        def told_step(m: str) -> None:
            say(f"  {m}")
            progress(m)

        flow = start(brain, HttpWeb(), profile, b / "run", reviewer=reviewer, say=told_step, on_lesson=lesson_written)
        presses = 0

        def on_ctrl_c(signum, frame) -> None:
            """The stages run on worker threads, and a plain Ctrl-C only reached the main one: the build
            ran on, writing and paying for lessons. The first press stops it before the next model call."""
            nonlocal presses, stopped
            if stopped:  # the build is already saying how it ended
                return
            presses += 1
            if presses == 1:
                engine.meter.stop_requested = True
                say("\n  Stopping before the next model call, so nothing more is spent. Ctrl-C again stops at "
                    "once, and loses the step that's running.")
                return
            stopped = True
            learn_cli.abandon()  # an exercise's tests run in a session of their own, and outlived the build
            save_spend(engine.meter, spend)
            if folder is not None:
                course_dir.note_running(folder, False)
            say(f"\nStopped. The step that was running is lost. To carry on: {carry_on(request, engine.name)}"
                + (f"\n{ready()}" if ready() else ""))
            sys.stdout.flush()
            handler.flush()
            os._exit(130)  # the worker threads can't be joined, and waiting on them is what the second press skips

        # only the main thread can catch signals, and a Ctrl-C someone set to be ignored (nohup) stays ignored.
        # asyncio.run leaves a handler that isn't Python's own alone. It stays until the build has said how it ended
        if threading.current_thread() is threading.main_thread() and \
                signal.getsignal(signal.SIGINT) is not signal.SIG_IGN:
            restore = signal.getsignal(signal.SIGINT)
            restore = signal.default_int_handler if restore is None else restore  # SIG_DFL is 0, and stays
            signal.signal(signal.SIGINT, on_ctrl_c)
        engine.run_pipeline(flow)
        course = flow.course()
        course_dir.write(course, folder)  # inside the try: a failure here is explained, not a traceback
        course_dir.note_finished(folder)
        write_atomic(b / "finished", str(folder))
    except KeyboardInterrupt:
        if handed_off:  # the build process has it now, and carries on: this terminal has nothing to stop
            say("\nIt's building in the background. learn stop stops it.")
            return 0
        stopped = True
        say(f"\nStopped. To carry on: {carry_on(request, engine.name)}" + (f"\n{ready()}" if ready() else ""))
        progress("Stopped.", advice="")
        notify(f"{subject}: the build stopped. {ready()}".strip())
        return 130
    except Exception as e:
        if handed_off:  # this terminal's screen or its copy of the lock failed, after the build process took over.
            logging.getLogger("learning").exception("after the hand-off")  # That one reports how the build goes
            return 0
        stopped = True
        kept = f"\n{ready()}" if ready() else ""
        if engine.meter.stop_requested:  # Ctrl-C or `learn stop`, reaching the build as an error from inside a stage
            say(f"\nStopped. Nothing more will be spent. To carry on: {carry_on(request, engine.name)}{kept}")
            progress("Stopped. Nothing more will be spent.", advice="")
            notify(f"{subject}: the build stopped. {ready()}".strip())
            return 130
        if not _caused_by(e, engine.budget_error):
            say(f"\nSomething went wrong: {hide_secrets(str(e))}\nThe details are in {b / 'build.log'}. Running the same "
                f"command again picks up from the last step that finished.{kept}")
            logging.getLogger("learning").exception("build failed")
            progress(f"Something went wrong: {hide_secrets(str(e))}",
                     advice=f"The details are in {b / 'build.log'}. To carry on from the last step that finished: "
                            f"{carry_on(request, engine.name)}")
            notify(f"{subject}: the build stopped because something went wrong. learn shows what to do.")
            return 1
        say(f"\nStopped at the spending cap: {hide_secrets(str(e))}\nRaise LEARNING_BUDGET_USD in {config_file()}, then run "
            f"the same command to carry on.{kept}")
        progress("Stopped at the spending cap.",
                 advice=f"Raise LEARNING_BUDGET_USD in {config_file()}, then run {carry_on(request, engine.name)} "
                        "to carry on.")
        notify(f"{subject}: the build stopped at your spending cap. learn shows what to do.")
        return 2
    finally:
        stopped = True
        if not handed_off:  # after the hand-off, the build's own process writes these
            try:
                save_spend(engine.meter, spend)
            except OSError as e:  # how the build ended is already said, and this mustn't take its place
                logging.getLogger("learning").warning("couldn't save the spend: %s", e)
                say(f"Couldn't save what this build spent (${engine.meter.spent_usd:.2f}): {hide_secrets(str(e))}")
            if folder is not None:  # a course with lessons still to come says the build has stopped
                course_dir.note_running(folder, False)
        if restore is not None:
            signal.signal(signal.SIGINT, restore)
        logging.getLogger().removeHandler(handler)  # the hold on the build folder lasts until the process ends

    problems = {p.lesson_id for p in open_problems(flow.board) if p.lesson_id}
    say(f"\nYour course is ready: {folder}")
    say(f"{len(course.lessons)} lessons, and it cost about ${engine.meter.spent_usd:.2f} to build.")
    progress(f"Ready: {len(course.lessons)} lessons, about ${engine.meter.spent_usd:.2f}.",
             advice=f"cd {folder} && learn next")
    notify(f"Your {subject} course is ready: {len(course.lessons)} lessons, about ${engine.meter.spent_usd:.2f}.")
    if problems:
        say(f"{len(problems)} lessons still have problems my checks found. Each one says so at the top.")
    say(f"Start with: cd {folder} && learn next")
    from .learn_cli import EDITORS, editor
    found = editor()
    name = EDITORS.get(Path(found).stem.lower(), Path(found).stem) if found else None
    chosen = os.environ.get("LEARN_EDITOR", "").strip().lower()
    say(f"That opens the first lesson in {name}, next to the files you'll change. Run learn check in {name}'s "
        "terminal to test your work." if name else
        "Work through it in VS Code or Cursor: each lesson is a README.md to read and an exercise/ folder of files "
        "to change, and you run learn check in the editor's terminal."
        + ("" if chosen == "none" else " To have learn next open them for you, get VS Code from "
           "https://code.visualstudio.com. On macOS, also run \"Shell Command: Install 'code' command in PATH\" "
           "from its Command Palette."))
    return 0


LESSON_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def course_command(argv: list[str], here: Path | None) -> bool:
    """Whether the words are for a course rather than a request to learn something.

    Outside a course, `learn next js app router` is a request to learn Next.js. But
    `learn check u1-l1` and `learn report "..."` are still course commands there, which then
    say you're not in a course instead of starting a paid build about them.
    """
    if not argv or argv[0] not in COURSE_COMMANDS:
        return False
    if argv[0] == "check":  # check --watch is still check
        argv = [a for a in argv if a != "--watch"]
    if here or len(argv) == 1 or argv[0] == "report":
        return True
    return len(argv) == 2 and bool(LESSON_ID.fullmatch(argv[1].lower())) and any(ch.isdigit() for ch in argv[1])


def slip(word: str, command: str) -> bool:
    """A typo of `command`: wrong capitals, two letters swapped, one letter missing or one doubled.
    One letter changed doesn't count, because nest, text and mint are real things to learn."""
    w = word.lower()
    if w == command:
        return word != command
    if len(w) == len(command):
        return sorted(w) == sorted(command)
    if len(w) == len(command) - 1:
        return any(command[:i] + command[i + 1:] == w for i in range(len(command)))
    if len(w) == len(command) + 1:
        return any(w[:i] + w[i + 1:] == command and w[i] in (w[i - 1:i] + w[i + 1:i + 2]) for i in range(len(w)))
    return False


# -- the command ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    here = course_root(Path.cwd().resolve())
    if course_command(argv, here):
        return in_course(argv)
    if not argv and here:
        return in_course(["next"])
    ap = argparse.ArgumentParser(prog="learn", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("request", nargs="*", help="what you want to learn, in your own words")
    ap.add_argument("--engine", choices=("adk", "strands"),
                    help="adk runs Gemini, strands runs Claude on Amazon Bedrock. Picked from your keys if unset")
    ap.add_argument("--no-review", action="store_true", help="skip the model reviewer, keep the mechanical checks")
    ap.add_argument("--fresh", action="store_true",
                    help="build a new copy in a new folder, even if this request was built before")
    ap.add_argument("--wait", action="store_true",
                    help="build in this terminal and wait for it, where it would go to the background")
    ap.add_argument("--worker", type=Path, help=argparse.SUPPRESS)  # the background build, started by detach
    ap.add_argument("--held-fd", type=int, help=argparse.SUPPRESS)  # and the lock it's handed
    args = ap.parse_args(argv)
    if args.worker:
        return work(args.worker, reviewer=not args.no_review, held_fd=args.held_fd)
    # one word that's only ever a slip of the fingers once started a paid build about it
    if [w.lower() for w in args.request] == ["help"]:
        ap.print_help()
        print("\nInside a course: learn " + ", learn ".join(COURSE_COMMANDS))
        return 0
    if [w.lower() for w in args.request] == ["stop"]:
        return stop_builds(here)
    if here and args.request and args.request[0] in COURSE_COMMANDS:  # a flag came first: learn --fresh next
        return in_course(args.request)
    if here and len(args.request) == 1:
        meant = next((c for c in COURSE_COMMANDS if slip(args.request[0], c)), None)
        if meant:
            print(f"`learn {args.request[0]}` isn't a command. Did you mean `learn {meant}`?\n"
                  f"To build a course about it, add a few words: learn \"{args.request[0]} for beginners\"")
            return 2
    # the frameworks warn about their own experimental features when they're imported, which
    # means nothing to someone learning TypeScript
    warnings.filterwarnings("ignore", module=r"(google|strands|opentelemetry|mcp|pydantic)(\.|$)")
    load_config()
    if not " ".join(args.request).strip():
        return list_courses()
    problems, typos = check_settings()
    for t in typos:
        print(t)
    if problems:
        print(f"Some settings can't be used (from your environment or {config_file()}):")
        for p in problems:
            print(f"  - {p}")
        print("Fix them and run the same command. Nothing was built and nothing was spent.")
        return 2
    name = pick_engine(args.engine, getpass.getpass, print)
    if name is None:
        return 1
    # in a terminal on macOS or Linux the build goes to the background. A script, Windows (no session
    # to put it in) and --wait keep it here
    background = os.name == "posix" and not args.wait and sys.stdin.isatty() and sys.stdout.isatty()
    return build(" ".join(args.request), load_engine(name), reviewer=not args.no_review, fresh=args.fresh,
                 background=background)


if __name__ == "__main__":
    sys.exit(main())

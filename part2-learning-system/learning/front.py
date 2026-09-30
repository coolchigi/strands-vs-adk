"""learn: tell it what you want to learn, and work through the course it builds.

    learn "I want to learn TypeScript so I can build a small web app"
    learn                 your courses, and how far you are in each
    learn next            inside a course folder: where you are, and what's next
    learn check           run the current exercise's tests
    learn hint            one hint at a time
    learn solution        show the answer, and record that you looked
    learn quiz            answer the questions, then see the answers
    learn review          questions you missed, when they're due again
    learn report "..."    flag something wrong in the current lesson
    learn status          every lesson, and what you've done

Courses go in ~/courses, one folder each (LEARN_HOME changes that). Building one takes 30
to 90 minutes, and if it stops, running the same request again picks up where it left off.
Keys and settings live in ~/.config/learning-system/env.
"""

from __future__ import annotations

import argparse
import getpass
import json
import logging
import os
import re
import subprocess
import sys
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
    env = {**os.environ, "LEARN_AS": "learn", "LEARN_ROOT": str(root)}
    return subprocess.run([sys.executable, "-m", "learning.learn_cli", *argv], cwd=root, env=env).returncode


def list_courses(say: Say = print) -> int:
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
        say(f"{c.name:24} {finished} of {len(lessons)} lessons done   {title}")
    for b in builds:
        say(f'{"(still building)":24} learn "{(b / "request.txt").read_text()}"   to carry on')
    say(f"\nCourses live in {root}. cd into one and type `learn next`.")
    return 0


# -- keys and the engine, set up once -------------------------------------------------------

def load_config() -> None:
    """KEY=VALUE lines from the config file, for anything not already set."""
    f = config_file()
    if f.is_file():
        for line in f.read_text().splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() and not key.strip().startswith("#"):
                os.environ.setdefault(key.strip(), value.strip())


def save_config(key: str, value: str) -> None:
    f = config_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    lines = [l for l in (f.read_text().splitlines() if f.exists() else []) if not l.startswith(f"{key}=")]
    f.write_text("\n".join([*lines, f"{key}={value}"]) + "\n")
    f.chmod(0o600)
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
        key = ask_secret("Paste it here (it won't show): ").strip()
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


def same_request(a: str, b: str) -> bool:
    return " ".join(a.split()).lower() == " ".join(b.split()).lower()


def find_build(root: Path, request: str, engine: str) -> Path | None:
    for b in sorted(builds_dir(root).glob("*")) if builds_dir(root).exists() else []:
        if (b / "request.txt").is_file() and same_request((b / "request.txt").read_text(), request) \
                and (b / "engine.txt").read_text() == engine:
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
    b.mkdir(parents=True)
    (b / "request.txt").write_text(request)
    (b / "engine.txt").write_text(engine)
    return b


def course_folder(root: Path, build: Path, subject: str) -> Path:
    """~/courses/<subject>, or <subject>-2 and so on if another course has that name."""
    saved = build / "course.txt"
    if saved.is_file():
        return Path(saved.read_text())
    base, n = slug(subject), 1
    taken = {Path(p.read_text()) for p in builds_dir(root).glob("*/course.txt")}
    folder = root / base
    while folder.exists() or folder in taken:
        n += 1
        folder = root / f"{base}-{n}"
    saved.write_text(str(folder))
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


def build(request: str, engine: Engine, ask: Ask = input, say: Say = print, reviewer: bool = True) -> int:
    from . import course_dir
    from .cli import _caused_by, load_spend, save_spend
    from .flow import open_problems, start
    from .model import LearnerProfile
    from .web import HttpWeb

    root = home()
    b = find_build(root, request, engine.name)
    resuming = b is not None
    b = b or new_build(root, request, engine.name)

    # the details go to a log in the build folder. The screen gets one line per step
    handler = logging.FileHandler(b / "build.log")
    handler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(message)s", "%H:%M:%S"))
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)
    logging.captureWarnings(True)  # library warnings go to the log too, not the learner's screen
    for noisy in ("strands", "botocore", "httpx", "mcp", "google_adk", "google_genai"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    spend = b / "spend.json"
    load_spend(engine.meter, spend)
    engine.meter.persist = lambda: save_spend(engine.meter, spend)
    engine.meter.say = lambda m: say(f"  {m}")  # the switch to a cheaper model is announced
    brain = engine.make_brain(engine.meter)
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
            saved.write_text(profile.model_dump_json(indent=1))
        folder = course_folder(root, b, profile.subject)
        cap = engine.meter.limit_usd
        if resuming:
            say(f"\nPicking up your {profile.subject} course where it stopped.")
        else:
            say(f"\nGot it. Building your {profile.subject} course in {folder}")
            say("This usually takes 30 to 90 minutes. You can stop it any time, and running the same "
                "command again picks up where it left off.")
            say(SUPPORTED)
        if cap:
            cheap = engine.meter.cheap_model
            say(f"Spending cap: ${cap:.2f}. Spent so far: ${engine.meter.spent_usd:.2f}."
                + (f" At ${engine.meter.switch_at * cap:.2f} it switches to a cheaper model ({cheap}) to finish."
                   if cheap else "")
                + f"\nChange these in {config_file()}\n")
        flow = start(brain, HttpWeb(), profile, b / "run", reviewer=reviewer, say=lambda m: say(f"  {m}"))
        engine.run_pipeline(flow)
        course = flow.course()
    except KeyboardInterrupt:
        say(f'\nStopped. Run the same command to carry on: learn "{request}"')
        return 130
    except Exception as e:
        if not _caused_by(e, engine.budget_error):
            say(f"\nSomething went wrong: {e}\nThe details are in {b / 'build.log'}. Running the same "
                "command again picks up from the last step that finished.")
            logging.getLogger("learning").exception("build failed")
            return 1
        say(f"\nStopped at the spending cap: {e}\nRaise LEARNING_BUDGET_USD in {config_file()}, then run "
            "the same command to carry on.")
        return 2
    finally:
        save_spend(engine.meter, spend)
        logging.getLogger().removeHandler(handler)

    course_dir.write(course, folder)
    (b / "finished").write_text(str(folder))
    problems = {p.lesson_id for p in open_problems(flow.board) if p.lesson_id}
    say(f"\nYour course is ready: {folder}")
    say(f"{len(course.lessons)} lessons, and it cost about ${engine.meter.spent_usd:.2f} to build.")
    if problems:
        say(f"{len(problems)} lessons still have problems my checks found. Each one says so at the top.")
    say(f"Start with: cd {folder} && learn next")
    return 0


# -- the command ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in COURSE_COMMANDS:
        return in_course(argv)
    if not argv and course_root(Path.cwd().resolve()):
        return in_course(["next"])
    ap = argparse.ArgumentParser(prog="learn", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("request", nargs="*", help="what you want to learn, in your own words")
    ap.add_argument("--engine", choices=("adk", "strands"),
                    help="adk runs Gemini, strands runs Claude on Amazon Bedrock. Picked from your keys if unset")
    ap.add_argument("--no-review", action="store_true", help="skip the model reviewer, keep the mechanical checks")
    args = ap.parse_args(argv)
    # the frameworks warn about their own experimental features when they're imported, which
    # means nothing to someone learning TypeScript
    warnings.filterwarnings("ignore", module=r"(google|strands|opentelemetry|mcp|pydantic)(\.|$)")
    load_config()
    if not args.request:
        return list_courses()
    name = pick_engine(args.engine, getpass.getpass, print)
    if name is None:
        return 1
    return build(" ".join(args.request), load_engine(name), reviewer=not args.no_review)


if __name__ == "__main__":
    sys.exit(main())

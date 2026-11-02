"""Writing a course to disk the way a learner works through it.

```text
course/
├── README.md              who it's for, what you'll be able to do, how to use it
├── learn.py               next, check, quiz, hint, solution, review, status
├── SOURCES.md             every source, and every claim taken from it
├── course.json            the whole course, for the judge and for refresh
└── units/
    └── u1-.../
        ├── README.md      the unit's outcomes, its lessons, its project
        └── u1-l1-.../
            ├── README.md  the lesson
            ├── exercise/  starter files, and the tests learn.py runs
            ├── quiz.json  questions only
            └── .answers/  solution, answers, hints. learn.py opens these for you
```
"""

from __future__ import annotations

import json
import logging
import random
import re
import shutil
import time
from pathlib import Path

from .checks import CITATION, MALFORMED_CITATION, OPTION_BY_POSITION, cited, unsafe_path
from .learn_cli import runner_for
from .model import Course, Lesson, LessonSpec, Problem, QuizItem, Unit
from .stages import write_atomic

log = logging.getLogger("learning")



def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48]


def unit_dir(unit: Unit) -> str:
    # ids are slugged too: they come from the model, and checks.curriculum asks for plain ones
    return f"units/{slug(unit.id)}-{slug(unit.title)}"


def lesson_dir(unit: Unit, spec: LessonSpec) -> str:
    return f"{unit_dir(unit)}/{slug(spec.id)}-{slug(spec.title)}"


def _cite(text: str, urls: dict[str, str]) -> str:
    """[c:ID] becomes a link to the page the claim came from. Several ids citing one page
    become one link."""
    def links(m: re.Match) -> str:
        pages = list(dict.fromkeys(urls[i] for i in cited(m.group(0)) if i in urls))
        return "(" + ", ".join(f"[source]({u})" for u in pages) + ")" if pages else ""
    # a citation the model mistyped links nowhere, so it doesn't show at all. The check
    # for lessons flags it
    return MALFORMED_CITATION.sub("", CITATION.sub(links, text))


def _one_line(detail: str, limit: int = 300) -> str:
    text = " ".join(detail.split())
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "..."


def known_problems(problems: list[Problem]) -> list[str]:
    """What our own checks and reviewers still found after every retry. Said up front, so a
    learner who hits it knows it's the course, not them."""
    if not problems:
        return []
    out = ["> **Known problems.** This lesson didn't pass all of our own checks. "
           "If something below doesn't work, it may be this:", ">"]
    out += [f"> - {_one_line(p.detail)}" for p in problems]
    return out + ["", "Found something else? `learn report \"what's wrong\"`", ""]


def shuffled(q: QuizItem, seed: str) -> QuizItem:
    """The same question with its options in a fair order.

    Models have a favourite slot for the right answer. Gemini put it first in 30 of 36
    questions, Claude second in 30 of 51, so a learner could pass by position. The seed
    keeps a course's order the same every time it's written.
    """
    if OPTION_BY_POSITION.search(q.explanation):
        return q  # the explanation points at options by position, and moving them would make it wrong
    order = list(range(len(q.options)))
    random.Random(seed).shuffle(order)
    return q.model_copy(update={"options": [q.options[i] for i in order], "answer": order.index(q.answer)})


NEEDS = {
    "terraform": "The tests run with `terraform test`, so you'll need "
                 "[Terraform](https://developer.hashicorp.com/terraform/install) installed.",
    "python": "The tests run with Python's own `unittest`, so there's nothing extra to install.",
    "node": "The tests run with Node's built-in test runner, so you'll need "
            "[Node.js](https://nodejs.org/en/download) 20 or newer, or 22.6 or newer for TypeScript. "
            "TypeScript is also type-checked with the TypeScript compiler, which `check` fetches once with npm.",
    None: "Nothing can check this exercise automatically, so you're the judge. When you're happy with "
          "it, `learn check` marks it done and `learn solution` shows the answer.",
}


def lesson_runner(lesson: Lesson) -> str | None:
    return runner_for([f.path for f in lesson.exercise.checks]) if lesson.exercise else None


def lesson_readme(unit: Unit, spec: LessonSpec, lesson: Lesson, urls: dict[str, str],
                  problems: list[Problem] | None = None) -> str:
    out = [f"# {spec.title}", "", f"*{unit.title}*", ""] + known_problems(problems or [])
    out += ["## By the end of this lesson you can", ""]
    out += [f"- {o.statement}" for o in spec.objectives]
    if lesson.recall.strip():
        out += ["", "## Where we are", "", lesson.recall.strip()]
    out += ["", "## The idea", "", _cite(lesson.explanation.strip(), urls),
            "", "## Worked example", "", _cite(lesson.worked_example.strip(), urls)]
    if lesson.exercise:
        out += ["", "## Your turn", "", lesson.exercise.task.strip(), "",
                NEEDS[lesson_runner(lesson)], "",
                "Your files are in `exercise/`. When you think it works:", "",
                "```bash", "learn check", "```", "",
                "Stuck? `learn hint` gives one hint at a time. "
                "`learn solution` shows the answer, and records that you looked."]
    asked = sum(answerable(q) for q in lesson.quiz)
    if asked:
        out += ["", "## Check yourself", "",
                f"{asked} question{'s' if asked != 1 else ''}. Answer {'them' if asked != 1 else 'it'} "
                "before you see the answers:", "",
                "```bash", "learn quiz", "```"]
    return "\n".join(out) + "\n"


def course_readme(c: Course, paths: dict[str, str]) -> str:
    cur, kb = c.curriculum, c.knowledge
    out = [f"# {cur.title}", "", cur.summary.strip(), "", "## Who this is for", "", "```text",
           c.profile.brief(), "```", "", "## What you'll be able to do", ""]
    out += [f"- {o}" for o in cur.outcomes]
    # only a version an official page states, named for what it numbers: an unchecked Python
    # version once appeared under a ledger course's name
    if kb.spec.version and kb.spec.version_checked:
        where = f" ([source]({kb.spec.version_url}))" if kb.spec.version_url else ""
        named = f"{kb.spec.version_of} {kb.spec.version}" if kb.spec.version_of else f"version {kb.spec.version}"
        out += ["", f"Written against {named}{where}."]
    kind = ("the official exam guide" if kb.spec.kind == "exam_guide"
            else "the official documentation, shaped by what you said you want to do")
    out += ["", f"What this course covers comes from {kind}. Every fact in a lesson links to the "
            "page it came from. `SOURCES.md` lists them all.", "", "## How to use it", "",
            "Work through it in VS Code or Cursor. `learn next` opens the lesson and the files you'll change, "
            "and you run the commands below in the editor's terminal.", "", "```bash",
            "learn next      # where you are, and what's next",
            "learn check     # run the tests for the lesson you're on",
            "learn check --watch  # check again every time you save",
            "learn hint      # one hint at a time",
            "learn quiz      # answer, then see the answers",
            "learn review    # questions you missed, when they're due again",
            "```", "", "No `learn` command? Type `python3 learn.py` wherever it says `learn` "
            "(`py learn.py` on Windows), and everything works the same from this folder. Each lesson's "
            "exercise says what you need installed to run its tests.", ""]
    if c.problems:
        out += ["## Known problems", "",
                "What our own checks and reviewers still found after every retry. Lessons with a "
                "problem say so at the top.", ""]
        out += [f"- {_one_line(p.detail if not p.lesson_id or p.detail.startswith(p.lesson_id) else f'{p.lesson_id}: {p.detail}')}"
                for p in c.problems]
        out += [""]
    out += ["## Units", ""]
    for u in cur.units:
        out += [f"### {u.id}. {u.title}", ""]
        written = {l.id for l in c.lessons}
        out += [f"{i}. [{s.title}]({paths[s.id]}/README.md)" if s.id in written else f"{i}. {s.title} (still being written)"
                for i, s in enumerate(u.lessons, 1)]
        if u.project:
            out += ["", f"**Project:** {u.project}"]
        out += [""]
    return "\n".join(out)


def sources_md(c: Course) -> str:
    out = ["# Sources", "", "Every claim a lesson teaches, the words it rests on, and where they are.", ""]
    for s in c.knowledge.sources:
        claims = [x for x in c.knowledge.claims if x.source_id == s.id]
        if not claims:
            continue
        out += [f"## [{s.title or s.url}]({s.url})", "", f"{s.tier.value}, fetched {s.fetched_at:%Y-%m-%d}", ""]
        out += [f"- {x.text}  \n  > {x.quote}" for x in claims]
        out += [""]
    return "\n".join(out)


def put(target: Path, content: str, keep: bool = False) -> None:
    """Write one file. `keep` leaves a file that's already there alone: the learner's own work.
    A path that clashes with another one in the same exercise (`src` and `src/app.py`) is
    skipped and logged, because the whole course is worth more than one broken file."""
    if target.is_file() and (keep or target.read_text(errors="replace") == content):
        return  # the learner's own work, or nothing new: a release rewrote every file every lesson
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        write_atomic(target, content)  # a stop mid-write mustn't leave an empty starter that's then kept
    except (FileExistsError, NotADirectoryError, IsADirectoryError) as e:
        log.warning("skipped %s: %s", target, e)


def place(folder: Path, files: list, keep: bool = False) -> None:
    """Write an exercise's files under `folder`, leaving out any whose path would land outside it.
    checks.lesson flags those paths, so a lesson that still has one says so at the top."""
    for f in files:
        if why := unsafe_path(f.path):
            log.warning("left out %r from %s: %s", f.path, folder, why)
        else:
            put(folder / f.path, f.content, keep)


def answerable(q: QuizItem) -> bool:
    return 0 <= q.answer < len(q.options)


def write(c: Course, root: Path, replace: bool = False) -> Path:
    """Write the course into `root`, adding to what's there.

    Rewriting a finished course once deleted the folder first, and a learner's progress and
    exercise edits with it. Now nothing is deleted and exercise files that exist are kept.
    `replace` starts from an empty folder, for the developer's out/ copies only.
    """
    root = Path(root)
    if replace and root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    root.chmod(0o700)  # the course carries your profile and the pages it read, courses from before included
    urls = {x.id: s.url for s in c.knowledge.sources for x in c.knowledge.claims if x.source_id == s.id}
    try:  # the lessons the learner already has: lessons.json is written last, so these were handed over whole
        handed = {l["id"] for l in json.loads((root / ".learn" / "lessons.json").read_text())}
    except (OSError, ValueError, TypeError, KeyError):
        handed = set()
    lessons = {l.id: l for l in c.lessons}
    paths: dict[str, str] = {}
    order: list[dict] = []

    for unit in c.curriculum.units:
        udir = root / unit_dir(unit)
        udir.mkdir(parents=True, exist_ok=True)
        lines = [f"# {unit.title}", "", "## Outcomes", ""] + [f"- {o}" for o in unit.outcomes] + ["", "## Lessons", ""]
        for spec in unit.lessons:
            rel = lesson_dir(unit, spec)
            paths[spec.id] = rel
            lesson = lessons.get(spec.id)
            if lesson is None:  # while the build is still writing it, there's nothing to link to
                lines.append(f"- {spec.title} (still being written)")
                continue
            lines.append(f"- [{spec.title}]({Path(rel).name}/README.md)")
            d = root / rel
            (d / ".answers").mkdir(parents=True, exist_ok=True)
            (d / "README.md").write_text(lesson_readme(unit, spec, lesson, urls,
                                                       [p for p in c.problems if p.lesson_id == spec.id]))
            # a lesson the learner has is theirs: a file they deleted stays deleted. One not handed
            # over yet is filled in, in case a write before this one stopped partway
            if lesson.exercise and spec.id not in handed:
                place(d / "exercise", lesson.exercise.starter + lesson.exercise.checks, keep=True)
            if lesson.exercise:
                place(d / ".answers" / "solution", lesson.exercise.solution)
                write_atomic(d / ".answers" / "hints.json", json.dumps(lesson.exercise.hints, indent=2))
            # a question whose answer isn't one of its options once crashed the whole write after
            # the build was paid for. The lesson's known-problems box already names it
            for i, q in enumerate(lesson.quiz):
                if not answerable(q):
                    log.warning("%s question %d left out: its answer %d isn't one of its %d options",
                                spec.id, i + 1, q.answer, len(q.options))
            quiz = [shuffled(q, f"{spec.id}#{i}") for i, q in enumerate(lesson.quiz) if answerable(q)]
            # whole files only: the learner can be using the course while the build adds to it
            write_atomic(d / "quiz.json", json.dumps(
                [{"stem": q.stem, "options": q.options, "objective": q.objective} for q in quiz], indent=2))
            write_atomic(d / ".answers" / "quiz.json", json.dumps(
                [{"answer": q.answer, "explanation": q.explanation} for q in quiz], indent=2))
            order.append({"id": spec.id, "title": spec.title, "path": rel,
                          "exercise": lesson.exercise is not None, "runner": lesson_runner(lesson)})
        if unit.project:
            lines += ["", "## Project", "", unit.project]
        (udir / "README.md").write_text("\n".join(lines) + "\n")

    (root / "README.md").write_text(course_readme(c, paths))
    (root / "SOURCES.md").write_text(sources_md(c))
    write_atomic(root / "course.json", c.model_dump_json(indent=2))  # `learn` reads it to list courses
    (root / ".learn").mkdir(exist_ok=True)
    write_atomic(root / ".learn" / "lessons.json", json.dumps(order, indent=2))
    write_atomic(root / "learn.py", Path(__file__).with_name("learn_cli.py").read_text())
    return root


# learn.py's note that lessons are still to come, while the build writes them or after it stopped
BUILDING = Path(".learn") / "building.json"


def note_building(root: Path, total: int, request: str, engine: str, pid: int) -> None:
    (root / BUILDING).parent.mkdir(parents=True, exist_ok=True)
    write_atomic(root / BUILDING, json.dumps({"total": total, "request": request, "engine": engine, "pid": pid,
                                              "running": True, "updated": time.time()}, indent=2))


def note_running(root: Path, running: bool, pid: int = 0) -> None:
    """Whether the build that's writing this course is still at it, and which process it is: a
    resumed build kept the old one's pid, and read as stopped. Only a course with lessons still to
    come has a note to change."""
    try:
        note = json.loads((root / BUILDING).read_text())
        note.update(running=running, updated=time.time(), **({"pid": pid} if pid else {}))
        write_atomic(root / BUILDING, json.dumps(note, indent=2))
    except (OSError, ValueError, AttributeError):
        pass


def note_finished(root: Path) -> None:
    (root / BUILDING).unlink(missing_ok=True)


def load(root: Path) -> Course:
    return Course.model_validate_json((Path(root) / "course.json").read_text())

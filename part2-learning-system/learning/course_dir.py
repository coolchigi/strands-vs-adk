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
import random
import re
import shutil
from pathlib import Path

from .checks import CITATION, MALFORMED_CITATION, OPTION_BY_POSITION, cited
from .learn_cli import runner_for
from .model import Course, Lesson, LessonSpec, Problem, QuizItem, Unit



def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48]


def lesson_dir(unit: Unit, spec: LessonSpec) -> str:
    return f"units/{unit.id}-{slug(unit.title)}/{spec.id}-{slug(spec.title)}"


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
    if lesson.quiz:
        out += ["", "## Check yourself", "",
                f"{len(lesson.quiz)} questions. Answer them before you see the answers:", "",
                "```bash", "learn quiz", "```"]
    return "\n".join(out) + "\n"


def course_readme(c: Course, paths: dict[str, str]) -> str:
    cur, kb = c.curriculum, c.knowledge
    out = [f"# {cur.title}", "", cur.summary.strip(), "", "## Who this is for", "", "```text",
           c.profile.brief(), "```", "", "## What you'll be able to do", ""]
    out += [f"- {o}" for o in cur.outcomes]
    if kb.spec.version:
        where = f" ([source]({kb.spec.version_url}))" if kb.spec.version_url else ""
        out += ["", f"Written against {c.profile.subject} {kb.spec.version}{where}."]
    kind = ("the official exam guide" if kb.spec.kind == "exam_guide"
            else "the official documentation, shaped by what you said you want to do")
    out += ["", f"What this course covers comes from {kind}. Every fact in a lesson links to the "
            "page it came from. `SOURCES.md` lists them all.", "", "## How to use it", "", "```bash",
            "learn next      # where you are, and what's next",
            "learn check     # run the current exercise's tests",
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
        out += [f"{i}. [{s.title}]({paths[s.id]}/README.md)" for i, s in enumerate(u.lessons, 1)]
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


def write(c: Course, root: Path) -> Path:
    root = Path(root)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    urls = {x.id: s.url for s in c.knowledge.sources for x in c.knowledge.claims if x.source_id == s.id}
    lessons = {l.id: l for l in c.lessons}
    paths: dict[str, str] = {}
    order: list[dict] = []

    for unit in c.curriculum.units:
        unit_dir = root / f"units/{unit.id}-{slug(unit.title)}"
        unit_dir.mkdir(parents=True)
        lines = [f"# {unit.title}", "", "## Outcomes", ""] + [f"- {o}" for o in unit.outcomes] + ["", "## Lessons", ""]
        for spec in unit.lessons:
            rel = lesson_dir(unit, spec)
            paths[spec.id] = rel
            lines.append(f"- [{spec.title}]({Path(rel).name}/README.md)")
            lesson = lessons.get(spec.id)
            if lesson is None:
                continue
            d = root / rel
            (d / ".answers").mkdir(parents=True)
            (d / "README.md").write_text(lesson_readme(unit, spec, lesson, urls,
                                                       [p for p in c.problems if p.lesson_id == spec.id]))
            if lesson.exercise:
                for f in lesson.exercise.starter + lesson.exercise.checks:
                    target = d / "exercise" / f.path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(f.content)
                for f in lesson.exercise.solution:
                    target = d / ".answers" / "solution" / f.path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(f.content)
                (d / ".answers" / "hints.json").write_text(json.dumps(lesson.exercise.hints, indent=2))
            quiz = [shuffled(q, f"{spec.id}#{i}") for i, q in enumerate(lesson.quiz)]
            (d / "quiz.json").write_text(json.dumps(
                [{"stem": q.stem, "options": q.options, "objective": q.objective} for q in quiz], indent=2))
            (d / ".answers" / "quiz.json").write_text(json.dumps(
                [{"answer": q.answer, "explanation": q.explanation} for q in quiz], indent=2))
            order.append({"id": spec.id, "title": spec.title, "path": rel,
                          "exercise": lesson.exercise is not None, "runner": lesson_runner(lesson)})
        if unit.project:
            lines += ["", "## Project", "", unit.project]
        (unit_dir / "README.md").write_text("\n".join(lines) + "\n")

    (root / "README.md").write_text(course_readme(c, paths))
    (root / "SOURCES.md").write_text(sources_md(c))
    (root / "course.json").write_text(c.model_dump_json(indent=2))
    (root / ".learn").mkdir()
    (root / ".learn" / "lessons.json").write_text(json.dumps(order, indent=2))
    shutil.copy(Path(__file__).with_name("learn_cli.py"), root / "learn.py")
    return root


def load(root: Path) -> Course:
    return Course.model_validate_json((Path(root) / "course.json").read_text())

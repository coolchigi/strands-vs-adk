"""Everything about a stage's output that can be checked without a model.

The feedback agent runs these first. A stage that fails one goes back with the reason,
and never costs a reviewer's time.
"""

from __future__ import annotations

import re

from . import exercises
from .model import (
    Course, Curriculum, Evidence, KnowledgeBase, Lesson, Level, Problem, Stage, Tier,
)
from .web import quote_on_page

HIGHER_ORDER = {Level.APPLY, Level.ANALYZE, Level.EVALUATE, Level.CREATE}
# [c:ID], or several at once: [c:ID, c:ID]. The teacher writes both
CITATION = re.compile(r"\[(c:[0-9a-f]{12}(?:\s*,\s*c:[0-9a-f]{12})*)\]")


MALFORMED_CITATION = re.compile(r"\[c:[^\]]*\]")  # after the good ones are taken out


def cited(text: str) -> list[str]:
    """Every claim id a text cites, in order."""
    return [i.strip()[2:] for group in CITATION.findall(text) for i in group.split(",")]
# "option 2", "(b)", "choice C": the model counts from 0, learn.py shows options from 1
OPTION_BY_POSITION = re.compile(r"\b(?:option|choice|answer)\s*\(?[0-9a-d]\)?(?![\w.])", re.I)
VAGUE_VERBS = ("understand", "know", "learn", "be familiar", "appreciate", "be aware")


# -- research ---------------------------------------------------------------------

def research(kb: KnowledgeBase, version_problem: str | None = None) -> list[Problem]:
    out: list[Problem] = []

    def add(check: str, detail: str) -> None:
        out.append(Problem(stage=Stage.RESEARCH, check=check, detail=detail))

    spec = kb.spec
    if not spec.objectives:
        add("no_objectives", "research produced no objectives to teach")
    if version_problem:
        add("version_unverified", version_problem)

    by_url = {s.url: s for s in kb.sources}
    ids = {o.id for o in spec.objectives}
    for o in spec.objectives:
        if o.parent_id and o.parent_id not in ids:
            add("orphan_objective", f"objective {o.id} names a parent {o.parent_id} that doesn't exist")
        if spec.kind == "exam_guide":
            # every objective of an exam must be the guide's own words
            src = by_url.get(o.source_url)
            if src is None or not quote_on_page(o.quote, src.content):
                add("objective_not_in_guide",
                    f"objective {o.id} ({o.statement!r}) isn't backed by a quote from the exam guide")

    # what someone does routinely at work has to be taught, and by one specific objective.
    # An exam guide sets its own scope, so its practice list is only background
    if spec.kind != "exam_guide":
        leaves = {o.id for o in spec.leaves()}
        for p in spec.practice:
            if not p.objective_id:
                add("practice_not_covered", f"no objective teaches this routine practice: {p.task!r}")
            elif p.objective_id not in ids:
                add("practice_not_covered", f"{p.task!r} is taught by objective {p.objective_id}, which doesn't exist")
            elif p.objective_id not in leaves:
                add("practice_not_covered", f"{p.task!r} is taught by objective {p.objective_id}, which is a whole "
                    "area. Name the objective under it that teaches this, or add one")

    sources = {s.id: s for s in kb.sources}
    for c in kb.claims:
        src = sources.get(c.source_id)
        if src is None:
            add("claim_source_missing", f"claim {c.id} names a source we don't have")
        elif not quote_on_page(c.quote, src.content):
            add("quote_not_on_page", f"claim {c.id} quotes {src.url} saying something it doesn't say")
        unknown = [i for i in c.objective_ids if i not in ids]
        if unknown:
            add("claim_unknown_objective", f"claim {c.id} serves objectives that don't exist: {unknown}")

    for oid, n in kb.coverage().items():
        if n == 0:
            add("objective_without_evidence", f"objective {oid} has no claims behind it")

    community_only = [oid for oid in kb.coverage()
                      if kb.claims_for(oid) and all(sources.get(c.source_id) and
                                                    sources[c.source_id].tier is Tier.COMMUNITY
                                                    for c in kb.claims_for(oid))]
    for oid in community_only:
        add("community_only", f"objective {oid} rests only on community sources")
    return out


# -- curriculum ---------------------------------------------------------------------

def curriculum(cur: Curriculum, kb: KnowledgeBase) -> list[Problem]:
    out: list[Problem] = []

    def add(check: str, detail: str, lesson_id: str | None = None) -> None:
        out.append(Problem(stage=Stage.CURRICULUM, check=check, detail=detail, lesson_id=lesson_id))

    lessons = cur.lessons()
    if not lessons:
        add("empty", "the curriculum has no lessons")
        return out

    objective_ids = {o.id for o in kb.spec.objectives}
    claim_ids = {c.id for c in kb.claims}
    seen: set[str] = set()
    covered: set[str] = set()
    all_ids = [l.id for l in lessons]
    if len(set(all_ids)) != len(all_ids):
        add("duplicate_lesson_id", "two lessons share an id")

    for unit in cur.units:
        if not unit.lessons:
            add("empty_unit", f"unit {unit.id} has no lessons")
        if not unit.project.strip():
            add("no_project", f"unit {unit.id} ends without an unguided project")
        for l in unit.lessons:
            if not l.objectives:
                add("no_objectives", f"{l.id} has no objectives", l.id)
            for o in l.objectives:
                statement = o.statement.lower()
                if statement.startswith(VAGUE_VERBS) or " understand " in f" {statement} ":
                    add("unmeasurable_objective",
                        f"{l.id}: {o.statement!r} can't be checked. Use a verb a learner can be seen doing.",
                        l.id)
                if not o.covers:
                    add("objective_serves_nothing", f"{l.id}: {o.statement!r} covers no spec objective", l.id)
                bad = [i for i in o.covers if i not in objective_ids]
                if bad:
                    add("unknown_objective", f"{l.id} covers objectives that don't exist: {bad}", l.id)
                covered.update(o.covers)
                if o.level in HIGHER_ORDER and o.evidence is Evidence.QUIZ:
                    add("misaligned_evidence",
                        f"{l.id}: {o.statement!r} asks the learner to {o.level.value}, "
                        "and a quiz can't show that. It needs an exercise.", l.id)
            for p in l.prerequisites:
                if p not in all_ids:
                    add("unknown_prerequisite", f"{l.id} depends on {p}, which doesn't exist", l.id)
                elif p not in seen:
                    add("prerequisite_after_use", f"{l.id} depends on {p}, which comes later", l.id)
            for r in l.reviews:
                if r not in seen:
                    add("review_of_later_lesson", f"{l.id} reviews {r}, which hasn't happened yet", l.id)
            unknown = [c for c in l.claim_ids if c not in claim_ids]
            if unknown:
                add("unknown_claim", f"{l.id} teaches from claims we don't have: {unknown}", l.id)
            if not l.claim_ids:
                add("lesson_without_claims", f"{l.id} has no claims to teach from", l.id)
            seen.add(l.id)

    leaves = {o.id for o in kb.spec.leaves()}
    parents_covered = {o.parent_id for o in kb.spec.objectives if o.id in covered}
    missing = sorted(leaves - covered - parents_covered)
    if missing:
        add("objectives_not_taught", f"no lesson covers objectives {missing}")
    return out


# -- lessons --------------------------------------------------------------------------

def lesson(l: Lesson, spec_claims: list[str], all_claims: set[str],
           needs_exercise: bool, run_exercise: bool = True) -> list[Problem]:
    out: list[Problem] = []

    def add(check: str, detail: str) -> None:
        out.append(Problem(stage=Stage.TEACHING, check=check, detail=detail, lesson_id=l.id))

    cited_here = set(cited(l.explanation))
    if not cited_here:
        add("no_citations", "the explanation cites no claims, so nothing in it is traceable")
    bad = MALFORMED_CITATION.findall(CITATION.sub("", l.explanation + l.worked_example))
    if bad:
        add("malformed_citation", f"these citations aren't [c:ID] with a 12 character id: {bad}")
    unknown = sorted(cited_here - all_claims)
    if unknown:
        add("unknown_citation", f"the explanation cites claims that don't exist: {unknown}")
    if not l.worked_example.strip():
        add("no_worked_example", "there's no worked example")

    if needs_exercise and l.exercise is None:
        add("no_exercise", "an objective here needs an exercise, and the lesson has none")
    if l.exercise is not None:
        if not l.exercise.task.strip():
            add("no_task", "the exercise doesn't say what to do")
        if not l.exercise.starter:
            add("no_starter", "the exercise gives the learner nothing to start from")
        if not l.exercise.hints:
            add("no_hints", "the exercise has no hints for a learner who is stuck")
        for p in exercises.stale_pins(l.exercise.solution + l.exercise.starter):
            add("provider_out_of_date", p)
        if run_exercise:
            for p in exercises.verify(l.exercise):
                add("exercise_does_not_work", p)

    if not l.quiz:
        add("no_quiz", "the lesson has no questions")
    for i, q in enumerate(l.quiz, 1):
        if not 3 <= len(q.options) <= 4:
            add("quiz_options", f"question {i} has {len(q.options)} options. Use 3 or 4.")
        if not 0 <= q.answer < len(q.options):
            add("quiz_answer", f"question {i} points at an answer that isn't one of its options")
        if len(set(o.strip().lower() for o in q.options)) != len(q.options):
            add("quiz_duplicate_option", f"question {i} repeats an option")
        if any(o.strip().lower() in ("all of the above", "none of the above") for o in q.options):
            add("quiz_all_or_none", f"question {i} uses all or none of the above")
        if not q.explanation.strip():
            add("quiz_no_explanation", f"question {i} doesn't explain its answer")
        if found := OPTION_BY_POSITION.search(q.explanation):
            add("quiz_option_by_position", f"question {i}'s explanation names an option by its position "
                f"(\"{found.group(0)}\"), and learn.py numbers options from 1. Name it by what it says.")
    return out


def course(c: Course, run_exercises: bool = True) -> list[Problem]:
    """The whole course, as the judge sees it."""
    specs = {l.id: l for l in c.curriculum.lessons()}
    all_claims = {x.id for x in c.knowledge.claims}
    out = research(c.knowledge) + curriculum(c.curriculum, c.knowledge)
    for l in c.lessons:
        spec = specs.get(l.id)
        needs = bool(spec and any(o.evidence is Evidence.EXERCISE for o in spec.objectives))
        out += lesson(l, spec.claim_ids if spec else [], all_claims, needs, run_exercises)
    missing = [i for i in specs if i not in {l.id for l in c.lessons}]
    if missing:
        out.append(Problem(stage=Stage.TEACHING, check="lessons_not_written",
                           detail=f"the curriculum plans lessons nobody wrote: {missing}"))
    return out

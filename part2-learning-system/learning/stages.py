"""The stages, written once. Each framework supplies a Brain and wires these into its graph.

A Brain asks an agent for a typed answer, with or without research tools. That's where the
frameworks differ: how an agent is built, how it reaches search and MCP servers, how
structured output comes back. The work around each call, fetching pages, checking quotes,
running exercises, is the same on both sides and lives here.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Protocol, TypeVar

from pydantic import BaseModel, Field, TypeAdapter

from . import checks, exercises, prompts
from .model import (
    Claim, Course, CourseFile, Curriculum, Dropped, Evidence, KnowledgeBase, LearnerProfile, Lesson,
    LessonSpec, Objective, Practice, Problem, Source, Spec, Stage, SubjectKind, Tier, normalise, short_id,
)
from .web import Web, check_version, host_of, quote_on_page, under

log = logging.getLogger("learning")
T = TypeVar("T", bound=BaseModel)

PAGE_CHARS = 40_000        # what an agent reads of one page. quotes are checked against all of it
PAGES_PER_AREA = 4
SPEC_PAGES = 20          # what defines the scope. A discipline spans several projects' docs
LESSON_ATTEMPTS = 3

Say = Callable[[str], None]  # one plain-language progress line, for the learner watching


def quiet(_: str) -> None:
    return None


class Brain(Protocol):
    def ask(self, name: str, instruction: str, prompt: str, schema: type[T], research: bool = False) -> T:
        """One agent call, returning `schema`. With research=True the agent can search and read."""


# -- what agents return ------------------------------------------------------------------

class SpecDraft(BaseModel):
    kind: str = Field(description="exam_guide or derived_from_docs")
    title: str = Field(description="What the course is about, e.g. 'Terraform' or an exam's full name")
    official_domains: list[str] = Field(description="Domains the maker owns, e.g. hashicorp.com")
    urls: list[str] = Field(description="The pages that define the scope, which you read")
    version: str | None = None
    version_url: str | None = None
    version_quote: str | None = None


class Cover(BaseModel):
    practice: str = Field(description="The practice item, word for word")
    objective_id: str = Field(description="The id of the objective that teaches all of it")


class ObjectiveTree(BaseModel):
    practice: list[str] = Field(default_factory=list, description=(
        "Written first: 10 to 20 things someone who uses this at work does routinely, "
        "each one short and concrete"))
    objectives: list[Objective]
    coverage: list[Cover] = Field(default_factory=list, description=(
        "Written last: for each practice item, the objective that teaches it"))


def covered(practice: list[Practice], coverage: list[Cover]) -> list[Practice]:
    """Each practice item with the objective the model says teaches it. An item the model
    didn't name, or named in other words, keeps what it had, and the checks flag it if that's nothing."""
    by_task = {normalise(c.practice): c.objective_id.strip() for c in coverage}
    return [p.model_copy(update={"objective_id": by_task.get(normalise(p.task)) or p.objective_id})
            for p in practice]


class Picks(BaseModel):
    urls: list[str]


class ClaimDraft(BaseModel):
    text: str
    quote: str
    objective_ids: list[str]


class ClaimDrafts(BaseModel):
    claims: list[ClaimDraft] = Field(default_factory=list)


class Finding(BaseModel):
    stage: Stage
    detail: str
    lesson_id: str | None = None


class Review(BaseModel):
    findings: list[Finding] = Field(default_factory=list)


def _feedback(reasons: list[str] | None) -> str:
    return ("\n\nThe last attempt was sent back. Fix this:\n" + "\n".join(f"- {r}" for r in reasons)) if reasons else ""


# -- intake ------------------------------------------------------------------------------

def intake(brain: Brain, conversation: str) -> LearnerProfile:
    return brain.ask("intake", prompts.INTAKE, conversation, LearnerProfile)


# -- research ------------------------------------------------------------------------------

@dataclass
class ResearchResult:
    knowledge: KnowledgeBase
    version_problem: str | None = None


def version_problem(web: Web, profile: LearnerProfile, draft: SpecDraft) -> str | None:
    """A tool, a language or an exam has a version, and a course that doesn't say which is
    teaching whatever the model remembers. A concept may not have one."""
    if not (draft.version or "").strip() and profile.kind is not SubjectKind.CONCEPT:
        return f"no version given: a {profile.kind.value} course needs the version it teaches, from an official page"
    return check_version(web, draft.version, draft.version_url, draft.version_quote, draft.official_domains)


def find_spec(brain: Brain, web: Web, profile: LearnerProfile, reasons: list[str] | None) -> tuple[SpecDraft, str | None]:
    draft = brain.ask("spec", prompts.FIND_SPEC, profile.brief() + _feedback(reasons), SpecDraft, research=True)
    problem = version_problem(web, profile, draft)
    if problem:
        # a version from memory is caught before a single page is read, with one more go
        log.info("version not verified, asking again: %s", problem)
        draft = brain.ask("spec", prompts.FIND_SPEC,
                          profile.brief() + _feedback((reasons or []) + [problem]), SpecDraft, research=True)
        problem = version_problem(web, profile, draft)
    log.info("spec: %s, version %s (%s), %d pages", draft.kind, draft.version,
             "verified" if not problem else problem, len(draft.urls))
    return draft, problem


def _fetch(web: Web, url: str, official: list[str], dropped: list[Dropped]) -> Source | None:
    page = web.get(url)
    if not page.ok:
        dropped.append(Dropped(url=url, reason=f"fetch returned {page.status}"))
        return None
    tier = Tier.OFFICIAL if under(host_of(page.url), official) else Tier.COMMUNITY
    return Source.build(url=page.url, title="", content=page.text, tier=tier)


def research(brain: Brain, web: Web, profile: LearnerProfile, reasons: list[str] | None = None,
             say: Say = quiet) -> ResearchResult:
    say(f"Looking for the official {profile.subject} documentation")
    draft, version_problem = find_spec(brain, web, profile, reasons)
    say(f"✓ Found it: {draft.title}" + (f", version {draft.version}" if draft.version and not version_problem else ""))
    dropped: list[Dropped] = []
    sources: dict[str, Source] = {}

    spec_pages = [s for s in (_fetch(web, u, draft.official_domains, dropped) for u in draft.urls[:SPEC_PAGES]) if s]
    for s in spec_pages:
        sources[s.id] = s
    reading = "\n\n".join(f"=== {s.url}\n{s.content[:PAGE_CHARS]}" for s in spec_pages)
    tree = brain.ask("objectives", prompts.OBJECTIVES,
                     f"{profile.brief()}\nScope: {draft.kind}\n\n{reading}" + _feedback(reasons), ObjectiveTree)

    # objectives quote the pages they come from. a quote that isn't there is dropped, and
    # for an exam guide the objective goes with it
    page_by_url = {s.url: s for s in spec_pages}
    objectives: list[Objective] = []
    for o in tree.objectives:
        page = page_by_url.get(o.source_url) or next(
            (s for s in spec_pages if o.quote and quote_on_page(o.quote, s.content)), None)
        if page and o.quote and quote_on_page(o.quote, page.content):
            objectives.append(o.model_copy(update={"source_url": page.url}))
        elif draft.kind == "exam_guide":
            dropped.append(Dropped(url=o.source_url, quote=o.quote, reason=f"objective {o.id} quote not in guide"))
        else:
            objectives.append(o.model_copy(update={"quote": "", "source_url": ""}))
    spec = Spec(kind=draft.kind, title=draft.title, urls=[s.url for s in spec_pages],
                version=draft.version, version_url=draft.version_url, version_quote=draft.version_quote,
                objectives=objectives, practice=covered([Practice(task=t) for t in tree.practice], tree.coverage))
    log.info("objectives: %d (%d leaves)", len(objectives), len(spec.leaves()))
    say(f"✓ Worked out {len(spec.leaves())} things you'll need to be able to do")

    claims: dict[str, Claim] = {}
    for top in [o for o in objectives if not o.parent_id]:
        group = [top] + [o for o in objectives if o.parent_id == top.id or (o.parent_id or "").startswith(top.id + ".")]
        say(f"Reading up on: {top.statement}")
        gather(brain, web, profile, spec, draft.official_domains, group, sources, claims, dropped)

    say(f"✓ Checked {len(claims)} facts, word for word, against {len(sources)} official pages")
    kb = KnowledgeBase(profile=profile, spec=spec, sources=list(sources.values()),
                       claims=list(claims.values()), dropped=dropped)
    return ResearchResult(knowledge=kb, version_problem=version_problem)


def gather(brain: Brain, web: Web, profile: LearnerProfile, spec: Spec, official: list[str],
           group: list[Objective], sources: dict[str, Source], claims: dict[str, Claim],
           dropped: list[Dropped], gaps: list[str] | None = None, pages: int = PAGES_PER_AREA) -> None:
    """Pick pages for some objectives, read them, and keep the claims whose quotes are on them."""
    listing = "\n".join(f"{o.id}  {o.statement}" for o in group)
    ask = f"{profile.brief()}\nVersion: {spec.version or 'current'}\n\nObjectives:\n{listing}"
    if gaps:
        ask += "\n\nA reviewer found these gaps. Find pages that fill them:\n" + "\n".join(f"- {g}" for g in gaps)
    picks = brain.ask("evidence", prompts.FIND_EVIDENCE.format(max_pages=pages), ask, Picks, research=True)
    ids = {o.id for o in group}
    for url in picks.urls[:pages]:
        source = sources.get(short_id(url)) or _fetch(web, url, official, dropped)
        if source is None:
            continue
        sources[source.id] = source
        found = brain.ask("extract", prompts.EXTRACT,
                          f"Objectives:\n{listing}\n\nPage: {source.url}\n\n{source.content[:PAGE_CHARS]}",
                          ClaimDrafts)
        kept = 0
        for c in found.claims:
            if quote_on_page(c.quote, source.content):
                cid = short_id(source.id, c.quote)
                serves = [i for i in c.objective_ids if i in ids]
                if cid in claims:
                    claims[cid].objective_ids = sorted(set(claims[cid].objective_ids) | set(serves))
                else:
                    claims[cid] = Claim(id=cid, text=c.text, quote=c.quote, source_id=source.id, objective_ids=serves)
                kept += 1
            else:
                dropped.append(Dropped(url=source.url, quote=c.quote, reason="quote is not on the page"))
        log.info("  %s: %d claims kept, %d dropped", source.url, kept, len(found.claims) - kept)


def revise_research(brain: Brain, web: Web, kb: KnowledgeBase, gaps: list[str], say: Say = quiet) -> ResearchResult:
    """Fill the gaps a review found, keeping everything already verified.

    Starting again from nothing threw away hundreds of checked claims to fix a handful of
    gaps, and cost as much as the first pass. The spec and its objectives stay, with any
    the review showed were missing added. The version was verified the first time.
    """
    # a gap can be something the learner must be able to do that no objective covers, like
    # a routine practice the tree left out. Evidence alone can't fill that, so objectives
    # come first. An exam guide sets its own objectives, so it gets none added
    spec = kb.spec
    if spec.kind != "exam_guide":
        added = brain.ask("objectives", prompts.ADD_OBJECTIVES,
                          f"{kb.profile.brief()}\n\nThe objective tree:\n{tree_listing(kb)}\n\n"
                          "The reviewer's gaps:\n" + "\n".join(f"- {g}" for g in gaps), ObjectiveTree)
        ids = {o.id for o in spec.objectives}
        new = [o.model_copy(update={"quote": "", "source_url": ""}) for o in added.objectives if o.id not in ids]
        # the practice items those gaps were about now name the objective that teaches them
        spec = spec.model_copy(update={"objectives": spec.objectives + new,
                                       "practice": covered(spec.practice, added.coverage)})
        if new:
            log.info("research revised: %d new objectives: %s", len(new), [o.statement for o in new])
            say(f"✓ Added {len(new)} thing{'s' if len(new) != 1 else ''} to learn that the research had left out")
    official = sorted({host_of(s.url) for s in kb.sources if s.tier is Tier.OFFICIAL})
    sources = {s.id: s for s in kb.sources}
    claims = {c.id: c.model_copy() for c in kb.claims}
    dropped = list(kb.dropped)
    before = len(claims)
    gather(brain, web, kb.profile, spec, official, spec.objectives, sources, claims, dropped,
           gaps=gaps, pages=PAGES_PER_AREA * 2)
    log.info("research revised: %d new claims, %d in all", len(claims) - before, len(claims))
    say(f"✓ Added {len(claims) - before} facts to fill the gaps, {len(claims)} in all")
    revised = kb.model_copy(update={"spec": spec, "sources": list(sources.values()),
                                    "claims": list(claims.values()), "dropped": dropped})
    return ResearchResult(knowledge=revised)


# -- curriculum ------------------------------------------------------------------------------

def claim_listing(kb: KnowledgeBase) -> str:
    tiers = {s.id: s.tier.value for s in kb.sources}
    return "\n".join(f"{c.id} [{tiers.get(c.source_id, '?')}] ({','.join(c.objective_ids)}) {c.text}"
                     for c in kb.claims)


def tree_listing(kb: KnowledgeBase) -> str:
    tree = "\n".join(f"{o.id}{f' ({o.weight:g}%)' if o.weight else ''}  {o.statement}" for o in kb.spec.objectives)
    if kb.spec.practice:
        tree += "\n\nWhat someone who uses this at work does routinely, and the objective that teaches it:\n" + "\n".join(
            f"- {p.task} (taught by {p.objective_id})" if p.objective_id else f"- {p.task} (no objective teaches this)"
            for p in kb.spec.practice)
    return tree


def curriculum(brain: Brain, kb: KnowledgeBase, reasons: list[str] | None = None) -> Curriculum:
    prompt = (f"Learner:\n{kb.profile.brief()}\n\nVersion: {kb.spec.version or 'current'}\n\n"
              f"Objective tree ({kb.spec.kind}):\n{tree_listing(kb)}\n\nClaims:\n{claim_listing(kb)}")
    return brain.ask("curriculum", prompts.CURRICULUM, prompt + _feedback(reasons), Curriculum)


# -- teaching ------------------------------------------------------------------------------

def files_text(files: list[CourseFile]) -> str:
    return "\n\n".join(f"--- {f.path} ---\n{f.content}" for f in files) or "(none yet)"


def write_lesson(brain: Brain, kb: KnowledgeBase, spec: LessonSpec, previous: list[CourseFile],
                 facts: list[str], reasons: list[str] | None = None) -> Lesson:
    by_id = {c.id: c for c in kb.claims}
    claims = "\n".join(f"{cid}: {by_id[cid].text}\n    quote: \"{by_id[cid].quote}\""
                       for cid in spec.claim_ids if cid in by_id)
    objectives = "\n".join(f"- {o.statement} ({o.level.value}, proved by {o.evidence.value})" for o in spec.objectives)
    prompt = (f"Learner:\n{kb.profile.brief()}\n\nVersion: {kb.spec.version or 'current'}\n\n"
              f"Lesson {spec.id}: {spec.title}\nObjectives:\n{objectives}\n"
              f"Exercise idea: {spec.exercise_idea or '(none)'}\n\n"
              f"The previous lesson's finished files:\n{files_text(previous)}\n\n"
              f"Claims you may teach from:\n{claims}")
    if facts:
        prompt += "\n\nAlready checked against the real world:\n" + "\n".join(f"- {f}" for f in facts)
    lesson = brain.ask("lesson", prompts.LESSON, prompt + _feedback(reasons), Lesson)
    return lesson.model_copy(update={"id": spec.id, "title": spec.title,
                                     "exercise": exercises.without_generated(lesson.exercise)})


@dataclass
class LessonResult:
    lesson: Lesson
    problems: list[Problem] = field(default_factory=list)
    attempts: int = 0


def teach_lesson(brain: Brain, kb: KnowledgeBase, spec: LessonSpec, previous: list[CourseFile],
                 facts: list[str], reviewer: bool = True, say: Say = quiet) -> LessonResult:
    """Write, check, and rewrite with the reasons until it passes or attempts run out.

    Mechanical checks first, including running the exercise. Only a lesson that passes
    them is worth a reviewer's time.
    """
    needs = any(o.evidence is Evidence.EXERCISE for o in spec.objectives)
    all_claims = {c.id for c in kb.claims}
    reasons: list[str] | None = None
    result = None
    for attempt in range(1, LESSON_ATTEMPTS + 1):
        lesson = write_lesson(brain, kb, spec, previous, facts, reasons)
        problems = checks.lesson(lesson, spec.claim_ids, all_claims, needs)
        for p in problems:
            if p.check == "provider_out_of_date" and p.detail not in facts:
                facts.append(p.detail)  # true for every lesson after this one too
        if not problems and reviewer:
            review = brain.ask("review_lesson", prompts.REVIEW_LESSON, lesson.model_dump_json(indent=1), Review)
            problems = [Problem(stage=Stage.TEACHING, check="review", detail=f.detail, lesson_id=spec.id)
                        for f in review.findings]
        result = LessonResult(lesson=lesson, problems=problems, attempts=attempt)
        log.info("%s attempt %d: %s", spec.id, attempt,
                 "passed" if not problems else "; ".join(p.check for p in problems))
        for p in problems:
            log.info("  %s %s: %s", spec.id, p.check, " ".join(p.detail.split())[:400])
        if not problems:
            break
        reasons = [p.detail for p in problems]
        if attempt < LESSON_ATTEMPTS:
            say(f"    it didn't pass its checks yet, rewriting (try {attempt + 1} of {LESSON_ATTEMPTS})")
    return result


# -- keeping the run --------------------------------------------------------------------------

_PROBLEMS = TypeAdapter(dict[str, list[Problem]])


class Checkpoint:
    """The run survives a crash. Each stage's output is saved as soon as it passes."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        (self.root / "lessons").mkdir(parents=True, exist_ok=True)

    def load(self, name: str, schema: type[T]) -> T | None:
        p = self.root / f"{name}.json"
        return schema.model_validate_json(p.read_text()) if p.exists() else None

    def save(self, name: str, value: BaseModel) -> None:
        (self.root / f"{name}.json").write_text(value.model_dump_json(indent=1))

    def load_problems(self) -> dict[str, list[Problem]]:
        p = self.root / "problems.json"
        return _PROBLEMS.validate_json(p.read_text()) if p.exists() else {}

    def save_problems(self, problems: dict[str, list[Problem]]) -> None:
        (self.root / "problems.json").write_bytes(_PROBLEMS.dump_json(problems, indent=1))

    def log(self, event: dict) -> None:
        with (self.root / "events.jsonl").open("a") as f:
            f.write(json.dumps(event) + "\n")


def assemble(kb: KnowledgeBase, cur: Curriculum, lessons: list[Lesson],
             problems: list[Problem] | None = None) -> Course:
    return Course(profile=kb.profile, knowledge=kb, curriculum=cur, lessons=lessons, problems=problems or [])

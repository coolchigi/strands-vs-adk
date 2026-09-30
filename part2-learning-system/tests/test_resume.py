"""What a run keeps when it stops and starts again, and what a teacher's files may contain."""

from __future__ import annotations

import pytest

from learning import flow as flows
from learning import stages
from learning.model import (
    CourseFile, Exercise, KnowledgeBase, LearnerProfile, Lesson, LessonSpec, Problem, Spec, Stage, SubjectKind,
)
from learning.web import FakeWeb


class Brain:
    """Answers with what it's given, and remembers every question."""

    def __init__(self, answer=None):
        self.answer, self.asked = answer, []

    def ask(self, name, instruction, prompt, schema, research=False):
        self.asked.append(name)
        if self.answer is None:
            raise AssertionError(f"{name} was asked, and nothing should have been")
        return self.answer


PROFILE = LearnerProfile(subject="Terraform", goal="build things", subject_is_clear=True)
KB = KnowledgeBase(profile=PROFILE, spec=Spec(kind="derived_from_docs", title="Terraform", version="1.16.4"))
LEFT_OVER = Problem(stage=Stage.RESEARCH, check="review", detail="no claim covers terraform destroy")


def test_a_resumed_run_does_not_review_again_what_it_already_sent_forward(tmp_path):
    # a stage is saved only when its review sent the run on. Reviewing it again on resume
    # once threw away half an hour of research over a finding it had already moved past.
    first = flows.start(Brain(), FakeWeb(), PROFILE, tmp_path)
    first.checkpoint.save("knowledge", KB)
    first.checkpoint.save_problems({"research": [LEFT_OVER]})

    again = flows.start(Brain(), FakeWeb(), PROFILE, tmp_path)
    again.research()
    assert again.review_research() == flows.CURRICULUM
    assert again.brain.asked == []
    assert flows.open_problems(again.board) == [LEFT_OVER]


def test_what_a_run_went_forward_with_reaches_the_course(tmp_path):
    f = flows.start(Brain(), FakeWeb(), PROFILE, tmp_path)
    f.checkpoint.save_problems({"research": [LEFT_OVER]})
    f = flows.start(Brain(), FakeWeb(), PROFILE, tmp_path)
    f.board.knowledge = KB
    f.board.curriculum = stages.Curriculum(title="Terraform", units=[])
    assert f.course().problems == [LEFT_OVER]


def test_files_terraform_generates_never_reach_the_learner():
    # a made-up lock file broke `terraform init` for one lesson and every lesson built on it
    lock = CourseFile(path=".terraform.lock.hcl", content='provider "registry.terraform.io/hashicorp/aws" {}')
    main = CourseFile(path="main.tf", content="# TODO")
    written = Lesson(id="x", title="x", explanation="", worked_example="",
                     exercise=Exercise(task="t", starter=[main, lock], solution=[main, lock],
                                       checks=[CourseFile(path="tests/a.tftest.hcl", content="")],
                                       hints=["h"]))
    lesson = stages.write_lesson(Brain(written), KB, LessonSpec(id="u1-l1", title="First"), [], [])
    paths = [f.path for f in lesson.exercise.starter + lesson.exercise.solution]
    assert paths == ["main.tf", "main.tf"]


@pytest.mark.parametrize("kind, version, wanted", [
    (SubjectKind.TOOL, None, "needs the version"),
    (SubjectKind.CERTIFICATION, "", "needs the version"),
    (SubjectKind.CONCEPT, None, None),
])
def test_a_tool_course_without_a_version_is_not_verified(kind, version, wanted):
    draft = stages.SpecDraft(kind="derived_from_docs", title="x", official_domains=["hashicorp.com"],
                             urls=[], version=version)
    found = stages.version_problem(FakeWeb(), PROFILE.model_copy(update={"kind": kind}), draft)
    assert (found is None) if wanted is None else (wanted in found)


class Researcher:
    """Picks one page and finds one claim on it. Records who was asked."""

    def __init__(self, url, quote, adds=(), coverage=()):
        self.url, self.quote, self.asked, self.adds, self.coverage = url, quote, [], list(adds), list(coverage)

    def ask(self, name, instruction, prompt, schema, research=False):
        self.asked.append(name)
        if name == "evidence":
            return stages.Picks(urls=[self.url])
        if name == "extract":
            return stages.ClaimDrafts(claims=[stages.ClaimDraft(text="destroy removes it", quote=self.quote,
                                                                objective_ids=["1"])])
        if name == "objectives":
            return stages.ObjectiveTree(objectives=self.adds, coverage=self.coverage)
        raise AssertionError(f"{name} was asked during a revision")


def test_a_gap_a_reviewer_found_is_filled_without_throwing_away_what_was_verified(tmp_path):
    # going back to research once deleted 306 verified claims to fill a few gaps, and
    # spent a whole first pass again doing it
    from learning.model import Claim, Objective, Source, Tier
    home = Source.build("https://developer.hashicorp.com/terraform/cli", "CLI", "terraform plan shows changes", Tier.OFFICIAL)
    kept = Claim(id="a" * 12, text="plan shows changes", quote="terraform plan shows changes",
                 source_id=home.id, objective_ids=["1"])
    kb = KB.model_copy(update={"spec": KB.spec.model_copy(update={"objectives": [Objective(id="1", statement="run the workflow")]}),
                               "sources": [home], "claims": [kept]})
    destroy = "https://developer.hashicorp.com/terraform/cli/commands/destroy"
    brain = Researcher(destroy, "terraform destroy command destroys all remote objects")
    f = flows.start(brain, FakeWeb(pages={destroy: "The terraform destroy command destroys all remote objects"}),
                    PROFILE, tmp_path)
    f.checkpoint.save("knowledge", kb)
    f.board.reasons = ["no claim covers terraform destroy"]
    f.research()
    assert "spec" not in brain.asked
    texts = sorted(c.text for c in f.board.knowledge.claims)
    assert texts == ["destroy removes it", "plan shows changes"]


def test_a_revision_adds_what_the_learner_must_do_that_no_objective_covered(tmp_path):
    # a Terraform run listed "pin registry module versions" as routine practice, and no
    # objective covered it. Filling evidence alone could never fix that
    from learning import checks
    from learning.model import Objective, Practice
    task = "Pin a shared module's version in every configuration that uses it"
    kb = KB.model_copy(update={"spec": KB.spec.model_copy(update={
        "objectives": [Objective(id="1", statement="write modules")], "practice": [Practice(task=task)]})})
    destroy = "https://developer.hashicorp.com/terraform/language/modules/sources"
    pin = Objective(id="1.1", parent_id="1", statement="Pin a shared module to a version with ?ref= or version")
    again = Objective(id="1", statement="write modules")
    brain = Researcher(destroy, "Terraform installs modules from", adds=[pin, again],
                       coverage=[stages.Cover(practice=task, objective_id="1.1")])
    f = flows.start(brain, FakeWeb(pages={destroy: "Terraform installs modules from a Git repository"}),
                    PROFILE, tmp_path)
    f.checkpoint.save("knowledge", kb)
    f.board.reasons = ["no objective teaches this routine practice: " + repr(task)]
    f.research()
    spec = f.board.knowledge.spec
    assert [o.statement for o in spec.objectives] == ["write modules", "Pin a shared module to a version with ?ref= or version"]
    # and the practice item now names it, so the check that sent it back is satisfied
    assert spec.practice == [Practice(task=task, objective_id="1.1")]
    assert "practice_not_covered" not in [p.check for p in checks.research(f.board.knowledge)]


def test_the_research_reviewer_sees_which_objective_teaches_each_routine_practice():
    # both Terraform courses left out pinning a shared module's version, which teams do all
    # the time. A check can only see that an objective was named. Whether it teaches the
    # whole item is the reviewer's call, so the reviewer has to see the pairing
    from learning.model import Practice
    kb = KB.model_copy(update={"spec": KB.spec.model_copy(update={"practice": [
        Practice(task="Pin provider and module versions", objective_id="2.1"),
        Practice(task="Commit the lock file")]})})
    listing = stages.tree_listing(kb)
    assert "Pin provider and module versions (taught by 2.1)" in listing
    assert "Commit the lock file (no objective teaches this)" in listing


class Reviewer:
    """Finds one thing, and keeps what it was shown."""

    def __init__(self):
        self.asked, self.prompts = [], []

    def ask(self, name, instruction, prompt, schema, research=False):
        self.asked.append(name)
        self.prompts.append(prompt)
        return stages.Review(findings=[stages.Finding(stage=Stage.RESEARCH, detail="2.1 teaches provider pins only")])


def test_the_research_reviewer_runs_even_when_a_mechanical_check_fails(tmp_path):
    # a run had one objective with no evidence. The reviewer only ran once the checks passed,
    # so it never saw the practice list, and all 3 attempts went on that one objective
    from learning.model import Objective
    kb = KB.model_copy(update={"spec": KB.spec.model_copy(update={"objectives": [
        Objective(id="1", statement="target a directory with -chdir")]})})
    f = flows.start(Reviewer(), FakeWeb(), PROFILE, tmp_path)
    f.board.knowledge = kb
    assert f.review_research() == flows.RESEARCH
    assert f.brain.asked == ["review_research"]
    assert sorted(p.check for p in f.board.problems["research"]) == ["objective_without_evidence", "review"]
    # told what the checks found, so it doesn't spend its findings repeating them
    assert "objective 1 has no claims behind it" in f.brain.prompts[0]


def test_the_objectives_step_says_which_objective_teaches_each_routine_practice(tmp_path):
    from learning import checks
    from learning.model import Objective
    docs = "https://developer.hashicorp.com/terraform/language/modules"
    pin, plan = "Pin a shared module's version", "Review a plan before applying it"

    class Researcher:
        def ask(self, name, instruction, prompt, schema, research=False):
            if name == "spec":
                return stages.SpecDraft(kind="derived_from_docs", title="Terraform",
                                        official_domains=["hashicorp.com"], urls=[docs])
            if name == "objectives":
                # the model copies the item back in its own typography, which still matches
                return stages.ObjectiveTree(
                    practice=[pin, plan],
                    objectives=[Objective(id="1", statement="use modules"),
                                Objective(id="1.1", parent_id="1", statement="pin a module's version")],
                    coverage=[stages.Cover(practice="pin a shared module’s version", objective_id="1.1")])
            if name == "evidence":
                return stages.Picks(urls=[])
            raise AssertionError(name)

    kb = stages.research(Researcher(), FakeWeb(pages={docs: "Modules are containers"}), PROFILE).knowledge
    assert [(p.task, p.objective_id) for p in kb.spec.practice] == [(pin, "1.1"), (plan, "")]
    uncovered = [p.detail for p in checks.research(kb) if p.check == "practice_not_covered"]
    assert uncovered == [f"no objective teaches this routine practice: {plan!r}"]

"""The rules the feedback agent enforces without a model, one test per rule."""

from __future__ import annotations

from learning import checks
from learning.model import (
    Claim, Curriculum, Evidence, KnowledgeBase, LearnerProfile, Lesson, LessonObjective, LessonSpec,
    Level, Objective, Practice, QuizItem, Source, Spec, Tier, Unit,
)

PAGE = "Terraform uses state to map real world resources to your configuration."


def kb(kind="derived_from_docs") -> KnowledgeBase:
    src = Source.build("https://developer.hashicorp.com/terraform/language/state", "State", PAGE, Tier.OFFICIAL)
    objectives = [Objective(id="1", statement="manage state"),
                  Objective(id="1.1", statement="explain what state records", parent_id="1"),
                  Objective(id="1.2", statement="move a resource in state", parent_id="1")]
    claims = [Claim(id="c" * 12, text="state maps resources", quote="state to map real world resources",
                    source_id=src.id, objective_ids=["1.1", "1.2"])]
    return KnowledgeBase(profile=LearnerProfile(subject="Terraform"), sources=[src], claims=claims,
                         spec=Spec(kind=kind, title="Terraform", objectives=objectives))


def lesson_spec(id="u1-l1", statement="explain what state records", level=Level.UNDERSTAND,
                evidence=Evidence.QUIZ, covers=("1.1", "1.2"), **kw) -> LessonSpec:
    return LessonSpec(id=id, title=id, claim_ids=["c" * 12],
                      objectives=[LessonObjective(statement=statement, level=level, covers=list(covers),
                                                  evidence=evidence)], **kw)


def cur(*lessons: LessonSpec, project="Move a resource and prove it.") -> Curriculum:
    return Curriculum(title="t", units=[Unit(id="u1", title="State", lessons=list(lessons), project=project)])


def names(problems) -> list[str]:
    return sorted(p.check for p in problems)


def test_a_sound_curriculum_passes():
    assert checks.curriculum(cur(lesson_spec()), kb()) == []


def test_an_objective_nobody_can_see_is_rejected():
    assert "unmeasurable_objective" in names(checks.curriculum(cur(lesson_spec(statement="understand state")), kb()))


def test_a_quiz_cannot_prove_the_learner_can_do_something():
    bad = lesson_spec(statement="move a resource in state", level=Level.APPLY, evidence=Evidence.QUIZ)
    assert "misaligned_evidence" in names(checks.curriculum(cur(bad), kb()))


def test_an_objective_no_lesson_teaches_is_caught():
    assert "objectives_not_taught" in names(checks.curriculum(cur(lesson_spec(covers=("1.1",))), kb()))


def test_a_prerequisite_that_comes_later_is_caught():
    first = lesson_spec(id="u1-l1", prerequisites=["u1-l2"])
    second = lesson_spec(id="u1-l2")
    assert "prerequisite_after_use" in names(checks.curriculum(cur(first, second), kb()))


def test_a_unit_without_a_project_is_caught():
    assert "no_project" in names(checks.curriculum(cur(lesson_spec(), project=""), kb()))


def test_a_claim_the_research_never_found_is_caught():
    bad = lesson_spec()
    bad.claim_ids = ["d" * 12]
    assert "unknown_claim" in names(checks.curriculum(cur(bad), kb()))


def test_research_rejects_a_quote_that_is_not_on_its_page():
    k = kb()
    k.claims[0].quote = "state is stored in the cloud by default"
    assert "quote_not_on_page" in names(checks.research(k))


def test_an_exam_objective_must_be_the_guides_own_words():
    k = kb(kind="exam_guide")
    assert "objective_not_in_guide" in names(checks.research(k))


def practising(*practice: Practice, kind="derived_from_docs") -> KnowledgeBase:
    k = kb(kind)
    return k.model_copy(update={"spec": k.spec.model_copy(update={"practice": list(practice)})})


PIN = "Pin a shared module's version with ?ref= or version"


def test_research_whose_routine_practice_is_all_taught_passes():
    assert checks.research(practising(Practice(task=PIN, objective_id="1.2"))) == []


def test_routine_practice_no_objective_teaches_is_caught():
    # both Terraform courses left out pinning a shared module's version. In two runs it was
    # on the practice list, and the objectives quietly dropped it
    found = checks.research(practising(Practice(task=PIN)))
    assert names(found) == ["practice_not_covered"]
    assert PIN in found[0].detail


def test_routine_practice_must_name_one_objective_that_exists():
    # naming a whole area ("1, manage state") says nothing about what's taught
    assert names(checks.research(practising(Practice(task=PIN, objective_id="1")))) == ["practice_not_covered"]
    assert names(checks.research(practising(Practice(task=PIN, objective_id="9.9")))) == ["practice_not_covered"]


def test_an_exam_guide_is_not_held_to_the_practice_list():
    found = checks.research(practising(Practice(task=PIN), kind="exam_guide"))
    assert "practice_not_covered" not in names(found)


def test_research_saved_before_coverage_was_tracked_still_loads():
    spec = Spec.model_validate({"kind": "derived_from_docs", "title": "Terraform", "practice": [PIN]})
    assert spec.practice == [Practice(task=PIN)]


def test_an_unverified_version_holds_research_back():
    assert "version_unverified" in names(checks.research(kb(), "version 1.9 is given with no page that states it"))


def lesson(**kw) -> Lesson:
    base = dict(id="u1-l1", title="t", explanation=f"State maps resources [c:{'c' * 12}].",
                worked_example="e", quiz=[QuizItem(stem="s", options=["a", "b", "c"], answer=0,
                                                    explanation="why", objective="o")])
    return Lesson(**{**base, **kw})


def test_a_sound_lesson_passes():
    assert checks.lesson(lesson(), ["c" * 12], {"c" * 12}, needs_exercise=False) == []


def test_an_explanation_with_nothing_to_trace_is_caught():
    assert "no_citations" in names(checks.lesson(lesson(explanation="State is great."), [], {"c" * 12}, False))


def test_a_lesson_that_owes_an_exercise_must_have_one():
    assert "no_exercise" in names(checks.lesson(lesson(), ["c" * 12], {"c" * 12}, needs_exercise=True))


def test_quiz_items_follow_the_item_writing_rules():
    bad = QuizItem(stem="s", options=["a", "All of the above"], answer=3, explanation="", objective="o")
    found = names(checks.lesson(lesson(quiz=[bad]), ["c" * 12], {"c" * 12}, False))
    assert {"quiz_options", "quiz_answer", "quiz_all_or_none", "quiz_no_explanation"} <= set(found)


def test_an_explanation_that_counts_options_is_caught():
    # the answer index counts from 0 and learn.py counts from 1, so one lesson told
    # learners "Option 1 is incorrect" about the right answer
    item = QuizItem(stem="s", options=["a", "b", "c"], answer=0, explanation="Option 1 is incorrect because",
                    objective="o")
    found = [p for p in checks.lesson(lesson(quiz=[item]), ["c" * 12], {"c" * 12}, False)
             if p.check == "quiz_option_by_position"]
    assert found and '"Option 1"' in found[0].detail
    fine = item.model_copy(update={"explanation": "`~> 6.0` allows 6.x. Picking `< 7.0` also allows 5.x."})
    assert "quiz_option_by_position" not in names(checks.lesson(lesson(quiz=[fine]), ["c" * 12], {"c" * 12}, False))


def test_a_made_up_claim_hiding_in_a_list_of_citations_is_caught():
    made_up = lesson(explanation=f"State maps resources [c:{'c' * 12}, c:{'d' * 12}].")
    assert "unknown_citation" in names(checks.lesson(made_up, ["c" * 12], {"c" * 12}, False))


def test_a_mistyped_citation_is_caught():
    # one lesson cited [c:bfaa726bb50], 11 characters, which linked nowhere
    typo = lesson(explanation=f"State maps resources [c:{'c' * 12}]. Like this [c:bfaa726bb50]:")
    assert "malformed_citation" in names(checks.lesson(typo, ["c" * 12], {"c" * 12}, False))

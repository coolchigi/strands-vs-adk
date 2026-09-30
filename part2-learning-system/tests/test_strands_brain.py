"""What the Strands brain does when the model doesn't return its structured answer."""

from __future__ import annotations

from types import SimpleNamespace

from strands.types.exceptions import StructuredOutputException

from impl.strands import brain as strands_brain


def test_a_missing_answer_is_asked_for_again_with_the_reason(monkeypatch):
    prompts = []

    class Agent:
        def __init__(self, **kw):
            pass

        def __call__(self, prompt, structured_output_model):
            prompts.append(prompt)
            if len(prompts) == 1:
                raise StructuredOutputException("The model failed to invoke the structured output tool")
            return SimpleNamespace(structured_output="a spec")

    monkeypatch.setattr(strands_brain, "Agent", Agent)
    b = strands_brain.StrandsBrain(research_tools=[])
    assert b.ask("spec", "find the docs", "TypeScript", object) == "a spec"
    assert prompts == ["TypeScript", "TypeScript" + strands_brain.ANSWER_PLEASE]

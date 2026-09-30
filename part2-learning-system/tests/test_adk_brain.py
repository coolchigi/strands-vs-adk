"""What the ADK brain does when Gemini stops a call, with no model behind it."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from impl.adk.brain import ANSWER_PLEASE, IN_YOUR_OWN_WORDS, NoAnswer, ask_again
from impl.adk.telemetry import Recitation, raise_for


def test_a_recitation_stop_is_its_own_error():
    # a lesson call once ended the whole run with "RuntimeError lesson failed: RECITATION None"
    with pytest.raises(Recitation):
        raise_for(SimpleNamespace(error_code="RECITATION", error_message=None), "lesson")


def test_a_recitation_stop_is_asked_again_with_the_reason():
    prompts = []

    def call(prompt):
        prompts.append(prompt)
        if len(prompts) < 3:
            raise Recitation("stopped")
        return "a lesson"

    assert ask_again(call, "write u3-l1") == "a lesson"
    assert prompts[0] == "write u3-l1" and prompts[2].endswith(IN_YOUR_OWN_WORDS)


def test_it_gives_up_after_its_tries():
    def call(prompt):
        raise Recitation("stopped")

    with pytest.raises(Recitation):
        ask_again(call, "p", tries=2)


def test_an_agent_that_ends_without_an_answer_is_asked_again_with_the_reason():
    # the TypeScript research agent searched for 2 minutes and stopped without answering
    prompts = []

    def call(prompt):
        prompts.append(prompt)
        if len(prompts) == 1:
            raise NoAnswer("spec ended its turn without an answer")
        return "a spec"

    assert ask_again(call, "find the docs") == "a spec"
    assert prompts[1] == "find the docs" + ANSWER_PLEASE

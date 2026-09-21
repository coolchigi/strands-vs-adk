"""Part 1, Evaluation: running an ADK eval set from pytest.

Install:  pip install "google-adk[test]"     (brings pytest-asyncio)
Run:      pytest test_researcher.py

Needs a real eval set file and a course_agent package next to it, so this is
skipped unless both are present.
"""
import pathlib

import pytest

EVALSET = pathlib.Path(__file__).parent / "researcher.evalset.json"


@pytest.mark.skipif(not EVALSET.exists(), reason="no eval set in this folder")
@pytest.mark.asyncio
async def test_researcher():
    from google.adk.evaluation.agent_evaluator import AgentEvaluator

    await AgentEvaluator.evaluate(
        agent_module="course_agent",
        eval_dataset_file_path_or_dir=str(EVALSET),
    )

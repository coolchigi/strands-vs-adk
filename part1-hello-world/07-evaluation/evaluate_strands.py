"""Part 1, Evaluation: the Strands Evals SDK.

Install:  pip install strands-agents-evals

Watch the name. You install strands-agents-evals and you import strands_evals.
`pip install strands-evals` is an unrelated package by another author.
"""
from strands_evals.evaluators import ToolCalled, TrajectoryEvaluator

# Deterministic: did the agent call the tool at all?
tool_called = ToolCalled(tool_name="get_course_topic")

# Model judged: was the trajectory sensible?
trajectory = TrajectoryEvaluator(
    rubric="""
    Evaluate the tool usage trajectory:
      1. Were the right tools chosen for the task?
      2. Were the tools used in a logical order?
      3. Were unnecessary tools avoided?

    Score 1.0 if the tools were used correctly and efficiently.
    Score 0.5 if the right tools were used but the sequence was suboptimal.
    Score 0.0 if the wrong tools were used or there were major inefficiencies.
    """,
    include_inputs=True,
)

if __name__ == "__main__":
    print(f"deterministic: {type(tool_called).__name__}")
    print(f"model judged:  {type(trajectory).__name__}")

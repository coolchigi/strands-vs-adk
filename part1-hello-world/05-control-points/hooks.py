"""Part 1, What control points do we have: Strands hooks.

Run:  python hooks.py

Hooks attach to an agent you already hold, which is the difference worth noting.
The ADK side has to pass its callbacks in at construction.
"""
from strands import Agent, tool
from strands.hooks import BeforeModelCallEvent, BeforeToolCallEvent


def log_model_call(event: BeforeModelCallEvent) -> None:
    print("Calling the model")


def inspect_tool_call(event: BeforeToolCallEvent) -> None:
    print(f"Calling: {event.tool_use['name']}")


@tool
def get_course_topic() -> str:
    """Get the topic for the course."""
    return "Building AI agents"


agent = Agent(tools=[get_course_topic])
agent.add_hook(log_model_call)
agent.add_hook(inspect_tool_call)

agent(
    "Create a lesson about photosynthesis.",
    limits={"turns": 5, "total_tokens": 50_000},
)

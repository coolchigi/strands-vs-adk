"""Part 1, Giving our agent a tool: ADK reads a plain function.

Run:  adk run course_agent      (from the 02_tools folder)
"""
from google.adk.agents import Agent


def get_course_topic() -> str:
    """Get the topic for the course."""
    return "Building AI agents"


root_agent = Agent(
    name="course_agent",
    model="gemini-flash-latest",
    description="Helps create learning materials.",
    instruction="You help create learning materials.",
    tools=[get_course_topic],
)

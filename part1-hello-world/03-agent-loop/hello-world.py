"""Part 1, Giving our agent a tool: the Strands @tool decorator.

Run:  python hello-world.py
"""
from strands import Agent, tool


@tool
def get_course_topic() -> str:
    """Get the topic for the course."""
    return "Building AI agents"


agent = Agent(tools=[get_course_topic])

agent("What topic should I teach?")

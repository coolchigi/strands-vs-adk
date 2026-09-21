"""Part 1, What if one agent isn't enough: ADK sub-agents.

Run:  adk run course_agent      (from the 06_multi_agent folder)

ADK gives you a parent and child relationship. The parent decides when to hand
off, and the child owns the turn once it does.
"""
from google.adk.agents import Agent

researcher = Agent(
    name="researcher",
    model="gemini-flash-latest",
    instruction="Find information from official documentation, blogs, and other reliable sources.",
)

curriculum_builder = Agent(
    name="curriculum_builder",
    model="gemini-flash-latest",
    instruction="Turn the research into a structured curriculum.",
    sub_agents=[researcher],
)

root_agent = Agent(
    name="course_agent",
    model="gemini-flash-latest",
    instruction="Coordinate the research and the curriculum.",
    sub_agents=[curriculum_builder],
)

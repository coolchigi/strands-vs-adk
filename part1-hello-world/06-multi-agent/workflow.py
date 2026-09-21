"""Part 1, What if one agent isn't enough: ADK's Workflow.

Workflow lives at google.adk.Workflow. It is not exported from
google.adk.agents, and LoopAgent now warns on construction that it is deprecated
in favour of Workflow, which cannot yet be an LlmAgent sub-agent.
"""
from google.adk import Workflow
from google.adk.agents import Agent

researcher = Agent(
    name="researcher",
    model="gemini-flash-latest",
    instruction="Find information from official documentation.",
)

curriculum_builder = Agent(
    name="curriculum_builder",
    model="gemini-flash-latest",
    instruction="Turn the research into a structured curriculum.",
)

teacher = Agent(
    name="teacher",
    model="gemini-flash-latest",
    instruction="Create lessons from the curriculum.",
)

root_agent = Workflow(
    name="learning_system",
    edges=[
        ("START", researcher, curriculum_builder, teacher),
    ],
)

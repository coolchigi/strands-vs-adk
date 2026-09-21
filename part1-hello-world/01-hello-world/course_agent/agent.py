"""Part 1, Hello World: the smallest ADK agent.

Run:  adk run course_agent      (from the 01_hello_world folder)
Needs GOOGLE_API_KEY in course_agent/.env
"""
from google.adk.agents import Agent

root_agent = Agent(
    model="gemini-flash-latest",
    name="root_agent",
    description="Says hello.",
    instruction="You are a helpful assistant.",
)

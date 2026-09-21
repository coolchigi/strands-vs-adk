"""Part 1, Where does state live: the ADK side."""
from google.adk.agents import Agent

root_agent = Agent(
    name="course_agent",
    model="gemini-flash-latest",
    description="Helps create learning materials.",
    instruction="You help create learning materials. The topic is {course_topic}.",
)

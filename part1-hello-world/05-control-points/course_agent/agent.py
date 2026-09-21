"""Part 1, What control points do we have: ADK callbacks.

Run:  adk run course_agent      (from the 05_control_points folder)

Callbacks are constructor arguments. There is no add_callback after the fact.
"""
from google.adk.agents import Agent


def before_model_callback(callback_context, llm_request):
    print("Calling the model")


def before_tool_callback(tool, args, tool_context):
    print(f"Calling: {tool.name}")


root_agent = Agent(
    name="course_agent",
    model="gemini-flash-latest",
    instruction="You help create learning materials.",
    before_model_callback=before_model_callback,
    before_tool_callback=before_tool_callback,
)

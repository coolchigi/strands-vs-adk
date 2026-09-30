"""google_search and output_schema on one ADK agent.

Run:  export GOOGLE_API_KEY=...  then  python examples/search_and_schema.py

Delete the generate_content_config line and the first model call fails with
400 INVALID_ARGUMENT: Please enable tool_config.include_server_side_tool_invocations
"""
import asyncio

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.tools import google_search
from google.genai import types
from pydantic import BaseModel


class Plan(BaseModel):
    official_domains: list[str]
    current_version: str | None = None


planner = Agent(
    name="plan",
    model="gemini-3.8-flash",
    instruction="Find the official docs domain and the current release of the subject. Use google_search.",
    tools=[google_search],
    output_schema=Plan,
    output_key="plan",
    generate_content_config=types.GenerateContentConfig(
        tool_config=types.ToolConfig(include_server_side_tool_invocations=True)
    ),
)


async def main() -> None:
    runner = InMemoryRunner(agent=planner, app_name="plan")
    session = await runner.session_service.create_session(app_name="plan", user_id="me")
    message = types.Content(role="user", parts=[types.Part(text="Terraform")])
    async for _ in runner.run_async(user_id="me", session_id=session.id, new_message=message):
        pass
    done = await runner.session_service.get_session(app_name="plan", user_id="me", session_id=session.id)
    print(done.state["plan"])


if __name__ == "__main__":
    asyncio.run(main())

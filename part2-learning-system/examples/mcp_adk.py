"""AWS's Knowledge MCP server as a tool on an ADK agent, next to google_search.

Run:  python examples/mcp_adk.py      (needs GOOGLE_API_KEY)
"""
import asyncio

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.tools import google_search
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams
from google.genai import types

aws_docs = McpToolset(connection_params=StreamableHTTPConnectionParams(url="https://knowledge-mcp.global.api.aws"))
researcher = Agent(
    name="researcher",
    model="gemini-3.8-flash",
    instruction="Answer from the AWS documentation, in one sentence.",
    tools=[google_search, aws_docs],
    generate_content_config=types.GenerateContentConfig(
        tool_config=types.ToolConfig(include_server_side_tool_invocations=True)
    ),
)


async def main() -> None:
    runner = InMemoryRunner(agent=researcher, app_name="docs")
    session = await runner.session_service.create_session(app_name="docs", user_id="me")
    message = types.Content(role="user", parts=[types.Part(text="How big can a single S3 object be?")])
    async for event in runner.run_async(user_id="me", session_id=session.id, new_message=message):
        if event.is_final_response() and event.content and event.content.parts:
            print("".join(part.text or "" for part in event.content.parts))
    await aws_docs.close()


asyncio.run(main())

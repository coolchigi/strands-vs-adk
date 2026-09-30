"""How the ADK side asks an agent for something.

One Agent per call, run in its own session, with the answer read back out of session
state under `output_key`. Research agents get ADK's own `google_search` and AWS's Knowledge
MCP server through `McpToolset`.

Three ADK details this depends on:

- `output_schema` next to any tool makes ADK add a function tool of its own,
  set_model_response, on the Gemini API. google_search is a built-in tool, and the API
  refuses built-ins mixed with function tools unless
  tool_config.include_server_side_tool_invocations is set.
- The instruction is passed as a function. A string instruction is a template: any
  `{name}` that is a valid identifier is replaced from session state, and a missing one
  raises. `{}` and `${var.region}` pass through, but a prompt that mentions `{region}`
  would break, so the instructions here opt out.
- ADK hands back an exception from a callback as an error event first.
- Every call runs on one event loop that lives as long as the brain. The MCP toolset keeps
  a session open on the loop it first ran on, and a fresh asyncio.run per call strands it.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
from typing import Any, Callable, TypeVar

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams
from google.genai import types
from pydantic import BaseModel

from learning.web import HttpWeb, docs_index

from .telemetry import Meter, Recitation, raise_for

log = logging.getLogger("learning")

_web = HttpWeb()


def list_docs_pages(url_prefix: str) -> str:
    """List the official documentation pages a site publishes under a URL prefix.

    Reads the site's own sitemap or llms.txt, so every URL returned is a real page.

    Args:
        url_prefix: like https://developer.hashicorp.com/terraform/language
    """
    urls = docs_index(_web, url_prefix)
    return "\n".join(urls) or f"no sitemap or llms.txt lists pages under {url_prefix}"

T = TypeVar("T", bound=BaseModel)

MODEL = os.environ.get("ADK_MODEL", "gemini-3.8-flash")
AWS_KNOWLEDGE_MCP_URL = "https://knowledge-mcp.global.api.aws"
SERVER_SIDE_TOOLS = types.ToolConfig(include_server_side_tool_invocations=True)


class AdkBrain:
    def __init__(self, meter: Meter | None = None, research_tools: list[Any] | None = None) -> None:
        self.meter = meter
        self._research_tools = research_tools
        self.sessions = InMemorySessionService()
        self._loop = asyncio.new_event_loop()
        threading.Thread(target=self._loop.run_forever, daemon=True, name="adk-brain").start()

    def research_tools(self) -> list[Any]:
        if self._research_tools is None:
            self._research_tools = [
                google_search,
                McpToolset(connection_params=StreamableHTTPConnectionParams(url=AWS_KNOWLEDGE_MCP_URL)),
                list_docs_pages,
            ]
        return self._research_tools

    def _agent(self, name: str, instruction: str, schema: type[BaseModel], research: bool) -> Agent:
        model = self.meter.current_model() if self.meter is not None else MODEL  # cheaper after the switch
        kw: dict[str, Any] = {
            "name": name,
            "model": model,
            "instruction": lambda ctx: instruction,  # a function, so {name} isn't read as a state key
            "output_schema": schema,
            "output_key": "answer",
        }
        if research:
            kw["tools"] = self.research_tools()
            kw["generate_content_config"] = types.GenerateContentConfig(tool_config=SERVER_SIDE_TOOLS)
        if self.meter is not None:
            kw.update(self.meter.callbacks(name, model))
        return Agent(**kw)

    async def _ask(self, agent: Agent, prompt: str, schema: type[T]) -> T:
        runner = Runner(app_name="learning", agent=agent, session_service=self.sessions)
        session = await self.sessions.create_session(app_name="learning", user_id="learner")
        message = types.Content(role="user", parts=[types.Part(text=prompt)])
        said = ""
        async for event in runner.run_async(user_id="learner", session_id=session.id, new_message=message):
            raise_for(event, agent.name)
            if event.content and event.content.parts:
                said = "".join(p.text or "" for p in event.content.parts) or said
        done = await self.sessions.get_session(app_name="learning", user_id="learner", session_id=session.id)
        raw = done.state.get("answer")
        if raw is None:
            raise NoAnswer(f"{agent.name} ended its turn without an answer"
                           + (f", saying: {' '.join(said.split())[:300]}" if said.strip() else ""))
        return schema.model_validate(json.loads(raw) if isinstance(raw, str) else raw)

    def ask(self, name: str, instruction: str, prompt: str, schema: type[T], research: bool = False) -> T:
        agent = self._agent(name, instruction, schema, research)
        return ask_again(
            lambda p: asyncio.run_coroutine_threadsafe(self._ask(agent, p, schema), self._loop).result(), prompt)


class NoAnswer(RuntimeError):
    """The agent ended its turn without returning its structured answer. A research agent
    did this once after 2 minutes of searching. Asked again, with the reason, it usually answers."""


TRIES = 3
IN_YOUR_OWN_WORDS = ("\n\nYour last answer was stopped for reciting text too closely. Write the prose "
                     "and code in your own words. Quotes you were asked to copy exactly stay exact.")
ANSWER_PLEASE = ("\n\nYour last attempt ended without returning an answer. Finish by returning your "
                 "answer in the required structure, with what you've found.")
REASONS = {Recitation: IN_YOUR_OWN_WORDS, NoAnswer: ANSWER_PLEASE}


def ask_again(call: Callable[[str], T], prompt: str, tries: int = TRIES) -> T:
    """Ask again when a call stops without a usable answer, saying why, up to `tries` times."""
    reason = ""
    for attempt in range(1, tries + 1):
        try:
            return call(prompt + reason)
        except (Recitation, NoAnswer) as e:
            if attempt == tries:
                raise
            reason = REASONS[type(e)]
            log.info("%s. Asking again (%d of %d)", e, attempt + 1, tries)
    raise AssertionError("unreachable")

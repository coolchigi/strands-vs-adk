"""How the Strands side asks an agent for something.

One Agent per call, with the instruction as its system prompt, and the answer back as a
typed object from `structured_output_model`. Strands has no search of its own, so research
agents get MCP servers passed straight into `tools`:

- AWS's Knowledge MCP server, for AWS documentation. It needs no key.
- `web_fetch` from strands.vended_tools, to read a page live. Search indexes run days
  behind, and a model quoting a stale copy of a page gets the version wrong.
- `list_docs_pages`, our own @tool, which lists the pages a docs site publishes under a
  prefix, from its own sitemap.
- Web search over MCP only with a key: Exa (EXA_API_KEY) or Tavily (TAVILY_API_KEY). Exa's
  keyless tier ran out partway through a single course build.
"""

from __future__ import annotations

import logging
import os
from typing import Any, TypeVar

from botocore.config import Config as BotocoreConfig
from pydantic import BaseModel
from strands import Agent, tool
from strands.models.bedrock import BedrockModel
from strands.tools.mcp import MCPClient
from strands.types.exceptions import StructuredOutputException
from strands.vended_tools.web_fetch import make_web_fetch

from learning.web import HttpWeb, docs_index

from .telemetry import Meter

_web = HttpWeb()


@tool
def list_docs_pages(url_prefix: str) -> str:
    """List the official documentation pages a site publishes under a URL prefix.

    Reads the site's own sitemap or llms.txt, so every URL returned is a real page.

    Args:
        url_prefix: like https://developer.hashicorp.com/terraform/language
    """
    urls = docs_index(_web, url_prefix)
    return "\n".join(urls) or f"no sitemap or llms.txt lists pages under {url_prefix}"

T = TypeVar("T", bound=BaseModel)

log = logging.getLogger("learning")
TRIES = 3
ANSWER_PLEASE = ("\n\nYour last attempt ended without returning an answer. Finish by returning your "
                 "answer in the required structure, with what you've found.")

MODEL_ID = os.environ.get("STRANDS_MODEL", "global.anthropic.claude-sonnet-4-6")
EXA_MCP_URL = "https://mcp.exa.ai/mcp"
TAVILY_MCP_URL = "https://mcp.tavily.com/mcp/?tavilyApiKey={key}"
AWS_KNOWLEDGE_MCP_URL = "https://knowledge-mcp.global.api.aws"


def search_url() -> str | None:
    if key := os.environ.get("TAVILY_API_KEY"):
        return TAVILY_MCP_URL.format(key=key)
    if key := os.environ.get("EXA_API_KEY"):
        return f"{EXA_MCP_URL}?exaApiKey={key}"
    return None


class StrandsBrain:
    def __init__(self, meter: Meter | None = None, research_tools: list[Any] | None = None) -> None:
        self.meter = meter
        self._models: dict[str, BedrockModel] = {}
        self._research_tools = research_tools

    def model(self, model_id: str) -> BedrockModel:
        """One client per model id. The meter picks the id: the cheaper model after the switch.

        Strands' own read timeout is 120s, and a whole curriculum as one structured answer
        outlasted it. Passing a config replaces that default, so set it here."""
        if model_id not in self._models:
            self._models[model_id] = BedrockModel(
                model_id=model_id, region_name=os.environ.get("AWS_REGION", "us-east-1"),
                boto_client_config=BotocoreConfig(read_timeout=600, retries={"max_attempts": 4, "mode": "adaptive"}))
        return self._models[model_id]

    def research_tools(self) -> list[Any]:
        if self._research_tools is None:
            self._research_tools = [
                MCPClient(url=AWS_KNOWLEDGE_MCP_URL),
                make_web_fetch(mode="markdown", max_content_chars=50_000),
                list_docs_pages,
            ]
            if url := search_url():
                self._research_tools.append(MCPClient(url=url))
        return self._research_tools

    def ask(self, name: str, instruction: str, prompt: str, schema: type[T], research: bool = False) -> T:
        reason = ""
        for attempt in range(1, TRIES + 1):
            # a fresh agent each time, so a failed attempt's conversation doesn't carry over.
            # callback_handler=None, or Strands prints every streamed token to stdout
            model_id = self.meter.current_model() if self.meter is not None else MODEL_ID
            agent = Agent(model=self.model(model_id), system_prompt=instruction, callback_handler=None,
                          tools=self.research_tools() if research else None, name=name)
            if self.meter is not None:
                self.meter.watch(agent, name, model_id)
            try:
                result = agent(prompt + reason, structured_output_model=schema)
                if result.structured_output is not None:
                    return result.structured_output
                problem = f"{name}: the model returned nothing shaped like {schema.__name__}"
            except StructuredOutputException as e:
                problem = f"{name}: {e}"
            if attempt == TRIES:
                raise RuntimeError(problem)
            reason = ANSWER_PLEASE
            log.info("%s. Asking again (%d of %d)", problem, attempt + 1, TRIES)
        raise AssertionError("unreachable")

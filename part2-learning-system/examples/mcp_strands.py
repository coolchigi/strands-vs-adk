"""AWS's Knowledge MCP server as a tool on a Strands agent. No key needed.

Run:  python examples/mcp_strands.py      (needs AWS credentials with Bedrock access)
"""
from strands import Agent
from strands.tools.mcp import MCPClient

aws_docs = MCPClient(url="https://knowledge-mcp.global.api.aws")
researcher = Agent(system_prompt="Answer from the AWS documentation, in one sentence.",
                   tools=[aws_docs], callback_handler=None)

print(researcher("How big can a single S3 object be?"))

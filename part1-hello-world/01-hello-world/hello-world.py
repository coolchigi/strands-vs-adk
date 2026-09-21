"""Part 1, Hello World: the smallest Strands agent.

Run:  python hello-world.py
Needs AWS credentials with Bedrock access. Strands defaults to Claude Sonnet 4
on Amazon Bedrock.
"""
from strands import Agent

agent = Agent()

agent("Hello, world!")

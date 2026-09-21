"""Part 1, Where does state live: Strands keeps it on the Agent.

Run:  python conversation.py
"""
from strands import Agent

agent = Agent()

agent("My name is Chigo.")

print(agent.messages)

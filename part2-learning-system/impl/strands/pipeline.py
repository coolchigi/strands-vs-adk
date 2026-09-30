"""The run as a Strands Graph.

Stages and reviews are nodes. A review sets where the run goes next, and conditional edges
read it, so the feedback loop is declared in the graph. set_max_node_executions is the
backstop. The flow itself also stops retrying a stage after a few attempts.

A graph node has to be an Agent or a MultiAgentBase, and these nodes are stages of plain
Python that call agents inside them. So each gets a small MultiAgentBase wrapper. A plain
function is accepted by add_node and build(), and only fails when the graph reaches it.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable

from strands.multiagent import GraphBuilder
from strands.multiagent.base import MultiAgentBase, MultiAgentResult, Status

from learning.flow import CURRICULUM, DONE, RESEARCH, TEACHING, Flow


class Step(MultiAgentBase):
    def __init__(self, name: str, work: Callable[[], Any]) -> None:
        super().__init__()
        self.name = name
        self.work = work

    async def invoke_async(self, task: Any, invocation_state: dict[str, Any] | None = None,
                           **kwargs: Any) -> MultiAgentResult:
        # the graph runs nodes on its event loop, and the stages block, so off it they go
        await asyncio.to_thread(self.work)
        # results stays empty: Strands walks into it to build the next node's input, so it
        # has to hold real results or nothing. the work travels on flow.board instead
        return MultiAgentResult(status=Status.COMPLETED, results={})


def build_graph(flow: Flow, max_node_executions: int = 24):
    board = flow.board

    def review(check: Callable[[], str]) -> Callable[[], None]:
        def run() -> None:
            board.route = check()
        return run

    def going(route: str):
        def condition(_state: Any) -> bool:
            return board.route == route
        condition.__name__ = f"to_{route}"
        return condition

    b = GraphBuilder()
    b.add_node(Step("research", flow.research), "research")
    b.add_node(Step("review_research", review(flow.review_research)), "review_research")
    b.add_node(Step("curriculum", flow.curriculum), "curriculum")
    b.add_node(Step("review_curriculum", review(flow.review_curriculum)), "review_curriculum")
    b.add_node(Step("teaching", flow.teaching), "teaching")
    b.add_node(Step("review_teaching", review(flow.review_teaching)), "review_teaching")

    b.add_edge("research", "review_research")
    b.add_edge("review_research", "research", condition=going(RESEARCH))
    b.add_edge("review_research", "curriculum", condition=going(CURRICULUM))
    b.add_edge("curriculum", "review_curriculum")
    b.add_edge("review_curriculum", "curriculum", condition=going(CURRICULUM))
    b.add_edge("review_curriculum", "research", condition=going(RESEARCH))
    b.add_edge("review_curriculum", "teaching", condition=going(TEACHING))
    b.add_edge("teaching", "review_teaching")

    b.set_entry_point("research")
    b.set_max_node_executions(max_node_executions)
    b.reset_on_revisit(True)
    return b.build()


def run(flow: Flow) -> Status:
    result = build_graph(flow)("build the course")
    if flow.board.route != DONE:
        raise RuntimeError(f"the graph stopped at {flow.board.route} with status {result.status}")
    return result.status

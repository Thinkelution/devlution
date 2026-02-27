"""LangGraph state-machine pipeline with stub agent nodes.

The graph mirrors the spec's flow: planner → coder → reviewer → tester → gate → PR,
with conditional edges for retries, escalation, and debugging loops.
Stub nodes are used until real agents replace them.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from langgraph.graph import END, StateGraph

from devlution.config import DevlutionConfig
from devlution.orchestrator.router import (
    route_debugger,
    route_gate,
    route_planner,
    route_reviewer,
    route_tester,
)

logger = logging.getLogger(__name__)


def _make_stub(name: str):
    """Create a stub node function that logs and passes state through."""

    def stub(state: dict[str, Any]) -> dict[str, Any]:
        logger.info("[stub:%s] Agent would run here", name)
        scores = dict(state.get("confidence_scores", {}))
        scores[name] = 0.95
        updates: dict[str, Any] = {"confidence_scores": scores}

        if name == "planner" and not state.get("tasks"):
            updates["tasks"] = [
                {
                    "id": "T1",
                    "title": f"Stub task from {name}",
                    "files_likely_affected": [],
                    "acceptance_criteria": ["Passes tests"],
                    "estimated_complexity": "medium",
                    "dependencies": [],
                }
            ]

        if name == "reviewer":
            updates["review_decision"] = "approve"

        if name == "tester":
            updates["test_results"] = {
                "passed": True,
                "total_tests": 1,
                "passed_tests": 1,
                "failed_tests": 0,
                "coverage_percent": 90.0,
                "output": "All tests passed (stub)",
                "failure_log": "",
            }

        if name == "gate":
            gate_id = f"gate-{uuid.uuid4().hex[:8]}"
            decisions = dict(state.get("gate_decisions", {}))
            decisions[gate_id] = {
                "gate_id": gate_id,
                "decision": "approved",
                "approver": "auto-stub",
                "method": "stub",
                "timestamp": datetime.utcnow().isoformat(),
                "reason": "",
            }
            updates["gate_decisions"] = decisions

        if name == "pr":
            updates["pr_url"] = "https://github.com/example/repo/pull/0 (stub)"

        return updates

    stub.__name__ = f"stub_{name}"
    return stub


def build_pipeline(config: DevlutionConfig) -> StateGraph:
    """Construct the Devlution pipeline graph (uses stubs until real agents are wired)."""

    graph = StateGraph(dict)

    graph.add_node("planner", _make_stub("planner"))
    graph.add_node("coder", _make_stub("coder"))
    graph.add_node("reviewer", _make_stub("reviewer"))
    graph.add_node("tester", _make_stub("tester"))
    graph.add_node("debugger", _make_stub("debugger"))
    graph.add_node("gate", _make_stub("gate"))
    graph.add_node("pr", _make_stub("pr"))

    graph.set_entry_point("planner")

    graph.add_conditional_edges(
        "planner",
        route_planner,
        {"proceed": "coder", "escalate": "gate", "abort": END},
    )

    graph.add_edge("coder", "reviewer")

    graph.add_conditional_edges(
        "reviewer",
        route_reviewer,
        {"approve": "tester", "request_changes": "coder", "escalate": "gate"},
    )

    graph.add_conditional_edges(
        "tester",
        route_tester,
        {"pass": "gate", "fail": "debugger", "coverage_fail": "coder"},
    )

    graph.add_conditional_edges(
        "debugger",
        route_debugger,
        {"fixed": "tester", "max_retries": "gate", "abort": END},
    )

    graph.add_conditional_edges(
        "gate",
        route_gate,
        {"approved": "pr", "rejected": END, "timeout": END},
    )

    graph.add_edge("pr", END)

    return graph

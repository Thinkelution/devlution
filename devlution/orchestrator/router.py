"""Conditional edge routing functions for the LangGraph pipeline.

Each router inspects PipelineState fields and returns a string key that maps
to the next node in the graph.
"""

from __future__ import annotations

from typing import Any

from devlution.orchestrator.state import PipelineStatus


def route_planner(state: dict[str, Any]) -> str:
    """After planner: proceed to coder, escalate, or abort."""
    confidence = state.get("confidence_scores", {}).get("planner", 1.0)
    tasks = state.get("tasks", [])

    if not tasks:
        return "abort"
    if confidence < 0.5:
        return "escalate"
    return "proceed"


def route_reviewer(state: dict[str, Any]) -> str:
    """After reviewer: approve → tester, request_changes → coder, or escalate."""
    decision = state.get("review_decision", "")
    confidence = state.get("confidence_scores", {}).get("reviewer", 1.0)

    if decision == "escalate_to_human" or confidence < 0.75:
        return "escalate"
    if decision == "request_changes":
        return "request_changes"
    return "approve"


def route_tester(state: dict[str, Any]) -> str:
    """After tester: pass → gate, fail → debugger, coverage_fail → coder."""
    test_results = state.get("test_results")
    if test_results is None:
        return "pass"

    if isinstance(test_results, dict):
        passed = test_results.get("passed", True)
        coverage = test_results.get("coverage_percent", 100.0)
    else:
        passed = test_results.passed
        coverage = test_results.coverage_percent

    if not passed:
        return "fail"
    if coverage < 80:
        return "coverage_fail"
    return "pass"


def route_debugger(state: dict[str, Any]) -> str:
    """After debugger: fixed → tester, max_retries → gate, abort."""
    iterations = state.get("iterations", {})
    debugger_attempts = iterations.get("debugger", 0)

    if debugger_attempts >= 3:
        return "max_retries"

    status = state.get("status", "")
    if status == PipelineStatus.FAILED or status == "failed":
        return "abort"

    return "fixed"


def route_gate(state: dict[str, Any]) -> str:
    """After gate: approved → pr, rejected or timeout → end."""
    gate_decisions = state.get("gate_decisions", {})

    for decision in gate_decisions.values():
        if isinstance(decision, dict):
            d = decision.get("decision", "")
        else:
            d = decision.decision

        if d == "rejected":
            return "rejected"
        if d == "timeout":
            return "timeout"

    return "approved"

"""Tests for devlution.orchestrator.router — conditional edge routing."""

from devlution.orchestrator.router import (
    route_debugger,
    route_gate,
    route_planner,
    route_reviewer,
    route_tester,
)


class TestRoutePlanner:
    def test_proceed_with_tasks(self) -> None:
        state = {"tasks": [{"id": "T1"}], "confidence_scores": {"planner": 0.9}}
        assert route_planner(state) == "proceed"

    def test_abort_no_tasks(self) -> None:
        state = {"tasks": [], "confidence_scores": {"planner": 0.9}}
        assert route_planner(state) == "abort"

    def test_escalate_low_confidence(self) -> None:
        state = {"tasks": [{"id": "T1"}], "confidence_scores": {"planner": 0.3}}
        assert route_planner(state) == "escalate"


class TestRouteReviewer:
    def test_approve(self) -> None:
        state = {"review_decision": "approve", "confidence_scores": {"reviewer": 0.95}}
        assert route_reviewer(state) == "approve"

    def test_request_changes(self) -> None:
        state = {"review_decision": "request_changes", "confidence_scores": {"reviewer": 0.9}}
        assert route_reviewer(state) == "request_changes"

    def test_escalate_explicit(self) -> None:
        state = {"review_decision": "escalate_to_human", "confidence_scores": {}}
        assert route_reviewer(state) == "escalate"

    def test_escalate_low_confidence(self) -> None:
        state = {"review_decision": "approve", "confidence_scores": {"reviewer": 0.5}}
        assert route_reviewer(state) == "escalate"


class TestRouteTester:
    def test_pass(self) -> None:
        state = {"test_results": {"passed": True, "coverage_percent": 90.0}}
        assert route_tester(state) == "pass"

    def test_fail(self) -> None:
        state = {"test_results": {"passed": False, "coverage_percent": 90.0}}
        assert route_tester(state) == "fail"

    def test_coverage_fail(self) -> None:
        state = {"test_results": {"passed": True, "coverage_percent": 50.0}}
        assert route_tester(state) == "coverage_fail"

    def test_none_results(self) -> None:
        state = {"test_results": None}
        assert route_tester(state) == "pass"


class TestRouteDebugger:
    def test_fixed(self) -> None:
        state = {"iterations": {"debugger": 1}, "status": "running"}
        assert route_debugger(state) == "fixed"

    def test_max_retries(self) -> None:
        state = {"iterations": {"debugger": 3}, "status": "running"}
        assert route_debugger(state) == "max_retries"

    def test_abort_on_failure(self) -> None:
        state = {"iterations": {"debugger": 1}, "status": "failed"}
        assert route_debugger(state) == "abort"


class TestRouteGate:
    def test_approved(self) -> None:
        state = {"gate_decisions": {"g1": {"decision": "approved"}}}
        assert route_gate(state) == "approved"

    def test_rejected(self) -> None:
        state = {"gate_decisions": {"g1": {"decision": "rejected"}}}
        assert route_gate(state) == "rejected"

    def test_timeout(self) -> None:
        state = {"gate_decisions": {"g1": {"decision": "timeout"}}}
        assert route_gate(state) == "timeout"

    def test_empty_decisions(self) -> None:
        state = {"gate_decisions": {}}
        assert route_gate(state) == "approved"

"""Integration tests — end-to-end stub pipeline execution."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from devlution.config import DevlutionConfig, load_config
from devlution.orchestrator.graph import build_pipeline
from devlution.supervision.audit_log import AuditLogger


FIXTURES = Path(__file__).parent.parent / "fixtures" / "sample_repo"


@pytest.fixture
def sample_config() -> DevlutionConfig:
    return load_config(FIXTURES / "devlution.yaml")


@pytest.fixture
def audit(tmp_path: Path) -> AuditLogger:
    return AuditLogger(tmp_path / "audit.jsonl")


class TestStubPipeline:
    """End-to-end tests using the stub agent nodes."""

    def test_full_pipeline_completes(self, sample_config: DevlutionConfig) -> None:
        graph = build_pipeline(sample_config)
        compiled = graph.compile()

        initial_state = {
            "pipeline_id": "test-001",
            "trigger": {"type": "manual"},
            "tasks": [],
            "current_task_idx": 0,
            "iterations": {},
            "confidence_scores": {},
            "review_comments": [],
            "review_decision": "",
            "test_results": None,
            "patch": "",
            "pr_url": "",
            "gate_decisions": {},
            "audit_entries": [],
            "status": "pending",
            "error": "",
        }

        final = compiled.invoke(initial_state)

        assert final.get("pr_url"), "Pipeline should produce a PR URL"
        assert final.get("confidence_scores"), "Should have confidence scores"
        assert "planner" in final["confidence_scores"]

    def test_pipeline_traverses_all_agents(self, sample_config: DevlutionConfig) -> None:
        graph = build_pipeline(sample_config)
        compiled = graph.compile()

        initial_state = {
            "pipeline_id": "test-002",
            "trigger": {"type": "github_issue", "issue_number": 1},
            "tasks": [],
            "current_task_idx": 0,
            "iterations": {},
            "confidence_scores": {},
            "review_comments": [],
            "review_decision": "",
            "test_results": None,
            "patch": "",
            "pr_url": "",
            "gate_decisions": {},
            "audit_entries": [],
            "status": "pending",
            "error": "",
        }

        final = compiled.invoke(initial_state)
        scores = final.get("confidence_scores", {})
        assert "planner" in scores, "Planner should have run"
        assert "reviewer" in scores, "Reviewer should have run"

    def test_pipeline_produces_pr_url(self, sample_config: DevlutionConfig) -> None:
        graph = build_pipeline(sample_config)
        compiled = graph.compile()

        initial_state = {
            "pipeline_id": "test-003",
            "trigger": {"type": "manual"},
            "tasks": [],
            "current_task_idx": 0,
            "iterations": {},
            "confidence_scores": {},
            "review_comments": [],
            "review_decision": "",
            "test_results": None,
            "patch": "",
            "pr_url": "",
            "gate_decisions": {},
            "audit_entries": [],
            "status": "pending",
            "error": "",
        }

        final = compiled.invoke(initial_state)
        assert "pr_url" in final, "Pipeline should end with PR creation"
        assert "stub" in final["pr_url"]


class TestConfigValidation:
    """Config validation edge cases."""

    def test_load_sample_fixture(self) -> None:
        config = load_config(FIXTURES / "devlution.yaml")
        assert config.project.name == "sample-service"
        assert config.agents.coder.max_iterations == 2

    def test_invalid_yaml_raises(self, tmp_path: Path) -> None:
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text(": invalid: yaml: content [")
        with pytest.raises(Exception):
            load_config(bad_yaml)

    def test_missing_required_field(self, tmp_path: Path) -> None:
        incomplete = tmp_path / "incomplete.yaml"
        incomplete.write_text(yaml.dump({"llm": {"model": "test"}}))
        with pytest.raises(Exception):
            load_config(incomplete)

    def test_minimal_valid_config(self, tmp_path: Path) -> None:
        minimal = tmp_path / "minimal.yaml"
        minimal.write_text(yaml.dump({"project": {"name": "min"}}))
        config = load_config(minimal)
        assert config.project.name == "min"
        assert config.llm.model == "claude-sonnet-4-20250514"


class TestFailurePaths:
    """Test routing through failure and escalation paths."""

    def test_empty_tasks_aborts(self, sample_config: DevlutionConfig) -> None:
        """When planner returns no tasks with low confidence, pipeline aborts."""
        from devlution.orchestrator.router import route_planner

        state = {"tasks": [], "confidence_scores": {"planner": 0.9}}
        assert route_planner(state) == "abort"

    def test_low_confidence_escalates(self, sample_config: DevlutionConfig) -> None:
        from devlution.orchestrator.router import route_planner

        state = {"tasks": [{"id": "T1"}], "confidence_scores": {"planner": 0.3}}
        assert route_planner(state) == "escalate"

    def test_test_failure_routes_to_debugger(self) -> None:
        from devlution.orchestrator.router import route_tester

        state = {"test_results": {"passed": False, "coverage_percent": 90.0}}
        assert route_tester(state) == "fail"

    def test_max_debug_retries_escalate(self) -> None:
        from devlution.orchestrator.router import route_debugger

        state = {"iterations": {"debugger": 3}, "status": "running"}
        assert route_debugger(state) == "max_retries"

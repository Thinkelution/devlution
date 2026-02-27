"""Tests for devlution.config — YAML loading and Pydantic validation."""

from pathlib import Path
from textwrap import dedent

import pytest
import yaml

from devlution.config import (
    DevlutionConfig,
    LLMConfig,
    ProjectConfig,
    load_config,
)


@pytest.fixture
def sample_yaml(tmp_path: Path) -> Path:
    config = {
        "project": {
            "name": "test-project",
            "language": "python",
            "test_command": "pytest",
            "lint_command": "ruff check .",
            "main_branch": "main",
        },
        "llm": {
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "temperature": 0.2,
        },
    }
    path = tmp_path / "devlution.yaml"
    path.write_text(yaml.dump(config))
    return path


@pytest.fixture
def full_yaml(tmp_path: Path) -> Path:
    config = {
        "project": {"name": "full-test", "language": "typescript"},
        "llm": {"provider": "anthropic", "model": "claude-sonnet-4-20250514"},
        "agents": {
            "planner": {"enabled": True, "max_subtasks": 5},
            "coder": {"enabled": True, "max_iterations": 2},
            "reviewer": {"enabled": True, "auto_approve_threshold": 0.85},
            "tester": {"enabled": True, "coverage_threshold": 90},
            "debugger": {"enabled": True, "max_fix_attempts": 2},
        },
        "supervision": {
            "gates": [
                {
                    "id": "test-gate",
                    "trigger": "before_merge",
                    "type": "human_approval",
                    "notify": ["slack"],
                    "timeout_hours": 12,
                }
            ],
            "audit_log": ".devlution/audit.jsonl",
        },
        "pipeline": {
            "flow": ["planner", "coder", "reviewer"],
            "triggers": [
                {"on": "github_issue", "label": "ai-task", "flow": ["planner", "coder"]}
            ],
        },
    }
    path = tmp_path / "devlution.yaml"
    path.write_text(yaml.dump(config))
    return path


def test_load_minimal_config(sample_yaml: Path) -> None:
    config = load_config(sample_yaml)
    assert config.project.name == "test-project"
    assert config.project.language == "python"
    assert config.llm.model == "claude-sonnet-4-20250514"
    assert config.llm.max_tokens == 4096


def test_load_full_config(full_yaml: Path) -> None:
    config = load_config(full_yaml)
    assert config.project.language == "typescript"
    assert config.agents.planner.max_subtasks == 5
    assert config.agents.reviewer.auto_approve_threshold == 0.85
    assert len(config.supervision.gates) == 1
    assert config.supervision.gates[0].id == "test-gate"
    assert config.pipeline.flow == ["planner", "coder", "reviewer"]


def test_load_config_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path.yaml")


def test_defaults_applied() -> None:
    config = DevlutionConfig(project=ProjectConfig(name="test"))
    assert config.llm.provider == "anthropic"
    assert config.agents.coder.max_iterations == 3
    assert config.agents.tester.coverage_threshold == 80
    assert config.supervision.audit_log == ".devlution/audit.jsonl"


def test_invalid_language() -> None:
    with pytest.raises(Exception):
        DevlutionConfig(
            project=ProjectConfig(name="bad", language="ruby")  # type: ignore[arg-type]
        )

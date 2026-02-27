"""Pydantic v2 configuration models for devlution.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    name: str
    language: Literal["python", "typescript", "go", "java"] = "python"
    test_command: str = "pytest"
    lint_command: str = "ruff check ."
    main_branch: str = "main"


class LLMConfig(BaseModel):
    provider: Literal["anthropic", "openai"] = "anthropic"
    model: str = "claude-sonnet-4-20250514"
    fallback_model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 8192
    temperature: float = 0.2


class PlannerAgentConfig(BaseModel):
    enabled: bool = True
    max_subtasks: int = 10


class CoderAgentConfig(BaseModel):
    enabled: bool = True
    max_iterations: int = 3
    style_guide: str = ".cursor/rules"


class ReviewerAgentConfig(BaseModel):
    enabled: bool = True
    auto_approve_threshold: float = 0.92
    block_on: list[str] = Field(default_factory=lambda: ["security", "data_loss"])


class TesterAgentConfig(BaseModel):
    enabled: bool = True
    frameworks: list[str] = Field(default_factory=lambda: ["pytest"])
    coverage_threshold: int = 80
    generate_on: list[str] = Field(
        default_factory=lambda: ["new_file", "modified_function"]
    )


class DebuggerAgentConfig(BaseModel):
    enabled: bool = True
    max_fix_attempts: int = 3
    sources: list[str] = Field(
        default_factory=lambda: ["ci_logs", "sentry", "test_output"]
    )


class AgentsConfig(BaseModel):
    planner: PlannerAgentConfig = Field(default_factory=PlannerAgentConfig)
    coder: CoderAgentConfig = Field(default_factory=CoderAgentConfig)
    reviewer: ReviewerAgentConfig = Field(default_factory=ReviewerAgentConfig)
    tester: TesterAgentConfig = Field(default_factory=TesterAgentConfig)
    debugger: DebuggerAgentConfig = Field(default_factory=DebuggerAgentConfig)


class GateConfig(BaseModel):
    id: str
    trigger: str
    type: Literal["human_approval", "confidence_gate", "time_gate", "branch_gate"] = (
        "human_approval"
    )
    notify: list[str] = Field(default_factory=list)
    timeout_hours: int = 24
    on_timeout: Literal["block", "auto_approve", "escalate"] = "block"
    threshold: float | None = None
    required_approvers: int = 0


class SupervisionConfig(BaseModel):
    gates: list[GateConfig] = Field(default_factory=list)
    audit_log: str = ".devlution/audit.jsonl"


class GitHubLabelsConfig(BaseModel):
    ai_generated: str = "ai-generated"
    needs_review: str = "needs-review"


class GitHubIntegrationConfig(BaseModel):
    enabled: bool = True
    auto_label_prs: bool = True
    pr_template: str = ".github/pull_request_template.md"
    labels: GitHubLabelsConfig = Field(default_factory=GitHubLabelsConfig)


class SentryConfig(BaseModel):
    enabled: bool = False
    project_slug: str = ""
    auto_create_issues: bool = True


class SlackConfig(BaseModel):
    enabled: bool = False
    channel: str = "#dev-pipeline"


class JiraConfig(BaseModel):
    enabled: bool = False


class IntegrationsConfig(BaseModel):
    github: GitHubIntegrationConfig = Field(default_factory=GitHubIntegrationConfig)
    sentry: SentryConfig = Field(default_factory=SentryConfig)
    slack: SlackConfig = Field(default_factory=SlackConfig)
    jira: JiraConfig = Field(default_factory=JiraConfig)


class TriggerConfig(BaseModel):
    on: str
    label: str | None = None
    cron: str | None = None
    flow: list[str] = Field(default_factory=list)


class PipelineConfig(BaseModel):
    flow: list[str] = Field(default_factory=list)
    triggers: list[TriggerConfig] = Field(default_factory=list)


class DevlutionConfig(BaseModel):
    """Top-level configuration validated from devlution.yaml."""

    project: ProjectConfig
    llm: LLMConfig = Field(default_factory=LLMConfig)
    agents: AgentsConfig = Field(default_factory=AgentsConfig)
    supervision: SupervisionConfig = Field(default_factory=SupervisionConfig)
    integrations: IntegrationsConfig = Field(default_factory=IntegrationsConfig)
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)


def load_config(path: Path | str = "devlution.yaml") -> DevlutionConfig:
    """Read a YAML config file and return a validated DevlutionConfig."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path) as f:
        raw: dict[str, Any] = yaml.safe_load(f)

    return DevlutionConfig.model_validate(raw)

"""Pipeline state and supporting types used throughout the orchestration layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class PipelineStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_FOR_HUMAN = "waiting_for_human"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


@dataclass
class TriggerEvent:
    type: str  # github_issue | ci_failure | sentry_alert | schedule | manual
    source: str = ""
    issue_number: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Task:
    id: str
    title: str
    files_likely_affected: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    estimated_complexity: str = "medium"  # low | medium | high
    dependencies: list[str] = field(default_factory=list)


@dataclass
class ReviewComment:
    file: str
    line: int
    severity: str  # warning | blocking
    body: str


@dataclass
class TestResult:
    passed: bool
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    coverage_percent: float = 0.0
    output: str = ""
    failure_log: str = ""


@dataclass
class GateDecision:
    gate_id: str
    decision: str  # approved | rejected | timeout
    approver: str = ""
    method: str = ""  # slack | github | cli
    timestamp: datetime = field(default_factory=datetime.utcnow)
    reason: str = ""


@dataclass
class AuditEntry:
    ts: datetime
    pipeline_id: str
    agent: str
    action: str
    details: dict[str, Any] = field(default_factory=dict)
    tokens_used: int | None = None
    confidence: float | None = None
    duration_ms: int | None = None


@dataclass
class PipelineState:
    """Full mutable state passed through the LangGraph pipeline."""

    pipeline_id: str
    trigger: TriggerEvent
    tasks: list[Task] = field(default_factory=list)
    current_task_idx: int = 0
    iterations: dict[str, int] = field(default_factory=dict)
    confidence_scores: dict[str, float] = field(default_factory=dict)
    review_comments: list[ReviewComment] = field(default_factory=list)
    review_decision: str = ""  # approve | request_changes | escalate_to_human
    test_results: TestResult | None = None
    patch: str = ""
    pr_url: str = ""
    gate_decisions: dict[str, GateDecision] = field(default_factory=dict)
    audit_entries: list[AuditEntry] = field(default_factory=list)
    status: PipelineStatus = PipelineStatus.PENDING
    error: str = ""

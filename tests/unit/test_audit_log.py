"""Tests for devlution.supervision.audit_log — JSONL audit logger."""

from pathlib import Path

import pytest

from devlution.supervision.audit_log import AuditLogger


@pytest.fixture
def audit(tmp_path: Path) -> AuditLogger:
    return AuditLogger(tmp_path / "test_audit.jsonl")


def test_record_and_read(audit: AuditLogger) -> None:
    audit.record("p1", "coder", "write_file", details={"file": "test.py"})
    audit.record("p1", "reviewer", "decision", confidence=0.91)

    entries = audit.read()
    assert len(entries) == 2
    assert entries[0]["agent"] == "coder"
    assert entries[1]["confidence"] == 0.91


def test_filter_by_pipeline(audit: AuditLogger) -> None:
    audit.record("p1", "coder", "write_file")
    audit.record("p2", "tester", "run_tests")
    audit.record("p1", "reviewer", "decision")

    entries = audit.read(pipeline_id="p1")
    assert len(entries) == 2
    assert all(e["pipeline_id"] == "p1" for e in entries)


def test_last_n(audit: AuditLogger) -> None:
    for i in range(10):
        audit.record("p1", "agent", f"action_{i}")

    entries = audit.read(last_n=3)
    assert len(entries) == 3
    assert entries[0]["action"] == "action_7"


def test_read_empty(audit: AuditLogger) -> None:
    entries = audit.read()
    assert entries == []


def test_clear(audit: AuditLogger) -> None:
    audit.record("p1", "test", "action")
    assert len(audit.read()) == 1

    audit.clear()
    assert len(audit.read()) == 0


def test_entry_has_timestamp(audit: AuditLogger) -> None:
    entry = audit.record("p1", "test", "action")
    assert "ts" in entry
    assert entry["pipeline_id"] == "p1"


def test_optional_fields(audit: AuditLogger) -> None:
    audit.record("p1", "test", "action", tokens_used=500, duration_ms=1200)
    entries = audit.read()
    assert entries[0]["tokens_used"] == 500
    assert entries[0]["duration_ms"] == 1200

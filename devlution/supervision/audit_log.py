"""Append-only JSONL audit logger for pipeline actions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AuditLogger:
    """Writes and reads structured audit entries to a JSONL file."""

    def __init__(self, path: str | Path = ".devlution/audit.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        pipeline_id: str,
        agent: str,
        action: str,
        details: dict[str, Any] | None = None,
        tokens_used: int | None = None,
        confidence: float | None = None,
        duration_ms: int | None = None,
    ) -> dict[str, Any]:
        """Append a single audit entry and return it."""
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "pipeline_id": pipeline_id,
            "agent": agent,
            "action": action,
            "details": details or {},
        }
        if tokens_used is not None:
            entry["tokens_used"] = tokens_used
        if confidence is not None:
            entry["confidence"] = confidence
        if duration_ms is not None:
            entry["duration_ms"] = duration_ms

        with open(self.path, "a") as f:
            f.write(json.dumps(entry) + "\n")

        return entry

    def read(
        self,
        last_n: int | None = None,
        pipeline_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Read audit entries, optionally filtering by pipeline or limiting count."""
        if not self.path.exists():
            return []

        entries: list[dict[str, Any]] = []
        with open(self.path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                if pipeline_id and entry.get("pipeline_id") != pipeline_id:
                    continue
                entries.append(entry)

        if last_n is not None:
            entries = entries[-last_n:]

        return entries

    def clear(self) -> None:
        """Remove the audit file (for testing)."""
        if self.path.exists():
            self.path.unlink()

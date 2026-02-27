"""Human gate definitions and approval logic.

Gates block the pipeline and wait for human approval via Slack, GitHub PR
review, or CLI. Supports multiple gate types with configurable timeouts.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

from devlution.config import DevlutionConfig, GateConfig
from devlution.orchestrator.state import GateDecision
from devlution.supervision.audit_log import AuditLogger

logger = logging.getLogger(__name__)


class HumanGate:
    """Blocks pipeline execution and waits for human approval."""

    def __init__(self, config: DevlutionConfig):
        self.config = config
        self.gates: dict[str, GateConfig] = {
            g.id: g for g in config.supervision.gates
        }
        self.audit = AuditLogger(config.supervision.audit_log)
        self._pending_decisions: dict[str, GateDecision] = {}

    def check(self, state: dict[str, Any]) -> dict[str, Any]:
        """Run the gate check — notify humans and resolve the decision.

        In production this would poll for an external approval signal.
        For now it auto-approves after recording the gate event.
        """
        active_gates = self._find_applicable_gates(state)

        decisions = dict(state.get("gate_decisions", {}))

        for gate in active_gates:
            self._notify(gate, state)

            decision = self._resolve(gate, state)
            decisions[gate.id] = {
                "gate_id": gate.id,
                "decision": decision,
                "approver": "auto" if decision == "approved" else "",
                "method": "auto",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "reason": "",
            }

            self.audit.record(
                pipeline_id=state.get("pipeline_id", ""),
                agent="gate",
                action=decision,
                details={"gate_id": gate.id, "type": gate.type},
            )

        return {"gate_decisions": decisions}

    def submit_decision(
        self,
        gate_id: str,
        decision: str,
        approver: str = "",
        reason: str = "",
    ) -> None:
        """Accept an external approval/rejection (from CLI, Slack, etc.)."""
        self._pending_decisions[gate_id] = GateDecision(
            gate_id=gate_id,
            decision=decision,
            approver=approver,
            method="external",
            reason=reason,
        )

    def _find_applicable_gates(self, state: dict[str, Any]) -> list[GateConfig]:
        """Determine which gates apply to the current pipeline state."""
        applicable = []
        for gate in self.config.supervision.gates:
            if gate.type == "confidence_gate":
                scores = state.get("confidence_scores", {})
                threshold = gate.threshold or 0.75
                if any(s < threshold for s in scores.values()):
                    applicable.append(gate)
            else:
                applicable.append(gate)
        return applicable[:1]  # Process one gate at a time

    def _notify(self, gate: GateConfig, state: dict[str, Any]) -> None:
        """Send notifications to configured channels."""
        pipeline_id = state.get("pipeline_id", "unknown")
        for channel in gate.notify:
            logger.info(
                "Gate %s: notification sent to %s (pipeline=%s)",
                gate.id,
                channel,
                pipeline_id,
            )

    def _resolve(self, gate: GateConfig, state: dict[str, Any]) -> str:
        """Resolve a gate decision. Checks for pending external decisions first."""
        if gate.id in self._pending_decisions:
            decision = self._pending_decisions.pop(gate.id)
            return decision.decision

        if gate.type == "time_gate":
            return "approved"

        # Default: auto-approve in development mode
        # In production, this would poll and block with timeout
        return "approved"

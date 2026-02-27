"""Human gate checkpoint logic and notification dispatch.

This module bridges the gate node in the pipeline graph with the supervision
layer, handling approval polling and notification routing.
"""

from __future__ import annotations

import logging
from typing import Any

from devlution.config import DevlutionConfig, GateConfig
from devlution.supervision.audit_log import AuditLogger

logger = logging.getLogger(__name__)


class CheckpointManager:
    """Manages human gate checkpoints within the pipeline."""

    def __init__(self, config: DevlutionConfig):
        self.config = config
        self.gates: dict[str, GateConfig] = {
            g.id: g for g in config.supervision.gates
        }
        self.audit = AuditLogger(config.supervision.audit_log)

    def get_gate(self, gate_id: str) -> GateConfig | None:
        return self.gates.get(gate_id)

    def should_block(self, gate_id: str, confidence: float | None = None) -> bool:
        """Determine if the pipeline should block at this gate."""
        gate = self.get_gate(gate_id)
        if gate is None:
            return False

        if gate.type == "confidence_gate" and confidence is not None:
            threshold = gate.threshold or 0.75
            return confidence < threshold

        return gate.type == "human_approval"

    def record_decision(
        self,
        gate_id: str,
        decision: str,
        approver: str = "",
        method: str = "cli",
        pipeline_id: str = "",
    ) -> dict[str, Any]:
        """Record a gate decision to the audit log."""
        entry = self.audit.record(
            pipeline_id=pipeline_id,
            agent="gate",
            action=decision,
            details={
                "gate_id": gate_id,
                "approver": approver,
                "method": method,
            },
        )
        logger.info("Gate %s: %s by %s via %s", gate_id, decision, approver, method)
        return entry

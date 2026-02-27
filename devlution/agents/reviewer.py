"""Reviewer Agent — evaluates code diffs against a quality rubric."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from devlution.agents.base import AgentInput, AgentOutput, BaseAgent
from devlution.orchestrator.state import ReviewComment

logger = logging.getLogger(__name__)

REVIEW_RUBRIC = {
    "correctness": "Does it solve the task without logic errors?",
    "security": "No vulnerabilities, secrets, or unsafe operations?",
    "style": "Matches existing codebase patterns and conventions?",
    "test_coverage": "Adequate tests added or updated?",
    "side_effects": "No regressions or broken existing behavior?",
}


class ReviewerAgent(BaseAgent):
    agent_name = "reviewer"

    def run(self, agent_input: AgentInput) -> AgentOutput:
        start = time.time()
        system_prompt = self.load_prompt()

        diff_text = agent_input.get("diff", "")
        task_title = agent_input.get("task_title", "")

        user_message = (
            f"## Task\n{task_title}\n\n"
            f"## Diff to Review\n```diff\n{diff_text[:8000]}\n```\n\n"
            f"Auto-approve threshold: {self.config.agents.reviewer.auto_approve_threshold}\n"
            f"Block on: {', '.join(self.config.agents.reviewer.block_on)}\n\n"
            "Review this diff and return your structured assessment."
        )

        try:
            response = self.call_llm(
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

            text = response.content[0].text if response.content else "{}"
            review = self._parse_review(text)

            confidence = review.get("confidence", 0.0)
            decision = review.get("decision", "escalate_to_human")

            threshold = self.config.agents.reviewer.auto_approve_threshold
            if confidence < threshold and decision == "approve":
                decision = "escalate_to_human"

            comments = [
                ReviewComment(
                    file=c.get("file", ""),
                    line=c.get("line", 0),
                    severity=c.get("severity", "warning"),
                    body=c.get("body", ""),
                )
                for c in review.get("comments", [])
            ]

            duration_ms = int((time.time() - start) * 1000)
            self._record_audit(
                "review_complete",
                details={
                    "decision": decision,
                    "comment_count": len(comments),
                    "scores": review.get("scores", {}),
                },
                confidence=confidence,
                duration_ms=duration_ms,
            )

            return AgentOutput(
                success=True,
                data={
                    "decision": decision,
                    "comments": [c.__dict__ for c in comments],
                    "scores": review.get("scores", {}),
                    "summary": review.get("summary", ""),
                },
                confidence=confidence,
                escalate=decision == "escalate_to_human",
            )

        except Exception as e:
            logger.error("Reviewer failed: %s", e)
            return AgentOutput(
                success=False, error=str(e), confidence=0.0, escalate=True
            )

    def _parse_review(self, text: str) -> dict[str, Any]:
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            return json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            return {
                "decision": "escalate_to_human",
                "confidence": 0.3,
                "comments": [],
                "summary": "Failed to parse review output",
            }

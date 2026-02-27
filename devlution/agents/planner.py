"""Planner Agent — decomposes a GitHub issue into structured tasks."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from devlution.agents.base import AgentInput, AgentOutput, BaseAgent
from devlution.config import DevlutionConfig
from devlution.orchestrator.state import PipelineState, Task

logger = logging.getLogger(__name__)

PLANNING_RUBRIC = {
    "completeness": "Does the plan cover all aspects of the issue?",
    "clarity": "Are tasks clearly defined with actionable acceptance criteria?",
    "scoping": "Are file hints accurate and task complexity estimates reasonable?",
    "independence": "Can each task be implemented independently?",
}


class PlannerAgent(BaseAgent):
    agent_name = "planner"

    def run(self, agent_input: AgentInput) -> AgentOutput:
        start = time.time()
        system_prompt = self.load_prompt()

        issue_title = agent_input.get("title", "")
        issue_body = agent_input.get("body", "")
        issue_labels = agent_input.get("labels", [])

        user_message = (
            f"## Issue\n**Title**: {issue_title}\n\n"
            f"**Body**:\n{issue_body}\n\n"
            f"**Labels**: {', '.join(issue_labels) if issue_labels else 'none'}\n\n"
            f"Maximum subtasks: {self.config.agents.planner.max_subtasks}\n\n"
            "Analyze this issue and produce a structured task breakdown."
        )

        try:
            response = self.call_llm(
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

            text = response.content[0].text if response.content else "{}"
            plan = self._parse_plan(text)

            tasks = [
                Task(
                    id=t.get("id", f"T{i+1}"),
                    title=t.get("title", ""),
                    files_likely_affected=t.get("files_likely_affected", []),
                    acceptance_criteria=t.get("acceptance_criteria", []),
                    estimated_complexity=t.get("estimated_complexity", "medium"),
                    dependencies=t.get("dependencies", []),
                )
                for i, t in enumerate(plan.get("tasks", []))
            ]

            confidence = plan.get("confidence", 0.0)

            if confidence < 0.5:
                confidence = self.score_confidence(text, PLANNING_RUBRIC)

            duration_ms = int((time.time() - start) * 1000)
            self._record_audit(
                "plan_complete",
                details={"task_count": len(tasks), "blockers": plan.get("blockers", [])},
                confidence=confidence,
                duration_ms=duration_ms,
            )

            return AgentOutput(
                success=True,
                data={
                    "tasks": [t.__dict__ for t in tasks],
                    "blockers": plan.get("blockers", []),
                },
                confidence=confidence,
                escalate=confidence < 0.5,
            )

        except Exception as e:
            logger.error("Planner failed: %s", e)
            return AgentOutput(success=False, error=str(e), confidence=0.0, escalate=True)

    def _parse_plan(self, text: str) -> dict[str, Any]:
        """Extract JSON plan from LLM response text."""
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            return json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            logger.warning("Failed to parse planner JSON, attempting line-by-line")
            for line in text.split("\n"):
                line = line.strip()
                if line.startswith("{"):
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        continue
            return {"tasks": [], "confidence": 0.0, "blockers": ["Failed to parse LLM output"]}

"""Debugger Agent — root cause analysis and minimal fixes for failures."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from devlution.agents.base import AgentInput, AgentOutput, BaseAgent
from devlution.tools import file_editor
from devlution.tools.code_executor import run_tests

logger = logging.getLogger(__name__)

DEBUGGER_RUBRIC = {
    "diagnosis": "Is the root cause correctly identified?",
    "fix_quality": "Is the fix minimal and correct?",
    "verification": "Was the fix verified against the failing test?",
    "safety": "Does the fix avoid introducing new issues?",
}


class DebuggerAgent(BaseAgent):
    agent_name = "debugger"

    def run(self, agent_input: AgentInput) -> AgentOutput:
        start = time.time()
        system_prompt = self.load_prompt()

        failure_log = agent_input.get("failure_log", "")
        source_files = agent_input.get("source_files", [])
        attempt = self.state.iterations.get("debugger", 0) + 1

        max_attempts = self.config.agents.debugger.max_fix_attempts

        file_contents: dict[str, str] = {}
        for fpath in source_files:
            try:
                file_contents[fpath] = file_editor.read_file(fpath)
            except FileNotFoundError:
                continue

        context_parts = [
            f"## Failure Log\n```\n{failure_log[:6000]}\n```",
            f"## Fix attempt: {attempt} of {max_attempts}",
        ]

        for fpath, content in file_contents.items():
            context_parts.append(f"## Source: {fpath}\n```\n{content[:4000]}\n```")

        user_message = "\n\n".join(context_parts)
        user_message += (
            "\n\nFollow the chain-of-thought protocol: parse error, identify path, "
            "hypothesize top 3 causes, generate minimal fix, verify."
        )

        try:
            response = self.call_llm(
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

            text = response.content[0].text if response.content else "{}"
            analysis = self._parse_response(text)

            self.state.iterations["debugger"] = attempt
            confidence = analysis.get("confidence", 0.0)

            should_escalate = attempt >= max_attempts and not analysis.get("verified", False)

            duration_ms = int((time.time() - start) * 1000)
            self._record_audit(
                "debug_complete",
                details={
                    "error_type": analysis.get("error_type", "unknown"),
                    "root_cause": analysis.get("root_cause", ""),
                    "attempt": attempt,
                    "verified": analysis.get("verified", False),
                },
                confidence=confidence,
                duration_ms=duration_ms,
            )

            return AgentOutput(
                success=analysis.get("verified", False),
                data=analysis,
                confidence=confidence,
                escalate=should_escalate,
            )

        except Exception as e:
            logger.error("Debugger failed: %s", e)
            self.state.iterations["debugger"] = attempt
            return AgentOutput(
                success=False,
                error=str(e),
                confidence=0.0,
                escalate=attempt >= max_attempts,
            )

    def _parse_response(self, text: str) -> dict[str, Any]:
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            return json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            return {
                "error_type": "unknown",
                "root_cause": "Failed to parse debugger output",
                "hypotheses": [],
                "verified": False,
                "confidence": 0.2,
            }

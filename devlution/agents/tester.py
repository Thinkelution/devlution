"""Tester Agent — generates and runs tests for code changes."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from devlution.agents.base import AgentInput, AgentOutput, BaseAgent
from devlution.orchestrator.state import TestResult
from devlution.tools.code_executor import run_tests

logger = logging.getLogger(__name__)

TESTER_RUBRIC = {
    "coverage": "Do the tests cover the changed code paths?",
    "edge_cases": "Are edge cases and error paths tested?",
    "clarity": "Are test names and assertions clear?",
    "isolation": "Are tests independent and not order-dependent?",
}


class TesterAgent(BaseAgent):
    agent_name = "tester"

    def run(self, agent_input: AgentInput) -> AgentOutput:
        start = time.time()
        system_prompt = self.load_prompt()

        changed_files = agent_input.get("changed_files", [])
        task_title = agent_input.get("task_title", "")

        user_message = (
            f"## Task\n{task_title}\n\n"
            f"## Changed Files\n" + "\n".join(f"- {f}" for f in changed_files) + "\n\n"
            f"Test framework: {', '.join(self.config.agents.tester.frameworks)}\n"
            f"Coverage threshold: {self.config.agents.tester.coverage_threshold}%\n"
            f"Generate on: {', '.join(self.config.agents.tester.generate_on)}\n\n"
            "Generate targeted tests for the changed code and return the result."
        )

        try:
            response = self.call_llm(
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

            text = response.content[0].text if response.content else "{}"
            result = self._parse_response(text)

            test_command = self.config.project.test_command
            exec_result = run_tests(test_command)

            test_output = TestResult(
                passed=exec_result.success,
                total_tests=result.get("test_results", {}).get("total_tests", 0),
                passed_tests=result.get("test_results", {}).get("passed_tests", 0),
                failed_tests=result.get("test_results", {}).get("failed_tests", 0),
                coverage_percent=result.get("test_results", {}).get("coverage_percent", 0.0),
                output=exec_result.stdout[:5000],
                failure_log=exec_result.stderr[:5000] if not exec_result.success else "",
            )

            confidence = result.get("confidence", 0.0)
            threshold = self.config.agents.tester.coverage_threshold
            if test_output.coverage_percent < threshold:
                confidence = min(confidence, test_output.coverage_percent / 100.0)

            duration_ms = int((time.time() - start) * 1000)
            self._record_audit(
                "test_complete",
                details={
                    "passed": test_output.passed,
                    "total": test_output.total_tests,
                    "coverage": test_output.coverage_percent,
                },
                confidence=confidence,
                duration_ms=duration_ms,
            )

            return AgentOutput(
                success=test_output.passed,
                data={
                    "test_results": test_output.__dict__,
                    "tests_written": result.get("tests_written", []),
                },
                confidence=confidence,
            )

        except Exception as e:
            logger.error("Tester failed: %s", e)
            return AgentOutput(success=False, error=str(e), confidence=0.0)

    def _parse_response(self, text: str) -> dict[str, Any]:
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            return json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            return {"tests_written": [], "confidence": 0.3}

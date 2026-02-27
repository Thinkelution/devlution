"""Coder Agent — implements code changes for a single task."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from devlution.agents.base import AgentInput, AgentOutput, BaseAgent
from devlution.tools import file_editor, git_ops
from devlution.tools.code_executor import run_command

logger = logging.getLogger(__name__)

CODER_RUBRIC = {
    "correctness": "Does the code implement the task requirements?",
    "style": "Does it follow existing codebase conventions?",
    "completeness": "Are all acceptance criteria addressed?",
    "minimality": "Are changes focused without unnecessary modifications?",
}


class CoderAgent(BaseAgent):
    agent_name = "coder"

    def run(self, agent_input: AgentInput) -> AgentOutput:
        start = time.time()
        system_prompt = self.load_prompt()

        task_title = agent_input.get("title", "")
        task_criteria = agent_input.get("acceptance_criteria", [])
        affected_files = agent_input.get("files_likely_affected", [])
        review_comments = agent_input.get("review_comments", [])

        file_contents: dict[str, str] = {}
        for fpath in affected_files:
            try:
                file_contents[fpath] = file_editor.read_file(fpath)
            except FileNotFoundError:
                file_contents[fpath] = "(new file — does not exist yet)"

        style_guide = self._load_style_guide()

        context_parts = [
            f"## Task\n**Title**: {task_title}",
            f"**Acceptance Criteria**:\n" + "\n".join(f"- {c}" for c in task_criteria),
            f"**Files to modify**: {', '.join(affected_files)}",
        ]

        if style_guide:
            context_parts.append(f"## Style Guide\n{style_guide[:2000]}")

        if file_contents:
            for fpath, content in file_contents.items():
                context_parts.append(f"## File: {fpath}\n```\n{content[:4000]}\n```")

        if review_comments:
            context_parts.append(
                "## Review Comments (from previous iteration)\n"
                + "\n".join(f"- {c}" for c in review_comments)
            )

        user_message = "\n\n".join(context_parts)
        user_message += "\n\nImplement the required changes. Return JSON with your changes."

        max_iterations = self.config.agents.coder.max_iterations
        iteration = self.state.iterations.get("coder", 0)

        try:
            response = self.call_llm(
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

            text = response.content[0].text if response.content else "{}"
            result = self._parse_response(text)
            confidence = result.get("confidence", 0.0)

            if confidence < 0.5:
                confidence = self.score_confidence(text, CODER_RUBRIC)

            self.state.iterations["coder"] = iteration + 1

            duration_ms = int((time.time() - start) * 1000)
            self._record_audit(
                "code_complete",
                details={
                    "files_modified": result.get("files_modified", []),
                    "iteration": iteration + 1,
                },
                confidence=confidence,
                duration_ms=duration_ms,
            )

            return AgentOutput(
                success=True,
                data=result,
                confidence=confidence,
                escalate=iteration + 1 >= max_iterations and confidence < 0.75,
            )

        except Exception as e:
            logger.error("Coder failed: %s", e)
            return AgentOutput(success=False, error=str(e), confidence=0.0)

    def _load_style_guide(self) -> str:
        """Try to load the project's style guide."""
        guide_path = self.config.agents.coder.style_guide
        for candidate in [guide_path, "CLAUDE.md", ".cursorrules"]:
            try:
                return file_editor.read_file(candidate)
            except FileNotFoundError:
                continue
        return ""

    def _parse_response(self, text: str) -> dict[str, Any]:
        """Extract JSON from the coder's LLM response."""
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            return json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            return {
                "files_modified": [],
                "summary": text[:200],
                "confidence": 0.3,
            }

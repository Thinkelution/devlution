"""BaseAgent — foundation class for all Devlution agents.

Every agent subclasses BaseAgent and implements `run()`. All LLM interactions,
logging, confidence scoring, and escalation flow through this base class.
"""

from __future__ import annotations

import logging
import time
from importlib import resources
from pathlib import Path
from typing import Any

import anthropic

from devlution.config import DevlutionConfig, LLMConfig
from devlution.orchestrator.state import AuditEntry, PipelineState
from devlution.supervision.audit_log import AuditLogger
from devlution.supervision.confidence import (
    CONFIDENCE_RUBRIC_PROMPT,
    build_confidence_prompt,
    parse_confidence_response,
)

logger = logging.getLogger(__name__)


class EscalationEvent:
    """Returned when an agent decides to escalate to a human."""

    def __init__(self, agent: str, reason: str, pipeline_id: str):
        self.agent = agent
        self.reason = reason
        self.pipeline_id = pipeline_id


class AgentInput:
    """Generic input wrapper for agent `run()` methods."""

    def __init__(self, **kwargs: Any):
        self.__dict__.update(kwargs)

    def get(self, key: str, default: Any = None) -> Any:
        return self.__dict__.get(key, default)


class AgentOutput:
    """Generic output wrapper from agent `run()` methods."""

    def __init__(
        self,
        success: bool = True,
        data: dict[str, Any] | None = None,
        confidence: float = 0.0,
        escalate: bool = False,
        error: str = "",
    ):
        self.success = success
        self.data = data or {}
        self.confidence = confidence
        self.escalate = escalate
        self.error = error


class BaseAgent:
    """Foundation for all pipeline agents.

    Subclasses must set `agent_name` and implement `run()`.
    """

    agent_name: str = "base"

    def __init__(self, config: DevlutionConfig, state: PipelineState):
        self.config = config
        self.state = state
        self.llm_config: LLMConfig = config.llm
        self.audit = AuditLogger(config.supervision.audit_log)
        self._client: anthropic.Anthropic | None = None

    @property
    def client(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic()
        return self._client

    def run(self, agent_input: AgentInput) -> AgentOutput:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement run()"
        )

    def load_prompt(self) -> str:
        """Load the system prompt for this agent.

        Looks for a user override at `.devlution/prompts/{agent_name}.md`
        first, then falls back to the bundled template.
        """
        user_override = Path(f".devlution/prompts/{self.agent_name}.md")
        if user_override.exists():
            return user_override.read_text()

        try:
            templates_pkg = resources.files("devlution.templates.prompts")
            prompt_file = templates_pkg / f"{self.agent_name}.md"
            return prompt_file.read_text()  # type: ignore[union-attr]
        except (FileNotFoundError, TypeError):
            return f"You are the {self.agent_name} agent in the Devlution pipeline."

    def call_llm(
        self,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
    ) -> anthropic.types.Message:
        """Call the Anthropic API with retry, logging, and token tracking."""
        model = model or self.llm_config.model
        max_tokens = max_tokens or self.llm_config.max_tokens

        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        start = time.time()
        last_error: Exception | None = None

        for attempt in range(3):
            try:
                response = self.client.messages.create(**kwargs)
                duration_ms = int((time.time() - start) * 1000)

                tokens = (
                    response.usage.input_tokens + response.usage.output_tokens
                    if response.usage
                    else 0
                )

                self.audit.record(
                    pipeline_id=self.state.pipeline_id,
                    agent=self.agent_name,
                    action="llm_call",
                    details={"model": model, "attempt": attempt + 1},
                    tokens_used=tokens,
                    duration_ms=duration_ms,
                )

                return response

            except anthropic.RateLimitError:
                wait = 2 ** (attempt + 1)
                logger.warning(
                    "Rate limited on attempt %d, retrying in %ds", attempt + 1, wait
                )
                time.sleep(wait)
                last_error = anthropic.RateLimitError.__class__()  # type: ignore[assignment]
            except anthropic.APIError as e:
                last_error = e
                logger.error("API error on attempt %d: %s", attempt + 1, e)
                if attempt < 2:
                    time.sleep(1)

        raise RuntimeError(
            f"LLM call failed after 3 attempts: {last_error}"
        )

    def score_confidence(self, output: str, rubric: dict[str, str]) -> float:
        """Ask the LLM to self-score an output against a rubric."""
        try:
            messages = build_confidence_prompt(output, rubric)
            response = self.call_llm(
                system=CONFIDENCE_RUBRIC_PROMPT,
                messages=messages,
                model=self.llm_config.fallback_model,
                max_tokens=512,
            )
            text = response.content[0].text if response.content else ""
            score = parse_confidence_response(text)

            self.audit.record(
                pipeline_id=self.state.pipeline_id,
                agent=self.agent_name,
                action="confidence_score",
                confidence=score,
                details={"rubric_keys": list(rubric.keys())},
            )

            return score
        except Exception as e:
            logger.warning("Confidence scoring failed: %s", e)
            return 0.5

    def escalate(self, reason: str) -> EscalationEvent:
        """Log an escalation event and mark the pipeline as waiting for human."""
        from devlution.orchestrator.state import PipelineStatus

        event = EscalationEvent(
            agent=self.agent_name,
            reason=reason,
            pipeline_id=self.state.pipeline_id,
        )

        self.state.status = PipelineStatus.WAITING_FOR_HUMAN

        self.audit.record(
            pipeline_id=self.state.pipeline_id,
            agent=self.agent_name,
            action="escalate",
            details={"reason": reason},
        )

        logger.info(
            "[%s] Escalated: %s (pipeline=%s)",
            self.agent_name,
            reason,
            self.state.pipeline_id,
        )

        return event

    def _record_audit(
        self,
        action: str,
        details: dict[str, Any] | None = None,
        confidence: float | None = None,
        duration_ms: int | None = None,
    ) -> None:
        """Convenience wrapper for audit logging."""
        self.audit.record(
            pipeline_id=self.state.pipeline_id,
            agent=self.agent_name,
            action=action,
            details=details,
            confidence=confidence,
            duration_ms=duration_ms,
        )

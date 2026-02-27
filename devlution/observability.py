"""Langfuse observability integration for LLM call tracing.

Wraps BaseAgent.call_llm() to emit generation spans with model, tokens,
and latency. Gracefully degrades to no-op when Langfuse is not configured.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any, Generator

logger = logging.getLogger(__name__)

_langfuse_client = None
_enabled: bool | None = None


def is_enabled() -> bool:
    """Check if Langfuse is configured and available."""
    global _enabled
    if _enabled is not None:
        return _enabled

    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "")
    _enabled = bool(public_key and secret_key)

    if not _enabled:
        logger.debug("Langfuse not configured — observability disabled")

    return _enabled


def get_client():
    """Get or create the Langfuse client."""
    global _langfuse_client
    if _langfuse_client is None and is_enabled():
        try:
            from langfuse import Langfuse
            _langfuse_client = Langfuse()
            logger.info("Langfuse client initialized")
        except Exception as e:
            logger.warning("Failed to initialize Langfuse: %s", e)
    return _langfuse_client


@contextmanager
def trace_pipeline(pipeline_id: str, trigger_type: str = "") -> Generator[Any, None, None]:
    """Create a Langfuse trace for a pipeline run."""
    client = get_client()
    if client is None:
        yield None
        return

    try:
        trace = client.trace(
            name=f"devlution-pipeline-{pipeline_id}",
            metadata={"pipeline_id": pipeline_id, "trigger": trigger_type},
        )
        yield trace
    except Exception as e:
        logger.warning("Langfuse trace error: %s", e)
        yield None
    finally:
        if client:
            try:
                client.flush()
            except Exception:
                pass


def record_generation(
    pipeline_id: str,
    agent_name: str,
    model: str,
    input_text: str,
    output_text: str,
    tokens_input: int = 0,
    tokens_output: int = 0,
    duration_ms: int = 0,
    trace: Any = None,
) -> None:
    """Record an LLM generation span in Langfuse."""
    client = get_client()
    if client is None:
        return

    try:
        if trace is not None:
            trace.generation(
                name=f"{agent_name}-llm-call",
                model=model,
                input=input_text[:1000],
                output=output_text[:1000],
                usage={
                    "input": tokens_input,
                    "output": tokens_output,
                    "total": tokens_input + tokens_output,
                },
                metadata={
                    "agent": agent_name,
                    "pipeline_id": pipeline_id,
                    "duration_ms": duration_ms,
                },
            )
        else:
            client.generation(
                name=f"{agent_name}-llm-call",
                model=model,
                input=input_text[:1000],
                output=output_text[:1000],
                usage={
                    "input": tokens_input,
                    "output": tokens_output,
                },
                metadata={
                    "agent": agent_name,
                    "pipeline_id": pipeline_id,
                },
            )
    except Exception as e:
        logger.debug("Langfuse generation recording failed: %s", e)


def flush() -> None:
    """Flush any pending Langfuse events."""
    client = get_client()
    if client:
        try:
            client.flush()
        except Exception:
            pass

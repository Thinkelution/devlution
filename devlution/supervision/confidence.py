"""Confidence scoring utilities used by agents to self-evaluate output quality."""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

CONFIDENCE_RUBRIC_PROMPT = """You are evaluating the quality of an AI agent's output.

Score the output on a scale from 0.0 to 1.0 against each criterion in the rubric.
Return ONLY a JSON object with this exact schema:
{
  "scores": {"<criterion>": <float 0.0-1.0>, ...},
  "overall": <float 0.0-1.0>,
  "reasoning": "<one sentence>"
}
"""


def build_confidence_prompt(output: str, rubric: dict[str, str]) -> list[dict[str, Any]]:
    """Build the messages list for a confidence-scoring LLM call."""
    rubric_text = "\n".join(f"- {k}: {v}" for k, v in rubric.items())
    return [
        {
            "role": "user",
            "content": (
                f"## Rubric\n{rubric_text}\n\n"
                f"## Agent Output\n```\n{output}\n```\n\n"
                "Score this output. Return JSON only."
            ),
        }
    ]


def parse_confidence_response(text: str) -> float:
    """Extract the overall confidence score from an LLM response."""
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        data = json.loads(text[start:end])
        score = float(data.get("overall", 0.0))
        return max(0.0, min(1.0, score))
    except (ValueError, json.JSONDecodeError, TypeError):
        logger.warning("Failed to parse confidence response, defaulting to 0.5")
        return 0.5

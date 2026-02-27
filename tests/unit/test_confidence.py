"""Tests for devlution.supervision.confidence — score parsing utilities."""

from devlution.supervision.confidence import (
    build_confidence_prompt,
    parse_confidence_response,
)


def test_parse_valid_response() -> None:
    text = '{"scores": {"correctness": 0.9}, "overall": 0.88, "reasoning": "Looks good"}'
    assert parse_confidence_response(text) == 0.88


def test_parse_response_with_surrounding_text() -> None:
    text = 'Here is the score:\n{"scores": {}, "overall": 0.72, "reasoning": "ok"}\nDone.'
    assert parse_confidence_response(text) == 0.72


def test_parse_clamps_above_one() -> None:
    text = '{"overall": 1.5}'
    assert parse_confidence_response(text) == 1.0


def test_parse_clamps_below_zero() -> None:
    text = '{"overall": -0.3}'
    assert parse_confidence_response(text) == 0.0


def test_parse_invalid_json_defaults() -> None:
    assert parse_confidence_response("not json at all") == 0.5


def test_build_confidence_prompt_structure() -> None:
    messages = build_confidence_prompt("some output", {"quality": "Is it good?"})
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert "quality" in messages[0]["content"]
    assert "some output" in messages[0]["content"]

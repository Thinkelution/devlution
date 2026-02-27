"""Static analysis wrappers — lint and type-check with structured output.

Wraps common tools (ruff, eslint, mypy, tsc) and parses their output
into structured findings for the Coder Agent's iteration loop.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from devlution.tools.code_executor import ExecutionResult, run_command


@dataclass
class Finding:
    file: str
    line: int
    column: int
    severity: str  # error | warning | info
    code: str
    message: str


@dataclass
class AnalysisResult:
    tool: str
    success: bool
    findings: list[Finding] = field(default_factory=list)
    raw_output: str = ""


def run_lint(lint_command: str, cwd: str = ".") -> AnalysisResult:
    """Run a lint command and parse the output into findings."""
    result = run_command(lint_command, cwd=cwd, timeout=60)
    findings = _parse_lint_output(result)
    return AnalysisResult(
        tool="lint",
        success=result.success,
        findings=findings,
        raw_output=result.stdout + result.stderr,
    )


def run_typecheck(typecheck_command: str, cwd: str = ".") -> AnalysisResult:
    """Run a type checker and parse the output."""
    result = run_command(typecheck_command, cwd=cwd, timeout=120)
    findings = _parse_lint_output(result)
    return AnalysisResult(
        tool="typecheck",
        success=result.success,
        findings=findings,
        raw_output=result.stdout + result.stderr,
    )


# Matches patterns like: file.py:10:5: E501 line too long
_LINT_PATTERN = re.compile(
    r"^(?P<file>[^:]+):(?P<line>\d+):(?P<col>\d+):\s*(?P<code>\S+)\s+(?P<msg>.+)$",
    re.MULTILINE,
)


def _parse_lint_output(result: ExecutionResult) -> list[Finding]:
    """Parse common lint output format into structured findings."""
    findings: list[Finding] = []
    combined = result.stdout + "\n" + result.stderr

    for match in _LINT_PATTERN.finditer(combined):
        code = match.group("code")
        severity = "error" if code.startswith("E") or code.startswith("F") else "warning"
        findings.append(
            Finding(
                file=match.group("file"),
                line=int(match.group("line")),
                column=int(match.group("col")),
                severity=severity,
                code=code,
                message=match.group("msg"),
            )
        )

    return findings

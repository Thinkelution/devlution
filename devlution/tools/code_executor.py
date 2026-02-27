"""Safe subprocess wrapper for running tests and commands.

Provides timeout-bounded execution with captured stdout/stderr,
used primarily by the Tester Agent.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 300  # 5 minutes


@dataclass
class ExecutionResult:
    success: bool
    stdout: str
    stderr: str
    returncode: int
    timed_out: bool = False


def run_command(
    cmd: str | list[str],
    cwd: str = ".",
    timeout: int = DEFAULT_TIMEOUT,
    env: dict[str, str] | None = None,
) -> ExecutionResult:
    """Execute a shell command with timeout and captured output."""
    if isinstance(cmd, str):
        shell = True
        cmd_display = cmd
    else:
        shell = False
        cmd_display = " ".join(cmd)

    logger.info("Executing: %s (cwd=%s, timeout=%ds)", cmd_display, cwd, timeout)

    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        return ExecutionResult(
            success=result.returncode == 0,
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode,
        )
    except subprocess.TimeoutExpired:
        logger.warning("Command timed out after %ds: %s", timeout, cmd_display)
        return ExecutionResult(
            success=False,
            stdout="",
            stderr=f"Command timed out after {timeout}s",
            returncode=-1,
            timed_out=True,
        )
    except FileNotFoundError as e:
        return ExecutionResult(
            success=False,
            stdout="",
            stderr=str(e),
            returncode=-1,
        )


def run_tests(
    test_command: str,
    cwd: str = ".",
    timeout: int = DEFAULT_TIMEOUT,
) -> ExecutionResult:
    """Run the project's test suite."""
    return run_command(test_command, cwd=cwd, timeout=timeout)


def run_lint(
    lint_command: str,
    cwd: str = ".",
    timeout: int = 60,
) -> ExecutionResult:
    """Run the project's linter."""
    return run_command(lint_command, cwd=cwd, timeout=timeout)

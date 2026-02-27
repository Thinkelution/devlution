"""Git operations wrapper using subprocess — branch, commit, push.

All git mutations in the pipeline go through this module for safety,
audit logging, and consistent error handling.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GitResult:
    success: bool
    stdout: str
    stderr: str
    returncode: int


def _run(args: list[str], cwd: str = ".") -> GitResult:
    """Run a git command and return structured output."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return GitResult(
            success=result.returncode == 0,
            stdout=result.stdout.strip(),
            stderr=result.stderr.strip(),
            returncode=result.returncode,
        )
    except subprocess.TimeoutExpired:
        return GitResult(success=False, stdout="", stderr="Git command timed out", returncode=-1)
    except FileNotFoundError:
        return GitResult(success=False, stdout="", stderr="git not found", returncode=-1)


def current_branch(cwd: str = ".") -> str:
    result = _run(["branch", "--show-current"], cwd)
    return result.stdout if result.success else "unknown"


def create_branch(name: str, cwd: str = ".") -> GitResult:
    return _run(["checkout", "-b", name], cwd)


def checkout(branch: str, cwd: str = ".") -> GitResult:
    return _run(["checkout", branch], cwd)


def add_all(cwd: str = ".") -> GitResult:
    return _run(["add", "-A"], cwd)


def commit(message: str, cwd: str = ".") -> GitResult:
    add_result = add_all(cwd)
    if not add_result.success:
        return add_result
    return _run(["commit", "-m", message], cwd)


def diff(staged: bool = False, cwd: str = ".") -> str:
    args = ["diff"]
    if staged:
        args.append("--staged")
    result = _run(args, cwd)
    return result.stdout


def push(remote: str = "origin", branch: str | None = None, cwd: str = ".") -> GitResult:
    args = ["push", remote]
    if branch:
        args.append(branch)
    else:
        args.extend(["--set-upstream", remote, current_branch(cwd)])
    return _run(args, cwd)


def status(cwd: str = ".") -> str:
    result = _run(["status", "--short"], cwd)
    return result.stdout


def log(n: int = 10, cwd: str = ".") -> str:
    result = _run(["log", f"-{n}", "--oneline"], cwd)
    return result.stdout

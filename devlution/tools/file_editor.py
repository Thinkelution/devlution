"""Safe file read/write/patch operations used by the Coder Agent.

All file mutations in the pipeline go through this module rather than
calling open() directly, enabling audit logging and safety checks.
"""

from __future__ import annotations

import difflib
import os
from pathlib import Path


def read_file(path: str, base_dir: str = ".") -> str:
    """Read a file's contents relative to the project root."""
    full = Path(base_dir) / path
    if not full.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return full.read_text()


def write_file(path: str, content: str, base_dir: str = ".") -> str:
    """Write content to a file, creating parent directories if needed."""
    full = Path(base_dir) / path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content)
    return str(full)


def patch_file(path: str, old: str, new: str, base_dir: str = ".") -> bool:
    """Replace a specific string occurrence in a file. Returns True if changed."""
    full = Path(base_dir) / path
    if not full.exists():
        raise FileNotFoundError(f"File not found: {path}")

    content = full.read_text()
    if old not in content:
        return False

    updated = content.replace(old, new, 1)
    full.write_text(updated)
    return True


def list_files(directory: str = ".", extensions: list[str] | None = None) -> list[str]:
    """List files in a directory, optionally filtered by extension."""
    results: list[str] = []
    base = Path(directory)
    for root, _, files in os.walk(base):
        for f in files:
            if extensions and not any(f.endswith(ext) for ext in extensions):
                continue
            rel = os.path.relpath(os.path.join(root, f), base)
            results.append(rel)
    return sorted(results)


def compute_diff(path: str, old_content: str, new_content: str) -> str:
    """Compute a unified diff between old and new content for a file."""
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    diff = difflib.unified_diff(old_lines, new_lines, fromfile=f"a/{path}", tofile=f"b/{path}")
    return "".join(diff)

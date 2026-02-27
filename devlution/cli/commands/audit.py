"""devlution audit — view and filter the pipeline audit log."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.syntax import Syntax

from devlution.supervision.audit_log import AuditLogger

app = typer.Typer()
console = Console()


@app.callback(invoke_without_command=True)
def audit(
    last: int = typer.Option(20, "--last", help="Number of recent entries to show"),
    pipeline_id: str = typer.Option("", help="Filter by pipeline ID"),
    raw: bool = typer.Option(False, "--raw", help="Output raw JSONL"),
    config_path: str = typer.Option("devlution.yaml", "--config", help="Path to devlution.yaml"),
) -> None:
    """View the devlution audit log."""
    try:
        from devlution.config import load_config
        config = load_config(config_path)
        audit_path = config.supervision.audit_log
    except FileNotFoundError:
        audit_path = ".devlution/audit.jsonl"

    logger = AuditLogger(audit_path)
    entries = logger.read(last_n=last, pipeline_id=pipeline_id or None)

    if not entries:
        console.print("[yellow]No audit entries found.[/yellow]")
        raise typer.Exit()

    if raw:
        for e in entries:
            print(json.dumps(e))
    else:
        for e in entries:
            formatted = json.dumps(e, indent=2)
            syntax = Syntax(formatted, "json", theme="monokai")
            console.print(syntax)
            console.print()

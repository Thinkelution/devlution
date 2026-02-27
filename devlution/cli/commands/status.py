"""devlution status — show current pipeline state."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from devlution.supervision.audit_log import AuditLogger

app = typer.Typer()
console = Console()


@app.callback(invoke_without_command=True)
def status(
    pipeline_id: str = typer.Option("", help="Filter by pipeline ID"),
    config_path: str = typer.Option("devlution.yaml", "--config", help="Path to devlution.yaml"),
) -> None:
    """Show the state of recent pipeline runs."""
    try:
        from devlution.config import load_config
        config = load_config(config_path)
        audit_path = config.supervision.audit_log
    except FileNotFoundError:
        audit_path = ".devlution/audit.jsonl"

    audit = AuditLogger(audit_path)
    entries = audit.read(last_n=50, pipeline_id=pipeline_id or None)

    if not entries:
        console.print("[yellow]No pipeline activity found.[/yellow]")
        console.print("Run `devlution run` to start a pipeline.")
        raise typer.Exit()

    pipelines: dict[str, list[dict]] = {}
    for e in entries:
        pid = e.get("pipeline_id", "unknown")
        pipelines.setdefault(pid, []).append(e)

    for pid, events in pipelines.items():
        table = Table(title=f"Pipeline: {pid}")
        table.add_column("Time", style="dim")
        table.add_column("Agent", style="cyan")
        table.add_column("Action")
        table.add_column("Confidence", justify="right")

        for e in events:
            ts = e.get("ts", "")[:19]
            conf = f"{e['confidence']:.2f}" if e.get("confidence") is not None else "-"
            table.add_row(ts, e.get("agent", ""), e.get("action", ""), conf)

        console.print(table)
        console.print()

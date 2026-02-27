"""devlution gate — approve or reject pending human gates from the CLI."""

from __future__ import annotations

import typer
from rich.console import Console

from devlution.orchestrator.checkpoints import CheckpointManager

app = typer.Typer()
console = Console()


@app.command("approve")
def approve(
    gate_id: str = typer.Option(..., "--id", help="Gate ID to approve"),
    pipeline_id: str = typer.Option("", help="Pipeline ID"),
    config_path: str = typer.Option("devlution.yaml", "--config", help="Path to devlution.yaml"),
) -> None:
    """Approve a pending human gate."""
    from devlution.config import load_config

    try:
        config = load_config(config_path)
    except FileNotFoundError:
        console.print("[red]Config not found. Run `devlution init` first.[/red]")
        raise typer.Exit(1)

    mgr = CheckpointManager(config)
    mgr.record_decision(
        gate_id=gate_id,
        decision="approved",
        approver="cli-user",
        method="cli",
        pipeline_id=pipeline_id,
    )
    console.print(f"[green]Gate '{gate_id}' approved.[/green]")


@app.command("reject")
def reject(
    gate_id: str = typer.Option(..., "--id", help="Gate ID to reject"),
    reason: str = typer.Option("", help="Rejection reason"),
    pipeline_id: str = typer.Option("", help="Pipeline ID"),
    config_path: str = typer.Option("devlution.yaml", "--config", help="Path to devlution.yaml"),
) -> None:
    """Reject a pending human gate."""
    from devlution.config import load_config

    try:
        config = load_config(config_path)
    except FileNotFoundError:
        console.print("[red]Config not found. Run `devlution init` first.[/red]")
        raise typer.Exit(1)

    mgr = CheckpointManager(config)
    mgr.record_decision(
        gate_id=gate_id,
        decision="rejected",
        approver="cli-user",
        method="cli",
        pipeline_id=pipeline_id,
    )
    console.print(f"[red]Gate '{gate_id}' rejected.[/red]")
    if reason:
        console.print(f"  Reason: {reason}")

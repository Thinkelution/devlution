"""devlution agent — run a single agent in isolation."""

from __future__ import annotations

import typer
from rich.console import Console

app = typer.Typer()
console = Console()


@app.callback(invoke_without_command=True)
def agent(
    name: str = typer.Argument(help="Agent to run: planner|coder|reviewer|tester|debugger"),
    task: str = typer.Option("", help="Task description (for coder agent)"),
    files: str = typer.Option("", help="Comma-separated file paths (for tester agent)"),
    log: str = typer.Option("", help="Path to failure log (for debugger agent)"),
    config_path: str = typer.Option("devlution.yaml", "--config", help="Path to devlution.yaml"),
) -> None:
    """Run a single Devlution agent outside the pipeline."""
    valid_agents = {"planner", "coder", "reviewer", "tester", "debugger"}
    if name not in valid_agents:
        console.print(f"[red]Unknown agent: {name}. Choose from: {', '.join(sorted(valid_agents))}[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan]Running agent: {name}[/cyan]")

    # Agents are wired in Phase 2 — for now show placeholder
    console.print(f"[yellow]Agent '{name}' execution not yet implemented (stub mode).[/yellow]")
    console.print("  Use `devlution run` to execute the full stub pipeline.")

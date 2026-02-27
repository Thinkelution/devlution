"""devlution run — trigger and execute the full pipeline."""

from __future__ import annotations

import logging
import uuid

import typer
from rich.console import Console

from devlution.config import load_config
from devlution.orchestrator.graph import build_pipeline

app = typer.Typer()
console = Console()
logger = logging.getLogger(__name__)


@app.callback(invoke_without_command=True)
def run(
    trigger: str = typer.Option("github_issue", help="Trigger type: github_issue|ci_failure|sentry_alert|manual"),
    issue: int = typer.Option(0, help="GitHub issue number (for github_issue trigger)"),
    config_path: str = typer.Option("devlution.yaml", "--config", help="Path to devlution.yaml"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
) -> None:
    """Run the Devlution pipeline end-to-end."""
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    try:
        config = load_config(config_path)
    except FileNotFoundError:
        console.print("[red]Config file not found. Run `devlution init` first.[/red]")
        raise typer.Exit(1)

    pipeline_id = uuid.uuid4().hex[:12]
    console.print(f"[bold]Pipeline {pipeline_id}[/bold] — trigger={trigger}")

    initial_state = {
        "pipeline_id": pipeline_id,
        "trigger": {"type": trigger, "issue_number": issue if issue else None},
        "tasks": [],
        "current_task_idx": 0,
        "iterations": {},
        "confidence_scores": {},
        "review_comments": [],
        "review_decision": "",
        "test_results": None,
        "patch": "",
        "pr_url": "",
        "gate_decisions": {},
        "audit_entries": [],
        "status": "pending",
        "error": "",
    }

    graph = build_pipeline(config)
    compiled = graph.compile()

    console.print("[cyan]Running pipeline...[/cyan]\n")

    final_state = compiled.invoke(initial_state)

    console.print("\n[bold green]Pipeline complete![/bold green]")
    console.print(f"  PR URL: {final_state.get('pr_url', 'N/A')}")
    console.print(f"  Status: {final_state.get('status', 'unknown')}")

    scores = final_state.get("confidence_scores", {})
    if scores:
        console.print("  Confidence scores:")
        for agent_name, score in scores.items():
            console.print(f"    {agent_name}: {score:.2f}")

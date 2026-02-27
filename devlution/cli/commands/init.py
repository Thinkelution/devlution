"""devlution init — scaffold config and CI files into a project."""

from __future__ import annotations

import shutil
from importlib import resources
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer()
console = Console()


@app.callback(invoke_without_command=True)
def init(
    language: str = typer.Option("python", help="Project language: python|typescript|go|java"),
    ci: str = typer.Option("", help="CI provider to generate config for: github-actions|gitlab-ci"),
    integrations: str = typer.Option(
        "github", help="Comma-separated integrations to enable: github,slack,sentry,jira"
    ),
    non_interactive: bool = typer.Option(False, "--non-interactive", help="Skip prompts"),
) -> None:
    """Initialize devlution in the current project."""
    target = Path("devlution.yaml")

    if target.exists() and not non_interactive:
        overwrite = typer.confirm("devlution.yaml already exists. Overwrite?", default=False)
        if not overwrite:
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Exit()

    template_pkg = resources.files("devlution.templates.configs")
    template_file = template_pkg / "devlution.yaml"

    config_text = template_file.read_text()  # type: ignore[union-attr]

    config_text = config_text.replace(
        'language: "python"', f'language: "{language}"'
    )

    enabled_integrations = {s.strip() for s in integrations.split(",") if s.strip()}
    for name in ("github", "sentry", "slack", "jira"):
        old = f"{name}:\n    enabled: {'true' if name == 'github' else 'false'}"
        new_val = "true" if name in enabled_integrations else "false"
        new = f"{name}:\n    enabled: {new_val}"
        config_text = config_text.replace(old, new)

    target.write_text(config_text)
    console.print(f"[green]Created {target}[/green]")

    devlution_dir = Path(".devlution")
    devlution_dir.mkdir(exist_ok=True)
    (devlution_dir / "prompts").mkdir(exist_ok=True)
    console.print(f"[green]Created {devlution_dir}/ directory[/green]")

    if ci:
        _generate_ci(ci)

    console.print("\n[bold]Devlution initialized![/bold] Edit devlution.yaml to configure your pipeline.")


def _generate_ci(provider: str) -> None:
    """Generate CI config files from templates."""
    try:
        ci_pkg = resources.files("devlution.templates.ci")
        if provider == "github-actions":
            dest = Path(".github/workflows/devlution.yaml")
            dest.parent.mkdir(parents=True, exist_ok=True)
            src = ci_pkg / "github-actions.yaml"
            dest.write_text(src.read_text())  # type: ignore[union-attr]
            console.print(f"[green]Created {dest}[/green]")
        elif provider == "gitlab-ci":
            dest = Path(".gitlab-ci.yml")
            src = ci_pkg / "gitlab-ci.yaml"
            dest.write_text(src.read_text())  # type: ignore[union-attr]
            console.print(f"[green]Created {dest}[/green]")
        else:
            console.print(f"[yellow]Unknown CI provider: {provider}[/yellow]")
    except (FileNotFoundError, TypeError):
        console.print(f"[yellow]CI template for {provider} not yet available[/yellow]")

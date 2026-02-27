"""Devlution CLI — entry point registered as `devlution` console script."""

import typer

from devlution.cli.commands.agent import app as agent_app
from devlution.cli.commands.audit import app as audit_app
from devlution.cli.commands.gate import app as gate_app
from devlution.cli.commands.init import app as init_app
from devlution.cli.commands.run import app as run_app
from devlution.cli.commands.status import app as status_app

app = typer.Typer(
    name="devlution",
    help="AI-augmented developer workflow framework — issue → code → test → PR with human gates.",
    no_args_is_help=True,
)

app.add_typer(init_app, name="init", help="Initialize devlution in a project")
app.add_typer(run_app, name="run", help="Run the full pipeline")
app.add_typer(agent_app, name="agent", help="Run a single agent in isolation")
app.add_typer(status_app, name="status", help="Show pipeline state")
app.add_typer(gate_app, name="gate", help="Approve or reject a pending gate")
app.add_typer(audit_app, name="audit", help="View the audit log")


if __name__ == "__main__":
    app()

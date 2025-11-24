"""Main CLI application."""

import typer
from rich.console import Console

from agentic_builder.cli.commands import (
    init_cmd,
    start,
    status,
    resume,
    cancel,
    logs,
    agents,
    tasks,
    usage,
)

app = typer.Typer(
    name="agentic-builder",
    help="AI-powered software project builder using orchestrated agents",
    no_args_is_help=True,
)
console = Console()

# Register command groups
app.add_typer(init_cmd.app, name="init")
app.add_typer(start.app, name="start")
app.add_typer(status.app, name="status")
app.add_typer(resume.app, name="resume")
app.add_typer(cancel.app, name="cancel")
app.add_typer(logs.app, name="logs")
app.add_typer(agents.app, name="agents")
app.add_typer(tasks.app, name="tasks")
app.add_typer(usage.app, name="usage")


@app.callback()
def main(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output in JSON format"
    ),
) -> None:
    """Agentic Builder - Build software projects with AI agents."""
    pass


if __name__ == "__main__":
    app()

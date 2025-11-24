"""Initialize command."""

from pathlib import Path

import typer
from rich.console import Console

from agentic_builder.api.claude_cli import ClaudeCLI
from agentic_builder.core.config import get_project_dir
from agentic_builder.storage.database import Database, get_db

app = typer.Typer(help="Initialize agentic-builder in the current directory")
console = Console()


@app.callback(invoke_without_command=True)
def init(
    project_type: str = typer.Option("", "--type", "-t", help="Project type hint"),
    name: str = typer.Option("", "--name", "-n", help="Project name"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing"),
    skip_cli_check: bool = typer.Option(
        False, "--skip-cli-check", help="Skip Claude CLI verification"
    ),
) -> None:
    """Initialize agentic-builder in the current directory."""
    project_dir = get_project_dir()

    # Verify Claude CLI is installed
    if not skip_cli_check:
        cli = ClaudeCLI()
        if not cli.verify_installation():
            console.print("[red]Error:[/red] Claude Code CLI not found.")
            console.print("\nPlease install Claude Code CLI:")
            console.print("  npm install -g @anthropic-ai/claude-code")
            console.print(
                "\nOr specify custom path via AGENTIC_CLAUDE_CLI_PATH "
                "environment variable."
            )
            console.print("\nUse --skip-cli-check to bypass this verification.")
            raise typer.Exit(1)
        console.print("[green]✓[/green] Claude Code CLI found")

    if project_dir.exists() and not force:
        console.print(
            "[red]Error:[/red] .agentic/ already exists. Use --force to overwrite."
        )
        raise typer.Exit(1)

    # Create directory structure
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "logs").mkdir(exist_ok=True)

    # Initialize database
    db = Database()
    db.initialize()

    # Set project name
    project_name = name or Path.cwd().name
    get_db().execute_write(
        "UPDATE config SET value = ? WHERE key = 'project_name'",
        (project_name,),
    )

    console.print(f"[green]Initialized agentic-builder in {project_dir}[/green]")
    console.print(f"Project: {project_name}")
    console.print("\nNext steps:")
    console.print('  agentic-builder start "Describe what you want to build"')

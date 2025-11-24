"""Tasks command."""

import typer
from rich.console import Console
from rich.table import Table

from agentic_builder.cli.output import format_status
from agentic_builder.core.config import get_project_dir
from agentic_builder.storage import tasks as task_storage
from agentic_builder.storage import workflows as workflow_storage

app = typer.Typer(help="List tasks in a workflow")
console = Console()


@app.callback(invoke_without_command=True)
def tasks(
    workflow_id: str = typer.Option(
        "", "--workflow-id", "-w", help="Workflow ID"
    ),
    status_filter: str = typer.Option(
        "", "--status", "-s", help="Filter by status"
    ),
    agent_filter: str = typer.Option(
        "", "--agent", "-a", help="Filter by agent type"
    ),
    show_dependencies: bool = typer.Option(
        False, "--deps", "-d", help="Show task dependencies"
    ),
) -> None:
    """List tasks in a workflow."""
    if not get_project_dir().exists():
        console.print("[red]Error:[/red] Not initialized.")
        raise typer.Exit(1)

    # Get workflow
    if workflow_id:
        workflow = workflow_storage.get_workflow(workflow_id)
    else:
        workflow = workflow_storage.get_latest_workflow()

    if not workflow:
        console.print("[yellow]No workflows found.[/yellow]")
        return

    console.print(f"\n[bold]Workflow:[/bold] {workflow['id']}")
    console.print(f"[bold]Status:[/bold] {format_status(workflow['status'])}\n")

    # Get tasks
    all_tasks = task_storage.get_workflow_tasks(workflow["id"])

    if status_filter:
        all_tasks = [t for t in all_tasks if t["status"] == status_filter.lower()]

    if agent_filter:
        all_tasks = [
            t for t in all_tasks if t["agent_type"].upper() == agent_filter.upper()
        ]

    if not all_tasks:
        console.print("[yellow]No tasks found matching criteria.[/yellow]")
        return

    # Build table
    table = Table(title=f"Tasks ({len(all_tasks)} total)")
    table.add_column("ID", style="dim", max_width=25)
    table.add_column("Agent")
    table.add_column("Title", max_width=35)
    table.add_column("Status")
    table.add_column("Priority")
    table.add_column("Tokens")

    if show_dependencies:
        table.add_column("Dependencies")

    for task in all_tasks:
        row = [
            task["id"][-20:],  # Show last 20 chars
            task["agent_type"],
            task["title"][:35],
            format_status(task["status"]),
            task.get("priority", "medium"),
            str(task.get("tokens_used", 0)),
        ]

        if show_dependencies:
            deps = task_storage.get_task_dependencies(task["id"])
            dep_str = ", ".join(d[-10:] for d in deps) if deps else "-"
            row.append(dep_str)

        table.add_row(*row)

    console.print(table)

    # Summary
    by_status: dict[str, int] = {}
    for task in all_tasks:
        status = task["status"]
        by_status[status] = by_status.get(status, 0) + 1

    console.print("\n[bold]Summary:[/bold]")
    for status, count in sorted(by_status.items()):
        console.print(f"  {format_status(status)}: {count}")

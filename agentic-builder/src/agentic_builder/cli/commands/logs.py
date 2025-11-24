"""Logs command."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from agentic_builder.core.config import get_project_dir
from agentic_builder.storage import tasks as task_storage
from agentic_builder.storage import workflows as workflow_storage

app = typer.Typer(help="View workflow logs")
console = Console()


@app.callback(invoke_without_command=True)
def logs(
    workflow_id: str = typer.Option(
        "", "--workflow-id", "-w", help="Workflow ID"
    ),
    task_id: str = typer.Option("", "--task-id", "-t", help="Specific task ID"),
    show_context: bool = typer.Option(
        False, "--context", "-c", help="Show task context XML"
    ),
    show_output: bool = typer.Option(
        False, "--output", "-o", help="Show task output XML"
    ),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of tasks to show"),
) -> None:
    """View workflow logs."""
    if not get_project_dir().exists():
        console.print("[red]Error:[/red] Not initialized.")
        raise typer.Exit(1)

    # Get specific task output
    if task_id:
        task = task_storage.get_task(task_id)
        if not task:
            console.print(f"[red]Error:[/red] Task not found: {task_id}")
            raise typer.Exit(1)

        console.print(f"\n[bold]Task:[/bold] {task['id']}")
        console.print(f"[bold]Agent:[/bold] {task['agent_type']}")
        console.print(f"[bold]Status:[/bold] {task['status']}")
        console.print(f"[bold]Title:[/bold] {task['title']}")

        if task.get("description"):
            console.print(f"[bold]Description:[/bold] {task['description']}")

        if task.get("error_message"):
            console.print(f"[bold red]Error:[/bold red] {task['error_message']}")

        # Show context
        if show_context:
            context = task_storage.get_task_context(task_id)
            if context:
                console.print("\n[bold]Context XML:[/bold]")
                syntax = Syntax(context, "xml", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title="Task Context"))

        # Show output
        if show_output:
            output = task_storage.get_task_output(task_id)
            if output:
                console.print("\n[bold]Output:[/bold]")
                console.print(f"Summary: {output.get('summary', 'N/A')}")

                if output.get("key_decisions"):
                    console.print("\n[bold]Key Decisions:[/bold]")
                    for decision in output["key_decisions"]:
                        console.print(f"  • {decision}")

                if output.get("output_xml"):
                    console.print("\n[bold]Output XML:[/bold]")
                    syntax = Syntax(
                        output["output_xml"], "xml", theme="monokai", line_numbers=True
                    )
                    console.print(Panel(syntax, title="Task Output"))
        return

    # Get workflow tasks
    if workflow_id:
        workflow = workflow_storage.get_workflow(workflow_id)
    else:
        workflow = workflow_storage.get_latest_workflow()

    if not workflow:
        console.print("[yellow]No workflows found.[/yellow]")
        return

    console.print(f"\n[bold]Workflow:[/bold] {workflow['id']}")
    console.print(f"[bold]Status:[/bold] {workflow['status']}\n")

    # Get tasks
    tasks = task_storage.get_workflow_tasks(workflow["id"])

    if not tasks:
        console.print("[yellow]No tasks found.[/yellow]")
        return

    # Show recent tasks
    console.print(f"[bold]Recent Tasks (showing {min(limit, len(tasks))}):[/bold]\n")

    for task in tasks[:limit]:
        status_color = {
            "completed": "green",
            "failed": "red",
            "running": "blue",
            "pending": "yellow",
        }.get(task["status"], "white")

        console.print(
            f"[{status_color}]●[/{status_color}] [{status_color}]{task['status']}[/{status_color}] "
            f"[bold]{task['agent_type']}[/bold]: {task['title']}"
        )

        if task.get("error_message"):
            console.print(f"  [red]Error: {task['error_message']}[/red]")

        output = task_storage.get_task_output(task["id"])
        if output and output.get("summary"):
            summary = output["summary"][:100]
            console.print(f"  Summary: {summary}...")

        console.print()

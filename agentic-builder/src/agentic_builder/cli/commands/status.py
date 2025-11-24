"""Status command."""

import typer
from rich.console import Console
from rich.table import Table

from agentic_builder.cli.output import format_status
from agentic_builder.core.config import get_project_dir
from agentic_builder.storage import tasks as task_storage
from agentic_builder.storage import workflows as workflow_storage

app = typer.Typer(help="Show workflow status")
console = Console()


@app.callback(invoke_without_command=True)
def status(
    workflow_id: str = typer.Option(
        "", "--workflow-id", "-w", help="Specific workflow ID"
    ),
    show_tasks: bool = typer.Option(
        False, "--tasks", "-t", help="Show task details"
    ),
    show_stages: bool = typer.Option(
        False, "--stages", "-s", help="Show stage details"
    ),
    all_workflows: bool = typer.Option(
        False, "--all", "-a", help="Show all workflows"
    ),
) -> None:
    """Show workflow status."""
    if not get_project_dir().exists():
        console.print("[red]Error:[/red] Not initialized.")
        raise typer.Exit(1)

    if all_workflows:
        workflows = workflow_storage.get_workflows(limit=20)
        if not workflows:
            console.print("[yellow]No workflows found.[/yellow]")
            return

        table = Table(title="Workflows")
        table.add_column("ID", style="dim")
        table.add_column("Type")
        table.add_column("Status")
        table.add_column("Tokens")
        table.add_column("Cost")
        table.add_column("Created")

        for wf in workflows:
            table.add_row(
                wf["id"],
                wf["workflow_type"],
                format_status(wf["status"]),
                f"{wf['total_tokens_used']:,}",
                f"${wf['estimated_cost_usd']:.4f}",
                wf["created_at"][:19] if wf["created_at"] else "",
            )
        console.print(table)
        return

    # Get single workflow
    if workflow_id:
        workflow = workflow_storage.get_workflow(workflow_id)
    else:
        workflow = workflow_storage.get_latest_workflow()

    if not workflow:
        console.print("[yellow]No workflows found.[/yellow]")
        return

    # Display workflow info
    console.print(f"\n[bold]Workflow:[/bold] {workflow['id']}")
    console.print(f"[bold]Type:[/bold] {workflow['workflow_type']}")
    console.print(f"[bold]Status:[/bold] {format_status(workflow['status'])}")
    console.print(f"[bold]Description:[/bold] {workflow['description']}")
    console.print(f"[bold]Tokens:[/bold] {workflow['total_tokens_used']:,}")
    console.print(f"[bold]Cost:[/bold] ${workflow['estimated_cost_usd']:.4f}")

    if workflow.get("started_at"):
        console.print(f"[bold]Started:[/bold] {workflow['started_at']}")
    if workflow.get("completed_at"):
        console.print(f"[bold]Completed:[/bold] {workflow['completed_at']}")
    if workflow.get("error_message"):
        console.print(f"[bold red]Error:[/bold red] {workflow['error_message']}")

    # Show stages
    if show_stages:
        stages = workflow_storage.get_workflow_stages(workflow["id"])
        if stages:
            console.print("\n[bold]Stages:[/bold]")
            table = Table()
            table.add_column("Order", style="dim")
            table.add_column("Name")
            table.add_column("Status")
            table.add_column("Parallel")

            for stage in stages:
                table.add_row(
                    str(stage["stage_order"]),
                    stage["stage_name"],
                    format_status(stage["status"]),
                    "Yes" if stage["parallel"] else "No",
                )
            console.print(table)

    # Show tasks
    if show_tasks:
        tasks = task_storage.get_workflow_tasks(workflow["id"])
        if tasks:
            console.print("\n[bold]Tasks:[/bold]")
            table = Table()
            table.add_column("ID", style="dim", max_width=30)
            table.add_column("Agent")
            table.add_column("Title", max_width=40)
            table.add_column("Status")
            table.add_column("Tokens")

            for task in tasks:
                table.add_row(
                    task["id"],
                    task["agent_type"],
                    task["title"][:40],
                    format_status(task["status"]),
                    str(task.get("tokens_used", 0)),
                )
            console.print(table)

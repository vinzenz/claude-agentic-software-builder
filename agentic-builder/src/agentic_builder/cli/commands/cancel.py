"""Cancel command."""

import asyncio

import typer
from rich.console import Console

from agentic_builder.core.config import get_project_dir
from agentic_builder.core.constants import WorkflowStatus
from agentic_builder.orchestration.engine import WorkflowEngine
from agentic_builder.storage import workflows as workflow_storage

app = typer.Typer(help="Cancel a running workflow")
console = Console()


@app.callback(invoke_without_command=True)
def cancel(
    workflow_id: str = typer.Option(
        "", "--workflow-id", "-w", help="Workflow ID to cancel"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force cancel without confirmation"
    ),
) -> None:
    """Cancel a running workflow."""
    if not get_project_dir().exists():
        console.print("[red]Error:[/red] Not initialized.")
        raise typer.Exit(1)

    # Get workflow
    if workflow_id:
        workflow = workflow_storage.get_workflow(workflow_id)
    else:
        # Get latest running workflow
        workflows = workflow_storage.get_workflows(status=WorkflowStatus.RUNNING.value)
        workflow = workflows[0] if workflows else None

    if not workflow:
        console.print("[yellow]No running workflows found.[/yellow]")
        return

    if workflow["status"] not in ("running", "paused", "pending"):
        console.print(
            f"[yellow]Workflow is already '{workflow['status']}'.[/yellow]"
        )
        return

    # Confirm cancellation
    if not force:
        confirm = typer.confirm(
            f"Cancel workflow {workflow['id']}?",
            default=False,
        )
        if not confirm:
            console.print("Cancelled.")
            return

    async def run() -> None:
        engine = WorkflowEngine()
        await engine.cancel(workflow["id"])

    asyncio.run(run())
    console.print(f"[green]Workflow {workflow['id']} cancelled.[/green]")

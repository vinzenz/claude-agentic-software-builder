"""Resume command."""

import asyncio

import typer
from rich.console import Console

from agentic_builder.core.config import get_project_dir
from agentic_builder.orchestration.engine import WorkflowEngine
from agentic_builder.storage import workflows as workflow_storage

app = typer.Typer(help="Resume a paused or failed workflow")
console = Console()


@app.callback(invoke_without_command=True)
def resume(
    workflow_id: str = typer.Option(
        "", "--workflow-id", "-w", help="Workflow ID to resume"
    ),
) -> None:
    """Resume a paused or failed workflow."""
    if not get_project_dir().exists():
        console.print("[red]Error:[/red] Not initialized.")
        raise typer.Exit(1)

    # Get workflow
    if workflow_id:
        workflow = workflow_storage.get_workflow(workflow_id)
    else:
        # Get latest resumable workflow
        workflows = workflow_storage.get_workflows()
        workflow = None
        for wf in workflows:
            if wf["status"] in ("paused", "failed"):
                workflow = wf
                break

    if not workflow:
        console.print("[yellow]No resumable workflows found.[/yellow]")
        console.print("Workflows must be in 'paused' or 'failed' status to resume.")
        return

    if workflow["status"] not in ("paused", "failed"):
        console.print(
            f"[red]Error:[/red] Cannot resume workflow in "
            f"'{workflow['status']}' status."
        )
        console.print("Only 'paused' or 'failed' workflows can be resumed.")
        raise typer.Exit(1)

    console.print(f"[blue]Resuming workflow:[/blue] {workflow['id']}")
    console.print(f"Previous status: {workflow['status']}\n")

    async def run() -> None:
        engine = WorkflowEngine()

        async def on_stage(event: str, data: dict) -> None:
            if event == "stage_started":
                console.print(
                    f"  [cyan]Stage:[/cyan] {data.get('stage_name', 'unknown')}"
                )
            elif event == "stage_completed":
                console.print("  [green]✓ Stage completed[/green]")
            elif event == "stage_failed":
                console.print("  [red]✗ Stage failed[/red]")

        async def on_workflow(event: str, data: dict) -> None:
            if event == "workflow_completed":
                console.print("\n[green]✓ Workflow completed successfully[/green]")
            elif event == "workflow_failed":
                error = data.get("error", "Unknown error")
                console.print(f"\n[red]✗ Workflow failed: {error}[/red]")

        engine.on_event("stage_started", on_stage)
        engine.on_event("stage_completed", on_stage)
        engine.on_event("stage_failed", on_stage)
        engine.on_event("workflow_completed", on_workflow)
        engine.on_event("workflow_failed", on_workflow)

        await engine.resume(workflow["id"])

    try:
        asyncio.run(run())
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

"""Start command."""

import asyncio

import typer
from rich.console import Console

from agentic_builder.core.config import get_project_dir
from agentic_builder.orchestration.engine import WorkflowEngine
from agentic_builder.orchestration.workflows import list_workflows

app = typer.Typer(help="Start a new project from a description")
console = Console()


@app.callback(invoke_without_command=True)
def start(
    description: str = typer.Argument(
        None, help="Description of what to build"
    ),
    workflow: str = typer.Option(
        "full_project", "--workflow", "-w", help="Workflow type"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show plan without executing"
    ),
    list_types: bool = typer.Option(
        False, "--list", "-l", help="List available workflow types"
    ),
) -> None:
    """Start a new project from a description."""
    if list_types:
        console.print("\n[bold]Available Workflow Types:[/bold]\n")
        for wf in list_workflows():
            console.print(f"  [cyan]{wf.id}[/cyan] - {wf.name}")
            console.print(f"    {wf.description}")
            stages = ", ".join(s.name for s in wf.stages)
            console.print(f"    Stages: {stages}\n")
        return

    # Require description for non-list operations
    if not description:
        console.print("[red]Error:[/red] Description is required.")
        console.print("Usage: agentic-builder start \"Your project description\"")
        raise typer.Exit(1)

    if not get_project_dir().exists():
        console.print(
            "[red]Error:[/red] Not initialized. Run 'agentic-builder init' first."
        )
        raise typer.Exit(1)

    if dry_run:
        console.print(f"[yellow]Dry run:[/yellow] Would start '{workflow}' workflow")
        console.print(f"Description: {description}")

        # Show workflow stages
        from agentic_builder.orchestration.workflows import get_workflow

        workflow_def = get_workflow(workflow)
        if workflow_def:
            console.print(f"\n[bold]Workflow: {workflow_def.name}[/bold]")
            console.print(f"Description: {workflow_def.description}\n")
            console.print("[bold]Stages:[/bold]")
            for i, stage in enumerate(workflow_def.stages, 1):
                parallel = " (parallel)" if stage.parallel else ""
                agents = ", ".join(a.value for a in stage.agent_types)
                console.print(f"  {i}. {stage.name}{parallel}: {agents}")
        return

    console.print(f"[blue]Starting workflow:[/blue] {workflow}")
    console.print(f"Description: {description}\n")

    async def run() -> str:
        engine = WorkflowEngine()

        # Register progress handlers
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

        workflow_id = await engine.create_and_execute(workflow, description)
        return workflow_id

    try:
        workflow_id = asyncio.run(run())
        console.print(f"\nWorkflow ID: [bold]{workflow_id}[/bold]")
        console.print("View status: agentic-builder status")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

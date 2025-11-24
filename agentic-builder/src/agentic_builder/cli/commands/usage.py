"""Usage command."""

import typer
from rich.console import Console
from rich.table import Table

from agentic_builder.context.budget import get_workflow_usage
from agentic_builder.core.config import get_project_dir
from agentic_builder.core.constants import DEFAULT_WORKFLOW_BUDGET
from agentic_builder.storage.database import get_db
from agentic_builder.storage import workflows as workflow_storage

app = typer.Typer(help="Show token usage statistics")
console = Console()


@app.callback(invoke_without_command=True)
def usage(
    workflow_id: str = typer.Option(
        "", "--workflow-id", "-w", help="Workflow ID"
    ),
    show_all: bool = typer.Option(
        False, "--all", "-a", help="Show usage for all workflows"
    ),
    by_agent: bool = typer.Option(
        False, "--by-agent", help="Break down by agent type"
    ),
    by_model: bool = typer.Option(
        False, "--by-model", help="Break down by model"
    ),
) -> None:
    """Show token usage statistics."""
    if not get_project_dir().exists():
        console.print("[red]Error:[/red] Not initialized.")
        raise typer.Exit(1)

    if show_all:
        # Show usage for all workflows
        workflows = workflow_storage.get_workflows(limit=20)
        if not workflows:
            console.print("[yellow]No workflows found.[/yellow]")
            return

        table = Table(title="Token Usage by Workflow")
        table.add_column("Workflow ID", style="dim")
        table.add_column("Type")
        table.add_column("Input Tokens", justify="right")
        table.add_column("Output Tokens", justify="right")
        table.add_column("Total Tokens", justify="right")
        table.add_column("Cost (USD)", justify="right")

        total_tokens = 0
        total_cost = 0.0

        for wf in workflows:
            usage_data = get_workflow_usage(wf["id"])
            total_tokens += usage_data["total_tokens"]
            total_cost += usage_data["total_cost"]

            table.add_row(
                wf["id"],
                wf["workflow_type"],
                f"{usage_data['total_input']:,}",
                f"{usage_data['total_output']:,}",
                f"{usage_data['total_tokens']:,}",
                f"${usage_data['total_cost']:.4f}",
            )

        console.print(table)
        console.print(f"\n[bold]Total Tokens:[/bold] {total_tokens:,}")
        console.print(f"[bold]Total Cost:[/bold] ${total_cost:.4f}")
        return

    # Get specific workflow
    if workflow_id:
        workflow = workflow_storage.get_workflow(workflow_id)
    else:
        workflow = workflow_storage.get_latest_workflow()

    if not workflow:
        console.print("[yellow]No workflows found.[/yellow]")
        return

    usage_data = get_workflow_usage(workflow["id"])

    console.print(f"\n[bold]Workflow:[/bold] {workflow['id']}")
    console.print(f"[bold]Type:[/bold] {workflow['workflow_type']}")
    console.print("\n[bold]Token Usage:[/bold]")
    console.print(f"  Input Tokens:  {usage_data['total_input']:,}")
    console.print(f"  Output Tokens: {usage_data['total_output']:,}")
    console.print(f"  Total Tokens:  {usage_data['total_tokens']:,}")
    console.print(f"\n[bold]Cost:[/bold] ${usage_data['total_cost']:.4f}")

    # Budget progress
    budget = DEFAULT_WORKFLOW_BUDGET
    percent = (usage_data["total_tokens"] / budget) * 100 if budget > 0 else 0
    bar_width = 30
    filled = int((percent / 100) * bar_width)
    bar = "█" * filled + "░" * (bar_width - filled)

    if percent >= 80:
        color = "red"
    elif percent >= 50:
        color = "yellow"
    else:
        color = "green"

    console.print(f"\n[bold]Budget:[/bold] [{color}]{bar}[/{color}] {percent:.1f}%")
    console.print(f"  {usage_data['total_tokens']:,} / {budget:,} tokens")

    # Breakdown by agent
    if by_agent:
        db = get_db()
        rows = db.execute(
            """
            SELECT agent_type,
                   SUM(input_tokens) as input_tokens,
                   SUM(output_tokens) as output_tokens,
                   SUM(cost_usd) as cost
            FROM token_usage
            WHERE workflow_run_id = ?
            GROUP BY agent_type
            ORDER BY cost DESC
            """,
            (workflow["id"],),
        )

        if rows:
            console.print("\n[bold]Usage by Agent:[/bold]")
            table = Table()
            table.add_column("Agent")
            table.add_column("Input", justify="right")
            table.add_column("Output", justify="right")
            table.add_column("Cost", justify="right")

            for row in rows:
                table.add_row(
                    row["agent_type"],
                    f"{row['input_tokens']:,}",
                    f"{row['output_tokens']:,}",
                    f"${row['cost']:.4f}",
                )
            console.print(table)

    # Breakdown by model
    if by_model:
        db = get_db()
        rows = db.execute(
            """
            SELECT model,
                   SUM(input_tokens) as input_tokens,
                   SUM(output_tokens) as output_tokens,
                   SUM(cost_usd) as cost
            FROM token_usage
            WHERE workflow_run_id = ?
            GROUP BY model
            ORDER BY cost DESC
            """,
            (workflow["id"],),
        )

        if rows:
            console.print("\n[bold]Usage by Model:[/bold]")
            table = Table()
            table.add_column("Model")
            table.add_column("Input", justify="right")
            table.add_column("Output", justify="right")
            table.add_column("Cost", justify="right")

            for row in rows:
                table.add_row(
                    row["model"],
                    f"{row['input_tokens']:,}",
                    f"{row['output_tokens']:,}",
                    f"${row['cost']:.4f}",
                )
            console.print(table)

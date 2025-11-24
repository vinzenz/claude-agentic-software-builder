"""Agents command."""

import typer
from rich.console import Console
from rich.table import Table

from agentic_builder.agents.registry import get_agent_config, get_all_agents
from agentic_builder.core.constants import AgentType

app = typer.Typer(help="List available agents")
console = Console()


@app.callback(invoke_without_command=True)
def agents(
    agent_type: str = typer.Option(
        "", "--type", "-t", help="Show details for specific agent type"
    ),
    show_capabilities: bool = typer.Option(
        False, "--capabilities", "-c", help="Show agent capabilities"
    ),
) -> None:
    """List available agents."""
    if agent_type:
        # Show specific agent details
        try:
            agent_enum = AgentType(agent_type.upper())
            config = get_agent_config(agent_enum)
        except ValueError:
            console.print(f"[red]Error:[/red] Unknown agent type: {agent_type}")
            console.print("\nAvailable types:")
            for agent in get_all_agents():
                console.print(f"  {agent.type.value}")
            raise typer.Exit(1)

        if not config:
            console.print(f"[red]Error:[/red] Agent not found: {agent_type}")
            raise typer.Exit(1)

        console.print(f"\n[bold]Agent: {config.name}[/bold]")
        console.print(f"Type: {config.type.value}")
        console.print(f"Description: {config.description}")
        console.print(f"Model Tier: {config.model_tier.value}")
        console.print(f"Prompt File: {config.prompt_file}")
        console.print(f"\nCapabilities:")
        for cap in config.capabilities:
            console.print(f"  • {cap}")
        return

    # List all agents
    all_agents = get_all_agents()

    # Group by model tier
    model_colors = {
        "haiku": "green",
        "sonnet": "blue",
        "opus": "magenta",
    }

    table = Table(title="Available Agents")
    table.add_column("Type", style="bold")
    table.add_column("Name")
    table.add_column("Model", style="dim")
    table.add_column("Description")

    if show_capabilities:
        table.add_column("Capabilities")

    for agent in all_agents:
        model_color = model_colors.get(agent.model_tier.value, "white")
        row = [
            agent.type.value,
            agent.name,
            f"[{model_color}]{agent.model_tier.value}[/{model_color}]",
            agent.description[:50] + ("..." if len(agent.description) > 50 else ""),
        ]

        if show_capabilities:
            row.append(", ".join(agent.capabilities))

        table.add_row(*row)

    console.print(table)

    console.print("\n[dim]Use --type <TYPE> for details on a specific agent[/dim]")
    console.print("[dim]Model tiers: haiku (fast/cheap), sonnet (balanced), opus (powerful)[/dim]")

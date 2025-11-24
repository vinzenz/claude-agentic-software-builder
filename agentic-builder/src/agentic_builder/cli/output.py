"""Output formatting utilities for CLI."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# Status colors
STATUS_COLORS = {
    "pending": "yellow",
    "running": "blue",
    "completed": "green",
    "failed": "red",
    "cancelled": "dim",
    "paused": "yellow",
    "assigned": "cyan",
    "blocked": "magenta",
    "skipped": "dim",
}


def get_status_color(status: str) -> str:
    """Get the color for a status.

    Args:
        status: Status string

    Returns:
        Rich color name
    """
    return STATUS_COLORS.get(status.lower(), "white")


def format_status(status: str) -> str:
    """Format status with color.

    Args:
        status: Status string

    Returns:
        Rich-formatted status string
    """
    color = get_status_color(status)
    return f"[{color}]{status}[/{color}]"


def print_success(message: str) -> None:
    """Print success message.

    Args:
        message: Message to print
    """
    console.print(f"[green]{message}[/green]")


def print_error(message: str) -> None:
    """Print error message.

    Args:
        message: Message to print
    """
    console.print(f"[red]Error:[/red] {message}")


def print_warning(message: str) -> None:
    """Print warning message.

    Args:
        message: Message to print
    """
    console.print(f"[yellow]Warning:[/yellow] {message}")


def print_info(message: str) -> None:
    """Print info message.

    Args:
        message: Message to print
    """
    console.print(f"[blue]{message}[/blue]")


def create_table(title: str, columns: list[tuple[str, str]]) -> Table:
    """Create a styled table.

    Args:
        title: Table title
        columns: List of (name, style) tuples

    Returns:
        Rich Table object
    """
    table = Table(title=title)
    for name, style in columns:
        table.add_column(name, style=style)
    return table


def create_progress() -> Progress:
    """Create a progress display.

    Returns:
        Rich Progress object
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    )

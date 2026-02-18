"""Rich-based logging helpers for manimator."""

from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text

console = Console()


def log_info(message: str) -> None:
    """Log an informational message."""
    console.print(f"[bold cyan]ℹ[/bold cyan]  {message}")


def log_success(message: str) -> None:
    """Log a success message."""
    console.print(f"[bold green]✓[/bold green]  {message}")


def log_error(message: str) -> None:
    """Log an error message."""
    console.print(f"[bold red]✗[/bold red]  {message}")


def log_warning(message: str) -> None:
    """Log a warning message."""
    console.print(f"[bold yellow]⚠[/bold yellow]  {message}")


def log_step(step: int, total: int, message: str) -> None:
    """Log a numbered step."""
    console.print(f"[bold magenta][{step}/{total}][/bold magenta] {message}")


def log_code(code: str, title: str = "Generated Manim Code") -> None:
    """Display syntax-highlighted Python code in a panel."""
    syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=f"[bold cyan]{title}[/bold cyan]", border_style="cyan"))


def log_panel(message: str, title: str = "", style: str = "blue") -> None:
    """Display a message inside a Rich panel."""
    console.print(Panel(Text(message), title=f"[bold]{title}[/bold]", border_style=style))


def log_retry(attempt: int, max_retries: int, error_summary: str) -> None:
    """Log an auto-correction retry attempt."""
    console.print(
        Panel(
            f"[yellow]{error_summary}[/yellow]",
            title=f"[bold yellow]⟳ Auto-correction attempt {attempt}/{max_retries}[/bold yellow]",
            border_style="yellow",
        )
    )

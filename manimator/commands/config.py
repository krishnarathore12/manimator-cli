"""'config' command — manage persistent manimator settings."""

from typing import Optional

import typer
from rich.table import Table
from typing_extensions import Annotated

from manimator.config_manager import ConfigManager
from manimator.utils.logger import console, log_success, log_info, log_error

app = typer.Typer()

VALID_PROVIDERS = ["openai", "anthropic", "ollama", "gemini"]
VALID_QUALITIES = ["low", "medium", "high", "ultra"]


@app.command()
def config(
    key: Annotated[Optional[str], typer.Option("--key", help="API key for the active provider")] = None,
    provider: Annotated[Optional[str], typer.Option("--provider", help="LLM provider: openai | anthropic | ollama | gemini")] = None,
    output: Annotated[Optional[str], typer.Option("--output", help="Default output directory")] = None,
    model: Annotated[Optional[str], typer.Option("--model", help="Default model name")] = None,
    retries: Annotated[Optional[int], typer.Option("--retries", help="Max auto-correction attempts")] = None,
    quality: Annotated[Optional[str], typer.Option("--quality", help="Default quality: low | medium | high | ultra")] = None,
    auto_preview: Annotated[Optional[bool], typer.Option("--auto-preview/--no-auto-preview", help="Auto-open video after render")] = None,
    show: Annotated[bool, typer.Option("--show", help="Print current configuration")] = False,
) -> None:
    """View or update manimator configuration."""
    config_manager = ConfigManager()
    cfg = config_manager.load()
    changed = False

    # Validate provider
    if provider is not None:
        if provider not in VALID_PROVIDERS:
            log_error(f"Invalid provider '{provider}'. Choose from: {', '.join(VALID_PROVIDERS)}")
            raise typer.Exit(1)
        cfg.provider = provider
        changed = True
        log_success(f"Provider set to [bold]{provider}[/bold]")

    # Store API key in keyring
    if key is not None:
        active_provider = provider or cfg.provider
        config_manager.set_api_key(active_provider, key)
        log_success(f"API key stored for [bold]{active_provider}[/bold] (in OS keyring)")

    if model is not None:
        cfg.model = model
        changed = True
        log_success(f"Default model set to [bold]{model}[/bold]")

    if output is not None:
        from pathlib import Path
        out_path = Path(output).expanduser().resolve()
        out_path.mkdir(parents=True, exist_ok=True)
        cfg.output_dir = str(out_path)
        changed = True
        log_success(f"Output directory set to [bold]{out_path}[/bold]")

    if retries is not None:
        if retries < 1:
            log_error("Retries must be at least 1.")
            raise typer.Exit(1)
        cfg.max_retries = retries
        changed = True
        log_success(f"Max retries set to [bold]{retries}[/bold]")

    if quality is not None:
        if quality not in VALID_QUALITIES:
            log_error(f"Invalid quality '{quality}'. Choose from: {', '.join(VALID_QUALITIES)}")
            raise typer.Exit(1)
        cfg.default_quality = quality  # type: ignore[assignment]
        changed = True
        log_success(f"Default quality set to [bold]{quality}[/bold]")

    if auto_preview is not None:
        cfg.auto_preview = auto_preview
        changed = True
        log_success(f"Auto-preview set to [bold]{auto_preview}[/bold]")

    if changed:
        config_manager.save(cfg)

    if show or not any([key, provider, output, model, retries, quality, auto_preview is not None]):
        _print_config(config_manager, cfg)


def _print_config(config_manager: ConfigManager, cfg) -> None:
    """Render the current configuration as a Rich table."""
    masked = config_manager.masked_config(cfg)

    table = Table(title="[bold cyan]manimator Configuration[/bold cyan]", show_header=True)
    table.add_column("Setting", style="bold")
    table.add_column("Value", style="green")

    table.add_row("Config file", str(config_manager.config_path))
    table.add_row("Provider", masked.get("provider", ""))
    table.add_row("Model", masked.get("model", ""))
    table.add_row("API Key", masked.get("api_key", "(not set)"))
    table.add_row("Output directory", masked.get("output_dir", ""))
    table.add_row("Default quality", masked.get("default_quality", ""))
    table.add_row("Max retries", str(masked.get("max_retries", "")))
    table.add_row("Auto-preview", str(masked.get("auto_preview", "")))
    table.add_row("Verbose", str(masked.get("verbose", "")))

    console.print()
    console.print(table)
    console.print()

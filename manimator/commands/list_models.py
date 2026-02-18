"""'list-models' command — display available models per provider."""

from typing import Optional

import typer
from rich.table import Table
from typing_extensions import Annotated

from manimator.config_manager import ConfigManager
from manimator.utils.logger import console, log_error, log_warning

app = typer.Typer()

PROVIDER_COLORS = {
    "openai": "green",
    "anthropic": "magenta",
    "ollama": "yellow",
    "gemini": "blue",
}


@app.command()
def list_models(
    provider: Annotated[
        Optional[str],
        typer.Option("--provider", help="Filter by provider: openai | anthropic | ollama | gemini"),
    ] = None,
) -> None:
    """List available models for all (or a specific) provider."""
    config_manager = ConfigManager()
    cfg = config_manager.load()

    providers_to_query = (
        [provider] if provider else ["openai", "anthropic", "gemini", "ollama"]
    )

    table = Table(
        title="[bold cyan]Available Models[/bold cyan]",
        show_header=True,
        header_style="bold",
    )
    table.add_column("Model", style="bold white", min_width=28)
    table.add_column("Provider", min_width=12)
    table.add_column("Context", min_width=14)
    table.add_column("Speed", min_width=12)
    table.add_column("Description")

    for pname in providers_to_query:
        color = PROVIDER_COLORS.get(pname, "white")
        try:
            provider_instance = _build_provider(pname, cfg, config_manager)
            models = provider_instance.list_models()
            for m in models:
                table.add_row(
                    m.get("name", ""),
                    f"[{color}]{pname}[/{color}]",
                    m.get("context", ""),
                    m.get("speed", ""),
                    m.get("description", ""),
                )
        except Exception as e:
            log_warning(f"Could not query [bold]{pname}[/bold]: {e}")

    console.print()
    console.print(table)
    console.print()


def _build_provider(provider_name: str, cfg, config_manager: ConfigManager):
    """Build a provider instance for listing models (no API key required for static lists)."""
    api_key = config_manager.get_api_key(provider_name) or "placeholder"

    if provider_name == "openai":
        from manimator.providers.openai_provider import OpenAIProvider
        return OpenAIProvider(api_key=api_key, model=cfg.model)

    elif provider_name == "anthropic":
        from manimator.providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider(api_key=api_key, model=cfg.model)

    elif provider_name == "gemini":
        from manimator.providers.gemini_provider import GeminiProvider
        return GeminiProvider(api_key=api_key, model=cfg.model)

    elif provider_name == "ollama":
        from manimator.providers.ollama_provider import OllamaProvider
        return OllamaProvider(model=cfg.model)

    else:
        raise ValueError(f"Unknown provider: {provider_name}")

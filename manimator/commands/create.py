"""'create' command — the core prompt-to-video pipeline."""

from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from manimator.config_manager import ConfigManager
from manimator.corrector import AutoCorrector
from manimator.renderer import ManimRenderer
from manimator.utils.logger import log_error, log_success
from manimator.utils.preview import open_video

app = typer.Typer()

QUALITY_CHOICES = ["low", "medium", "high", "ultra"]


def _get_provider(provider_name: str, model: str, config_manager: ConfigManager):
    """Instantiate the correct LLM provider."""
    api_key = config_manager.get_api_key(provider_name)

    if provider_name == "openai":
        from manimator.providers.openai_provider import OpenAIProvider
        if not api_key:
            log_error("OpenAI API key not set. Run: manimator config --key <key> --provider openai")
            raise typer.Exit(1)
        return OpenAIProvider(api_key=api_key, model=model)

    elif provider_name == "anthropic":
        from manimator.providers.anthropic_provider import AnthropicProvider
        if not api_key:
            log_error("Anthropic API key not set. Run: manimator config --key <key> --provider anthropic")
            raise typer.Exit(1)
        return AnthropicProvider(api_key=api_key, model=model)

    elif provider_name == "gemini":
        from manimator.providers.gemini_provider import GeminiProvider
        if not api_key:
            log_error("Gemini API key not set. Run: manimator config --key <key> --provider gemini")
            raise typer.Exit(1)
        return GeminiProvider(api_key=api_key, model=model)

    elif provider_name == "ollama":
        from manimator.providers.ollama_provider import OllamaProvider
        return OllamaProvider(model=model)

    else:
        log_error(f"Unknown provider: {provider_name}")
        raise typer.Exit(1)


@app.command()
def create(
    description: Annotated[str, typer.Argument(help="Natural-language description of the animation")],
    quality: Annotated[
        Optional[str],
        typer.Option("--quality", "-q", help="Render quality: low | medium | high | ultra"),
    ] = None,
    preview: Annotated[bool, typer.Option("--preview", "-p", help="Open video after render")] = False,
    provider: Annotated[Optional[str], typer.Option(help="LLM provider: openai | anthropic | ollama | gemini")] = None,
    model: Annotated[Optional[str], typer.Option(help="Model name (overrides config default)")] = None,
    output: Annotated[Optional[Path], typer.Option("--output", "-o", help="Output directory")] = None,
    retries: Annotated[Optional[int], typer.Option("--retries", "-r", help="Max auto-correction attempts")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show generated code and LLM prompts")] = False,
) -> None:
    """Generate a Manim animation from a natural-language description."""
    config_manager = ConfigManager()
    config = config_manager.load()

    # Resolve options (CLI flags override config defaults)
    resolved_quality = quality or config.default_quality
    resolved_provider = provider or config.provider
    resolved_model = model or config.model
    resolved_output = output or Path(config.output_dir)
    resolved_retries = retries if retries is not None else config.max_retries
    resolved_preview = preview or config.auto_preview
    resolved_verbose = verbose or config.verbose

    if resolved_quality not in QUALITY_CHOICES:
        log_error(f"Invalid quality '{resolved_quality}'. Choose from: {', '.join(QUALITY_CHOICES)}")
        raise typer.Exit(1)

    # Instantiate provider
    try:
        llm_provider = _get_provider(resolved_provider, resolved_model, config_manager)
    except RuntimeError as e:
        log_error(str(e))
        raise typer.Exit(1)

    # Set up renderer
    cache_dir = config_manager.ensure_cache_dir()
    renderer = ManimRenderer(cache_dir=cache_dir)

    # Run the auto-correction pipeline
    corrector = AutoCorrector(
        provider=llm_provider,
        renderer=renderer,
        max_retries=resolved_retries,
        verbose=resolved_verbose,
    )

    output_path = corrector.run(
        description=description,
        quality=resolved_quality,
        output_dir=resolved_output,
    )

    if output_path and resolved_preview:
        log_success("Opening video preview…")
        open_video(output_path)

    if not output_path:
        raise typer.Exit(1)

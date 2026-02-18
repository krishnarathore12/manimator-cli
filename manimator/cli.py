"""manimator — main Typer CLI entry point."""

import typer
from rich import print as rprint
from rich.console import Console

from manimator import __version__, __app_name__

_console = Console()

ASCII_BANNER = r"""
 ███╗   ███╗ █████╗ ███╗   ██╗██╗███╗   ███╗ █████╗ ████████╗ ██████╗ ██████╗
 ████╗ ████║██╔══██╗████╗  ██║██║████╗ ████║██╔══██╗╚══██╔══╝██╔═══██╗██╔══██╗
 ██╔████╔██║███████║██╔██╗ ██║██║██╔████╔██║███████║   ██║   ██║   ██║██████╔╝
 ██║╚██╔╝██║██╔══██║██║╚██╗██║██║██║╚██╔╝██║██╔══██║   ██║   ██║   ██║██╔══██╗
 ██║ ╚═╝ ██║██║  ██║██║ ╚████║██║██║ ╚═╝ ██║██║  ██║   ██║   ╚██████╔╝██║  ██║
 ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝     ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝
"""


def _print_banner() -> None:
    """Print the ASCII art banner with Rich styling."""
    lines = ASCII_BANNER.rstrip().splitlines()
    colors = ["bright_cyan", "cyan", "bright_cyan", "cyan", "bright_cyan", "cyan"]
    for i, line in enumerate(lines):
        color = colors[i % len(colors)]
        _console.print(f"[bold {color}]{line}[/bold {color}]")
    _console.print()
    _console.print(
        f"  [dim]Natural Language[/dim] [bold magenta]→[/bold magenta] "
        f"[dim]Mathematical Animations[/dim]   [dim]v{__version__}[/dim]"
    )
    _console.print()

app = typer.Typer(
    name=__app_name__,
    help=(
        "[bold cyan]manimator[/bold cyan] — Natural Language → Mathematical Animations.\n\n"
        "Turn plain-English prompts into polished .mp4 animations using LLMs and Manim."
    ),
    add_completion=True,
    rich_markup_mode="rich",
    no_args_is_help=False,  # We handle no-args ourselves to show the banner
)


def _version_callback(value: bool) -> None:
    if value:
        rprint(f"[bold cyan]{__app_name__}[/bold cyan] version [bold]{__version__}[/bold]")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "--version",
        "-V",
        help="Show version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """manimator — Natural Language → Mathematical Animations."""
    if ctx.invoked_subcommand is None:
        _print_banner()
        _console.print(ctx.get_help())
        raise typer.Exit(0)


# ── create ────────────────────────────────────────────────────────────────────

from typing import Optional
from pathlib import Path
from typing_extensions import Annotated

QUALITY_CHOICES = ["low", "medium", "high", "ultra"]


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
    from manimator.config_manager import ConfigManager
    from manimator.corrector import AutoCorrector
    from manimator.renderer import ManimRenderer
    from manimator.utils.logger import log_error, log_success
    from manimator.utils.preview import open_video

    config_manager = ConfigManager()
    cfg = config_manager.load()

    resolved_quality = quality or cfg.default_quality
    resolved_provider = provider or cfg.provider
    resolved_model = model or cfg.model
    resolved_output = output or Path(cfg.output_dir)
    resolved_retries = retries if retries is not None else cfg.max_retries
    resolved_preview = preview or cfg.auto_preview
    resolved_verbose = verbose or cfg.verbose

    if resolved_quality not in QUALITY_CHOICES:
        log_error(f"Invalid quality '{resolved_quality}'. Choose from: {', '.join(QUALITY_CHOICES)}")
        raise typer.Exit(1)

    try:
        llm_provider = _get_provider(resolved_provider, resolved_model, config_manager)
    except RuntimeError as e:
        from manimator.utils.logger import log_error
        log_error(str(e))
        raise typer.Exit(1)

    cache_dir = config_manager.ensure_cache_dir()
    renderer = ManimRenderer(cache_dir=cache_dir)

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


# ── chat ──────────────────────────────────────────────────────────────────────

@app.command()
def chat(
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
    """Interactive chat session — describe, render, then iterate with follow-up changes."""
    from manimator.config_manager import ConfigManager
    from manimator.conversation import ConversationManager, generate_video_name, generate_unique_filename
    from manimator.corrector import AutoCorrector
    from manimator.prompt_builder import build_user_prompt, build_followup_prompt
    from manimator.renderer import ManimRenderer
    from manimator.utils.logger import log_error, log_success, log_info, console
    from manimator.utils.preview import open_video
    from rich.prompt import Prompt
    from rich.table import Table

    config_manager = ConfigManager()
    cfg = config_manager.load()

    resolved_quality = quality or cfg.default_quality
    resolved_provider = provider or cfg.provider
    resolved_model = model or cfg.model
    resolved_output = output or Path(cfg.output_dir)
    resolved_retries = retries if retries is not None else cfg.max_retries
    resolved_preview = preview or cfg.auto_preview
    resolved_verbose = verbose or cfg.verbose

    if resolved_quality not in QUALITY_CHOICES:
        log_error(f"Invalid quality '{resolved_quality}'. Choose from: {', '.join(QUALITY_CHOICES)}")
        raise typer.Exit(1)

    try:
        llm_provider = _get_provider(resolved_provider, resolved_model, config_manager)
    except RuntimeError as e:
        log_error(str(e))
        raise typer.Exit(1)

    cache_dir = config_manager.ensure_cache_dir()
    renderer = ManimRenderer(cache_dir=cache_dir)

    corrector = AutoCorrector(
        provider=llm_provider,
        renderer=renderer,
        max_retries=resolved_retries,
        verbose=resolved_verbose,
    )

    conversation = ConversationManager()
    generated_videos: list[Path] = []

    # ── Banner ────────────────────────────────────────────────────────────
    _print_banner()
    console.print("[bold cyan]Interactive Chat Mode[/bold cyan]")
    console.print("[dim]Describe your animation, render it, then iterate with follow-up changes.[/dim]")
    console.print("[dim]Type [bold]done[/bold], [bold]quit[/bold], or [bold]exit[/bold] to end the session.[/dim]\n")

    # ── Step 1: Initial description ────────────────────────────────────────
    description = Prompt.ask("[bold magenta]🎬 Describe your animation[/bold magenta]")
    if not description.strip():
        log_error("Empty description. Exiting.")
        raise typer.Exit(1)

    # Auto-generate a video name from the description
    base_name = generate_video_name(description)
    version = 1
    output_file = generate_unique_filename(resolved_output, base_name, version)

    # Build initial prompt and generate
    user_prompt = build_user_prompt(description)
    conversation.add_user_message(user_prompt)

    output_path = corrector.run(
        description=description,
        quality=resolved_quality,
        output_dir=resolved_output,
        output_filename=output_file.name,
    )

    if output_path:
        generated_videos.append(output_path)
        # Read back the generated code from the renderer's cache for follow-ups
        last_code = _read_last_generated_code(cache_dir)
        conversation.add_assistant_message(last_code)

        if resolved_preview:
            log_success("Opening video preview…")
            open_video(output_path)
    else:
        log_error("Initial generation failed. Exiting chat session.")
        raise typer.Exit(1)

    # ── Follow-up loop ─────────────────────────────────────────────────────
    while True:
        console.print()
        change_request = Prompt.ask(
            "[bold yellow]✏  Enter follow-up changes[/bold yellow] [dim](or 'done' to finish)[/dim]"
        )
        normalized = change_request.strip().lower()
        if normalized in ("done", "quit", "exit", "q"):
            break

        if not change_request.strip():
            console.print("[dim]Empty input — skipping.[/dim]")
            continue

        version += 1
        output_file = generate_unique_filename(resolved_output, base_name, version)

        # Build follow-up prompt with previous code
        followup_prompt = build_followup_prompt(change_request, last_code)
        conversation.add_user_message(followup_prompt)

        followup_path, new_code = corrector.run_followup(
            messages=conversation.get_messages(),
            quality=resolved_quality,
            output_dir=resolved_output,
            output_filename=output_file.name,
        )

        if followup_path:
            generated_videos.append(followup_path)
            last_code = new_code
            conversation.add_assistant_message(new_code)

            if resolved_preview:
                log_success("Opening video preview…")
                open_video(followup_path)
        else:
            log_error("Follow-up generation failed. You can try again or type 'done' to exit.")
            if new_code:
                conversation.add_assistant_message(new_code)
                last_code = new_code

    # ── Session summary ────────────────────────────────────────────────────
    console.print()
    if generated_videos:
        table = Table(title="[bold cyan]🎞  Generated Videos[/bold cyan]", show_header=True)
        table.add_column("#", style="bold", width=4)
        table.add_column("File", style="green")
        for i, vpath in enumerate(generated_videos, 1):
            table.add_row(str(i), str(vpath))
        console.print(table)
    console.print("\n[bold cyan]👋 Chat session ended. Happy animating![/bold cyan]\n")


def _read_last_generated_code(cache_dir: Path) -> str:
    """Read the most recently created Python script from the cache directory."""
    scripts = sorted(cache_dir.glob("scene_*.py"), key=lambda p: p.stat().st_mtime, reverse=True)
    if scripts:
        return scripts[0].read_text(encoding="utf-8")
    return ""


# ── config ────────────────────────────────────────────────────────────────────

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
    from manimator.config_manager import ConfigManager
    from manimator.utils.logger import console, log_success, log_error
    from rich.table import Table

    config_manager = ConfigManager()
    cfg = config_manager.load()
    changed = False

    if provider is not None:
        if provider not in VALID_PROVIDERS:
            log_error(f"Invalid provider '{provider}'. Choose from: {', '.join(VALID_PROVIDERS)}")
            raise typer.Exit(1)
        cfg.provider = provider
        changed = True
        log_success(f"Provider set to [bold]{provider}[/bold]")

    if key is not None:
        active_provider = provider or cfg.provider
        config_manager.set_api_key(active_provider, key)
        log_success(f"API key stored for [bold]{active_provider}[/bold] (in OS keyring)")

    if model is not None:
        cfg.model = model
        changed = True
        log_success(f"Default model set to [bold]{model}[/bold]")

    if output is not None:
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


# ── list-models ───────────────────────────────────────────────────────────────

@app.command(name="list-models")
def list_models(
    provider: Annotated[
        Optional[str],
        typer.Option("--provider", help="Filter by provider: openai | anthropic | ollama | gemini"),
    ] = None,
) -> None:
    """List available models for all (or a specific) provider."""
    from manimator.config_manager import ConfigManager
    from manimator.utils.logger import console, log_warning
    from rich.table import Table

    config_manager = ConfigManager()
    cfg = config_manager.load()

    providers_to_query = (
        [provider] if provider else ["openai", "anthropic", "gemini", "ollama"]
    )

    PROVIDER_COLORS = {
        "openai": "green",
        "anthropic": "magenta",
        "ollama": "yellow",
        "gemini": "blue",
    }

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
            p = _get_provider_for_listing(pname, cfg, config_manager)
            for m in p.list_models():
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


# ── shared helpers ────────────────────────────────────────────────────────────

def _get_provider(provider_name: str, model: str, config_manager):
    """Instantiate the correct LLM provider for generation."""
    from manimator.utils.logger import log_error
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
        return GeminiProvider(api_key=api_key, model=model or "gemini-2.5-flash-preview-04-17")
    elif provider_name == "ollama":
        from manimator.providers.ollama_provider import OllamaProvider
        return OllamaProvider(model=model)
    else:
        log_error(f"Unknown provider: {provider_name}")
        raise typer.Exit(1)


def _get_provider_for_listing(provider_name: str, cfg, config_manager):
    """Build a provider instance just for listing models (no key required)."""
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

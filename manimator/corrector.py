"""Auto-correction loop for manimator."""

import ast
from pathlib import Path
from typing import Optional

from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from manimator.providers.base import LLMProvider
from manimator.prompt_builder import build_system_prompt, build_user_prompt, build_correction_prompt, build_followup_prompt
from manimator.renderer import ManimRenderer, RenderResult
from manimator.utils.logger import (
    console,
    log_info,
    log_success,
    log_error,
    log_warning,
    log_code,
    log_retry,
    log_panel,
)


def _validate_python_syntax(code: str) -> tuple[bool, str]:
    """Check that the generated code is valid Python."""
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        return False, f"SyntaxError at line {e.lineno}: {e.msg}"


def _extract_code_block(raw: str) -> str:
    """Strip markdown code fences if the LLM included them."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        # Remove first line (```python or ```) and last line (```)
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        return "\n".join(inner).strip()
    return raw


class AutoCorrector:
    """
    Orchestrates the generate → validate → render → correct loop.

    On each failure, the error is sent back to the LLM with the original
    code for an auto-correction attempt, up to max_retries times.
    """

    def __init__(
        self,
        provider: LLMProvider,
        renderer: ManimRenderer,
        max_retries: int = 3,
        verbose: bool = False,
    ) -> None:
        self._provider = provider
        self._renderer = renderer
        self._max_retries = max_retries
        self._verbose = verbose

    def run(
        self,
        description: str,
        quality: str,
        output_dir: Path,
        output_filename: Optional[str] = None,
    ) -> Optional[Path]:
        """
        Run the full pipeline. Returns the output .mp4 path on success, or None.
        """
        system_prompt = build_system_prompt(quality)
        user_prompt = build_user_prompt(description)

        console.rule("[bold blue]🎬 manimator[/bold blue]")
        log_info(f"Prompt: [italic]{description}[/italic]")
        log_info(f"Quality: [bold]{quality}[/bold]  |  Max retries: [bold]{self._max_retries}[/bold]")
        console.print()

        # ── Step 1: Initial code generation ──────────────────────────────────
        code = self._generate_with_spinner(system_prompt, user_prompt, label="Generating Manim code")
        if not code:
            log_error("LLM returned empty response.")
            return None

        code = _extract_code_block(code)

        if self._verbose:
            log_code(code, title="Generated Manim Code (attempt 1)")

        # ── Correction loop ───────────────────────────────────────────────────
        last_error = ""
        for attempt in range(1, self._max_retries + 2):  # +1 for initial attempt
            # Syntax check
            valid, syntax_error = _validate_python_syntax(code)
            if not valid:
                last_error = syntax_error
                log_warning(f"Syntax error detected: {syntax_error}")
            else:
                # Render
                log_info(f"Rendering (attempt {attempt})…")
                result: RenderResult = self._renderer.render(code, quality, output_dir, output_filename)

                if result.success and result.output_path:
                    console.print()
                    log_success(f"Animation rendered successfully!")
                    log_success(f"Output: [bold green]{result.output_path}[/bold green]")
                    return result.output_path

                last_error = result.error

                # Fast-fail for environment errors — these can't be fixed by correcting code.
                # The renderer tags these with "ENV_ERROR:" prefix.
                if last_error.startswith("ENV_ERROR:"):
                    console.print()
                    clean_msg = last_error[len("ENV_ERROR:"):].strip()
                    log_error(clean_msg)
                    if "ffmpeg" in clean_msg.lower():
                        log_panel(
                            "Install ffmpeg on Fedora:\n\n"
                            "  sudo dnf install ffmpeg\n\n"
                            "If ffmpeg is not in the default repos, enable RPM Fusion first:\n\n"
                            "  sudo dnf install https://mirrors.rpmfusion.org/free/fedora/"
                            "rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm\n"
                            "  sudo dnf install ffmpeg",
                            title="Missing Dependency: ffmpeg",
                            style="red",
                        )
                    elif "latex" in clean_msg.lower():
                        log_panel(
                            "LaTeX is required by Manim for rendering math text.\n\n"
                            "Install on Fedora:\n\n"
                            "  sudo dnf install -y texlive-latex texlive-dvipng "
                            "texlive-amsmath texlive-standalone\n\n"
                            "Then re-run your command.",
                            title="Missing Dependency: LaTeX",
                            style="red",
                        )
                    elif "manim" in clean_msg.lower():
                        log_panel(
                            "Install Manim with:\n\n  pip install manim\n\nThen re-run your command.",
                            title="Missing Dependency: manim",
                            style="red",
                        )
                    else:
                        log_panel(clean_msg, title="Environment Error", style="red")
                    return None

            # Check if we've exhausted retries
            if attempt > self._max_retries:
                break

            # ── Auto-correction ───────────────────────────────────────────────
            log_retry(attempt, self._max_retries, last_error[:500])

            correction_prompt = build_correction_prompt(code, last_error)
            corrected = self._generate_with_spinner(
                system_prompt,
                correction_prompt,
                label=f"Auto-correcting (attempt {attempt}/{self._max_retries})",
            )
            if not corrected:
                log_error("LLM returned empty correction response.")
                break

            code = _extract_code_block(corrected)

            if self._verbose:
                log_code(code, title=f"Corrected Code (attempt {attempt + 1})")

        # ── All retries exhausted ─────────────────────────────────────────────
        console.print()
        log_error(f"Failed after {self._max_retries} correction attempt(s).")
        log_panel(
            last_error[-1000:] if len(last_error) > 1000 else last_error,
            title="Last Error",
            style="red",
        )
        console.print(
            "\n[yellow]💡 Tip:[/yellow] Try simplifying your prompt, "
            "or use [bold]--verbose[/bold] to inspect the generated code."
        )
        return None

    def _generate_with_spinner(
        self, system_prompt: str, user_prompt: str, label: str
    ) -> str:
        """Call the LLM provider with a Rich spinner."""
        result = ""
        with Progress(
            SpinnerColumn(),
            TextColumn(f"[bold cyan]{label}…[/bold cyan]"),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("", total=None)
            result = self._provider.generate(system_prompt, user_prompt)
        return result

    def _generate_with_history_spinner(
        self, system_prompt: str, messages: list[dict], label: str
    ) -> str:
        """Call the LLM provider with conversation history and a Rich spinner."""
        result = ""
        with Progress(
            SpinnerColumn(),
            TextColumn(f"[bold cyan]{label}…[/bold cyan]"),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("", total=None)
            result = self._provider.generate_with_history(system_prompt, messages)
        return result

    def run_followup(
        self,
        messages: list[dict],
        quality: str,
        output_dir: Path,
        output_filename: Optional[str] = None,
    ) -> tuple[Optional[Path], str]:
        """
        Run a follow-up generation using conversation history.

        Returns (output_path, generated_code) — output_path is None on failure.
        """
        system_prompt = build_system_prompt(quality)

        console.rule("[bold blue]🎬 manimator — follow-up[/bold blue]")
        console.print()

        # Generate code from conversation history
        code_raw = self._generate_with_history_spinner(
            system_prompt, messages, label="Generating updated Manim code"
        )
        if not code_raw:
            log_error("LLM returned empty response.")
            return None, ""

        code = _extract_code_block(code_raw)

        if self._verbose:
            log_code(code, title="Generated Manim Code (follow-up)")

        # Correction loop (same as run())
        last_error = ""
        for attempt in range(1, self._max_retries + 2):
            valid, syntax_error = _validate_python_syntax(code)
            if not valid:
                last_error = syntax_error
                log_warning(f"Syntax error detected: {syntax_error}")
            else:
                log_info(f"Rendering (attempt {attempt})…")
                result: RenderResult = self._renderer.render(code, quality, output_dir, output_filename)

                if result.success and result.output_path:
                    console.print()
                    log_success("Animation rendered successfully!")
                    log_success(f"Output: [bold green]{result.output_path}[/bold green]")
                    return result.output_path, code

                last_error = result.error

                if last_error.startswith("ENV_ERROR:"):
                    clean_msg = last_error[len("ENV_ERROR:"):].strip()
                    log_error(clean_msg)
                    return None, code

            if attempt > self._max_retries:
                break

            log_retry(attempt, self._max_retries, last_error[:500])
            correction_prompt = build_correction_prompt(code, last_error)
            corrected = self._generate_with_spinner(
                system_prompt,
                correction_prompt,
                label=f"Auto-correcting (attempt {attempt}/{self._max_retries})",
            )
            if not corrected:
                log_error("LLM returned empty correction response.")
                break

            code = _extract_code_block(corrected)

            if self._verbose:
                log_code(code, title=f"Corrected Code (attempt {attempt + 1})")

        console.print()
        log_error(f"Failed after {self._max_retries} correction attempt(s).")
        log_panel(
            last_error[-1000:] if len(last_error) > 1000 else last_error,
            title="Last Error",
            style="red",
        )
        return None, code

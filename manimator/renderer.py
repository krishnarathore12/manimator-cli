"""Manim subprocess renderer for manimator."""

import re
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from manimator.utils.logger import console, log_info, log_error

# Map quality names to Manim CLI flags
QUALITY_FLAGS: dict[str, str] = {
    "low": "-ql",
    "medium": "-qm",
    "high": "-qh",
    "ultra": "-qk",
}

SCENE_CLASS_NAME = "GeneratedScene"


class RenderResult:
    """Result of a Manim render attempt."""

    def __init__(
        self,
        success: bool,
        output_path: Optional[Path] = None,
        error: str = "",
        stdout: str = "",
    ) -> None:
        self.success = success
        self.output_path = output_path
        self.error = error
        self.stdout = stdout


class ManimRenderer:
    """Wraps the Manim CLI as a subprocess."""

    def __init__(self, cache_dir: Path) -> None:
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def write_script(self, code: str) -> Path:
        """Write generated code to a temp .py file and return its path."""
        script_path = self._cache_dir / f"scene_{uuid.uuid4().hex[:8]}.py"
        script_path.write_text(code, encoding="utf-8")
        return script_path

    def render(
        self,
        code: str,
        quality: str,
        output_dir: Path,
        output_filename: Optional[str] = None,
    ) -> RenderResult:
        """
        Render a Manim scene from the given Python code string.

        Returns a RenderResult with success status, output path, and any errors.
        """
        quality_flag = QUALITY_FLAGS.get(quality, "-qm")
        output_dir.mkdir(parents=True, exist_ok=True)

        script_path = self.write_script(code)

        cmd = [
            "manim",
            quality_flag,
            "--output_file", SCENE_CLASS_NAME,
            "--media_dir", str(output_dir / ".manim_media"),
            str(script_path),
            SCENE_CLASS_NAME,
        ]

        log_info(f"Running Manim renderer at [bold]{quality}[/bold] quality…")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5-minute timeout
            )
        except subprocess.TimeoutExpired:
            return RenderResult(
                success=False,
                error="TIMEOUT: Manim render timed out after 5 minutes.",
            )
        except FileNotFoundError:
            return RenderResult(
                success=False,
                error=(
                    "ENV_ERROR: Manim executable not found. "
                    "Please install it with: pip install manim"
                ),
            )

        combined_output = result.stdout + result.stderr

        # Detect ffmpeg missing — Manim raises FileNotFoundError internally
        # which shows up as a Python traceback in the output
        if "FileNotFoundError" in combined_output and "ffmpeg" in combined_output.lower():
            return RenderResult(
                success=False,
                error="ENV_ERROR: ffmpeg not found. Please install ffmpeg (e.g. sudo dnf install ffmpeg).",
                stdout=combined_output,
            )
        # Also catch the generic Popen FileNotFoundError without ffmpeg mention
        if "FileNotFoundError" in combined_output and "[Errno 2]" in combined_output:
            # Extract the actual missing executable name from the error
            import re as _re
            match = _re.search(r"FileNotFoundError.*?'([^']+)'", combined_output)
            missing = match.group(1) if match else "a required executable"
            return RenderResult(
                success=False,
                error=f"ENV_ERROR: Required program not found: '{missing}'. Make sure ffmpeg and LaTeX are installed.",
                stdout=combined_output,
            )

        # Detect LaTeX compilation failures — these are environment issues, not code bugs
        if "latex error converting to" in combined_output.lower():
            return RenderResult(
                success=False,
                error="ENV_ERROR: LaTeX compilation failed. LaTeX is either not installed or missing packages.",
                stdout=combined_output,
            )

        if result.returncode == 0:
            # Find the output .mp4 file
            mp4_path = self._find_output_mp4(output_dir / ".manim_media", quality)
            if mp4_path:
                # Copy to the user's output dir with custom or default name
                fname = output_filename or f"{SCENE_CLASS_NAME}.mp4"
                if not fname.endswith(".mp4"):
                    fname += ".mp4"
                final_path = output_dir / fname
                import shutil
                shutil.copy2(mp4_path, final_path)
                return RenderResult(
                    success=True,
                    output_path=final_path,
                    stdout=combined_output,
                )
            # Manim succeeded but we can't find the file — search more broadly
            mp4_path = self._find_output_mp4_broad(output_dir)
            if mp4_path:
                return RenderResult(
                    success=True,
                    output_path=mp4_path,
                    stdout=combined_output,
                )

        return RenderResult(
            success=False,
            error=self._extract_error(combined_output),
            stdout=combined_output,
        )

    def _find_output_mp4(self, media_dir: Path, quality: str) -> Optional[Path]:
        """Search for the rendered .mp4 inside Manim's media directory."""
        quality_dir_map = {
            "low": "480p15",
            "medium": "720p30",
            "high": "1080p60",
            "ultra": "2160p60",
        }
        subdir = quality_dir_map.get(quality, "720p30")

        # Manim puts files in media_dir/videos/<script_name>/<quality>/
        for mp4 in media_dir.rglob("*.mp4"):
            if subdir in str(mp4) or SCENE_CLASS_NAME in mp4.stem:
                return mp4
        return None

    def _find_output_mp4_broad(self, search_root: Path) -> Optional[Path]:
        """Broad search for any .mp4 in the output directory tree."""
        mp4s = list(search_root.rglob("*.mp4"))
        if mp4s:
            # Return the most recently modified one
            return max(mp4s, key=lambda p: p.stat().st_mtime)
        return None

    def _extract_error(self, output: str) -> str:
        """Extract the most relevant error lines from Manim output."""
        lines = output.splitlines()
        error_lines = []
        capture = False
        for line in lines:
            if any(kw in line for kw in ("Error", "Traceback", "Exception", "error:")):
                capture = True
            if capture:
                error_lines.append(line)
        # Return last 30 lines of error context
        relevant = error_lines[-30:] if len(error_lines) > 30 else error_lines
        return "\n".join(relevant) if relevant else output[-2000:]

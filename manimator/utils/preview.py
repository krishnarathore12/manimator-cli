"""Cross-platform video preview utility."""

import subprocess
import sys
from pathlib import Path


def open_video(path: str | Path) -> None:
    """Open a video file in the system's default media player."""
    path = str(path)
    if sys.platform == "darwin":
        subprocess.Popen(["open", path])
    elif sys.platform == "win32":
        subprocess.Popen(["start", path], shell=True)
    else:
        # Linux / BSD
        subprocess.Popen(["xdg-open", path])

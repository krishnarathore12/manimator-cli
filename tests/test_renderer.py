"""Tests for ManimRenderer."""

import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from manimator.renderer import ManimRenderer, QUALITY_FLAGS, SCENE_CLASS_NAME


class TestQualityFlags:
    def test_all_qualities_mapped(self):
        for quality in ["low", "medium", "high", "ultra"]:
            assert quality in QUALITY_FLAGS

    def test_flag_values(self):
        assert QUALITY_FLAGS["low"] == "-ql"
        assert QUALITY_FLAGS["medium"] == "-qm"
        assert QUALITY_FLAGS["high"] == "-qh"
        assert QUALITY_FLAGS["ultra"] == "-qk"


class TestManimRenderer:
    def test_write_script(self, tmp_path):
        renderer = ManimRenderer(cache_dir=tmp_path)
        code = "from manim import *\nclass GeneratedScene(Scene): pass"
        script_path = renderer.write_script(code)
        assert script_path.exists()
        assert script_path.read_text() == code
        assert script_path.suffix == ".py"

    def test_render_success(self, tmp_path):
        renderer = ManimRenderer(cache_dir=tmp_path)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create a fake mp4 file that the renderer would find
        media_dir = output_dir / ".manim_media"
        media_dir.mkdir()
        fake_mp4_dir = media_dir / "videos" / "scene" / "720p30"
        fake_mp4_dir.mkdir(parents=True)
        fake_mp4 = fake_mp4_dir / f"{SCENE_CLASS_NAME}.mp4"
        fake_mp4.write_bytes(b"fake video data")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Manim Community v0.18.0\nFile ready at..."
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            result = renderer.render("some code", "medium", output_dir)

        assert result.success is True
        assert result.output_path is not None

    def test_render_failure(self, tmp_path):
        renderer = ManimRenderer(cache_dir=tmp_path)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: NameError: name 'Foo' is not defined\nTraceback..."

        with patch("subprocess.run", return_value=mock_result):
            result = renderer.render("bad code", "medium", output_dir)

        assert result.success is False
        assert "NameError" in result.error or len(result.error) > 0

    def test_render_manim_not_found(self, tmp_path):
        renderer = ManimRenderer(cache_dir=tmp_path)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = renderer.render("some code", "medium", output_dir)

        assert result.success is False
        assert "not found" in result.error.lower() or "manim" in result.error.lower()

    def test_render_timeout(self, tmp_path):
        renderer = ManimRenderer(cache_dir=tmp_path)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="manim", timeout=300)):
            result = renderer.render("some code", "medium", output_dir)

        assert result.success is False
        assert "timed out" in result.error.lower()

    def test_extract_error_from_output(self, tmp_path):
        renderer = ManimRenderer(cache_dir=tmp_path)
        output = "Some normal output\nTraceback (most recent call last):\n  File 'x.py', line 5\nNameError: name 'Foo' is not defined"
        error = renderer._extract_error(output)
        assert "NameError" in error or "Traceback" in error

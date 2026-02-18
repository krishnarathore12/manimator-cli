"""Tests for prompt_builder module."""

from manimator.prompt_builder import (
    build_system_prompt,
    build_user_prompt,
    build_correction_prompt,
)


class TestBuildSystemPrompt:
    def test_contains_scene_class_name(self):
        prompt = build_system_prompt("medium")
        assert "GeneratedScene" in prompt

    def test_contains_manim_import_rule(self):
        prompt = build_system_prompt("medium")
        assert "manim" in prompt.lower()

    def test_quality_injected(self):
        for quality in ["low", "medium", "high", "ultra"]:
            prompt = build_system_prompt(quality)
            assert quality.upper() in prompt

    def test_quality_hint_injected(self):
        low_prompt = build_system_prompt("low")
        assert "simple" in low_prompt.lower() or "fast" in low_prompt.lower()

        ultra_prompt = build_system_prompt("ultra")
        assert "publication" in ultra_prompt.lower() or "maximum" in ultra_prompt.lower()

    def test_no_markdown_fences_rule(self):
        prompt = build_system_prompt("medium")
        assert "ONLY" in prompt or "only" in prompt


class TestBuildUserPrompt:
    def test_contains_description(self):
        desc = "Show a Fourier series approximation"
        prompt = build_user_prompt(desc)
        assert desc in prompt

    def test_contains_class_name_reminder(self):
        prompt = build_user_prompt("any description")
        assert "GeneratedScene" in prompt


class TestBuildCorrectionPrompt:
    def test_contains_original_code(self):
        code = "from manim import *\nclass GeneratedScene(Scene): pass"
        error = "NameError: name 'Foo' is not defined"
        prompt = build_correction_prompt(code, error)
        assert code in prompt

    def test_contains_error(self):
        code = "some code"
        error = "SyntaxError at line 5"
        prompt = build_correction_prompt(code, error)
        assert error in prompt

    def test_contains_fix_instruction(self):
        prompt = build_correction_prompt("code", "error")
        assert "fix" in prompt.lower() or "correct" in prompt.lower()

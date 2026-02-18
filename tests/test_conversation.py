"""Tests for conversation manager and follow-up features."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from manimator.conversation import (
    ConversationManager,
    generate_video_name,
    generate_unique_filename,
)
from manimator.prompt_builder import build_followup_prompt
from manimator.providers.base import LLMProvider


class TestGenerateVideoName:
    def test_basic_description(self):
        assert generate_video_name("a spinning blue circle") == "spinning_blue_circle"

    def test_strips_filler_words(self):
        result = generate_video_name("Show the Pythagorean theorem with animation")
        assert result == "show_pythagorean_theorem_animation"

    def test_truncates_to_four_words(self):
        result = generate_video_name("create a beautiful rotating 3d cube that spins")
        assert len(result.split("_")) <= 4

    def test_removes_special_characters(self):
        result = generate_video_name("Show f(x) = x^2 graph!")
        assert "(" not in result
        assert "!" not in result

    def test_empty_description(self):
        assert generate_video_name("") == "animation"

    def test_only_filler_words(self):
        assert generate_video_name("a the an") == "animation"


class TestGenerateUniqueFilename:
    def test_creates_v1(self, tmp_path):
        result = generate_unique_filename(tmp_path, "test", 1)
        assert result == tmp_path / "test_v1.mp4"

    def test_creates_v2(self, tmp_path):
        result = generate_unique_filename(tmp_path, "test", 2)
        assert result == tmp_path / "test_v2.mp4"

    def test_skips_existing_files(self, tmp_path):
        # Create v1 so it should skip to v2
        (tmp_path / "test_v1.mp4").write_bytes(b"fake")
        result = generate_unique_filename(tmp_path, "test", 1)
        assert result == tmp_path / "test_v2.mp4"

    def test_skips_multiple_existing(self, tmp_path):
        (tmp_path / "test_v1.mp4").write_bytes(b"fake")
        (tmp_path / "test_v2.mp4").write_bytes(b"fake")
        (tmp_path / "test_v3.mp4").write_bytes(b"fake")
        result = generate_unique_filename(tmp_path, "test", 1)
        assert result == tmp_path / "test_v4.mp4"

    def test_creates_output_dir_if_missing(self, tmp_path):
        out = tmp_path / "new_dir" / "subdir"
        result = generate_unique_filename(out, "test", 1)
        assert out.exists()
        assert result == out / "test_v1.mp4"


class TestConversationManager:
    def test_empty_initially(self):
        cm = ConversationManager()
        assert len(cm) == 0
        assert cm.get_messages() == []

    def test_add_user_message(self):
        cm = ConversationManager()
        cm.add_user_message("hello")
        msgs = cm.get_messages()
        assert len(msgs) == 1
        assert msgs[0] == {"role": "user", "content": "hello"}

    def test_add_assistant_message(self):
        cm = ConversationManager()
        cm.add_assistant_message("code here")
        msgs = cm.get_messages()
        assert len(msgs) == 1
        assert msgs[0] == {"role": "assistant", "content": "code here"}

    def test_preserves_order(self):
        cm = ConversationManager()
        cm.add_user_message("first")
        cm.add_assistant_message("second")
        cm.add_user_message("third")
        msgs = cm.get_messages()
        assert len(msgs) == 3
        assert msgs[0]["content"] == "first"
        assert msgs[1]["content"] == "second"
        assert msgs[2]["content"] == "third"

    def test_get_messages_returns_copy(self):
        cm = ConversationManager()
        cm.add_user_message("test")
        msgs = cm.get_messages()
        msgs.clear()
        assert len(cm.get_messages()) == 1  # original unaffected


class TestBuildFollowupPrompt:
    def test_includes_previous_code(self):
        result = build_followup_prompt("make it red", "from manim import *\nclass GeneratedScene(Scene): pass")
        assert "from manim import *" in result
        assert "GeneratedScene" in result

    def test_includes_change_request(self):
        result = build_followup_prompt("make it red", "some code")
        assert "make it red" in result

    def test_includes_instructions(self):
        result = build_followup_prompt("change", "code")
        assert "GeneratedScene" in result


class TestBaseProviderFallback:
    def test_generate_with_history_falls_back(self):
        """The default generate_with_history should use the last user message."""

        class MockProvider(LLMProvider):
            def generate(self, system_prompt: str, user_prompt: str) -> str:
                return f"GENERATED:{user_prompt}"

            def list_models(self) -> list[dict]:
                return []

        provider = MockProvider()
        messages = [
            {"role": "user", "content": "first message"},
            {"role": "assistant", "content": "response"},
            {"role": "user", "content": "second message"},
        ]
        result = provider.generate_with_history("system", messages)
        assert result == "GENERATED:second message"

    def test_generate_with_history_empty_messages(self):
        class MockProvider(LLMProvider):
            def generate(self, system_prompt: str, user_prompt: str) -> str:
                return f"GENERATED:{user_prompt}"

            def list_models(self) -> list[dict]:
                return []

        provider = MockProvider()
        result = provider.generate_with_history("system", [])
        assert result == "GENERATED:"

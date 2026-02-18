"""Tests for ConfigManager."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from manimator.config_manager import ManimatorConfig, ConfigManager


class TestManimatorConfig:
    def test_defaults(self):
        cfg = ManimatorConfig()
        assert cfg.provider == "openai"
        assert cfg.model == "gpt-4o"
        assert cfg.max_retries == 3
        assert cfg.default_quality == "medium"
        assert cfg.auto_preview is False
        assert cfg.verbose is False

    def test_custom_values(self):
        cfg = ManimatorConfig(
            provider="anthropic",
            model="claude-sonnet-4-5",
            max_retries=5,
            default_quality="high",
        )
        assert cfg.provider == "anthropic"
        assert cfg.model == "claude-sonnet-4-5"
        assert cfg.max_retries == 5
        assert cfg.default_quality == "high"

    def test_invalid_retries(self):
        with pytest.raises(Exception):
            ManimatorConfig(max_retries=0)

    def test_invalid_provider(self):
        with pytest.raises(Exception):
            ManimatorConfig(provider="unknown_provider")

    def test_invalid_quality(self):
        with pytest.raises(Exception):
            ManimatorConfig(default_quality="super_ultra")


class TestConfigManager:
    def test_load_defaults_when_no_file(self, tmp_path):
        manager = ConfigManager()
        with patch.object(manager, "_config_path", tmp_path / "nonexistent.json"):
            cfg = manager.load()
        assert isinstance(cfg, ManimatorConfig)
        assert cfg.provider == "openai"

    def test_save_and_load_roundtrip(self, tmp_path):
        manager = ConfigManager()
        config_file = tmp_path / "config.json"
        with patch.object(manager, "_config_path", config_file):
            cfg = ManimatorConfig(provider="gemini", model="gemini-2.5-flash", max_retries=7)
            manager.save(cfg)
            loaded = manager.load()
        assert loaded.provider == "gemini"
        assert loaded.model == "gemini-2.5-flash"
        assert loaded.max_retries == 7

    def test_save_creates_parent_dirs(self, tmp_path):
        manager = ConfigManager()
        config_file = tmp_path / "deep" / "nested" / "config.json"
        with patch.object(manager, "_config_path", config_file):
            cfg = ManimatorConfig()
            manager.save(cfg)
        assert config_file.exists()

    def test_load_corrupt_file_returns_defaults(self, tmp_path):
        manager = ConfigManager()
        config_file = tmp_path / "config.json"
        config_file.write_text("{ invalid json !!!", encoding="utf-8")
        with patch.object(manager, "_config_path", config_file):
            cfg = manager.load()
        assert isinstance(cfg, ManimatorConfig)

    def test_get_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
        manager = ConfigManager()
        with patch("keyring.get_password", return_value=None):
            key = manager.get_api_key("openai")
        assert key == "test-key-123"

    def test_masked_config_masks_key(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-abcdefghijklmnopqrstuvwxyz1234")
        manager = ConfigManager()
        cfg = ManimatorConfig()
        with patch("keyring.get_password", return_value=None):
            masked = manager.masked_config(cfg)
        assert "api_key" in masked
        assert "sk-abcde" in masked["api_key"]
        assert "1234" in masked["api_key"]

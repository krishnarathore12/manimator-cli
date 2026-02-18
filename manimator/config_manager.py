"""Configuration management for manimator."""

import json
import os
import sys
from pathlib import Path
from typing import Literal, Optional

import keyring
from pydantic import BaseModel, field_validator

KEYRING_SERVICE = "manimator"


class ManimatorConfig(BaseModel):
    """Pydantic v2 schema for manimator configuration."""

    provider: Literal["openai", "anthropic", "ollama", "gemini"] = "openai"
    model: str = "gpt-4o"
    output_dir: str = str(Path.home() / "Videos" / "manimator")
    max_retries: int = 3
    default_quality: Literal["low", "medium", "high", "ultra"] = "medium"
    auto_preview: bool = False
    verbose: bool = False

    @field_validator("max_retries")
    @classmethod
    def retries_must_be_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("max_retries must be at least 1")
        return v


def _get_config_path() -> Path:
    """Return the platform-appropriate config file path."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "manimator" / "config.json"


def _get_cache_dir() -> Path:
    """Return the platform-appropriate cache directory for temp scripts."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return base / "manimator" / "scripts"


class ConfigManager:
    """Manages loading, saving, and validating manimator configuration."""

    def __init__(self) -> None:
        self._config_path = _get_config_path()
        self._cache_dir = _get_cache_dir()

    @property
    def config_path(self) -> Path:
        return self._config_path

    @property
    def cache_dir(self) -> Path:
        return self._cache_dir

    def load(self) -> ManimatorConfig:
        """Load config from disk, returning defaults if the file doesn't exist."""
        if self._config_path.exists():
            try:
                data = json.loads(self._config_path.read_text(encoding="utf-8"))
                return ManimatorConfig(**data)
            except Exception:
                # Corrupt config — return defaults
                return ManimatorConfig()
        return ManimatorConfig()

    def save(self, config: ManimatorConfig) -> None:
        """Persist config to disk."""
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config_path.write_text(
            config.model_dump_json(indent=2), encoding="utf-8"
        )

    def ensure_cache_dir(self) -> Path:
        """Create and return the temp script cache directory."""
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        return self._cache_dir

    # ── API key helpers ──────────────────────────────────────────────────────

    def set_api_key(self, provider: str, key: str) -> None:
        """Store an API key in the OS keyring."""
        keyring.set_password(KEYRING_SERVICE, provider, key)

    def get_api_key(self, provider: str) -> Optional[str]:
        """Retrieve an API key from the OS keyring."""
        # Also check environment variables as a fallback
        env_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GEMINI_API_KEY",
        }
        key = keyring.get_password(KEYRING_SERVICE, provider)
        if key:
            return key
        env_var = env_map.get(provider)
        if env_var:
            return os.environ.get(env_var)
        return None

    def masked_config(self, config: ManimatorConfig) -> dict:
        """Return config as a dict with API keys masked."""
        data = config.model_dump()
        # Add masked key info
        key = self.get_api_key(config.provider)
        if key:
            data["api_key"] = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
        else:
            data["api_key"] = "(not set)"
        return data

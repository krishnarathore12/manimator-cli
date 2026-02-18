"""Conversation history manager for manimator chat sessions."""

import re
from pathlib import Path


# Common filler words to strip when generating slugs
_FILLER_WORDS = frozenset({
    "a", "an", "the", "that", "which", "with", "and", "or", "of", "for",
    "to", "in", "on", "at", "by", "is", "it", "its", "my", "me",
    "this", "from", "into", "about", "some", "very", "really",
})


def generate_video_name(description: str) -> str:
    """
    Auto-generate a short snake_case slug from a user description.

    Examples:
        "a spinning blue circle"  -> "spinning_blue_circle"
        "Show the Pythagorean theorem with animation"  -> "pythagorean_theorem_animation"
    """
    # Lowercase, keep only alphanumeric and spaces
    text = re.sub(r"[^a-z0-9\s]", "", description.lower())
    words = text.split()
    # Strip filler words
    words = [w for w in words if w not in _FILLER_WORDS]
    # Take up to 4 meaningful words
    slug = "_".join(words[:4])
    return slug or "animation"


def generate_unique_filename(output_dir: Path, base_name: str, version: int) -> Path:
    """
    Generate a unique output filename like `<base_name>_v<version>.mp4`.

    If the file already exists, increment the version until a free slot is found.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    while True:
        path = output_dir / f"{base_name}_v{version}.mp4"
        if not path.exists():
            return path
        version += 1


class ConversationManager:
    """Manages multi-turn conversation history for chat sessions."""

    def __init__(self) -> None:
        self._messages: list[dict] = []

    def add_user_message(self, content: str) -> None:
        """Append a user message to the conversation history."""
        self._messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str) -> None:
        """Append an assistant (LLM) response to the conversation history."""
        self._messages.append({"role": "assistant", "content": content})

    def get_messages(self) -> list[dict]:
        """Return a copy of the full conversation message list."""
        return list(self._messages)

    def __len__(self) -> int:
        return len(self._messages)

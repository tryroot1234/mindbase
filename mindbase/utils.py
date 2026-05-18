"""Utility functions for mindbase."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path


def open_editor(content: str = "") -> str:
    """Open the user's preferred editor and return the content."""
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
    if not editor:
        # Try common editors
        for cmd in ("vim", "nvim", "nano", "vi", "notepad"):
            if _command_exists(cmd):
                editor = cmd
                break
    if not editor:
        editor = "notepad"

    with tempfile.NamedTemporaryFile(
        suffix=".md", mode="w", delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        tmp_path = f.name

    try:
        subprocess.run([editor, tmp_path], check=True)
        return Path(tmp_path).read_text(encoding="utf-8")
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def _command_exists(cmd: str) -> bool:
    """Check if a command exists on PATH."""
    try:
        subprocess.run(
            [cmd, "--version"] if cmd != "notepad" else [cmd],
            capture_output=True,
            timeout=2,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def truncate(text: str, max_len: int = 80) -> str:
    """Truncate text to max_len, adding ellipsis if needed."""
    text = text.replace("\n", " ").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def format_tags(tags: list[str]) -> str:
    """Format tags for display."""
    if not tags:
        return ""
    return " ".join(f"#{t}" for t in tags)

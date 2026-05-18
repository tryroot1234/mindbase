"""Utility functions for mindbase."""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path


QUIT_MARKER = "<!-- QUIT: Save this file empty to discard changes -->\n\n"


def _sanitize_filename(name: str) -> str:
    """Sanitize a string for use as a filename."""
    # Remove invalid characters
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', name)
    # Collapse whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    # Truncate
    if len(name) > 100:
        name = name[:100].strip()
    return name or "untitled"


def open_editor(content: str = "", title: str = "", allow_quit: bool = True) -> str | None:
    """Open the user's preferred editor and return the content.

    If allow_quit is True and the file is saved empty, returns None
    to indicate the user wants to discard changes.
    """
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
    if not editor:
        for cmd in ("vim", "nvim", "nano", "vi", "notepad"):
            if _command_exists(cmd):
                editor = cmd
                break
    if not editor:
        editor = "notepad"

    header = QUIT_MARKER if allow_quit else ""
    filename = _sanitize_filename(title) + ".md" if title else None

    if filename:
        tmp_dir = tempfile.mkdtemp()
        tmp_path = os.path.join(tmp_dir, filename)
        Path(tmp_path).write_text(header + content, encoding="utf-8")
    else:
        with tempfile.NamedTemporaryFile(
            suffix=".md", mode="w", delete=False, encoding="utf-8"
        ) as f:
            f.write(header + content)
            tmp_path = f.name

    try:
        subprocess.run([editor, tmp_path], check=True)
        raw = Path(tmp_path).read_text(encoding="utf-8")
        # Strip the quit marker if present
        if allow_quit and raw.startswith(QUIT_MARKER.strip()):
            raw = raw[len(QUIT_MARKER):]
        # Empty content means discard
        if allow_quit and not raw.strip():
            return None
        return raw
    finally:
        Path(tmp_path).unlink(missing_ok=True)
        if filename:
            Path(tmp_dir).rmdir()


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

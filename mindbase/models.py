"""Data models for mindbase."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Entry:
    """A knowledge base entry."""

    id: int | None = None
    title: str = ""
    content: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def tag_string(self) -> str:
        return ", ".join(self.tags) if self.tags else ""

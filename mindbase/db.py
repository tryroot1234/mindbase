"""SQLite database layer for mindbase."""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

from mindbase.models import Entry

# CJK Unified Ideographs and extensions
_CJK_RANGES = (
    (0x4E00, 0x9FFF),    # CJK Unified Ideographs
    (0x3400, 0x4DBF),    # CJK Unified Ideographs Extension A
    (0x20000, 0x2A6DF),  # CJK Unified Ideographs Extension B
    (0x2A700, 0x2B73F),  # CJK Unified Ideographs Extension C
    (0x2B740, 0x2B81F),  # CJK Unified Ideographs Extension D
    (0xF900, 0xFAFF),    # CJK Compatibility Ideographs
    (0x3000, 0x303F),    # CJK Symbols and Punctuation
    (0xFF00, 0xFFEF),    # Fullwidth Forms
    (0x3040, 0x309F),    # Hiragana
    (0x30A0, 0x30FF),    # Katakana
)

_CJK_RE = re.compile(
    "[" + "".join(chr(s) + "-" + chr(e) for s, e in _CJK_RANGES) + "]"
)


def _tokenize_cjk(text: str) -> str:
    """Insert spaces around CJK characters for FTS5 tokenization.

    Each CJK character becomes a standalone token, while Latin/other
    text is preserved as-is. This allows substring search on CJK text.
    """
    result = []
    for ch in text:
        cp = ord(ch)
        is_cjk = any(s <= cp <= e for s, e in _CJK_RANGES)
        if is_cjk:
            result.append(f" {ch} ")
        else:
            result.append(ch)
    return "".join(result)

DEFAULT_DB_DIR = Path.home() / ".mindbase"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "mindbase.db"


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Get a database connection, creating the DB if needed."""
    path = db_path or DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _init_schema(conn)
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    """Initialize the database schema."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL DEFAULT '',
            title_fts TEXT NOT NULL DEFAULT '',
            content_fts TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS entry_tags (
            entry_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (entry_id, tag_id),
            FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
            title_fts, content_fts, content=entries, content_rowid=id,
            tokenize='unicode61'
        );

        CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN
            INSERT INTO entries_fts(rowid, title_fts, content_fts)
            VALUES (new.id, new.title_fts, new.content_fts);
        END;

        CREATE TRIGGER IF NOT EXISTS entries_ad AFTER DELETE ON entries BEGIN
            INSERT INTO entries_fts(entries_fts, rowid, title_fts, content_fts)
            VALUES ('delete', old.id, old.title_fts, old.content_fts);
        END;

        CREATE TRIGGER IF NOT EXISTS entries_au AFTER UPDATE ON entries BEGIN
            INSERT INTO entries_fts(entries_fts, rowid, title_fts, content_fts)
            VALUES ('delete', old.id, old.title_fts, old.content_fts);
            INSERT INTO entries_fts(rowid, title_fts, content_fts)
            VALUES (new.id, new.title_fts, new.content_fts);
        END;
    """)
    conn.commit()


# --- Entry CRUD ---

def add_entry(conn: sqlite3.Connection, entry: Entry) -> Entry:
    """Add a new entry to the database."""
    now = datetime.now(UTC).isoformat()
    title_fts = _tokenize_cjk(entry.title)
    content_fts = _tokenize_cjk(entry.content)
    cur = conn.execute(
        "INSERT INTO entries (title, content, title_fts, content_fts, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (entry.title, entry.content, title_fts, content_fts, now, now),
    )
    entry.id = cur.lastrowid
    entry.created_at = datetime.fromisoformat(now)
    entry.updated_at = entry.created_at
    _sync_tags(conn, entry)
    conn.commit()
    return entry


def update_entry(conn: sqlite3.Connection, entry: Entry) -> Entry:
    """Update an existing entry."""
    now = datetime.now(UTC).isoformat()
    title_fts = _tokenize_cjk(entry.title)
    content_fts = _tokenize_cjk(entry.content)
    conn.execute(
        "UPDATE entries SET title=?, content=?, title_fts=?, content_fts=?, updated_at=? WHERE id=?",
        (entry.title, entry.content, title_fts, content_fts, now, entry.id),
    )
    entry.updated_at = datetime.fromisoformat(now)
    _sync_tags(conn, entry)
    conn.commit()
    return entry


def delete_entry(conn: sqlite3.Connection, entry_id: int) -> bool:
    """Delete an entry by ID."""
    cur = conn.execute("DELETE FROM entries WHERE id=?", (entry_id,))
    conn.commit()
    return cur.rowcount > 0


def get_entry(conn: sqlite3.Connection, entry_id: int) -> Entry | None:
    """Get a single entry by ID."""
    row = conn.execute(
        "SELECT id, title, content, created_at, updated_at FROM entries WHERE id=?",
        (entry_id,),
    ).fetchone()
    if not row:
        return None
    return _row_to_entry(conn, row)


def list_entries(
    conn: sqlite3.Connection,
    tag: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Entry]:
    """List entries, optionally filtered by tag."""
    if tag:
        rows = conn.execute(
            """SELECT e.id, e.title, e.content, e.created_at, e.updated_at
               FROM entries e
               JOIN entry_tags et ON e.id = et.entry_id
               JOIN tags t ON et.tag_id = t.id
               WHERE t.name = ?
               ORDER BY e.updated_at DESC
               LIMIT ? OFFSET ?""",
            (tag, limit, offset),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, title, content, created_at, updated_at FROM entries "
            "ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [_row_to_entry(conn, r) for r in rows]


def search_entries(
    conn: sqlite3.Connection, query: str, limit: int = 20
) -> list[Entry]:
    """Full-text search entries with CJK support."""
    tokenized = _tokenize_cjk(query).strip()
    if not tokenized:
        return []

    # Build a query that matches any token (OR logic for broad results)
    tokens = tokenized.split()
    if len(tokens) > 1:
        fts_query = " OR ".join(f'"{t}"' for t in tokens)
    else:
        fts_query = f'"{tokens[0]}"'

    rows = conn.execute(
        """SELECT e.id, e.title, e.content, e.created_at, e.updated_at
           FROM entries_fts fts
           JOIN entries e ON e.id = fts.rowid
           WHERE entries_fts MATCH ?
           ORDER BY rank
           LIMIT ?""",
        (fts_query, limit),
    ).fetchall()
    return [_row_to_entry(conn, r) for r in rows]


def count_entries(conn: sqlite3.Connection) -> int:
    """Get total entry count."""
    row = conn.execute("SELECT COUNT(*) FROM entries").fetchone()
    return row[0]


def list_all_tags(conn: sqlite3.Connection) -> list[tuple[str, int]]:
    """List all tags with their usage count."""
    rows = conn.execute(
        """SELECT t.name, COUNT(et.entry_id) as cnt
           FROM tags t
           LEFT JOIN entry_tags et ON t.id = et.tag_id
           GROUP BY t.id
           ORDER BY cnt DESC"""
    ).fetchall()
    return [(r["name"], r["cnt"]) for r in rows]


def export_entries(conn: sqlite3.Connection) -> list[dict]:
    """Export all entries as dicts."""
    rows = conn.execute(
        "SELECT id, title, content, created_at, updated_at FROM entries ORDER BY id"
    ).fetchall()
    result = []
    for r in rows:
        tags = _get_tags_for_entry(conn, r["id"])
        result.append({
            "id": r["id"],
            "title": r["title"],
            "content": r["content"],
            "tags": tags,
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        })
    return result


def import_entries(conn: sqlite3.Connection, data: list[dict]) -> int:
    """Import entries from dicts. Returns count imported."""
    count = 0
    for item in data:
        entry = Entry(
            title=item.get("title", ""),
            content=item.get("content", ""),
            tags=item.get("tags", []),
        )
        add_entry(conn, entry)
        count += 1
    return count


# --- Tag helpers ---

def _get_or_create_tag(conn: sqlite3.Connection, name: str) -> int:
    """Get tag ID by name, creating if needed."""
    row = conn.execute("SELECT id FROM tags WHERE name=?", (name,)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute("INSERT INTO tags (name) VALUES (?)", (name,))
    return cur.lastrowid


def _sync_tags(conn: sqlite3.Connection, entry: Entry) -> None:
    """Sync tags for an entry (replace all)."""
    conn.execute("DELETE FROM entry_tags WHERE entry_id=?", (entry.id,))
    for tag_name in entry.tags:
        tag_id = _get_or_create_tag(conn, tag_name.strip().lower())
        conn.execute(
            "INSERT OR IGNORE INTO entry_tags (entry_id, tag_id) VALUES (?, ?)",
            (entry.id, tag_id),
        )


def _get_tags_for_entry(conn: sqlite3.Connection, entry_id: int) -> list[str]:
    """Get tag names for an entry."""
    rows = conn.execute(
        """SELECT t.name FROM tags t
           JOIN entry_tags et ON t.id = et.tag_id
           WHERE et.entry_id = ?""",
        (entry_id,),
    ).fetchall()
    return [r["name"] for r in rows]


def _row_to_entry(conn: sqlite3.Connection, row: sqlite3.Row) -> Entry:
    """Convert a DB row to an Entry model."""
    return Entry(
        id=row["id"],
        title=row["title"],
        content=row["content"],
        tags=_get_tags_for_entry(conn, row["id"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )

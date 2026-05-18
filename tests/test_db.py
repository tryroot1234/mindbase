"""Tests for the database layer."""

import sqlite3
from pathlib import Path

import pytest

from mindbase.db import (
    add_entry,
    count_entries,
    delete_entry,
    export_entries,
    get_connection,
    get_entry,
    import_entries,
    list_all_tags,
    list_entries,
    search_entries,
    update_entry,
)
from mindbase.models import Entry


@pytest.fixture
def conn(tmp_path: Path) -> sqlite3.Connection:
    """Create a temporary database connection."""
    db_path = tmp_path / "test.db"
    c = get_connection(db_path)
    yield c
    c.close()


def test_add_entry(conn: sqlite3.Connection) -> None:
    entry = Entry(title="Test Note", content="Hello world", tags=["python", "test"])
    entry = add_entry(conn, entry)
    assert entry.id is not None
    assert entry.title == "Test Note"
    assert entry.content == "Hello world"
    assert set(entry.tags) == {"python", "test"}


def test_get_entry(conn: sqlite3.Connection) -> None:
    entry = add_entry(conn, Entry(title="Find me", content="content"))
    found = get_entry(conn, entry.id)
    assert found is not None
    assert found.title == "Find me"


def test_get_entry_not_found(conn: sqlite3.Connection) -> None:
    assert get_entry(conn, 999) is None


def test_update_entry(conn: sqlite3.Connection) -> None:
    entry = add_entry(conn, Entry(title="Old", content="old content"))
    entry.title = "New"
    entry.content = "new content"
    entry.tags = ["updated"]
    entry = update_entry(conn, entry)

    found = get_entry(conn, entry.id)
    assert found.title == "New"
    assert found.content == "new content"
    assert found.tags == ["updated"]


def test_delete_entry(conn: sqlite3.Connection) -> None:
    entry = add_entry(conn, Entry(title="Delete me"))
    assert delete_entry(conn, entry.id) is True
    assert get_entry(conn, entry.id) is None


def test_delete_entry_not_found(conn: sqlite3.Connection) -> None:
    assert delete_entry(conn, 999) is False


def test_list_entries(conn: sqlite3.Connection) -> None:
    add_entry(conn, Entry(title="A"))
    add_entry(conn, Entry(title="B"))
    add_entry(conn, Entry(title="C"))
    entries = list_entries(conn)
    assert len(entries) == 3


def test_list_entries_with_tag(conn: sqlite3.Connection) -> None:
    add_entry(conn, Entry(title="Tagged", tags=["python"]))
    add_entry(conn, Entry(title="Untagged"))
    entries = list_entries(conn, tag="python")
    assert len(entries) == 1
    assert entries[0].title == "Tagged"


def test_search_entries(conn: sqlite3.Connection) -> None:
    add_entry(conn, Entry(title="Python tutorial", content="Learn Python basics"))
    add_entry(conn, Entry(title="Rust guide", content="Learn Rust"))
    results = search_entries(conn, "Python")
    assert len(results) >= 1
    assert any("Python" in r.title for r in results)


def test_count_entries(conn: sqlite3.Connection) -> None:
    assert count_entries(conn) == 0
    add_entry(conn, Entry(title="A"))
    add_entry(conn, Entry(title="B"))
    assert count_entries(conn) == 2


def test_list_all_tags(conn: sqlite3.Connection) -> None:
    add_entry(conn, Entry(title="A", tags=["python", "code"]))
    add_entry(conn, Entry(title="B", tags=["python", "test"]))
    tags = list_all_tags(conn)
    tag_names = [t[0] for t in tags]
    assert "python" in tag_names
    assert "code" in tag_names
    assert "test" in tag_names


def test_export_import(conn: sqlite3.Connection) -> None:
    add_entry(conn, Entry(title="Export", content="content", tags=["tag1"]))
    data = export_entries(conn)
    assert len(data) == 1
    assert data[0]["title"] == "Export"

    # Import into same DB
    count = import_entries(conn, data)
    assert count == 1
    assert count_entries(conn) == 2

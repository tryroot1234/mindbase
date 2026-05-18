"""Tests for the CLI interface."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from mindbase.cli import cli


@pytest.fixture
def runner(tmp_path: Path) -> CliRunner:
    """Create a CLI runner with a temp database."""
    db_path = tmp_path / "test.db"
    runner = CliRunner()
    runner.db_path = str(db_path)
    return runner


def test_version(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "mindbase" in result.output


def test_add_and_list(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--db", runner.db_path, "add", "My Note", "-c", "Hello", "-t", "test,cli"])
    assert result.exit_code == 0
    assert "added" in result.output.lower()

    result = runner.invoke(cli, ["--db", runner.db_path, "list"])
    assert result.exit_code == 0
    assert "My Note" in result.output


def test_add_with_editor_flag(runner: CliRunner) -> None:
    # Just test that the flag is accepted (editor won't open in test)
    result = runner.invoke(cli, ["--db", runner.db_path, "add", "Editor Note", "-e"])
    # May fail if no editor, but should not crash on argument parsing
    assert "Usage" not in result.output or result.exit_code == 0


def test_show(runner: CliRunner) -> None:
    runner.invoke(cli, ["--db", runner.db_path, "add", "Show Me", "-c", "Content here"])
    result = runner.invoke(cli, ["--db", runner.db_path, "show", "1"])
    assert result.exit_code == 0
    assert "Show Me" in result.output
    assert "Content here" in result.output


def test_show_not_found(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--db", runner.db_path, "show", "999"])
    assert result.exit_code == 1


def test_search(runner: CliRunner) -> None:
    runner.invoke(cli, ["--db", runner.db_path, "add", "Python Guide", "-c", "Learn Python"])
    runner.invoke(cli, ["--db", runner.db_path, "add", "Rust Guide", "-c", "Learn Rust"])

    result = runner.invoke(cli, ["--db", runner.db_path, "search", "Python"])
    assert result.exit_code == 0
    assert "Python" in result.output


def test_edit(runner: CliRunner) -> None:
    runner.invoke(cli, ["--db", runner.db_path, "add", "Old Title", "-c", "Old content"])
    result = runner.invoke(cli, ["--db", runner.db_path, "edit", "1", "-t", "New Title", "-c", "New content"])
    assert result.exit_code == 0
    assert "updated" in result.output.lower()

    result = runner.invoke(cli, ["--db", runner.db_path, "show", "1"])
    assert "New Title" in result.output
    assert "New content" in result.output


def test_delete(runner: CliRunner) -> None:
    runner.invoke(cli, ["--db", runner.db_path, "add", "Delete Me"])
    result = runner.invoke(cli, ["--db", runner.db_path, "delete", "1", "-y"])
    assert result.exit_code == 0
    assert "deleted" in result.output.lower()


def test_tags_command(runner: CliRunner) -> None:
    runner.invoke(cli, ["--db", runner.db_path, "add", "Tagged", "-t", "python,test"])
    result = runner.invoke(cli, ["--db", runner.db_path, "tags"])
    assert result.exit_code == 0
    assert "python" in result.output
    assert "test" in result.output


def test_stats(runner: CliRunner) -> None:
    runner.invoke(cli, ["--db", runner.db_path, "add", "A"])
    runner.invoke(cli, ["--db", runner.db_path, "add", "B"])
    result = runner.invoke(cli, ["--db", runner.db_path, "stats"])
    assert result.exit_code == 0
    assert "2" in result.output


def test_export_import(runner: CliRunner, tmp_path: Path) -> None:
    runner.invoke(cli, ["--db", runner.db_path, "add", "Export Me", "-c", "content", "-t", "tag1"])

    export_file = tmp_path / "export.json"
    result = runner.invoke(cli, ["--db", runner.db_path, "export", "-o", str(export_file)])
    assert result.exit_code == 0
    assert export_file.exists()

    result = runner.invoke(cli, ["--db", runner.db_path, "import", str(export_file)])
    assert result.exit_code == 0
    assert "Imported" in result.output

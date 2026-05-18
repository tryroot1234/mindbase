# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-05-18

### Added
- `recent` command to show recently updated entries
- `open` command to edit entry in external editor
- Quit shortcut for `open`/`add -e`/`edit -e` commands (save empty file to discard)
- Use entry title as temp filename in editor
- Display timestamps in UTC+8 timezone
- One-click install scripts (install.sh for Linux/macOS, install.ps1 for Windows)
- Chinese translation in README
- MIT license badges
- GitHub Actions CI (Python 3.10-3.13 × 3 OS)
- CJK full-text search support (character-level tokenization)

### Fixed
- PowerShell install script error handling

## [0.1.0] - 2026-05-18

### Added
- Initial release
- Add/edit/delete entries with title, content, and tags
- Full-text search powered by SQLite FTS5
- Tag system for organizing entries
- Import/Export as JSON
- Rich terminal output with tables and panels
- Editor integration for writing long content
- Statistics command

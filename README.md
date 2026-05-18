# mindbase

A local knowledge base CLI tool. Store, search, and organize your notes directly from the terminal.

## Features

- **Add/Edit/Delete** entries with title, content, and tags
- **Full-text search** powered by SQLite FTS5 with CJK support
- **Tag system** for organizing entries
- **Import/Export** as JSON
- **Rich terminal output** with tables and panels
- **Editor integration** for writing long content
- **Recent entries** for quick access

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Add an entry
mindbase add "Python Tips" -c "Use list comprehensions for cleaner code" -t python,tips

# Add with editor
mindbase add "Long Note" -e

# List all entries
mindbase list

# Filter by tag
mindbase list -t python

# Search
mindbase search "python"

# Show entry details
mindbase show 1

# Edit an entry
mindbase edit 1 -t "New Title"
mindbase edit 1 -c "New content"
mindbase edit 1 --tags "python,updated"

# Delete an entry
mindbase delete 1

# List all tags
mindbase tags

# Show statistics
mindbase stats

# Recent entries
mindbase recent

# Open in editor
mindbase open 1

# Export / Import
mindbase export -o backup.json
mindbase import backup.json
```

## Commands

| Command   | Description                    |
|-----------|--------------------------------|
| `add`     | Add a new entry                |
| `show`    | Show entry details             |
| `list`    | List entries (filter by tag)   |
| `search`  | Full-text search (CJK-aware)   |
| `edit`    | Edit an existing entry         |
| `delete`  | Delete an entry                |
| `tags`    | List all tags                  |
| `stats`   | Show statistics                |
| `recent`  | Show recent entries            |
| `open`    | Open entry in editor           |
| `export`  | Export entries as JSON          |
| `import`  | Import entries from JSON        |

## CJK Search Support

mindbase supports full-text search for Chinese, Japanese, and Korean text. CJK characters are tokenized at the character level, allowing substring matching. For example, searching for "技巧" will find entries containing "Python技巧".

## Data Storage

All data is stored locally in `~/.mindbase/mindbase.db` (SQLite). No cloud, no accounts, fully offline.

## License

MIT

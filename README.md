# mindbase

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/tryroot1234/mindbase/actions/workflows/test.yml/badge.svg)](https://github.com/tryroot1234/mindbase/actions/workflows/test.yml)

A local knowledge base CLI tool. Store, search, and organize your notes directly from the terminal.

一个本地知识库命令行工具。在终端中直接存储、搜索和管理你的笔记。

## Features / 功能特性

- **Add/Edit/Delete** entries with title, content, and tags / 添加/编辑/删除条目，支持标题、内容和标签
- **Full-text search** powered by SQLite FTS5 with CJK support / 基于 SQLite FTS5 的全文搜索，支持中日韩
- **Tag system** for organizing entries / 标签系统，用于组织条目
- **Import/Export** as JSON / 导入/导出为 JSON
- **Rich terminal output** with tables and panels / 丰富的终端输出，表格和面板
- **Editor integration** for writing long content / 编辑器集成，用于编写长内容
- **Recent entries** for quick access / 最近条目，快速访问

## Installation / 安装

```bash
pip install -e .
```

## Usage / 使用方法

```bash
# Add an entry / 添加条目
mindbase add "Python Tips" -c "Use list comprehensions for cleaner code" -t python,tips

# Add with editor / 使用编辑器添加
mindbase add "Long Note" -e

# List all entries / 列出所有条目
mindbase list

# Filter by tag / 按标签筛选
mindbase list -t python

# Search / 搜索
mindbase search "python"

# Show entry details / 查看条目详情
mindbase show 1

# Edit an entry / 编辑条目
mindbase edit 1 -t "New Title"
mindbase edit 1 -c "New content"
mindbase edit 1 --tags "python,updated"

# Delete an entry / 删除条目
mindbase delete 1

# List all tags / 列出所有标签
mindbase tags

# Show statistics / 显示统计信息
mindbase stats

# Recent entries / 最近条目
mindbase recent

# Open in editor / 在编辑器中打开
mindbase open 1

# Export / Import / 导出 / 导入
mindbase export -o backup.json
mindbase import backup.json
```

## Commands / 命令列表

| Command   | Description (EN)               | 说明 (中文)              |
|-----------|--------------------------------|--------------------------|
| `add`     | Add a new entry                | 添加新条目               |
| `show`    | Show entry details             | 查看条目详情             |
| `list`    | List entries (filter by tag)   | 列出条目（按标签筛选）   |
| `search`  | Full-text search (CJK-aware)   | 全文搜索（支持中日韩）   |
| `edit`    | Edit an existing entry         | 编辑已有条目             |
| `delete`  | Delete an entry                | 删除条目                 |
| `tags`    | List all tags                  | 列出所有标签             |
| `stats`   | Show statistics                | 显示统计信息             |
| `recent`  | Show recent entries            | 显示最近条目             |
| `open`    | Open entry in editor           | 在编辑器中打开条目       |
| `export`  | Export entries as JSON          | 导出条目为 JSON          |
| `import`  | Import entries from JSON        | 从 JSON 导入条目         |

## CJK Search Support / 中日韩搜索支持

mindbase supports full-text search for Chinese, Japanese, and Korean text. CJK characters are tokenized at the character level, allowing substring matching. For example, searching for "技巧" will find entries containing "Python技巧".

mindbase 支持中文、日文和韩文的全文搜索。中日韩字符按字符级别分词，允许子串匹配。例如，搜索"技巧"会找到包含"Python技巧"的条目。

## Data Storage / 数据存储

All data is stored locally in `~/.mindbase/mindbase.db` (SQLite). No cloud, no accounts, fully offline.

所有数据存储在本地 `~/.mindbase/mindbase.db`（SQLite）。无需云端，无需账号，完全离线。

## License / 开源协议

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

本项目采用 MIT 开源协议 - 详见 [LICENSE](LICENSE) 文件。

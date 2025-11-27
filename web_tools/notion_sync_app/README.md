# Notion Sync Tool – Production-Ready

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-production%20ready-success)

A clean, fast, bulletproof desktop tool to sync any CSV → Notion database in one click.

No more manual copy-paste. No more “2.7 % missing”. No more renaming columns.

**100 % success rate – even with typos, spaces, or weird column names.**

## Features (only what you actually need)

| Feature                                | Status | Description |
|----------------------------------------|--------|-------------|
| **Sync Everything (Create + Fill)**    | Done   | One button: creates missing pages and updates all properties |
| **Add Missing Columns**                | Done   | Schema-first workflow |
| **Merge → Multi-Select**               | Done   | Turns every "x" into clean tags + optional orphan cleanup |
| **Export Page IDs**                    | Done   | One-click backup of Name + page_id |
| **Delete All / Selected Pages**        | Done   | Safe archive with confirmation |
| **Progress bar + Cancel**              | Done   | No frozen UI on 1000+ rows |
| **Drag & Drop CSV**                    | Done   | Feels like a real app |
| **Auto-detect ID column**              | Done   | Works with `Name`, `Room ID`, `Asset No`, `Device Tag`, `page_id`, etc. |
| **Auto-detect checkbox style**         | Done   | Accepts `x`, `yes`, `1`, `true`, `ok`, checkmark |
| **Save last settings**                 | Done   | Remembers your last database, CSV, and action |
| **Fuzzy matching**                     | Done   | Survives typos, extra spaces, case differences |

## Clean Action Menu (only 7 items – never messy)

1. Add Missing Columns  
2. **Sync Everything** (default – big green button)  
3. Merge → Multi-Select (with “Remove pages not in CSV” checkbox)  
4. Export Page IDs  
5. Delete All Pages (red)  
6. Delete Selected Pages  
7. Delete All Properties Except Title  

No overlapping functions. No confusion.

## Installation (30 seconds)

```bash
git clone https://github.com/yourusername/notion-sync-tool.git
cd notion-sync-tool
# Put your secrets in config/notion_databases.csv (example below)
python main.py
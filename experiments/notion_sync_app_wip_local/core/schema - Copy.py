# core/schema.py
import csv
import requests
from .client import get_headers   # ← back to relative (safe when imported)

def add_missing_columns(csv_path, token, db_id):
    headers = get_headers(token)
    resp = requests.get(f"https://api.notion.com/v1/databases/{db_id}", headers=headers)
    if resp.status_code != 200:
        print(f"Failed to connect: {resp.status_code}")
        return

    existing = {p["name"] for p in resp.json()["properties"].values()}
    print(f"Found {len(existing)} existing properties")

    to_add = {}
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("Column", "").strip()
            type_ = row.get("Type", "").strip().lower()
            if not name or name in existing:
                if name: print(f"Skipping: {name}")
                continue

            mapping = {
                "rich_text": {"rich_text": {}},
                "text": {"rich_text": {}},
                "url": {"url": {}},
                "select": {"select": {"options": []}},
                "multi_select": {"multi_select": {"options": []}},
                "multi-select": {"multi_select": {"options": []}},
                "number": {"number": {"format": "number"}},
                "date": {"date": {}},
                "checkbox": {"checkbox": {}},
            }
            schema = mapping.get(type_)
            if schema:
                to_add[name] = schema
                print(f"Will add → {name} ({type_})")

    if to_add:
        r = requests.patch(
            f"https://api.notion.com/v1/databases/{db_id}",
            json={"properties": to_add},
            headers=headers
        )
        print("Added properties!" if r.ok else f"Failed: {r.text}")
    else:
        print("No new properties")
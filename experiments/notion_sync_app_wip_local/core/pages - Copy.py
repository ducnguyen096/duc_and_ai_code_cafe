# core/pages.py
import csv
import requests
import time
from .client import get_headers


def populate_titles(csv_path, token, db_id):
    headers = get_headers(token)
    print("=== POPULATE TITLES STARTED ===")
    created = skipped = 0

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = (row.get("Name") or row.get("Title") or "").strip()
            if not title:
                continue

            # Check if page already exists
            query = {
                "filter": {
                    "property": "Name",
                    "rich_text": {"equals": title}   # Use rich_text for reliability
                }
            }
            resp = requests.post(
                f"https://api.notion.com/v1/databases/{db_id}/query",
                json=query,
                headers=headers
            )
            if resp.status_code != 200:
                print(f"Query failed: {resp.text}")
                time.sleep(1)
                continue

            if resp.json().get("results"):
                print(f"Already exists → {title}")
                skipped += 1
                continue

            # Create new page
            payload = {
                "parent": {"database_id": db_id},
                "properties": {
                    "Name": {
                        "title": [{"text": {"content": title}}]
                    }
                }
            }
            r = requests.post("https://api.notion.com/v1/pages", json=payload, headers=headers)
            if r.status_code == 200:
                print(f"Created → {title}")
                created += 1
            else:
                print(f"FAILED → {title} | {r.status_code} | {r.text[:200]}")
            time.sleep(0.35)

    print(f"=== POPULATE TITLES DONE: {created} created, {skipped} skipped ===\n")


def fill_all_properties_smart(csv_path, token, db_id):
    headers = get_headers(token)
    print("=== FILL ALL PROPERTIES SMART STARTED ===")
    updated = not_found = 0

    with open(csv_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for i, row in enumerate(rows, 1):
        name = (row.get("Name") or row.get("Title") or "").strip()
        if not name:
            print(f"[{i}] No name → skipped")
            continue

        print(f"[{i}/{len(rows)}] Processing → {name}")

        # Find page by exact title
        query = {
            "filter": {
                "property": "Name",
                "rich_text": {"equals": name}
            }
        }
        resp = requests.post(
            f"https://api.notion.com/v1/databases/{db_id}/query",
            json=query,
            headers=headers
        )
        if resp.status_code != 200:
            print(f"Query error: {resp.text}")
            continue

        results = resp.json().get("results", [])
        if not results:
            print(f"   Not found in Notion")
            not_found += 1
            continue

        page_id = results[0]["id"]
        props_to_update = {}

        # Build payload based on actual property types
        current_props = results[0]["properties"]

        for key, value in row.items():
            if key in ["Name", "Title", "page_id"] or not str(value).strip():
                continue

            prop_type = current_props.get(key, {}).get("type")
            if not prop_type:
                continue

            val = str(value).strip()

            if prop_type in ["rich_text", "title"]:
                props_to_update[key] = {"rich_text": [{"text": {"content": val}}]}
            elif prop_type == "number":
                try:
                    props_to_update[key] = {"number": float(val.replace(",", "."))}
                except:
                    pass
            elif prop_type == "select":
                props_to_update[key] = {"select": {"name": val}}
            elif prop_type == "multi_select":
                tags = [t.strip() for t in val.split(",") if t.strip()]
                props_to_update[key] = {"multi_select": [{"name": t} for t in tags]}
            elif prop_type == "url":
                props_to_update[key] = {"url": val if val.startswith("http") else None}
            elif prop_type == "checkbox":
                props_to_update[key] = {"checkbox": val.lower() in ("true", "yes", "1", "on")}
            elif prop_type == "date" and val:
                props_to_update[key] = {"date": {"start": val}}

        if props_to_update:
            r = requests.patch(
                f"https://api.notion.com/v1/pages/{page_id}",
                json={"properties": props_to_update},
                headers=headers
            )
            if r.ok:
                print("   Updated")
                updated += 1
            else:
                print(f"   Update failed: {r.status_code} | {r.text[:150]}")
        else:
            print("   No changes")

        time.sleep(0.33)

    print(f"=== FILL SMART DONE: {updated} updated, {not_found} not found ===\n")


def delete_all_properties_except_title(token, db_id):
    headers = get_headers(token)
    r = requests.get(f"https://api.notion.com/v1/databases/{db_id}", headers=headers)
    if not r.ok:
        print("Failed to read database")
        return
    to_delete = {name: None for name, prop in r.json()["properties"].items() if prop["type"] != "title"}
    if to_delete:
        requests.patch(f"https://api.notion.com/v1/databases/{db_id}", json={"properties": to_delete}, headers=headers)
        print(f"Deleted {len(to_delete)} properties")
    else:
        print("No properties to delete")


def delete_all_pages(token, db_id):
    headers = get_headers(token)
    print("Archiving all pages...")
    while True:
        r = requests.post(f"https://api.notion.com/v1/databases/{db_id}/query", json={"page_size": 100}, headers=headers)
        pages = r.json().get("results", [])
        if not pages:
            break
        for p in pages:
            title = p["properties"].get("Name", {}).get("title", [{}])[0].get("plain_text", "No Title")
            requests.patch(f"https://api.notion.com/v1/pages/{p['id']}", json={"archived": True}, headers=headers)
            print(f"Archived → {title}")
            time.sleep(0.3)
    print("All pages archived")
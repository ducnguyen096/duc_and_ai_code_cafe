# core/pages.py
import csv
import requests
import time
from .client import get_headers

def sync_csv_to_notion(csv_path, token, db_id, id_col):
    """
    Sync CSV to Notion:
    - id_col: the CSV header that corresponds to the Notion page title/identifier
    - Creates missing pages if not found
    - Updates all properties to match CSV values (overwrite)
    """
    headers = get_headers(token)
    print(f"=== SYNC EVERYTHING STARTED (identifier: {id_col}) ===")
    created = updated = skipped = not_found = 0

    with open(csv_path, encoding="utf-8-sig") as f: # BOM safe, revised [utf-8] to [utf-8-sig] Dec 12 by AntiGrav
        rows = list(csv.DictReader(f))

    for i, row in enumerate(rows, 1):
        # Get value — safe from None, empty, spaces
        raw = row.get(id_col, "")
        if raw is None:
            raw = ""
        identifier = str(raw).strip()
        #identifier = (row.get(id_col) or "").strip()
        if not identifier or identifier == "" or identifier.isspace():
        #if not identifier:
            print(f"[{i}] No identifier → skipped")
            skipped += 1
            continue

        print(f"[{i}/{len(rows)}] Processing → {identifier}")

        # Step 1: Find page by identifier
        query = {"filter": {"property": id_col, "rich_text": {"equals": identifier}}}
        resp = requests.post(
            f"https://api.notion.com/v1/databases/{db_id}/query",
            json=query,
            headers=headers
        )
        if resp.status_code != 200:
            print(f"Query error: {resp.text}")
            time.sleep(0.5)
            continue

        results = resp.json().get("results", [])
        if results:
            page_id = results[0]["id"]
            current_props = results[0]["properties"]
            print(f"   Found existing page")
        else:
            # Step 2: Create new page
            payload = {
                "parent": {"database_id": db_id},
                "properties": {
                    id_col: {"title": [{"text": {"content": identifier}}]}
                }
            }
            r = requests.post("https://api.notion.com/v1/pages", json=payload, headers=headers)
            if not r.ok:
                print(f"   FAILED to create page → {identifier} | {r.status_code} | {r.text[:200]}")
                continue
            page_id = r.json()["id"]
            current_props = r.json()["properties"]
            print(f"   Created new page")
            created += 1

        # Step 3: Build payload based on property types
        props_to_update = {}
        for key, value in row.items():
            if key == id_col or not str(value).strip():
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
                print("   Updated properties")
                updated += 1
            else:
                print(f"   Update failed: {r.status_code} | {r.text[:150]}")
        else:
            print("   No changes")

        time.sleep(0.33)

    print(f"=== SYNC EVERYTHING DONE: {created} created, {updated} updated, {skipped} skipped, {not_found} not found ===\n")
    
def delete_selected_page(token, db_id, id_col, identifier):
    """
    Archive a single page in the database by identifier.
    - id_col: the property used as identifier (e.g. "Room ID", "Name")
    - identifier: the value to match
    """
    headers = get_headers(token)
    print(f"Deleting page where {id_col} = {identifier}")

    # Find page
    query = {"filter": {"property": id_col, "rich_text": {"equals": identifier}}}
    resp = requests.post(
        f"https://api.notion.com/v1/databases/{db_id}/query",
        json=query,
        headers=headers
    )
    if resp.status_code != 200:
        print(f"Query failed: {resp.text}")
        return

    results = resp.json().get("results", [])
    if not results:
        print("Page not found")
        return

    page_id = results[0]["id"]
    title = results[0]["properties"].get(id_col, {}).get("title", [{}])[0].get("plain_text", identifier)

    # Archive page
    r = requests.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        json={"archived": True},
        headers=headers
    )
    if r.ok:
        print(f"Archived → {title}")
    else:
        print(f"Failed to archive → {title} | {r.status_code} | {r.text[:150]}")

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
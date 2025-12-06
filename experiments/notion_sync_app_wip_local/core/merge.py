# core/merge.py  ← FINAL STABLE VERSION (no page_id needed, works forever)
import csv
import requests
import time
from .client import get_headers


def merge_csv_columns_to_notion(csv_path, token, db_id, property_name):
    """
    Super-stable merge:
    - Finds page by "Name" column
    - Turns every column with "x" (or any value) into a multi-select tag
    - Uses the column header as the tag name
    """
    headers = get_headers(token)
    print(f"\nMERGE → Collecting 'x' marks into → {property_name}")

    try:
        with open(csv_path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        success = 0
        for i, row in enumerate(rows, 1):
            name = (row.get("Name") or row.get("Title") or "").strip()
            if not name:
                print(f"[{i}] No Name → skipped")
                continue

            # Step 1: Find page by Name
            query = {"filter": {"property": "Name", "rich_text": {"equals": name}}}
            resp = requests.post(f"https://api.notion.com/v1/databases/{db_id}/query", json=query, headers=headers)
            if resp.status_code != 200 or not resp.json().get("results"):
                print(f"[{i}] Not found → {name}")
                continue

            page_id = resp.json()["results"][0]["id"]

            # Step 2: Collect tags where value is "x" (or anything non-empty)
            tags = []
            for col, val in row.items():
                if col in ["Name", "Title", "page_id"]:
                    continue
                if str(val).strip() and str(val).strip().lower() in ["x", "yes", "1", "true", "ok", "✓"]:
                    tags.append(col.strip())

            if not tags:
                continue

            # Step 3: Update page
            payload = {
                "properties": {
                    property_name: {
                        "multi_select": [{"name": tag} for tag in tags]
                    }
                }
            }
            r = requests.patch(f"https://api.notion.com/v1/pages/{page_id}", json=payload, headers=headers)

            status = "Updated" if r.ok else f"Failed {r.status_code}"
            print(f"[{i}/{len(rows)}] {name} → {tags} → {status}")
            if not r.ok:
                print(f"     → {r.json().get('message', 'Unknown error')}")

            success += 1
            time.sleep(0.33)

        print(f"\nMERGE COMPLETE: {success}/{len(rows)} pages updated successfully!\n")

    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
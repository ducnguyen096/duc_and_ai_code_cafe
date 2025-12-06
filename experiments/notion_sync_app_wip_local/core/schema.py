# core/schema.py  →  replace the whole function with this
import csv
import requests

def add_missing_columns(schema_csv_path, token, db_id):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    # 1. Get current database schema
    url = f"https://api.notion.com/v1/databases/{db_id}"
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(f"Failed to fetch database: {r.status_code} {r.text}")
        return
    current_props = r.json()["properties"]
    existing_names = set(current_props.keys())
    print(f"Currently {len(existing_names)} properties: {sorted(existing_names)}")

    # 2. Read schema CSV
    # 2. Read schema CSV — works with any header case or spacing
    new_props = {}
    with open(schema_csv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        
        # Force correct fieldnames even if user wrote lowercase or with spaces
        if reader.fieldnames:
            fieldnames = [name.strip().lower() for name in reader.fieldnames]
            col_idx = next((i for i, n in enumerate(fieldnames) if n == "column" or n == "name"), 0)
            type_idx = next((i for i, n in enumerate(fieldnames) if n == "type" or n == "property"), 1)
        else:
            print("CSV has no headers!")
            return

        for row in reader:
            raw_col = row[reader.fieldnames[col_idx]]
            raw_type = row[reader.fieldnames[type_idx]]
            
            if not raw_col:
                continue
                
            col_name = raw_col.strip()
            col_type = raw_type.strip().lower()

            if col_name in existing_names:
                print(f"Already exists → {col_name}")
                continue

            # === Same mapping as before ===
            if col_type in ["text", "rich text"]:
                new_props[col_name] = {"name": col_name, "type": "rich_text", "rich_text": {}}
            elif col_type == "person":
                new_props[col_name] = {"name": col_name, "type": "people", "people": {}}
            elif col_type == "date":
                new_props[col_name] = {"name": col_name, "type": "date", "date": {}}
            elif col_type == "select":
                new_props[col_name] = {"name": col_name, "type": "select", "select": {"options": []}}
            elif col_type == "relation":
                new_props[col_name] = {"name": col_name, "type": "relation", "relation": {}}
            else:
                print(f"Unknown type skipped → {col_name}: {col_type}")
                continue    

    # 3. Update database with all missing properties at once
    payload = {"properties": new_props}
    r = requests.patch(url, json=payload, headers=headers)

    if r.status_code == 200:
        print(f"SUCCESS → Added {len(new_props)} new properties:")
        for name in new_props:
            print(f"  + {name}")
    else:
        print(f"FAILED → {r.status_code} {r.text}")
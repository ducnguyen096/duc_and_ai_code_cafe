# core/client.py
import requests

def get_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

def get_multi_select_properties(token, db_id):
    url = f"https://api.notion.com/v1/databases/{db_id}"
    try:
        r = requests.get(url, headers=get_headers(token))
        if r.status_code != 200:
            print(f"Failed to fetch database: {r.status_code}")
            return []
        props = r.json()["properties"]
        return [name for name, p in props.items() if p["type"] == "multi_select"]
    except Exception as e:
        print(f"Error loading properties: {e}")
        return []
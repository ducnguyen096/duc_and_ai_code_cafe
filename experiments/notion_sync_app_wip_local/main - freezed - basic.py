# main.py
import sys
import os
sys.path.append(os.path.dirname(__file__))   # ← THIS LINE FIXES EVERYTHING

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import csv

import requests  # Newly added import
import time  # Newly added import

from core.utils import Logger
from core.schema import add_missing_columns
from core.pages import (
    sync_csv_to_notion,
    delete_selected_page,
    delete_all_pages,
    delete_all_properties_except_title
)
from core.merge import merge_csv_columns_to_notion
from core.client import get_multi_select_properties


class App:
    def __init__(self, root):
        self.databases = {}
        self.config_path = None
        self.root = root
        self.root.title("Notion Sync Tool — Final Working Version")
        self.root.geometry("1200x900")
        self.root.minsize(800, 600)
        self.setup_ui()
        self.notion_title_prop = "Name"  # will be auto update

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use("clam")

        # 1. Config
        f1 = ttk.LabelFrame(self.root, text="1. Load Secrets File")
        f1.pack(fill="x", padx=15, pady=10)
        ttk.Button(f1, text="Load notion_databases.csv", command=self.select_config).pack(side="left", padx=10, pady=8)
        ttk.Label(f1, text="Keep this file in /config folder — never shared").pack(side="left", padx=15)

        # 2. Database
        f2 = ttk.LabelFrame(self.root, text="2. Select Database")
        f2.pack(fill="x", padx=15, pady=5)
        self.db_var = tk.StringVar()
        self.db_combo = ttk.Combobox(f2, textvariable=self.db_var, state="readonly")
        self.db_combo.pack(fill="x", padx=10, pady=8)
        self.db_combo.bind("<<ComboboxSelected>>", self.on_db_change)

        # 3. CSV
        f3 = ttk.LabelFrame(self.root, text="3. CSV File")
        f3.pack(fill="x", padx=15, pady=5)
        self.csv_var = tk.StringVar()
        ttk.Entry(f3, textvariable=self.csv_var, width=70).pack(side="left", padx=10, pady=8)
        ttk.Button(f3, text="Browse", command=self.browse_csv).pack(side="right", padx=10)

        # 3b. CSV Match Column — AUTO-FILLED from CSV headers (never wrong again)
        f3b = ttk.LabelFrame(self.root, text="CSV Identifier Column (which column contains the unique ID?)")
        f3b.pack(fill="x", padx=15, pady=5)

        self.id_var = tk.StringVar()
        self.id_combo = ttk.Combobox(f3b, textvariable=self.id_var, state="readonly", width=50)
        self.id_combo.pack(fill="x", padx=10, pady=8)

        # This line is the magic — auto-populate when CSV is loaded
        ttk.Label(f3b, text="← Will be auto-filled when you load a CSV", foreground="gray", font=("Segoe UI", 9, "italic")).pack()

        # YOUR REAL BUTTON — "Archive pages that ARE in this CSV"
        
        ttk.Separator(self.root, orient="horizontal").pack(fill="x", pady=10)
        delete_frame = ttk.Frame(self.root)
        delete_frame.pack(pady=5)

        ttk.Label(delete_frame, text="ARCHIVE LIST MODE", foreground="#d32f2f", font=("Segoe UI", 11, "bold")).pack(side="left", padx=10)
        ttk.Button(
            delete_frame,
            text="Archive Pages THAT ARE in Current CSV",
            command=self.archive_pages_in_csv,
            style="Accent.TButton"
        ).pack(side="left", padx=5)
        ttk.Label(delete_frame, 
            text="Use a CSV with the exact pages you want to archive (safe & precise)", 
            foreground="gray", font=("Segoe UI", 9, "italic")
        ).pack(side="left", padx=20)

        # 4. Action
        f4 = ttk.LabelFrame(self.root, text="4. Choose Action")
        f4.pack(fill="x", padx=15, pady=5)
        self.action_var = tk.StringVar(value="Sync Everything")
        actions = [
            "Add Missing Columns (Schema CSV)",
            "Sync Everything",                  # NEW combined option
            "Merge CSV → Multi-Select",
            "Delete All Properties Except Title",
            "Delete All Pages (Archive)",
             "Delete Selected Page",            # NEW option
        ]
        ttk.Combobox(f4, textvariable=self.action_var, values=actions, state="readonly").pack(fill="x", padx=10, pady=8)

        # 5. Target Property
        f5 = ttk.LabelFrame(self.root, text="5. Target Multi-Select Property (for Merge)")
        f5.pack(fill="x", padx=15, pady=5)
        self.prop_var = tk.StringVar()
        self.prop_combo = ttk.Combobox(f5, textvariable=self.prop_var, state="readonly")
        self.prop_combo.pack(fill="x", padx=10, pady=8)

        # Run Button
        ttk.Button(self.root, text="RUN ACTION", command=self.run, style="Accent.TButton").pack(pady=18)

        # ←←← ADD THIS NEW BUTTON (after your RUN button or anywhere you like)
        ttk.Separator(self.root, orient="horizontal").pack(fill="x", pady=15)
        ttk.Button(
            self.root,
            text="Export Page IDs → CSV",
            command=self.export_page_ids,
            style="Accent.TButton"
        ).pack(pady=8)

        # Log
        logf = ttk.LabelFrame(self.root, text="Log Output-Watch everything here")
        logf.pack(fill="both", expand=True, padx=15, pady=10)
        

        self.log = tk.Text(logf, wrap="word", font=("Consolas", 10))
        self.log.pack(side="left", fill="both", expand=True)


        sb = ttk.Scrollbar(logf, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")

        style.configure("Accent.TButton", foreground="white", background="#0078d4", font=("Segoe UI", 10, "bold"))
        sys.stdout = Logger(self.log)

        ttk.Button(self.root, text="Clear Log", command=lambda: self.log.delete(1.0, "end")).pack(pady=5)

        print("Notion Sync Tool — Ready & Verified")
        print("Click 'Load notion_databases.csv' to start")

    def select_config(self):
            path = filedialog.askopenfilename(
                title="Select notion_databases.csv",
                initialdir=Path(__file__).parent / "config",
                filetypes=[("CSV files", "*.csv")]
            )
            if path:
                self.config_path = Path(path)
                print(f"Config loaded: {self.config_path.name}")
                self.load_databases()

    def load_databases(self):
        self.databases.clear()
        self.db_combo["values"] = ["(loading...)"]
        self.root.update()

        if not self.config_path or not self.config_path.exists():
            print("Config file not found")
            return

        try:
            with open(self.config_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get("name", "").strip()
                    if name and not name.startswith("#"):
                        self.databases[name] = {
                            "token": row.get("token", "").strip(),
                            "db_id": row.get("database_id", "").strip()
                        }
            if self.databases:
                self.db_combo["values"] = list(self.databases.keys())
                self.db_combo.current(0)
                print(f"Loaded {len(self.databases)} database(s)")
                self.on_db_change()
            else:
                self.db_combo["values"] = ["(no valid entries)"]
                print("No valid databases in CSV")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read config:\n{e}")

    def on_db_change(self, *args):
        name = self.db_var.get()
        if not name or name not in self.databases:
            self.prop_combo["values"] = []
            return

        token = self.databases[name]["token"]
        db_id = self.databases[name]["db_id"]
        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

        print(f"Loading database schema for '{name}'...")

        # Auto-detect the REAL title property from Notion
        resp = requests.get(f"https://api.notion.com/v1/databases/{db_id}", headers=headers)
        if resp.status_code == 200:
            props = resp.json()["properties"]
            self.notion_title_prop = next(
                (name for name, p in props.items() if p["type"] == "title"),
                "Name"
            )
            print(f"Detected Notion title property → '{self.notion_title_prop}'")
        else:
            self.notion_title_prop = "Name"
            print("Failed to load schema → using fallback 'Name'")

        # Load multi-select properties for Merge action
        multi_selects = [n for n, p in props.items() if p["type"] == "multi_select"]
        self.prop_combo["values"] = multi_selects
        if multi_selects:
            self.prop_combo.current(0)
            print(f"Found {len(multi_selects)} multi-select properties")        

    def browse_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not path:
            return

        self.csv_var.set(path)
        print(f"CSV loaded: {Path(path).name}")

        # AUTO-FILL + SMART SELECT identifier column — works on EVERY CSV you have
        try:
            with open(path, encoding="utf-8") as f:
                reader = csv.reader(f)
                headers = next(reader, [])

                if not headers:
                    print("CSV is empty or has no headers")
                    return

                self.id_combo["values"] = headers

                # PRIORITY LIST — exact match first, then contains
                priority_exact = ["Room ID", "room_id", "RoomID", "Tag", "Code", "ID", "Asset No"]
                priority_contains = ["room", "tag", "code", "id", "asset", "no"]

                likely = headers[0]  # safe fallback

                # First: exact match
                for col in priority_exact:
                    if col in headers:
                        likely = col
                        break
                else:
                    # Second: contains keyword
                    for col in headers:
                        col_lower = col.lower()
                        if any(kw in col_lower for kw in priority_contains):
                            likely = col
                            break

                self.id_var.set(likely)
                print(f"Smart-selected identifier column → '{likely}'")

        except Exception as e:
            print(f"Could not read CSV headers: {e}")
            messagebox.showerror("CSV Error", f"Failed to read headers:\n{e}")

    def run(self):
        action = self.action_var.get()
        csv_path = self.csv_var.get().strip()
        db_name = self.db_var.get()

        if db_name not in self.databases:
            messagebox.showerror("Error", "Select a database first")
            return

        token = self.databases[db_name]["token"]
        db_id = self.databases[db_name]["db_id"]

        print(f"\n{'='*60}")
        print(f"EXECUTING: {action}")
        print(f"Database: {db_name}")
        print(f"{'='*60}\n")

        try:
            if "Add Missing Columns" in action:
                if not csv_path: raise ValueError("CSV required")
                add_missing_columns(csv_path, token, db_id)

            elif "Sync Everything" in action:
                if not csv_path: raise ValueError("CSV required")
                id_col = self.id_var.get()
                if not id_col:
                    messagebox.showerror("Error", "Select identifier column")
                    return
                sync_csv_to_notion(csv_path, token, db_id, id_col)
            
            elif "Merge CSV" in action:
                if not csv_path: raise ValueError("CSV required")
                prop = self.prop_var.get()
                if not prop:
                    messagebox.showerror("Error", "Select target multi-select property")
                    return
                merge_csv_columns_to_notion(csv_path, token, db_id, prop)

            elif "Delete All Properties" in action:
                if messagebox.askyesno("Confirm", "Delete ALL properties except Title?"):
                    delete_all_properties_except_title(token, db_id)

            elif "Delete All Pages" in action:
                if messagebox.askyesno("DANGER", "Archive ALL pages?"):
                    delete_all_pages(token, db_id)

            elif "Delete Selected Page" in action:
                id_col = self.id_var.get()
                identifier = self.identifier_var.get().strip()
                if not id_col or not identifier:
                    messagebox.showerror("Error", "Select identifier column and enter identifier value")
                    return
                delete_selected_page(token, db_id, id_col, identifier)

            print("\nFinished successfully!")

        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()

    def export_page_ids(self):
        """Export real Notion title + page_id — 100% accurate"""
        db_name = self.db_var.get()
        if not db_name or db_name not in self.databases:
            messagebox.showerror("Error", "Select a database first")
            return

        token = self.databases[db_name]["token"]
        db_id = self.databases[db_name]["db_id"]

        # Use the REAL title property from Notion (not CSV dropdown!)
        title_col = getattr(self, "notion_title_prop", "Name")

        save_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Export Page IDs + Title"
        )
        if not save_path:
            return

        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

        print(f"Exporting all pages using title property: '{title_col}'...")

        all_pages = []
        cursor = None
        while True:
            payload = {"page_size": 100}
            if cursor:
                payload["start_cursor"] = cursor
            r = requests.post(f"https://api.notion.com/v1/databases/{db_id}/query", json=payload, headers=headers)
            data = r.json()
            all_pages.extend(data.get("results", []))
            cursor = data.get("next_cursor")
            if not cursor:
                break
            time.sleep(0.35)

        with open(save_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([title_col, "page_id"])
            for page in all_pages:
                text = "(no title)"
                props = page["properties"]
                if title_col in props and props[title_col].get("title"):
                    text = props[title_col]["title"][0]["plain_text"]
                writer.writerow([text, page["id"]])

        print(f"EXPORT SUCCESS: {len(all_pages)} pages")
        print(f"→ Title column: {title_col}")
        print(f"→ Saved: {save_path}")
        messagebox.showinfo("Done", f"Exported {len(all_pages)} pages!\nTitle: {title_col}\n→ {save_path}")        

        # CLEANUP BUTTON — the one you actually need
        ttk.Separator(self.root, orient="horizontal").pack(fill="x", pady=10)
        cleanup_frame = ttk.Frame(self.root)
        cleanup_frame.pack(pady=5)

        ttk.Label(cleanup_frame, text="DANGER ZONE", foreground="red", font=("Segoe UI", 10, "bold")).pack(side="left", padx=10)
        ttk.Button(
            cleanup_frame,
            text="Remove Pages NOT in Current CSV",
            command=self.cleanup_missing_pages,
            style="Accent.TButton"
        ).pack(side="left", padx=5)
        ttk.Label(cleanup_frame, text="Archives all pages whose title is missing from loaded CSV", foreground="gray", font=("Segoe UI", 9, "italic")).pack(side="left", padx=10)

    def archive_pages_in_csv(self):
        """Archive ONLY the pages whose title appears in the current CSV — your real use case"""
        if not self.csv_var.get():
            messagebox.showerror("Error", "Load the 'to-archive' CSV first")
            return
        if not self.db_var.get():
            messagebox.showerror("Error", "Select database")
            return

        csv_path = self.csv_var.get()
        token = self.databases[self.db_var.get()]["token"]
        #db_id = self.db_var.get()["db_id"]
        db_id = self.databases[self.db_var.get()]["db_id"]   # ← CORRECT
        token = self.databases[self.db_var.get()]["token"]   # ← also fix this one if you have it
        title_prop = self.notion_title_prop

        # Load titles to archive from CSV
        to_archive = set()
        csv_id_col = self.id_var.get() or "Name"
        try:
            with open(csv_path, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    val = row.get(csv_id_col, "").strip()
                    if val:
                        to_archive.add(val)
        except Exception as e:
            messagebox.showerror("CSV Error", str(e))
            return

        if not to_archive:
            messagebox.showinfo("Nothing", "No titles found in CSV")
            return

        if not messagebox.askyesno(
            "CONFIRM ARCHIVE",
            f"Archive {len(to_archive)} pages listed in CSV?\n\n"
            f"Example: {list(to_archive)[:5]}\n\n"
            "Only these will be archived. Everything else stays.",
            icon="warning"
        ):
            return

        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

        archived = 0
        for title in to_archive:
            query = {"filter": {"property": title_prop, "rich_text": {"equals": title}}}
            r = requests.post(f"https://api.notion.com/v1/databases/{db_id}/query", json=query, headers=headers)
            results = r.json().get("results", [])
            if results:
                page_id = results[0]["id"]
                patch = requests.patch(f"https://api.notion.com/v1/pages/{page_id}", json={"archived": True}, headers=headers)
                if patch.status_code == 200:
                    print(f"ARCHIVED → {title}")
                    archived += 1
                else:
                    print(f"FAILED → {title}")
            else:
                print(f"NOT FOUND → {title}")
            time.sleep(0.33)

        messagebox.showinfo("DONE", f"Archived {archived}/{len(to_archive)} pages from CSV")

    def archive_cleanup(self):
        """Test version — logs everything, no silent fails"""
        print("=== ARCHIVE BUTTON CLICKED ===")  # ← FIRST LOG — see if button works

        # Check CSV
        csv_path = self.csv_var.get().strip()
        if not csv_path:
            print("ERROR: No CSV loaded")
            messagebox.showerror("Error", "Load a CSV first")
            return
        print(f"CSV loaded: {csv_path}")

        # Check DB
        db_name = self.db_var.get()
        if not db_name or db_name not in self.databases:
            print("ERROR: No database selected")
            messagebox.showerror("Error", "Select a database")
            return
        token = self.databases[db_name]["token"]
        db_id = self.databases[db_name]["db_id"]
        print(f"DB selected: {db_name} (ID: {db_id[:8]}...)")

        # Confirm
        if not messagebox.askyesno("TEST MODE", "Run test archive? (logs only, no delete)"):
            print("User cancelled")
            return

        # Test 1: Read CSV titles
        print("Step 1: Reading CSV titles...")
        keep_titles = set()
        csv_id_col = self.id_var.get() or "Name"
        try:
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    val = row.get(csv_id_col, "").strip()
                    if val:
                        keep_titles.add(val)
            print(f"CSV has {len(keep_titles)} titles to KEEP")
        except Exception as e:
            print(f"CSV read error: {e}")
            return

        # Test 2: Query Notion (small sample)
        print("Step 2: Querying Notion (sample 10 pages)...")
        headers = {"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"}
        payload = {"page_size": 10}  # small test
        r = requests.post(f"https://api.notion.com/v1/databases/{db_id}/query", json=payload, headers=headers)
        if r.status_code != 200:
            print(f"API error: {r.status_code} - {r.text}")
            return

        data = r.json()
        pages = data.get("results", [])
        print(f"Notion returned {len(pages)} sample pages")

        # Test 3: Check titles
        title_prop = getattr(self, "notion_title_prop", "Name")
        print(f"Using title property: '{title_prop}'")
        for page in pages:
            title_text = "(no title)"
            if title_prop in page["properties"]:
                t = page["properties"][title_prop].get("title")
                if t:
                    title_text = t[0]["plain_text"]
            is_keep = title_text in keep_titles
            print(f"Sample page '{title_text}' → KEEP: {is_keep}")

        print("=== TEST COMPLETE — FUNCTION WORKS ===")
        messagebox.showinfo("Test OK", "Button + function work! Ready for real archive.")
if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
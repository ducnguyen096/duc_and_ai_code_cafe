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
        self.root.geometry("940x740")
        self.root.minsize(800, 600)
        self.setup_ui()

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

        # 3b. Identifier Column
        f3b = ttk.LabelFrame(self.root, text="Identifier Column (Page Title)")
        f3b.pack(fill="x", padx=15, pady=5)
        self.id_var = tk.StringVar()
        self.id_combo = ttk.Combobox(f3b, textvariable=self.id_var, state="readonly")
        self.id_combo.pack(fill="x", padx=10, pady=8)

        # 3c. Identifier Value (for Delete Selected Page)
        f3c = ttk.LabelFrame(self.root, text="Identifier Value (Delete Selected Page)")
        f3c.pack(fill="x", padx=15, pady=5)
        self.identifier_var = tk.StringVar()
        ttk.Entry(f3c, textvariable=self.identifier_var).pack(fill="x", padx=10, pady=8)

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
        logf = ttk.LabelFrame(self.root, text="Log Output")
        logf.pack(fill="both", expand=True, padx=15, pady=10)
        self.log = tk.Text(logf, wrap="word", font=("Consolas", 10))
        sb = ttk.Scrollbar(logf, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        self.log.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        style.configure("Accent.TButton", foreground="white", background="#0078d4", font=("Segoe UI", 10, "bold"))
        sys.stdout = Logger(self.log)

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
        print(f"Loading properties for '{name}'...")
        props = get_multi_select_properties(token, db_id)
        print("Properties returned:", props)  # Debug line


        # Normalize to strings
        
        if props:
            prop_names = [p if isinstance(p, str) else str(p) for p in props]
            self.prop_combo["values"] = prop_names
            self.prop_combo.current(0)
            print(f"Found {len(props)} multi-select properties")
        else:
            self.prop_combo["values"] = []
            print("No multi-select properties")

    def browse_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path:
            self.csv_var.set(path)
            # Load headers into identifier dropdown
            try:
                with open(path, encoding="utf-8") as f:
                    reader = csv.reader(f)
                    headers = next(reader, [])
                    self.id_combo["values"] = headers
                    if headers:
                        self.id_combo.current(0)
                        print(f"Identifier column options loaded: {headers}")
            except Exception as e:
                print(f"Failed to read CSV headers: {e}")            
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
        """Export all pages: Title + page_id → CSV (your golden backup)"""
        db_name = self.db_var.get()
        if not db_name or db_name not in self.databases:
            messagebox.showerror("Error", "Select a database first")
            return

        token = self.databases[db_name]["token"]
        db_id = self.databases[db_name]["db_id"]
        id_col = self.id_var.get() or "Name"  # fallback to Name if nothing selected

        save_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save Page IDs as..."
        )
        if not save_path:
            return

        headers = {"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"}
        pages = []
        cursor = None

        print(f"Exporting all pages from '{db_name}'...")
        while True:
            payload = {"page_size": 100}
            if cursor:
                payload["start_cursor"] = cursor
            r = requests.post(f"https://api.notion.com/v1/databases/{db_id}/query", json=payload, headers=headers)
            data = r.json()
            pages.extend(data.get("results", []))
            cursor = data.get("next_cursor")
            if not cursor:
                break
            time.sleep(0.35)

        try:
            with open(save_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([id_col, "page_id"])  # header
                for p in pages:
                    title_text = "(empty)"
                    if id_col in p["properties"] and p["properties"][id_col]["title"]:
                        title_text = p["properties"][id_col]["title"][0]["plain_text"]
                    writer.writerow([title_text, p["id"]])
            print(f"Exported {len(pages)} pages → {save_path}")
            messagebox.showinfo("Success", f"Exported {len(pages)} pages!\n{save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Save failed:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
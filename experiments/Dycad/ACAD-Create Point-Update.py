# Run OK in AutoCAD Python environment with pyautocad installed
# Writen by Windows Copilot under conceptual guidance of Duk, November 2025
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import threading
import os
from pyautocad import Autocad, APoint
import pythoncom
#import time

df = None  # Global to hold loaded data

def insert_points(dwg_path):
    pythoncom.CoInitialize()  # 👈 Initialize COM for this thread
    global df
    #pythoncom.CoInitialize()  # 👈 Initialize COM for this thread
    try:
        acad = Autocad(create_if_not_exists=True)
        app = acad.app
        doc = app.Documents.Add() # 👈 This creates a new DWG
        import time
        time.sleep(1.5)  # 👈 Wait for the document to be ready
        modelspace = doc.ModelSpace
        #time.sleep(1.5)  # 👈 Wait for the document to be ready
        circle_radius = 2000     # 15 meters radius = 30 meters diameter
        text_height = 3000        # 5 meters tall text

        for _, row in df.iterrows():
            x = float(row.get("X", 0))
            y = float(row.get("Y", 0))
            name = str(row.get("Name", ""))


            pt = APoint(x, -y)  # Left Handed, mirror Y
            modelspace.AddCircle(pt, circle_radius)
            if name:
                modelspace.AddText(name, pt, text_height)

        doc.SaveAs(dwg_path)
        doc.Close(False)  # 👈 This releases the file
        messagebox.showinfo("Success", f"DWG saved to:\n{dwg_path}")
        root.quit()  # 👈 This closes the app
    except Exception as e:
        messagebox.showerror("Error", str(e))

def load_file():
    global df
    filepath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if not filepath:
        return
    try:
        df = pd.read_csv(filepath)
        file_label.config(text=f"Loaded: {os.path.basename(filepath)}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def run_insertion():
    if df is None:
        messagebox.showerror("Error", "No CSV file loaded.")
        return
    output_path = output_entry.get().strip()
    if not output_path.lower().endswith(".dwg"):
        messagebox.showerror("Error", "Output file must end with .dwg")
        return
    threading.Thread(target=insert_points, args=(output_path,), daemon=True).start()

# UI Setup
root = tk.Tk()
root.title("AutoCAD Point Importer")

frame = tk.Frame(root, padx=20, pady=20)
frame.pack()

tk.Label(frame, text="Step 1: Load CSV with X, Y, Name columns").pack()
tk.Button(frame, text="Browse CSV", command=load_file).pack(pady=5)
file_label = tk.Label(frame, text="No file loaded")
file_label.pack()

tk.Label(frame, text="Step 2: Output DWG file path").pack(pady=(20, 5))
output_entry = tk.Entry(frame, width=50)
output_entry.insert(0, os.path.expanduser("~\\inserted_points.dwg"))
output_entry.pack()

tk.Label(frame, text="Step 3: Run").pack(pady=(20, 5))
tk.Button(frame, text="Run", command=run_insertion, bg="green", fg="white").pack()

root.mainloop()
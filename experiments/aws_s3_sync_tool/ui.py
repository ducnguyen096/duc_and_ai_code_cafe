import tkinter as tk
from tkinter import messagebox
import s3_list, s3_delete, s3_sync

def list_buckets_ui():
    try:
        buckets = s3_list.list_buckets()
        messagebox.showinfo("Buckets", "\n".join(buckets))
    except Exception as e:
        messagebox.showerror("Error", str(e))

def delete_bucket_ui():
    bucket_name = entry_bucket.get()
    if not bucket_name:
        messagebox.showerror("Error", "Enter bucket name")
        return
    try:
        msg = s3_delete.delete_bucket(bucket_name)
        messagebox.showinfo("Success", msg)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def sync_bucket_ui():
    bucket_name = entry_bucket.get()
    local_path = entry_path.get()
    if not bucket_name or not local_path:
        messagebox.showerror("Error", "Enter bucket name and local path")
        return
    try:
        msg = s3_sync.sync_bucket(bucket_name, local_path, direction="upload")
        messagebox.showinfo("Success", msg)
    except Exception as e:
        messagebox.showerror("Error", str(e))

# Tkinter UI setup
root = tk.Tk()
root.title("AWS S3 Manager")

tk.Label(root, text="Bucket Name:").grid(row=0, column=0, padx=5, pady=5)
entry_bucket = tk.Entry(root, width=40)
entry_bucket.grid(row=0, column=1, padx=5, pady=5)

tk.Label(root, text="Local Path:").grid(row=1, column=0, padx=5, pady=5)
entry_path = tk.Entry(root, width=40)
entry_path.grid(row=1, column=1, padx=5, pady=5)

tk.Button(root, text="List Buckets", command=list_buckets_ui).grid(row=2, column=0, padx=5, pady=5)
tk.Button(root, text="Delete Bucket", command=delete_bucket_ui).grid(row=2, column=1, padx=5, pady=5)
tk.Button(root, text="Sync Bucket", command=sync_bucket_ui).grid(row=3, column=0, columnspan=2, padx=5, pady=5)

root.mainloop()
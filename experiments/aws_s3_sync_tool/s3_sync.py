import subprocess

def sync_bucket(bucket_name: str, local_path: str, direction: str = "upload"):
    """
    Sync local folder with S3 bucket.
    direction = "upload" → local → S3
    direction = "download" → S3 → local
    """
    if direction == "upload":
        cmd = ["aws", "s3", "sync", local_path, f"s3://{bucket_name}"]
    elif direction == "download":
        cmd = ["aws", "s3", "sync", f"s3://{bucket_name}", local_path]
    else:
        raise ValueError("direction must be 'upload' or 'download'")
    
    subprocess.run(cmd, check=True)
    return f"Sync {direction} completed"
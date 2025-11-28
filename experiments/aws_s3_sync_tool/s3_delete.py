import boto3

s3 = boto3.client('s3')

def delete_bucket(bucket_name: str):
    """Delete a bucket by name."""
    s3.delete_bucket(Bucket=bucket_name)
    return f"Bucket '{bucket_name}' deleted"
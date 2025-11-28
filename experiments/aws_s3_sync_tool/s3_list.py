import boto3

s3 = boto3.client('s3')

def list_buckets():
    """Return a list of bucket names."""
    response = s3.list_buckets()
    return [bucket['Name'] for bucket in response['Buckets']]
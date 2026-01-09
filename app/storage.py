# app/storage.py
import os
import boto3
from dotenv import load_dotenv

load_dotenv()

# ===== Cloudflare R2 Config =====
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET_NAME")

# Create S3-compatible client for R2
s3 = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    region_name="auto"
)

def upload_blob(key: str, content_bytes: bytes):
    """
    Upload encrypted invoice blob to Cloudflare R2
    """
    s3.put_object(
        Bucket=R2_BUCKET,
        Key=key,
        Body=content_bytes
    )
    return f"s3://{R2_BUCKET}/{key}"

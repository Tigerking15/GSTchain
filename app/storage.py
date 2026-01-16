# app/storage.py
import os
import json
import base64
import boto3
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()

R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET_NAME")

s3 = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    region_name="auto"
)

def ensure_bucket():
    try:
        s3.head_bucket(Bucket=R2_BUCKET)
    except ClientError:
        s3.create_bucket(Bucket=R2_BUCKET)

def upload_blob(key: str, content_bytes: bytes) -> str:
    ensure_bucket()

    s3.put_object(
        Bucket=R2_BUCKET,
        Key=key,
        Body=content_bytes,
        ContentType="application/octet-stream"
    )

    return f"s3://{R2_BUCKET}/{key}"


def upload_json(key: str, data: dict) -> str:
    """
    Upload JSON-safe data to Cloudflare R2
    """
    ensure_bucket()

    content_bytes = json.dumps(data, indent=2).encode("utf-8")

    s3.put_object(
        Bucket=R2_BUCKET,
        Key=key,
        Body=content_bytes,
        ContentType="application/json"
    )

    return f"s3://{R2_BUCKET}/{key}"

def download_blob(key: str) -> bytes:
    obj = s3.get_object(Bucket=R2_BUCKET, Key=key)
    return obj["Body"].read()
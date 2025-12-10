# app/storage.py
import os, boto3
from botocore.client import Config
from dotenv import load_dotenv
load_dotenv()

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "invoices")

s3 = boto3.resource(
    's3',
    endpoint_url=f"http://{MINIO_ENDPOINT}",
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    config=Config(signature_version='s3v4'),
    region_name='us-east-1'
)

def ensure_bucket():
    try:
        s3.create_bucket(Bucket=MINIO_BUCKET)
    except Exception:
        pass

def upload_blob(key: str, content_bytes: bytes):
    ensure_bucket()
    obj = s3.Object(MINIO_BUCKET, key)
    obj.put(Body=content_bytes)
    return f"s3://{MINIO_BUCKET}/{key}"

import json
import boto3
import os
from dotenv import load_dotenv
from app.crypto_decrypt import decrypt_payload

load_dotenv()

s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("R2_ENDPOINT"),
    aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
    region_name="auto"
)

BUCKET = os.getenv("R2_BUCKET_NAME")

def fetch_and_decrypt(object_key: str):
    obj = s3.get_object(Bucket=BUCKET, Key=object_key)
    encrypted_json = json.loads(obj["Body"].read().decode("utf-8"))
    return decrypt_payload(encrypted_json)

if __name__ == "__main__":
    key = "25aeeb00d0e812a959105780b343499a1311fde8d2d71d2eb2fa9ad5d68d9c42.json.json"
    invoice = fetch_and_decrypt(key)
    print(json.dumps(invoice, indent=2))

from fastapi import APIRouter
from app.models import SessionLocal, InvoiceMeta
from app.storage import download_blob
from app.crypto import decrypt_blob
import json
import hashlib

router = APIRouter()

@router.get("/verify/{invoice_hash}")
def verify(invoice_hash: str):
    db = SessionLocal()
    try:
        meta = db.query(InvoiceMeta).filter(
            InvoiceMeta.invoice_hash == invoice_hash
        ).first()

        if not meta:
            return {"valid": False, "reason": "Invoice not found"}

        key = meta.object_path.replace("s3://", "").split("/", 1)[1]
        encrypted_blob_bytes = download_blob(key)
        encrypted_blob = json.loads(encrypted_blob_bytes.decode("utf-8"))
        decrypted_bytes = decrypt_blob(encrypted_blob)

        # The decrypted_bytes contain the canonical invoice WITHOUT metadata
        # This is the exact same data that was hashed during ingestion
        # So we can directly compute the hash from it
        recomputed_hash = hashlib.sha256(decrypted_bytes).hexdigest()

        hash_match = recomputed_hash == invoice_hash
        onchain = meta.onchain_txid is not None

        return {
            "valid": hash_match and onchain,
            "hash_match": hash_match,
            "tampered": not hash_match,
            "onchain": onchain,
            "onchain_txid": meta.onchain_txid,
        }
    finally:
        db.close() 
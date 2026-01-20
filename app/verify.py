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


@router.get("/invoice/{invoice_hash}")
def get_invoice_data(invoice_hash: str):
    """
    Get the full decrypted invoice JSON data.
    This allows auditors to view the actual invoice content.
    """
    db = SessionLocal()
    try:
        meta = db.query(InvoiceMeta).filter(
            InvoiceMeta.invoice_hash == invoice_hash
        ).first()

        if not meta:
            return {"error": "Invoice not found", "invoice_hash": invoice_hash}

        key = meta.object_path.replace("s3://", "").split("/", 1)[1]
        encrypted_blob_bytes = download_blob(key)
        encrypted_blob = json.loads(encrypted_blob_bytes.decode("utf-8"))
        decrypted_bytes = decrypt_blob(encrypted_blob)
        
        # Parse the decrypted JSON
        invoice_data = json.loads(decrypted_bytes.decode("utf-8"))

        return {
            "invoice_hash": invoice_hash,
            "ingestion_id": meta.ingestion_id,
            "supplier_gstin": meta.supplier_gstin,
            "recipient_gstin": meta.recipient_gstin,
            "onchain_txid": meta.onchain_txid,
            "object_path": meta.object_path,
            "invoice_data": invoice_data
        }
    except Exception as e:
        return {"error": str(e), "invoice_hash": invoice_hash}
    finally:
        db.close()


@router.get("/invoices/by-gstin/{gstin}")
def get_invoices_by_gstin(gstin: str):
    """
    Get all invoices involving a specific GSTIN (as supplier or recipient).
    """
    gstin = gstin.upper().strip()
    db = SessionLocal()
    try:
        # Find as supplier
        as_supplier = db.query(InvoiceMeta).filter(
            InvoiceMeta.supplier_gstin == gstin
        ).all()
        
        # Find as recipient
        as_recipient = db.query(InvoiceMeta).filter(
            InvoiceMeta.recipient_gstin == gstin
        ).all()
        
        invoices = []
        seen_hashes = set()
        
        for inv in as_supplier + as_recipient:
            if inv.invoice_hash not in seen_hashes:
                seen_hashes.add(inv.invoice_hash)
                invoices.append({
                    "invoice_hash": inv.invoice_hash,
                    "ingestion_id": inv.ingestion_id,
                    "supplier_gstin": inv.supplier_gstin,
                    "recipient_gstin": inv.recipient_gstin,
                    "onchain_txid": inv.onchain_txid,
                    "role": "supplier" if inv.supplier_gstin == gstin else "recipient"
                })
        
        return {
            "gstin": gstin,
            "total_invoices": len(invoices),
            "as_supplier": len([i for i in invoices if i["role"] == "supplier"]),
            "as_recipient": len([i for i in invoices if i["role"] == "recipient"]),
            "invoices": invoices
        }
    finally:
        db.close() 
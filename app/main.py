# app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid, json, os
from datetime import datetime
from app.normalize import canonicalize
from app.crypto import encrypt_bytes
from app.storage import upload_blob
from app.models import init_db, SessionLocal, InvoiceMeta
from app.anchor import mock_anchor
from app.graph import upsert_edge

app = FastAPI(title="GST Circular Trade Detector - Ingest API")
init_db()

class InvoiceIn(BaseModel):
    invoice_id: str
    invoice_date: str
    supplier_gstin: str
    recipient_gstin: str
    supplier_pan: str = None
    recipient_pan: str = None
    supplier_name: str = None
    recipient_name: str = None
    supplier_address: str = None
    recipient_address: str = None
    items: list = []
    total_value: float = 0.0
    tax_total: float = 0.0
    place_of_supply: str = None
    supply_type: str = "B2B"
    currency: str = "INR"
    source_type: str = "API"
    source_system: str = None

@app.post("/invoices")
def ingest_invoice(payload: InvoiceIn):
    # add ingestion metadata
    ingest_meta = {
        "ingestion_id": str(uuid.uuid4()),
        "ingestion_timestamp": datetime.utcnow().isoformat() + "Z"
    }
    rec = payload.dict()
    rec.update(ingest_meta)
    # canonicalize
    try:
        canonical, serialized = canonicalize(rec)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Normalization failed: {e}")

    invoice_hash = canonical["metadata"]["invoice_hash"]
    # encrypt blob
    enc = encrypt_bytes(serialized)
    # upload to MinIO
    key = f"{invoice_hash}.json.enc"
    obj_path = upload_blob(key, json.dumps(enc).encode("utf-8"))
    canonical["metadata"]["file_pointer"] = obj_path

    # anchor (mock)
    anchor_res = mock_anchor(invoice_hash, canonical["supplier"]["gstin"], canonical["recipient"]["gstin"], canonical["total_value"])
    canonical["metadata"]["onchain_txid"] = anchor_res["txid"]
    canonical["metadata"]["onchain_timestamp"] = datetime.utcfromtimestamp(anchor_res["timestamp"]).isoformat() + "Z"

    # persist metadata in Postgres
    db = SessionLocal()
    meta = InvoiceMeta(
        id=str(uuid.uuid4()),
        ingestion_id=canonical["ingestion"]["ingestion_id"],
        supplier_gstin=canonical["supplier"]["gstin"],
        recipient_gstin=canonical["recipient"]["gstin"],
        invoice_id=canonical["invoice_id"],
        invoice_date=datetime.fromisoformat(canonical["invoice_date"]),
        invoice_hash=invoice_hash,
        object_path=obj_path,
        onchain_txid=canonical["metadata"]["onchain_txid"]
    )
    try:
        db.add(meta)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB write failed: {e}")
    finally:
        db.close()

    # create graph edge in Neo4j
    try:
        upsert_edge(canonical["supplier"]["gstin"], canonical["recipient"]["gstin"],
                    invoice_hash, canonical["invoice_date"], canonical["total_value"],
                    canonical["metadata"]["onchain_txid"], canonical["ingestion"]["ingestion_id"])
    except Exception as e:
        # log and continue: graph failure shouldn't block ingestion
        print("Graph write failed:", e)

    # run quick rule checks (placeholder)
    # e.g., duplicate invoice number across unrelated GSTINs -> later you can add queries
    response = {
        "status": "ingested",
        "ingestion_id": canonical["ingestion"]["ingestion_id"],
        "invoice_hash": invoice_hash,
        "onchain_txid": canonical["metadata"]["onchain_txid"],
        "object_path": obj_path
    }
    return response

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid, json
from datetime import datetime

from app.normalize import canonicalize
from app.crypto import encrypt_bytes
from app.storage import upload_blob
from app.models import init_db, SessionLocal, InvoiceMeta
from app.anchor import mock_anchor
from app.graph import upsert_edge

# --------------------------------------------------
# App init
# --------------------------------------------------
app = FastAPI(title="GST Circular Trade Detector - Ingest API")
init_db()

# --------------------------------------------------
# SCHEMA (UPDATED TO YOUR NEW INVOICE FORMAT)
# --------------------------------------------------

class InvoiceMetadata(BaseModel):
    supply_type: Optional[str] = "B2B"
    source_system: Optional[str] = None
    is_einvoice: Optional[bool] = False


class Header(BaseModel):
    invoice_id: str
    invoice_date: str
    currency: Optional[str] = "INR"
    place_of_supply: Optional[str] = None


class Compliance(BaseModel):
    irn: Optional[str] = None
    ack_no: Optional[str] = None
    ack_date: Optional[str] = None
    qr_code_data: Optional[str] = None


class Party(BaseModel):
    gstin: str
    pan: Optional[str] = None
    name: Optional[str] = None
    address: Optional[str] = None


class Item(BaseModel):
    item_id: Optional[int] = None
    description: Optional[str] = None
    hsn_sac: Optional[str] = None
    quantity: Optional[float] = None
    uom: Optional[str] = None
    unit_price: Optional[float] = None
    taxable_value: Optional[float] = None
    gst_rate: Optional[float] = None
    cgst_amount: Optional[float] = None
    sgst_amount: Optional[float] = None
    igst_amount: Optional[float] = None


class Totals(BaseModel):
    total_taxable_value: Optional[float] = 0.0
    cgst_total: Optional[float] = 0.0
    sgst_total: Optional[float] = 0.0
    igst_total: Optional[float] = 0.0
    tax_total: Optional[float] = 0.0
    grand_total: Optional[float] = 0.0


class InvoiceIn(BaseModel):
    invoice_metadata: Optional[InvoiceMetadata] = None
    header: Header
    compliance: Optional[Compliance] = None
    supplier: Party
    recipient: Party
    items: List[Item] = []
    totals: Totals

# --------------------------------------------------
# API ENDPOINT
# --------------------------------------------------

@app.post("/invoices")
def ingest_invoice(payload: InvoiceIn):

    ingest_meta = {
        "ingestion_id": str(uuid.uuid4()),
        "ingestion_timestamp": datetime.utcnow().isoformat() + "Z"
    }

    rec = payload.dict()
    rec.update(ingest_meta)

    # ---------------- Normalization ----------------
    try:
        canonical, serialized = canonicalize(rec)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Normalization failed: {e}")

    invoice_hash = canonical["metadata"]["invoice_hash"]

    # ---------------- Encryption -------------------
    enc = encrypt_bytes(serialized)

    # ---------------- Object Storage ---------------
    key = f"{invoice_hash}.json.enc"
    obj_path = upload_blob(key, json.dumps(enc).encode("utf-8"))
    canonical["metadata"]["file_pointer"] = obj_path

    # ---------------- Blockchain Anchor ------------
    anchor_res = mock_anchor(
        invoice_hash,
        canonical["supplier"]["gstin"],
        canonical["recipient"]["gstin"],
        canonical["total_value"]
    )

    canonical["metadata"]["onchain_txid"] = anchor_res["txid"]
    canonical["metadata"]["onchain_timestamp"] = (
        datetime.utcfromtimestamp(anchor_res["timestamp"]).isoformat() + "Z"
    )

    # ---------------- Postgres ---------------------
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

    # ---------------- Neo4j Graph ------------------
    try:
        upsert_edge(
            canonical["supplier"]["gstin"],
            canonical["recipient"]["gstin"],
            invoice_hash,
            canonical["invoice_date"],
            canonical["total_value"],
            canonical["metadata"]["onchain_txid"],
            canonical["ingestion"]["ingestion_id"]
        )
    except Exception as e:
        print("Graph write failed:", e)

    # ---------------- Response ---------------------
    return {
        "status": "ingested",
        "ingestion_id": canonical["ingestion"]["ingestion_id"],
        "invoice_hash": invoice_hash,
        "onchain_txid": canonical["metadata"]["onchain_txid"],
        "object_path": obj_path
    }

# app/normalize.py
from dateutil import parser as dparser
import json
import hashlib

def iso_date(s: str):
    return dparser.parse(s).date().isoformat()

def canonicalize(record: dict) -> dict:
    # minimal mapping — extend with fuzzy mapping rules & confidence
    canonical = {
        "invoice_id": record.get("invoice_id"),
        "invoice_date": iso_date(record.get("invoice_date")),
        "irn": record.get("irn") or None,
        "supplier": {
            "gstin": record.get("supplier_gstin", "").strip().upper(),
            "pan": record.get("supplier_pan"),
            "legal_name": record.get("supplier_name"),
            "address": record.get("supplier_address"),
        },
        "recipient": {
            "gstin": record.get("recipient_gstin", "").strip().upper(),
            "pan": record.get("recipient_pan"),
            "legal_name": record.get("recipient_name"),
            "address": record.get("recipient_address"),
        },
        "items": record.get("items", []),
        "total_value": float(record.get("total_value", 0)),
        "tax_total": float(record.get("tax_total", 0)),
        "place_of_supply": record.get("place_of_supply"),
        "supply_type": record.get("supply_type", "B2B"),
        "currency": record.get("currency", "INR"),
        "original_source": {
            "source_type": record.get("source_type", "CSV"),
            "source_system": record.get("source_system"),
        },
        "ingestion": {
            "ingestion_id": record.get("ingestion_id"),
            "ingestion_timestamp": record.get("ingestion_timestamp")
        },
        "metadata": {
            "invoice_hash": None,
            "file_pointer": None,
            "onchain_txid": None,
            "onchain_timestamp": None
        }
    }
    # deterministic serialization
    serialized = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    canonical["metadata"]["invoice_hash"] = hashlib.sha256(serialized).hexdigest()
    return canonical, serialized

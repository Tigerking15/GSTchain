# app/normalize.py
from dateutil import parser as dparser
import json
import hashlib


def iso_date(s: str):
    if not s:
        return None
    return dparser.parse(s).date().isoformat()


def canonicalize(record: dict):
    """
    Accepts BOTH:
    - Old flat invoice format
    - New nested e-invoice-like format

    Always outputs the SAME canonical structure.
    """

    # -------------------------------
    # Detect format (nested vs flat)
    # -------------------------------

    is_nested = "header" in record and "supplier" in record and "totals" in record

    if is_nested:
        # -------- NEW NESTED FORMAT --------
        header = record.get("header", {})
        supplier = record.get("supplier", {})
        recipient = record.get("recipient", {})
        totals = record.get("totals", {})
        compliance = record.get("compliance", {})
        metadata = record.get("invoice_metadata", {})

        invoice_id = header.get("invoice_id")
        invoice_date = iso_date(header.get("invoice_date"))

        supplier_gstin = supplier.get("gstin", "").strip().upper()
        recipient_gstin = recipient.get("gstin", "").strip().upper()

        supplier_pan = supplier.get("pan")
        recipient_pan = recipient.get("pan")

        supplier_name = supplier.get("name")
        recipient_name = recipient.get("name")

        supplier_address = supplier.get("address")
        recipient_address = recipient.get("address")

        total_value = float(totals.get("grand_total", 0.0))
        tax_total = float(totals.get("tax_total", 0.0))

        place_of_supply = header.get("place_of_supply")
        supply_type = metadata.get("supply_type", "B2B")
        currency = header.get("currency", "INR")

        irn = compliance.get("irn")
        ack_no = compliance.get("ack_no")
        ack_date = compliance.get("ack_date")

        source_type = "E-INVOICE" if metadata.get("is_einvoice") else "CSV"
        source_system = metadata.get("source_system")

        items = record.get("items", [])

    else:
        # -------- OLD FLAT FORMAT --------
        invoice_id = record.get("invoice_id")
        invoice_date = iso_date(record.get("invoice_date"))

        supplier_gstin = record.get("supplier_gstin", "").strip().upper()
        recipient_gstin = record.get("recipient_gstin", "").strip().upper()

        supplier_pan = record.get("supplier_pan")
        recipient_pan = record.get("recipient_pan")

        supplier_name = record.get("supplier_name")
        recipient_name = record.get("recipient_name")

        supplier_address = record.get("supplier_address")
        recipient_address = record.get("recipient_address")

        total_value = float(record.get("total_value", 0))
        tax_total = float(record.get("tax_total", 0))

        place_of_supply = record.get("place_of_supply")
        supply_type = record.get("supply_type", "B2B")
        currency = record.get("currency", "INR")

        irn = record.get("irn")

        source_type = record.get("source_type", "CSV")
        source_system = record.get("source_system")

        items = record.get("items", [])

    # -------------------------------
    # Canonical structure (UNCHANGED)
    # -------------------------------

    canonical = {
        "invoice_id": invoice_id,
        "invoice_date": invoice_date,
        "irn": irn,
        "ack_no": ack_no,
        "ack_date": ack_date,

        "supplier": {
            "gstin": supplier_gstin,
            "pan": supplier_pan,
            "legal_name": supplier_name,
            "address": supplier_address,
        },
        "recipient": {
            "gstin": recipient_gstin,
            "pan": recipient_pan,
            "legal_name": recipient_name,
            "address": recipient_address,
        },
        "items": items,
        "total_value": total_value,
        "tax_total": tax_total,
        "place_of_supply": place_of_supply,
        "supply_type": supply_type,
        "currency": currency,
        "original_source": {
            "source_type": source_type,
            "source_system": source_system,
        },
        "ingestion": {
            "ingestion_id": record.get("ingestion_id"),
            "ingestion_timestamp": record.get("ingestion_timestamp"),
        },
        "metadata": {
            "invoice_hash": None,
            "file_pointer": None,
            "onchain_txid": None,
            "onchain_timestamp": None,
        },
    }

    # -------------------------------
    # Deterministic hashing
    # -------------------------------

    serialized = json.dumps(
        canonical,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False
    ).encode("utf-8")

    canonical["metadata"]["invoice_hash"] = hashlib.sha256(serialized).hexdigest()

    return canonical, serialized

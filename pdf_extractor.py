import pdfplumber
import json
import re
import requests
import time

# ================= CONFIG =================
API_URL = "http://127.0.0.1:8000/invoices"
REQUEST_TIMEOUT = 10
# ==========================================


def process_invoice(pdf_path):
    all_text = ""
    table_raw_data = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text += text + "\n"

            extracted_table = page.extract_table()
            if extracted_table:
                table_raw_data.extend(extracted_table)

    def find_val(label):
        match = re.search(rf"{label}:\s*(.*)", all_text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    raw_supply_type = find_val("Supply Type")
    is_einvoice_text = find_val("Is E-Invoice")

    final_supply_type = raw_supply_type
    if is_einvoice_text and is_einvoice_text.lower() == "yes":
        final_supply_type = "E-INV"

    invoice_json = {
        "invoice_metadata": {
            "supply_type": final_supply_type,
            "source_system": find_val("Source System"),
            "is_einvoice": is_einvoice_text and is_einvoice_text.lower() == "yes"
        },
        "header": {
            "invoice_id": find_val("Invoice ID"),
            "invoice_date": find_val("Invoice Date"),
            "currency": find_val("Currency"),
            "place_of_supply": find_val("Place of Supply")
        },
        "compliance": {
            "irn": find_val("IRN") if final_supply_type == "E-INV" else None,
            "ack_no": find_val("Ack No"),
            "ack_date": find_val("Ack Date")
        },
        "supplier": {
            "name": find_val("Supplier Name"),
            "gstin": find_val("Supplier GSTIN"),
            "pan": find_val("Supplier PAN"),
            "address": find_val("Supplier Address")
        },
        "recipient": {
            "name": find_val("Recipient Name"),
            "gstin": find_val("Recipient GSTIN") if final_supply_type != "B2C" else None,
            "pan": find_val("Recipient PAN"),
            "address": find_val("Recipient Address")
        },
        "items": [],
        "totals": {
            "total_taxable_value": float(find_val("Total Taxable Value") or 0),
            "cgst_total": float(find_val("Total CGST") or 0),
            "sgst_total": float(find_val("Total SGST") or 0),
            "grand_total": float(find_val("Grand Total") or 0)
        },
        "final_validation": {}
    }

    accumulated_taxable = 0.0
    accumulated_cgst = 0.0
    accumulated_sgst = 0.0

    if table_raw_data:
        for row in table_raw_data[1:]:
            if row and len(row) >= 10 and row[1]:
                taxable = float(row[6])
                gst_rate = float(row[7])
                cgst_in_pdf = float(row[8])
                sgst_in_pdf = float(row[9])

                accumulated_taxable += taxable
                accumulated_cgst += cgst_in_pdf
                accumulated_sgst += sgst_in_pdf

                expected_tax = round((taxable * (gst_rate / 2)) / 100, 2)
                math_status = "MATCHED"
                if cgst_in_pdf != expected_tax:
                    math_status = f"ERROR (Expected {expected_tax})"

                invoice_json["items"].append({
                    "item_id": row[0],
                    "description": row[1],
                    "hsn_sac": row[2],
                    "quantity": row[3],
                    "uom": row[4],
                    "unit_price": row[5],
                    "taxable_value": taxable,
                    "gst_rate": gst_rate,
                    "cgst_amount": cgst_in_pdf,
                    "sgst_amount": sgst_in_pdf,
                    "math_validation": math_status
                })

    calc_grand_total = round(
        accumulated_taxable + accumulated_cgst + accumulated_sgst, 2
    )

    invoice_json["final_validation"] = {
        "items_taxable_sum": round(accumulated_taxable, 2),
        "items_gst_sum": round(accumulated_cgst + accumulated_sgst, 2),
        "calculated_grand_total": calc_grand_total,
        "grand_total_status": (
            "MATCHED"
            if abs(calc_grand_total - invoice_json["totals"]["grand_total"]) < 0.01
            else f"MISMATCH (PDF says {invoice_json['totals']['grand_total']})"
        )
    }

    return invoice_json


def send_invoice_to_api(invoice_json):
    try:
        response = requests.post(
            API_URL,
            json=invoice_json,
            timeout=REQUEST_TIMEOUT
        )

        if response.status_code == 200:
            print("✅ Ingested | Hash:", response.json().get("invoice_hash"))
        else:
            print("❌ Failed:", response.status_code, response.text)

    except Exception as e:
        print("❌ API Error:", e)


# ============ ENTRY POINT ============
if __name__ == "__main__":
    pdf_path = "invoice.pdf"   # change or loop over a folder

    try:
        invoice_data = process_invoice(pdf_path)
        send_invoice_to_api(invoice_data)

    except Exception as e:
        print("❌ Processing Error:", e)

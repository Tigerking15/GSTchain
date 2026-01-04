import json
import requests
import time

API_URL = "http://127.0.0.1:8000/invoices"
JSON_FILE = "new_invoices.json"

def bulk_ingest():
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        invoices = json.load(f)

    print(f"Found {len(invoices)} invoices. Starting upload...\n")

    success = 0
    failed = 0

    for idx, invoice in enumerate(invoices, start=1):
        try:
            response = requests.post(API_URL, json=invoice, timeout=10)

            if response.status_code == 200:
                success += 1
                print(f"[{idx}] ✅ Ingested | Hash: {response.json().get('invoice_hash')}")
            else:
                failed += 1
                print(f"[{idx}] ❌ Failed ({response.status_code}) | {response.text}")

        except Exception as e:
            failed += 1
            print(f"[{idx}] ❌ Error | {e}")

        # small delay to avoid hammering API
        time.sleep(0.05)

    print("\n==== INGEST SUMMARY ====")
    print(f"Total   : {len(invoices)}")
    print(f"Success : {success}")
    print(f"Failed  : {failed}")

if __name__ == "__main__":
    bulk_ingest()

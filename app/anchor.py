# app/anchor.py
import uuid, time
def mock_anchor(invoice_hash: str, supplier: str, recipient: str, amount: float) -> dict:
    # Replace with Hyperledger Fabric / Quorum call
    txid = f"MOCKTX-{uuid.uuid4().hex[:12]}-{int(time.time())}"
    return {"txid": txid, "timestamp": int(time.time())}

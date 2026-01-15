from web3 import Web3
import os
import time

w3 = Web3(Web3.HTTPProvider(os.getenv("BLOCKCHAIN_RPC_URL")))

PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY")
WALLET_ADDRESS = Web3.to_checksum_address(os.getenv("WALLET_ADDRESS"))
CHAIN_ID = int(os.getenv("CHAIN_ID"))

def anchor_hash_on_chain(invoice_hash: str, supplier: str, recipient: str, amount: float):
    hash_bytes = w3.to_bytes(hexstr=invoice_hash)

    tx = {
        "chainId": CHAIN_ID,
        "from": WALLET_ADDRESS,
        "to": WALLET_ADDRESS,     # self‑tx (proof anchor)
        "value": 0,
        "nonce": w3.eth.get_transaction_count(WALLET_ADDRESS),
        "data": hash_bytes,
    }

    # 🔥 IMPORTANT: estimate gas
    gas_estimate = w3.eth.estimate_gas(tx)
    tx["gas"] = gas_estimate + 5000  # safety buffer
    tx["gasPrice"] = w3.eth.gas_price

    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)

    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    return {
        "txid": tx_hash.hex(),
        "timestamp": int(time.time()),
        "blockNumber": receipt.blockNumber
    }

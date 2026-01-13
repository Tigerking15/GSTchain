import os
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv

load_dotenv()

# 🔑 MUST be HEX, 64 chars = 32 bytes = AES-256
KEY_HEX = os.getenv("MASTER_KEY_HEX")
if not KEY_HEX:
    raise RuntimeError("MASTER_KEY_HEX not set")

KEY = bytes.fromhex(KEY_HEX)  # ✅ CORRECT

def decrypt_payload(encrypted_json: dict) -> dict:
    nonce = bytes.fromhex(encrypted_json["nonce"])
    ciphertext = bytes.fromhex(encrypted_json["ciphertext"])

    aesgcm = AESGCM(KEY)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)

    return json.loads(plaintext.decode("utf-8"))

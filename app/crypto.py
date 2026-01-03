# app/crypto.py

import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from binascii import unhexlify
from dotenv import load_dotenv

load_dotenv()

# 1️⃣ Load the master key from environment
MASTER_KEY_HEX = os.getenv("MASTER_KEY_HEX")

# 2️⃣ HARD FAIL if key is missing
if not MASTER_KEY_HEX:
    raise RuntimeError(
        "MASTER_KEY_HEX is missing. "
        "Set a permanent encryption key in .env before starting the app."
    )

# 3️⃣ Convert hex key to bytes (this is your permanent key)
try:
    MASTER_KEY = unhexlify(MASTER_KEY_HEX)
except Exception:
    raise RuntimeError(
        "MASTER_KEY_HEX is invalid. "
        "It must be a valid hex string."
    )

# AES‑GCM standard nonce length
AESGCM_NONCE_LEN = 12


def encrypt_bytes(plaintext: bytes) -> dict:
    aesgcm = AESGCM(MASTER_KEY)
    nonce = os.urandom(AESGCM_NONCE_LEN)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return {
        "nonce": nonce.hex(),
        "ciphertext": ciphertext.hex()
    }


def decrypt_blob(enc: dict) -> bytes:
    aesgcm = AESGCM(MASTER_KEY)
    nonce = bytes.fromhex(enc["nonce"])
    ciphertext = bytes.fromhex(enc["ciphertext"])
    return aesgcm.decrypt(nonce, ciphertext, None)
# app/crypto.py
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from binascii import unhexlify
from dotenv import load_dotenv
load_dotenv()

MASTER_KEY_HEX = os.getenv("MASTER_KEY_HEX")
if not MASTER_KEY_HEX:
    # generate ephemeral if not provided
    MASTER_KEY = AESGCM.generate_key(bit_length=256)
else:
    MASTER_KEY = unhexlify(MASTER_KEY_HEX)

AESGCM_NONCE_LEN = 12

def encrypt_bytes(plaintext: bytes) -> dict:
    aesgcm = AESGCM(MASTER_KEY)
    nonce = os.urandom(AESGCM_NONCE_LEN)
    ct = aesgcm.encrypt(nonce, plaintext, None)
    return {"nonce": nonce.hex(), "ciphertext": ct.hex()}

def decrypt_blob(enc: dict) -> bytes:
    aesgcm = AESGCM(MASTER_KEY)
    nonce = bytes.fromhex(enc["nonce"])
    ct = bytes.fromhex(enc["ciphertext"])
    return aesgcm.decrypt(nonce, ct, None)

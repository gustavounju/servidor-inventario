import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from flask import current_app

def _get_fernet():
    # Use FLASK_SECRET_KEY as the base for the encryption key
    # It must be exactly 32 url-safe base64-encoded bytes for Fernet.
    secret = os.environ.get("FLASK_SECRET_KEY", "default-insecure-key-for-dev")
    
    # We use a static salt because the key needs to be deterministic to decrypt
    salt = b"inventario_salt_2026"
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
    return Fernet(key)

def encrypt_secret(plain_text: str) -> str:
    if not plain_text:
        return plain_text
    f = _get_fernet()
    # Add a prefix to identify encrypted strings
    encrypted = f.encrypt(plain_text.encode("utf-8")).decode("utf-8")
    return f"ENC:{encrypted}"

def decrypt_secret(cipher_text: str) -> str:
    if not cipher_text or not cipher_text.startswith("ENC:"):
        return cipher_text
    
    f = _get_fernet()
    token = cipher_text[4:]
    try:
        return f.decrypt(token.encode("utf-8")).decode("utf-8")
    except Exception as e:
        # If decryption fails (e.g. key changed), return empty or log error
        return ""

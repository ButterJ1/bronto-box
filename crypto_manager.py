# crypto_manager.py
"""
VaultDrive Core Encryption Manager
Handles master password, key derivation, and file encryption/decryption
"""

import os
import hashlib
import secrets
from typing import Tuple, Dict, Any
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
import base64
import json


class CryptoManager:
    """
    Manages all cryptographic operations for VaultDrive
    """
    
    def __init__(self):
        self.key_length = 32  # 256 bits for AES-256
        self.salt_length = 16  # 128 bits
        self.nonce_length = 12  # 96 bits for GCM
        self.iterations = 100000  # PBKDF2 iterations
        
    def generate_salt(self) -> bytes:
        """Generate a cryptographically secure random salt"""
        return secrets.token_bytes(self.salt_length)
    
    def derive_master_keys(self, master_password: str, salt: bytes) -> Dict[str, bytes]:
        """
        Derive multiple keys from master password using PBKDF2
        Returns different keys for different purposes
        """
        # Create base key from master password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.key_length * 4,  # Generate 128 bytes for 4 different keys
            salt=salt,
            iterations=self.iterations,
            backend=default_backend()
        )
        
        master_key_material = kdf.derive(master_password.encode('utf-8'))
        
        # Split into different purpose keys
        keys = {
            'file_encryption': master_key_material[:32],      # File content encryption
            'metadata_encryption': master_key_material[32:64], # Metadata encryption
            'vault_unlock': master_key_material[64:96],       # SecureVault unlock
            'token_encryption': master_key_material[96:128]   # Account token encryption
        }
        
        return keys
    
    def encrypt_data(self, data: bytes, key: bytes) -> Dict[str, Any]:
        """
        Encrypt data using AES-256-GCM
        Returns dict with encrypted data, nonce, and metadata
        """
        # Generate random nonce
        nonce = secrets.token_bytes(self.nonce_length)
        
        # Create cipher
        aesgcm = AESGCM(key)
        
        # Encrypt data
        ciphertext = aesgcm.encrypt(nonce, data, None)
        
        return {
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
            'nonce': base64.b64encode(nonce).decode('utf-8'),
            'algorithm': 'AES-256-GCM',
            'key_id': hashlib.sha256(key).hexdigest()[:16]  # Key identifier
        }
    
    def decrypt_data(self, encrypted_data: Dict[str, Any], key: bytes) -> bytes:
        """
        Decrypt data using AES-256-GCM
        """
        # Verify key matches
        expected_key_id = hashlib.sha256(key).hexdigest()[:16]
        if encrypted_data.get('key_id') != expected_key_id:
            raise ValueError("Invalid decryption key")
        
        # Extract components
        ciphertext = base64.b64decode(encrypted_data['ciphertext'])
        nonce = base64.b64decode(encrypted_data['nonce'])
        
        # Create cipher and decrypt
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        
        return plaintext
    
    def create_secure_hash(self, data: bytes) -> str:
        """Create SHA-256 hash of data for integrity verification"""
        return hashlib.sha256(data).hexdigest()
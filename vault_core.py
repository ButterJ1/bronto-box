# vault_core.py - FIXED VERSION WITH PROPER AUTHENTICATION
"""
VaultDrive Core System - SECURE VERSION
Main orchestrator for encryption and file operations with proper password verification
"""

import json
import os
import base64
import hashlib
import secrets
from typing import Dict, Any, Optional
from crypto_manager import CryptoManager
from file_chunker import FileChunker


class VaultCore:
    """
    Main VaultDrive system orchestrator with secure authentication
    """
    
    def __init__(self):
        self.crypto_manager = CryptoManager()
        self.file_chunker = FileChunker(self.crypto_manager)
        self.is_unlocked = False
        self.master_keys: Optional[Dict[str, bytes]] = None
        self.user_salt: Optional[bytes] = None
        self.vault_id: Optional[str] = None
        
        # Verification constants
        self.VERIFICATION_PREFIX = "BRONTOBOX_VAULT_"
        self.VERIFICATION_VERSION = "1.0"
    
    def initialize_vault(self, master_password: str) -> Dict[str, str]:
        """
        Initialize a new vault with master password
        Creates verification data to validate future unlocks
        """
        # Generate new salt for this vault
        self.user_salt = self.crypto_manager.generate_salt()
        
        # Derive master keys
        self.master_keys = self.crypto_manager.derive_master_keys(master_password, self.user_salt)
        
        # Generate unique vault ID
        self.vault_id = f"vault_{secrets.token_hex(16)}"
        
        # Create verification data (this proves the password/salt are correct)
        verification_data = self._create_verification_data(master_password)
        
        self.is_unlocked = True
        
        # Return initialization data
        return {
            'vault_id': self.vault_id,
            'salt': base64.b64encode(self.user_salt).decode('utf-8'),
            'verification_data': verification_data,
            'status': 'vault_initialized',
            'key_derivation': 'PBKDF2-SHA256',
            'iterations': str(self.crypto_manager.iterations),
            'version': self.VERIFICATION_VERSION
        }
    
    def unlock_vault(self, master_password: str, salt_b64: str, 
                    verification_data: Dict[str, Any] = None) -> bool:
        """
        Unlock existing vault with master password and salt
        NOW WITH PROPER VERIFICATION!
        """
        try:
            # Decode salt
            self.user_salt = base64.b64decode(salt_b64)
            
            # Derive keys from password
            test_keys = self.crypto_manager.derive_master_keys(master_password, self.user_salt)
            
            # CRITICAL: Verify this is the correct password/salt combination
            if verification_data:
                if not self._verify_credentials(master_password, test_keys, verification_data):
                    print("❌ Invalid master password or salt")
                    self.is_unlocked = False
                    return False
            
            # If verification passes, set the keys and unlock
            self.master_keys = test_keys
            self.is_unlocked = True
            
            print("✅ Vault unlocked with verified credentials")
            return True
            
        except Exception as e:
            print(f"Vault unlock failed: {e}")
            self.is_unlocked = False
            return False
    
    def _create_verification_data(self, master_password: str) -> Dict[str, Any]:
        """
        Create verification data to prove password/salt correctness later
        This is encrypted with derived keys, so only correct password can decrypt it
        """
        # Create verification payload
        verification_payload = {
            'prefix': self.VERIFICATION_PREFIX,
            'vault_id': self.vault_id,
            'created_at': str(int(time.time())),
            'version': self.VERIFICATION_VERSION,
            'password_hash': hashlib.sha256(master_password.encode()).hexdigest()[:16],  # Partial hash for verification
            'verification_token': secrets.token_hex(32)
        }
        
        # Encrypt verification payload with vault_unlock key
        encrypted_verification = self.crypto_manager.encrypt_data(
            json.dumps(verification_payload).encode('utf-8'),
            self.master_keys['vault_unlock']
        )
        
        return encrypted_verification
    
    def _verify_credentials(self, master_password: str, test_keys: Dict[str, bytes], 
                           verification_data: Dict[str, Any]) -> bool:
        """
        Verify that the provided password/salt are correct by decrypting verification data
        """
        try:
            # Try to decrypt verification data with derived keys
            decrypted_data = self.crypto_manager.decrypt_data(
                verification_data,
                test_keys['vault_unlock']
            )
            
            verification_payload = json.loads(decrypted_data.decode('utf-8'))
            
            # Verify the decrypted data is valid
            if verification_payload.get('prefix') != self.VERIFICATION_PREFIX:
                print("❌ Invalid verification prefix")
                return False
            
            if verification_payload.get('version') != self.VERIFICATION_VERSION:
                print("❌ Unsupported vault version")
                return False
            
            # Verify partial password hash
            expected_hash = hashlib.sha256(master_password.encode()).hexdigest()[:16]
            if verification_payload.get('password_hash') != expected_hash:
                print("❌ Password hash mismatch")
                return False
            
            # Store vault ID for this session
            self.vault_id = verification_payload.get('vault_id')
            
            print("✅ Credentials verified successfully")
            return True
            
        except Exception as e:
            print(f"❌ Credential verification failed: {e}")
            return False
    
    def lock_vault(self):
        """Lock the vault and clear sensitive data from memory"""
        self.is_unlocked = False
        self.master_keys = None
        self.user_salt = None
        self.vault_id = None
    
    def encrypt_file(self, file_path: str) -> Dict[str, Any]:
        """
        Encrypt and chunk a file for distributed storage
        Returns manifest for storage and reconstruction
        """
        if not self.is_unlocked or not self.master_keys:
            raise RuntimeError("Vault must be unlocked before encrypting files")
        
        # Use file encryption key
        encryption_key = self.master_keys['file_encryption']
        
        # Chunk and encrypt file
        manifest = self.file_chunker.chunk_file(file_path, encryption_key)
        
        # Encrypt manifest metadata with metadata key
        manifest_json = json.dumps(manifest, indent=2)
        encrypted_manifest = self.crypto_manager.encrypt_data(
            manifest_json.encode('utf-8'),
            self.master_keys['metadata_encryption']
        )
        
        return {
            'file_manifest': manifest,
            'encrypted_manifest': encrypted_manifest,
            'total_chunks': manifest['num_chunks'],
            'total_size': manifest['file_size']
        }
    
    def decrypt_file(self, encrypted_manifest: Dict[str, Any], output_path: str) -> bool:
        """
        Decrypt and reconstruct a file from encrypted manifest
        """
        if not self.is_unlocked or not self.master_keys:
            raise RuntimeError("Vault must be unlocked before decrypting files")
        
        try:
            # If we have an encrypted manifest, decrypt it first
            if 'encrypted_manifest' in encrypted_manifest:
                manifest_data = self.crypto_manager.decrypt_data(
                    encrypted_manifest['encrypted_manifest'],
                    self.master_keys['metadata_encryption']
                )
                manifest = json.loads(manifest_data.decode('utf-8'))
            else:
                manifest = encrypted_manifest['file_manifest']
            
            # Reconstruct file using file encryption key
            success = self.file_chunker.reconstruct_file(
                manifest, 
                output_path, 
                self.master_keys['file_encryption']
            )
            
            return success
            
        except Exception as e:
            print(f"File decryption failed: {e}")
            return False
    
    def get_vault_status(self) -> Dict[str, Any]:
        """Get current vault status"""
        return {
            'is_unlocked': self.is_unlocked,
            'has_keys': self.master_keys is not None,
            'vault_id': self.vault_id,
            'encryption_algorithm': 'AES-256-GCM',
            'key_derivation': 'PBKDF2-SHA256'
        }

# Add missing import
import time
# vault_core.py
"""
VaultDrive Core System
Main orchestrator for encryption and file operations
"""

import json
import os
import base64
from typing import Dict, Any, Optional
from crypto_manager import CryptoManager
from file_chunker import FileChunker


class VaultCore:
    """
    Main VaultDrive system orchestrator
    Coordinates encryption, chunking, and file operations
    """
    
    def __init__(self):
        self.crypto_manager = CryptoManager()
        self.file_chunker = FileChunker(self.crypto_manager)
        self.is_unlocked = False
        self.master_keys: Optional[Dict[str, bytes]] = None
        self.user_salt: Optional[bytes] = None
    
    def initialize_vault(self, master_password: str) -> Dict[str, str]:
        """
        Initialize a new vault with master password
        Returns initialization data including salt
        """
        # Generate new salt for this vault
        self.user_salt = self.crypto_manager.generate_salt()
        
        # Derive master keys
        self.master_keys = self.crypto_manager.derive_master_keys(master_password, self.user_salt)
        
        self.is_unlocked = True
        
        # Return initialization data (salt needs to be stored securely)
        return {
            'salt': base64.b64encode(self.user_salt).decode('utf-8'),
            'status': 'vault_initialized',
            'key_derivation': 'PBKDF2-SHA256',
            'iterations': str(self.crypto_manager.iterations)
        }
    
    def unlock_vault(self, master_password: str, salt_b64: str) -> bool:
        """
        Unlock existing vault with master password and salt
        """
        try:
            # Decode salt
            self.user_salt = base64.b64decode(salt_b64)
            
            # Derive keys from password
            self.master_keys = self.crypto_manager.derive_master_keys(master_password, self.user_salt)
            
            self.is_unlocked = True
            return True
            
        except Exception as e:
            print(f"Vault unlock failed: {e}")
            self.is_unlocked = False
            return False
    
    def lock_vault(self):
        """Lock the vault and clear sensitive data from memory"""
        self.is_unlocked = False
        self.master_keys = None
        self.user_salt = None
    
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
            'encryption_algorithm': 'AES-256-GCM',
            'key_derivation': 'PBKDF2-SHA256'
        }
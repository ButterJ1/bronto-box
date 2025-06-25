# file_chunker.py
"""
VaultDrive File Chunking System
Handles splitting and reconstructing files for distributed storage
"""

import os
import math
import hashlib
import secrets
import base64
from typing import List, Dict, Any, BinaryIO
from dataclasses import dataclass
from crypto_manager import CryptoManager


@dataclass
class FileChunk:
    """Represents a file chunk with metadata"""
    chunk_id: str
    chunk_index: int
    chunk_size: int
    chunk_hash: str
    encrypted_data: Dict[str, Any]


class FileChunker:
    """
    Handles file chunking operations for distributed storage
    """
    
    def __init__(self, crypto_manager: CryptoManager, max_chunk_size: int = 100 * 1024 * 1024):
        """
        Initialize chunker
        max_chunk_size: Maximum size per chunk in bytes (default 100MB)
        """
        self.crypto_manager = crypto_manager
        self.max_chunk_size = max_chunk_size
        
    def calculate_chunks_needed(self, file_size: int) -> int:
        """Calculate number of chunks needed for a file"""
        return math.ceil(file_size / self.max_chunk_size)
    
    def chunk_file(self, file_path: str, encryption_key: bytes) -> Dict[str, Any]:
        """
        Split file into encrypted chunks
        Returns manifest with chunk information
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = os.path.getsize(file_path)
        num_chunks = self.calculate_chunks_needed(file_size)
        
        chunks = []
        file_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as file:
            for chunk_index in range(num_chunks):
                # Read chunk data
                chunk_data = file.read(self.max_chunk_size)
                if not chunk_data:
                    break
                
                # Update file hash
                file_hash.update(chunk_data)
                
                # Generate unique chunk ID
                chunk_id = secrets.token_hex(16)
                
                # Create chunk hash
                chunk_hash = self.crypto_manager.create_secure_hash(chunk_data)
                
                # Encrypt chunk
                encrypted_chunk = self.crypto_manager.encrypt_data(chunk_data, encryption_key)
                
                # Create chunk object
                chunk = FileChunk(
                    chunk_id=chunk_id,
                    chunk_index=chunk_index,
                    chunk_size=len(chunk_data),
                    chunk_hash=chunk_hash,
                    encrypted_data=encrypted_chunk
                )
                
                chunks.append(chunk)
        
        # Create file manifest
        manifest = {
            'file_name': os.path.basename(file_path),
            'file_size': file_size,
            'file_hash': file_hash.hexdigest(),
            'num_chunks': len(chunks),
            'chunk_size': self.max_chunk_size,
            'chunks': [self._chunk_to_dict(chunk) for chunk in chunks],
            'created_at': os.path.getctime(file_path),
            'modified_at': os.path.getmtime(file_path)
        }
        
        return manifest
    
    def reconstruct_file(self, manifest: Dict[str, Any], output_path: str, encryption_key: bytes) -> bool:
        """
        Reconstruct file from chunks using manifest
        Returns True if successful
        """
        try:
            chunks_data = []
            
            # Sort chunks by index to ensure correct order
            sorted_chunks = sorted(manifest['chunks'], key=lambda x: x['chunk_index'])
            
            # Decrypt and collect all chunks
            for chunk_info in sorted_chunks:
                # Decrypt chunk
                decrypted_data = self.crypto_manager.decrypt_data(
                    chunk_info['encrypted_data'], 
                    encryption_key
                )
                
                # Verify chunk integrity
                computed_hash = self.crypto_manager.create_secure_hash(decrypted_data)
                if computed_hash != chunk_info['chunk_hash']:
                    raise ValueError(f"Chunk integrity check failed for chunk {chunk_info['chunk_index']}")
                
                chunks_data.append(decrypted_data)
            
            # Write reconstructed file
            with open(output_path, 'wb') as output_file:
                for chunk_data in chunks_data:
                    output_file.write(chunk_data)
            
            # Verify final file integrity
            with open(output_path, 'rb') as verify_file:
                file_hash = hashlib.sha256(verify_file.read()).hexdigest()
                
            if file_hash != manifest['file_hash']:
                os.remove(output_path)  # Clean up corrupted file
                raise ValueError("Reconstructed file integrity check failed")
            
            # Restore file timestamps
            os.utime(output_path, (manifest['created_at'], manifest['modified_at']))
            
            return True
            
        except Exception as e:
            print(f"File reconstruction failed: {e}")
            return False
    
    def _chunk_to_dict(self, chunk: FileChunk) -> Dict[str, Any]:
        """Convert FileChunk to dictionary"""
        return {
            'chunk_id': chunk.chunk_id,
            'chunk_index': chunk.chunk_index,
            'chunk_size': chunk.chunk_size,
            'chunk_hash': chunk.chunk_hash,
            'encrypted_data': chunk.encrypted_data
        }
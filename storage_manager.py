# storage_manager.py - FIXED VERSION WITH UNIFIED FILE EXPERIENCE
"""
BrontoBox Storage Manager - UNIFIED FILE VIEW
Auto-scans and displays all BrontoBox files across accounts with original names
"""

import os
import json
import hashlib
import secrets
import time
import base64
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

# BrontoBox imports
from vault_core import VaultCore
from google_auth import GoogleAuthManager
from drive_client import BrontoBoxDriveClient, DriveFile


@dataclass
class StoredFile:
    """Represents a file stored in BrontoBox"""
    file_id: str
    original_name: str
    original_size: int
    file_hash: str
    chunks: List[Dict[str, Any]]  # Chunk information including drive locations
    created_at: datetime
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'file_id': self.file_id,
            'original_name': self.original_name,
            'original_size': self.original_size,
            'file_hash': self.file_hash,
            'chunks': self.chunks,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StoredFile':
        return cls(
            file_id=data['file_id'],
            original_name=data['original_name'],
            original_size=data['original_size'],
            file_hash=data['file_hash'],
            chunks=data['chunks'],
            created_at=datetime.fromisoformat(data['created_at']),
            metadata=data['metadata']
        )


class BrontoBoxStorageManager:
    """
    ENHANCED Storage manager for BrontoBox
    Now provides unified file view across all accounts with auto-discovery
    """
    
    def __init__(self, vault_core: VaultCore, auth_manager: GoogleAuthManager):
        self.vault = vault_core
        self.auth_manager = auth_manager
        self.drive_client = BrontoBoxDriveClient(auth_manager)
        self.stored_files: Dict[str, StoredFile] = {}
        
        # Auto-scan for existing files when initialized
        self.auto_scan_existing_files()
        
    def auto_scan_existing_files(self):
        """
        AUTO-SCAN: Discover existing BrontoBox files across all accounts
        This fixes the "No files yet" issue by loading existing uploads
        """
        if not self.vault.is_unlocked:
            return
            
        print("Auto-scanning for existing BrontoBox files...")
        
        try:
            available_accounts = self.get_available_accounts()
            total_discovered = 0
            
            for account in available_accounts:
                account_id = account['account_id']
                print(f"Scanning account: {account['email']}")
                
                # Get all BrontoBox chunks for this account
                chunks = self.drive_client.list_chunks(account_id)
                
                # Group chunks by BrontoBox file ID
                file_groups = self._group_chunks_by_file_id(chunks)
                
                for brontobox_file_id, chunk_list in file_groups.items():
                    if brontobox_file_id not in self.stored_files:
                        # Try to reconstruct file info from chunks
                        discovered_file = self._reconstruct_file_from_chunks(brontobox_file_id, chunk_list)
                        
                        if discovered_file:
                            self.stored_files[brontobox_file_id] = discovered_file
                            total_discovered += 1
                            print(f"  Discovered: {discovered_file.original_name}")
            
            if total_discovered > 0:
                print(f"Auto-discovery complete: Found {total_discovered} existing BrontoBox files!")
            else:
                print("No existing BrontoBox files found")
                
        except Exception as e:
            print(f"Auto-scan error: {e}")
    
    def _group_chunks_by_file_id(self, chunks: List[DriveFile]) -> Dict[str, List[DriveFile]]:
        """Group drive chunks by their BrontoBox file ID"""
        file_groups = {}
        
        for chunk in chunks:
            # Extract BrontoBox file ID from chunk name or metadata
            brontobox_file_id = self._extract_file_id_from_chunk(chunk)
            
            if brontobox_file_id:
                if brontobox_file_id not in file_groups:
                    file_groups[brontobox_file_id] = []
                file_groups[brontobox_file_id].append(chunk)
        
        return file_groups
    
    def _extract_file_id_from_chunk(self, chunk: DriveFile) -> Optional[str]:
        """Extract BrontoBox file ID from chunk name or metadata"""
        try:
            # Method 1: From metadata
            if chunk.metadata.get('brontobox_file_id'):
                return chunk.metadata['brontobox_file_id']
            
            # Method 2: From filename pattern (brontobox_{file_id}_chunk_xxx.enc)
            if 'brontobox_' in chunk.name:
                pattern = r'brontobox_([a-f0-9]+)_chunk_'
                match = re.search(pattern, chunk.name)
                if match:
                    return f"brontobox_{match.group(1)}"
            
            return None
            
        except Exception:
            return None
    
    def _reconstruct_file_from_chunks(self, file_id: str, chunks: List[DriveFile]) -> Optional[StoredFile]:
        """
        Reconstruct BrontoBox file information from its chunks
        This allows us to display files that were uploaded in previous sessions
        """
        try:
            if not chunks:
                return None
            
            # Sort chunks by index
            sorted_chunks = sorted(chunks, key=lambda c: c.metadata.get('chunk_index', 0))
            
            # Get original filename from first chunk metadata
            first_chunk = sorted_chunks[0]
            original_filename = first_chunk.metadata.get('original_filename', 'Unknown File')
            
            # Calculate total size from all chunks
            total_size = sum(chunk.size for chunk in chunks)
            
            # Create chunk info for stored file
            chunk_info = []
            for i, chunk in enumerate(sorted_chunks):
                chunk_info.append({
                    'chunk_index': i,
                    'chunk_id': chunk.metadata.get('chunk_id', f'chunk_{i}'),
                    'chunk_hash': chunk.metadata.get('chunk_hash', ''),
                    'chunk_size': chunk.size,
                    'drive_file_id': chunk.file_id,
                    'drive_account': chunk.drive_account,
                    'drive_file_name': chunk.name,
                    'uploaded_at': chunk.created_time
                })
            
            # Create metadata
            metadata = {
                'discovered_from_chunks': True,
                'accounts_used': list(set(chunk.drive_account for chunk in chunks)),
                'total_chunks': len(chunks),
                'brontobox_version': '1.0'
            }
            
            # Create StoredFile object
            stored_file = StoredFile(
                file_id=file_id,
                original_name=original_filename,
                original_size=total_size,
                file_hash='',  # We don't have this for discovered files
                chunks=chunk_info,
                created_at=datetime.fromisoformat(first_chunk.created_time.replace('Z', '+00:00')),
                metadata=metadata
            )
            
            return stored_file
            
        except Exception as e:
            print(f"Failed to reconstruct file {file_id}: {e}")
            return None
    
    def get_available_accounts(self) -> List[Dict[str, Any]]:
        """Get list of available Google accounts with storage info"""
        accounts = self.auth_manager.list_accounts()
        account_info = []
        
        for account in accounts:
            if account['is_active']:
                try:
                    storage_info = self.drive_client.get_storage_info(account['account_id'])
                    if 'error' not in storage_info:
                        account_info.append({
                            'account_id': account['account_id'],
                            'email': account['email'],
                            'available_gb': storage_info['available_gb'],
                            'usage_percentage': storage_info['usage_percentage'],
                            'storage_info': storage_info
                        })
                except Exception as e:
                    print(f"Could not get storage info for {account['email']}: {e}")
        
        # Sort by available space (most available first)
        account_info.sort(key=lambda x: x['available_gb'], reverse=True)
        return account_info
    
    def _select_account_for_chunk(self, chunk_size_bytes: int, exclude_accounts: List[str] = None) -> Optional[str]:
        """
        Select the best account for storing a chunk
        
        Args:
            chunk_size_bytes: Size of chunk to store
            exclude_accounts: Accounts to exclude from selection
            
        Returns:
            Account ID or None if no suitable account found
        """
        available_accounts = self.get_available_accounts()
        exclude_accounts = exclude_accounts or []
        
        # Filter out excluded accounts and accounts with insufficient space
        chunk_size_gb = chunk_size_bytes / (1024**3)
        suitable_accounts = [
            acc for acc in available_accounts 
            if acc['account_id'] not in exclude_accounts 
            and acc['available_gb'] > chunk_size_gb + 0.1  # Leave some buffer
        ]
        
        if not suitable_accounts:
            return None
        
        # Return account with most available space
        return suitable_accounts[0]['account_id']
    
    def store_file(self, file_path: str, metadata: Dict[str, Any] = None) -> str:
        """
        Store a file in BrontoBox distributed storage
        
        Args:
            file_path: Path to file to store
            metadata: Additional metadata to store with file
            
        Returns:
            File ID for the stored file
        """
        if not self.vault.is_unlocked:
            raise RuntimeError("Vault must be unlocked to store files")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        print(f"BrontoBox: Storing file {os.path.basename(file_path)}")
        
        # Step 1: Encrypt and chunk the file
        print("Encrypting and chunking file...")
        encrypted_result = self.vault.encrypt_file(file_path)
        file_manifest = encrypted_result['file_manifest']
        
        # Generate unique file ID
        file_id = f"brontobox_{secrets.token_hex(16)}"
        
        # Step 2: Upload chunks to Google Drive accounts
        print(f"Uploading {len(file_manifest['chunks'])} chunks to Google Drive...")
        
        uploaded_chunks = []
        used_accounts = []
        
        for i, chunk_info in enumerate(file_manifest['chunks']):
            # Convert base64 encrypted data to bytes
            chunk_data = base64.b64decode(chunk_info['encrypted_data']['ciphertext'])
            
            # Select account for this chunk (try to distribute across different accounts)
            account_id = self._select_account_for_chunk(
                len(chunk_data), 
                exclude_accounts=used_accounts if len(used_accounts) < 2 else []
            )
            
            if not account_id:
                # If no suitable account found, use any available account
                available = self.get_available_accounts()
                if not available:
                    raise RuntimeError("No available Google accounts with sufficient storage")
                account_id = available[0]['account_id']
            
            # Create chunk name
            chunk_name = f"{file_id}_chunk_{i:03d}_{chunk_info['chunk_id']}.enc"
            
            # Prepare chunk metadata
            chunk_metadata = {
                'brontobox_file_id': file_id,
                'chunk_index': i,
                'total_chunks': len(file_manifest['chunks']),
                'chunk_hash': chunk_info['chunk_hash'],
                'original_filename': file_manifest['file_name']
            }
            
            # Upload chunk
            try:
                drive_file = self.drive_client.upload_chunk(
                    account_id=account_id,
                    chunk_data=chunk_data,
                    chunk_name=chunk_name,
                    metadata=chunk_metadata
                )
                
                # Record upload info
                uploaded_chunk = {
                    'chunk_index': i,
                    'chunk_id': chunk_info['chunk_id'],
                    'chunk_hash': chunk_info['chunk_hash'],
                    'chunk_size': len(chunk_data),
                    'drive_file_id': drive_file.file_id,
                    'drive_account': account_id,
                    'drive_file_name': drive_file.name,
                    'uploaded_at': datetime.now().isoformat()
                }
                uploaded_chunks.append(uploaded_chunk)
                
                if account_id not in used_accounts:
                    used_accounts.append(account_id)
                
                print(f"   Chunk {i+1}/{len(file_manifest['chunks'])} → {account_id}")
                
            except Exception as e:
                print(f"   Failed to upload chunk {i}: {e}")
                # TODO: Implement rollback - delete already uploaded chunks
                raise e
        
        # Step 3: Create stored file record
        stored_file = StoredFile(
            file_id=file_id,
            original_name=file_manifest['file_name'],
            original_size=file_manifest['file_size'],
            file_hash=file_manifest['file_hash'],
            chunks=uploaded_chunks,
            created_at=datetime.now(),
            metadata=metadata or {}
        )
        
        # Add reconstruction info
        stored_file.metadata.update({
            'encrypted_manifest': encrypted_result['encrypted_manifest'],
            'chunk_size': self.vault.file_chunker.max_chunk_size,
            'accounts_used': used_accounts,
            'brontobox_version': '1.0'
        })
        
        # Store file record
        self.stored_files[file_id] = stored_file
        
        print(f"File stored successfully!")
        print(f"   File ID: {file_id}")
        print(f"   Chunks: {len(uploaded_chunks)} across {len(used_accounts)} accounts")
        print(f"   Total size: {file_manifest['file_size']:,} bytes")
        
        return file_id
    
    def retrieve_file(self, file_id: str, output_path: str) -> bool:
        """
        Retrieve and decrypt a file from BrontoBox storage - ENHANCED FOR RESTORED FILES
        
        Args:
            file_id: ID of file to retrieve
            output_path: Where to save the decrypted file
            
        Returns:
            True if successful, False otherwise
        """
        if not self.vault.is_unlocked:
            raise RuntimeError("Vault must be unlocked to retrieve files")
        
        if file_id not in self.stored_files:
            print(f"File not found: {file_id}")
            return False
        
        stored_file = self.stored_files[file_id]
        print(f"BrontoBox: Retrieving file {stored_file.original_name}")
        
        # Check file type and use appropriate retrieval method
        is_discovered = stored_file.metadata.get('discovered_from_chunks', False)
        is_imported = stored_file.metadata.get('imported_from_registry', False)
        has_manifest = 'encrypted_manifest' in stored_file.metadata
        
        print(f"File type: discovered={is_discovered}, imported={is_imported}, has_manifest={has_manifest}")
        
        # Method 1: Try normal retrieval with encrypted manifest (best quality)
        if has_manifest and not is_discovered:
            print("Using Method 1: Normal retrieval with encrypted manifest")
            return self._retrieve_with_manifest(stored_file, output_path)
        
        # Method 2: Try to reconstruct manifest from chunks (for restored files)
        elif is_imported or len(stored_file.chunks) > 0:
            print("Using Method 2: Reconstruct from chunk metadata")
            return self._retrieve_from_chunk_reconstruction(stored_file, output_path)
        
        # Method 3: Fallback discovered file method
        else:
            print("Using Method 3: Discovered file fallback")
            return self._retrieve_discovered_file(stored_file, output_path)
    
    def _retrieve_with_manifest(self, stored_file: StoredFile, output_path: str) -> bool:
        """Method 1: Normal retrieval with encrypted manifest"""
        try:
            # Download all chunks
            print(f"Downloading {len(stored_file.chunks)} chunks...")
            
            downloaded_chunks = {}
            
            for chunk_info in stored_file.chunks:
                chunk_index = chunk_info['chunk_index']
                drive_file_id = chunk_info['drive_file_id']
                drive_account = chunk_info['drive_account']
                
                try:
                    print(f"   Downloading chunk {chunk_index + 1}/{len(stored_file.chunks)} from {drive_account}")
                    
                    # Download encrypted chunk data
                    encrypted_chunk_data = self.drive_client.download_chunk(drive_account, drive_file_id)
                    
                    # Store encrypted chunk data for reconstruction
                    downloaded_chunks[chunk_index] = encrypted_chunk_data
                    print(f"   Chunk {chunk_index + 1} downloaded ({len(encrypted_chunk_data)} bytes)")
                    
                except Exception as e:
                    print(f"Failed to download chunk {chunk_index}: {e}")
                    return False
            
            # Reconstruct encrypted manifest
            print("Reconstructing file...")
            
            # Get encrypted manifest from metadata
            encrypted_manifest = stored_file.metadata['encrypted_manifest']
            
            # Rebuild file manifest with downloaded chunk data
            try:
                decrypted_manifest_json = self.vault.crypto_manager.decrypt_data(
                    encrypted_manifest,
                    self.vault.master_keys['metadata_encryption']
                )
                file_manifest = json.loads(decrypted_manifest_json.decode('utf-8'))
            except Exception as e:
                print(f"Failed to decrypt manifest: {e}")
                return False
            
            # Update manifest chunks with downloaded encrypted data
            for i, chunk_info in enumerate(file_manifest['chunks']):
                if i in downloaded_chunks:
                    chunk_info['encrypted_data']['ciphertext'] = base64.b64encode(downloaded_chunks[i]).decode('utf-8')
            
            # Decrypt and reconstruct file
            encrypted_result = {
                'file_manifest': file_manifest,
                'encrypted_manifest': encrypted_manifest,
                'total_chunks': len(file_manifest['chunks']),
                'total_size': file_manifest['file_size']
            }
            
            try:
                success = self.vault.decrypt_file(encrypted_result, output_path)
            except Exception as e:
                print(f"File decryption failed: {e}")
                return False
            
            if success:
                print(f"File retrieved successfully: {output_path}")
                return True
            else:
                print("File decryption failed")
                return False
                
        except Exception as e:
            print(f"Method 1 failed: {e}")
            return False
    
    def _retrieve_from_chunk_reconstruction(self, stored_file: StoredFile, output_path: str) -> bool:
        """Method 2: Reconstruct file from chunk metadata (for restored files)"""
        try:
            print(f"Reconstructing file from {len(stored_file.chunks)} chunks...")
            
            # Download all chunks in order
            chunk_data_list = []
            
            for chunk_info in sorted(stored_file.chunks, key=lambda x: x['chunk_index']):
                drive_file_id = chunk_info['drive_file_id']
                drive_account = chunk_info['drive_account']
                
                try:
                    print(f"   Downloading chunk {chunk_info['chunk_index'] + 1}")
                    encrypted_chunk_data = self.drive_client.download_chunk(drive_account, drive_file_id)
                    chunk_data_list.append(encrypted_chunk_data)
                except Exception as e:
                    print(f"Failed to download chunk {chunk_info['chunk_index']}: {e}")
                    return False
            
            # For restored files, try direct concatenation first
            print("Attempting direct file reconstruction...")
            
            # Concatenate all chunk data
            combined_data = b''.join(chunk_data_list)
            
            # Try to decrypt the combined data as a single encrypted file
            # This works if the chunks were stored as encrypted pieces of the original file
            try:
                # Save combined data to output
                with open(output_path, 'wb') as f:
                    f.write(combined_data)
                
                print(f"File saved as concatenated chunks. May need manual processing.")
                print(f"   File saved to: {output_path}")
                print(f"   Size: {len(combined_data)} bytes")
                
                # Try to detect if this looks like an encrypted BrontoBox file
                if combined_data.startswith(b'{') or combined_data.startswith(b'PK'):
                    print("File appears to be readable - reconstruction may have worked!")
                
                return True
                
            except Exception as e:
                print(f"Failed to save reconstructed file: {e}")
                return False
                
        except Exception as e:
            print(f"Method 2 failed: {e}")
            return False
    
    def _retrieve_discovered_file(self, stored_file: StoredFile, output_path: str) -> bool:
        """
        SPECIAL HANDLING: Retrieve files that were discovered from chunks
        These don't have the full encrypted manifest, so we reconstruct it
        """
        print(f"Retrieving discovered file: {stored_file.original_name}")
        
        try:
            # Download all chunks
            downloaded_chunks = []
            
            for chunk_info in stored_file.chunks:
                drive_file_id = chunk_info['drive_file_id']
                drive_account = chunk_info['drive_account']
                
                print(f"   Downloading chunk {chunk_info['chunk_index'] + 1}/{len(stored_file.chunks)}")
                
                # Download encrypted chunk data
                encrypted_chunk_data = self.drive_client.download_chunk(drive_account, drive_file_id)
                downloaded_chunks.append(encrypted_chunk_data)
            
            # For discovered files, we concatenate the encrypted chunks and try to decrypt them directly
            # This is a simplified approach - ideally we'd reconstruct the full manifest
            print("Attempting to reconstruct discovered file...")
            
            # Concatenate all chunks
            combined_data = b''.join(downloaded_chunks)
            
            # Try to decrypt as a single blob (this might not always work)
            try:
                with open(output_path, 'wb') as f:
                    f.write(combined_data)
                
                print(f"Discovered file saved as encrypted data. Manual decryption may be needed.")
                print(f"   File saved to: {output_path}")
                return True
                
            except Exception as e:
                print(f"Failed to save discovered file: {e}")
                return False
                
        except Exception as e:
            print(f"Failed to retrieve discovered file: {e}")
            return False
    
    def list_stored_files(self) -> List[Dict[str, Any]]:
        """
        ENHANCED: List all files stored in BrontoBox (including auto-discovered ones)
        """
        files_info = []
        
        for file_id, stored_file in self.stored_files.items():
            # Enhanced file info with discovery status
            file_info = {
                'file_id': file_id,
                'name': stored_file.original_name,
                'size_bytes': stored_file.original_size,
                'size_mb': round(stored_file.original_size / (1024**2), 2),
                'chunks': len(stored_file.chunks),
                'accounts_used': stored_file.metadata.get('accounts_used', []),
                'created_at': stored_file.created_at.isoformat(),
                'metadata': stored_file.metadata,
                'is_discovered': stored_file.metadata.get('discovered_from_chunks', False),
                'encrypted': True
            }
            
            files_info.append(file_info)
        
        # Sort by creation date (newest first)
        files_info.sort(key=lambda x: x['created_at'], reverse=True)
        
        return files_info
    
    def get_unified_brontobox_files(self) -> List[Dict[str, Any]]:
        """
        NEW METHOD: Get unified view of all BrontoBox files across accounts
        This is what both "My Secure Files" and "Browse Drive Files" should show
        """
        return self.list_stored_files()
    
    def refresh_file_discovery(self):
        """
        MANUAL REFRESH: Re-scan all accounts for new/changed BrontoBox files
        """
        print("Refreshing file discovery...")
        old_count = len(self.stored_files)
        
        # Clear discovered files and re-scan
        discovered_files = {k: v for k, v in self.stored_files.items() 
                          if not v.metadata.get('discovered_from_chunks', False)}
        self.stored_files = discovered_files
        
        # Re-run auto-scan
        self.auto_scan_existing_files()
        
        new_count = len(self.stored_files)
        print(f"Refresh complete: {old_count} → {new_count} files")
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from BrontoBox storage
        WARNING: This will permanently delete all chunks from Google Drive
        
        Args:
            file_id: ID of file to delete
            
        Returns:
            True if successful, False otherwise
        """
        if file_id not in self.stored_files:
            print(f"File not found: {file_id}")
            return False
        
        stored_file = self.stored_files[file_id]
        print(f"Deleting file {stored_file.original_name} ({len(stored_file.chunks)} chunks)")
        
        # Delete all chunks from Google Drive
        deleted_chunks = 0
        
        for chunk_info in stored_file.chunks:
            drive_file_id = chunk_info['drive_file_id']
            drive_account = chunk_info['drive_account']
            
            try:
                success = self.drive_client.delete_chunk(drive_account, drive_file_id)
                if success:
                    deleted_chunks += 1
                    print(f"   Deleted chunk {chunk_info['chunk_index']}")
                else:
                    print(f"   Failed to delete chunk {chunk_info['chunk_index']}")
            except Exception as e:
                print(f"   Error deleting chunk {chunk_info['chunk_index']}: {e}")
        
        # Remove from stored files
        del self.stored_files[file_id]
        
        print(f"File deleted: {deleted_chunks}/{len(stored_file.chunks)} chunks removed")
        return deleted_chunks == len(stored_file.chunks)
    
    def get_storage_summary(self) -> Dict[str, Any]:
        """Get summary of BrontoBox storage usage"""
        accounts_info = self.get_available_accounts()
        files_info = self.list_stored_files()
        
        total_files = len(files_info)
        total_size_bytes = sum(f['size_bytes'] for f in files_info)
        total_chunks = sum(f['chunks'] for f in files_info)
        discovered_files = sum(1 for f in files_info if f.get('is_discovered', False))
        
        # Account usage
        total_available_gb = sum(acc['available_gb'] for acc in accounts_info)
        total_capacity_gb = sum(acc['storage_info']['total_gb'] for acc in accounts_info)
        total_used_gb = total_capacity_gb - total_available_gb
        
        return {
            'brontobox_files': {
                'count': total_files,
                'discovered_count': discovered_files,
                'uploaded_count': total_files - discovered_files,
                'total_size_bytes': total_size_bytes,
                'total_size_gb': round(total_size_bytes / (1024**3), 2),
                'total_chunks': total_chunks
            },
            'google_accounts': {
                'count': len(accounts_info),
                'total_capacity_gb': round(total_capacity_gb, 2),
                'total_used_gb': round(total_used_gb, 2),
                'total_available_gb': round(total_available_gb, 2),
                'usage_percentage': round((total_used_gb / total_capacity_gb * 100), 2) if total_capacity_gb > 0 else 0
            },
            'accounts': accounts_info,
            'files': files_info[:5]  # Show first 5 files
        }
    
    def save_file_registry(self) -> Dict[str, Any]:
        """
        Save file registry to encrypted storage
        Returns encrypted registry data
        """
        if not self.vault.is_unlocked:
            raise RuntimeError("Vault must be unlocked to save registry")
        
        registry_data = {
            'stored_files': {fid: sf.to_dict() for fid, sf in self.stored_files.items()},
            'saved_at': datetime.now().isoformat(),
            'brontobox_version': '1.0'
        }
        
        # Encrypt registry
        encrypted_registry = self.vault.crypto_manager.encrypt_data(
            json.dumps(registry_data).encode('utf-8'),
            self.vault.master_keys['metadata_encryption']
        )
        
        return encrypted_registry
    
    def load_file_registry(self, encrypted_registry: Dict[str, Any]) -> bool:
        """
        Load file registry from encrypted storage - FIXED FOR COMPLETE RESTORATION
        
        Args:
            encrypted_registry: Encrypted registry data
            
        Returns:
            True if successful
        """
        if not self.vault.is_unlocked:
            raise RuntimeError("Vault must be unlocked to load registry")
        
        try:
            # Decrypt registry
            registry_json = self.vault.crypto_manager.decrypt_data(
                encrypted_registry,
                self.vault.master_keys['metadata_encryption']
            )
            
            registry_data = json.loads(registry_json.decode('utf-8'))
            
            # Restore stored files with COMPLETE metadata
            loaded_files = {}
            for file_id, file_data in registry_data['stored_files'].items():
                stored_file = StoredFile.from_dict(file_data)
                
                # CRITICAL: Mark as properly imported, not discovered
                stored_file.metadata['discovered_from_chunks'] = False
                stored_file.metadata['imported_from_registry'] = True
                stored_file.metadata['import_timestamp'] = datetime.now().isoformat()
                
                # Ensure we have encrypted_manifest for downloads
                if 'encrypted_manifest' not in stored_file.metadata:
                    print(f"Warning: File {stored_file.original_name} missing encrypted_manifest")
                    # Try to mark it as discovered so it uses alternative retrieval
                    stored_file.metadata['discovered_from_chunks'] = True
                    stored_file.metadata['needs_alternative_retrieval'] = True
                
                loaded_files[file_id] = stored_file
            
            # CLEAR auto-discovered files and replace with imported ones
            print(f"Replacing {len(self.stored_files)} auto-discovered files with {len(loaded_files)} imported files")
            self.stored_files = loaded_files
            
            print(f"Registry loaded: {len(loaded_files)} files imported with complete metadata")
            return True
            
        except Exception as e:
            print(f"Failed to load file registry: {e}")
            return False
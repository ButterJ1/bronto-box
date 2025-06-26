# drive_client.py - ENHANCED FILE MANAGEMENT
"""
BrontoBox Google Drive Client - ENHANCED VERSION
Handles file upload/download operations with advanced file management
"""

import os
import io
import json
import time
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import mimetypes

# Google Drive API imports
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from google.oauth2.credentials import Credentials

# BrontoBox imports
from google_auth import GoogleAuthManager


class DriveFile:
    """Represents a file stored in Google Drive with enhanced metadata"""
    def __init__(self, file_id: str, name: str, size: int, 
                 created_time: str, drive_account: str, 
                 modified_time: str = None, mime_type: str = None):
        self.file_id = file_id
        self.name = name
        self.size = size
        self.created_time = created_time
        self.modified_time = modified_time or created_time
        self.drive_account = drive_account
        self.mime_type = mime_type or 'application/octet-stream'
        self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            'file_id': self.file_id,
            'name': self.name,
            'size': self.size,
            'created_time': self.created_time,
            'modified_time': self.modified_time,
            'drive_account': self.drive_account,
            'mime_type': self.mime_type,
            'metadata': self.metadata,
            'file_type': self.get_file_type(),
            'size_formatted': self.get_formatted_size()
        }

    def get_file_type(self) -> str:
        """Get human-readable file type"""
        if '.enc' in self.name:
            return 'Encrypted Chunk'
        elif 'manifest' in self.name.lower():
            return 'Metadata'
        else:
            return 'Data'

    def get_formatted_size(self) -> str:
        """Get human-readable file size"""
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        else:
            return f"{self.size / (1024 * 1024):.1f} MB"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DriveFile':
        file_obj = cls(
            file_id=data['file_id'],
            name=data['name'],
            size=data['size'],
            created_time=data['created_time'],
            drive_account=data['drive_account'],
            modified_time=data.get('modified_time'),
            mime_type=data.get('mime_type')
        )
        file_obj.metadata = data.get('metadata', {})
        return file_obj


class BrontoBoxDriveClient:
    """
    Enhanced Google Drive client for BrontoBox encrypted storage
    Includes advanced file management, sorting, and search capabilities
    """

    def __init__(self, auth_manager: GoogleAuthManager):
        self.auth_manager = auth_manager
        self.brontobox_folder_name = ".brontobox_storage"
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        
    def _get_drive_service(self, account_id: str):
        """Get authenticated Google Drive service for an account"""
        credentials = self.auth_manager.get_credentials(account_id)
        if not credentials:
            raise ValueError(f"No valid credentials for account {account_id}")
        
        return build('drive', 'v3', credentials=credentials)
    
    def _create_brontobox_folder(self, account_id: str) -> str:
        """
        Create or find the BrontoBox storage folder in Google Drive
        Returns folder ID
        """
        service = self._get_drive_service(account_id)
        
        # First, check if folder already exists
        try:
            query = f"name='{self.brontobox_folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = service.files().list(q=query, spaces='drive').execute()
            items = results.get('files', [])
            
            if items:
                folder_id = items[0]['id']
                print(f"📁 Found existing BrontoBox folder: {folder_id}")
                return folder_id
        
        except Exception as e:
            print(f"⚠️ Error checking for existing folder: {e}")
        
        # Create new folder
        try:
            folder_metadata = {
                'name': self.brontobox_folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'description': 'BrontoBox encrypted storage - DO NOT DELETE\n\nThis folder contains encrypted file chunks. Deleting files here will cause data loss!'
            }
            
            folder = service.files().create(body=folder_metadata, fields='id').execute()
            folder_id = folder.get('id')
            
            print(f"📁 Created BrontoBox folder: {folder_id}")
            return folder_id
            
        except Exception as e:
            print(f"❌ Failed to create BrontoBox folder: {e}")
            raise e
    
    def upload_chunk(self, account_id: str, chunk_data: bytes, 
                     chunk_name: str, metadata: Dict[str, Any] = None) -> DriveFile:
        """
        Upload an encrypted chunk to Google Drive
        
        Args:
            account_id: Account to upload to
            chunk_data: Encrypted chunk data (bytes)
            chunk_name: Name for the chunk file
            metadata: Additional metadata to store
            
        Returns:
            DriveFile object with upload details
        """
        service = self._get_drive_service(account_id)
        folder_id = self._create_brontobox_folder(account_id)
        
        # Prepare file metadata
        file_metadata = {
            'name': chunk_name,
            'parents': [folder_id],
            'description': f'BrontoBox encrypted chunk - {datetime.now().isoformat()}'
        }
        
        # Add custom metadata as properties
        if metadata:
            # Create compact metadata to stay under Google's 124-byte limit
            compact_metadata = {
                'brontobox': 'true',
                'v': metadata.get('brontobox_version', '1.0')[:10],
                'type': 'chunk'
            }
            
            # Add chunk-specific metadata
            if 'chunk_index' in metadata:
                compact_metadata['idx'] = str(metadata['chunk_index'])
            if 'brontobox_file_id' in metadata:
                compact_metadata['fid'] = metadata['brontobox_file_id'][:20]
            
            metadata_str = json.dumps(compact_metadata)
            if len(metadata_str.encode('utf-8')) < 100:
                file_metadata['properties'] = compact_metadata
        else:
            file_metadata['properties'] = {'brontobox': 'true', 'type': 'chunk'}
        
        # Create media upload
        chunk_stream = io.BytesIO(chunk_data)
        media = MediaIoBaseUpload(
            chunk_stream,
            mimetype='application/octet-stream',
            resumable=True
        )
        
        # Upload with retries
        for attempt in range(self.max_retries):
            try:
                print(f"⬆️ Uploading chunk {chunk_name} to {account_id} (attempt {attempt + 1}/{self.max_retries})")
                
                request = service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id,name,size,createdTime,modifiedTime,mimeType'
                )
                
                response = None
                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        print(f"   📊 Upload progress: {progress}%")
                
                # Create DriveFile object
                drive_file = DriveFile(
                    file_id=response['id'],
                    name=response['name'],
                    size=int(response.get('size', len(chunk_data))),
                    created_time=response['createdTime'],
                    modified_time=response.get('modifiedTime'),
                    drive_account=account_id,
                    mime_type=response.get('mimeType')
                )
                drive_file.metadata = metadata or {}
                
                print(f"✅ Chunk uploaded successfully: {response['id']}")
                return drive_file
                
            except HttpError as e:
                error_code = e.resp.status
                print(f"⚠️ HTTP Error {error_code}: {e}")
                
                if error_code == 403:  # Quota exceeded
                    print("❌ Storage quota exceeded!")
                    raise e
                elif error_code == 401:  # Unauthorized
                    print("❌ Authentication failed!")
                    raise e
                elif attempt < self.max_retries - 1:
                    print(f"🔄 Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    print("❌ Max retries exceeded")
                    raise e
                    
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"⚠️ Upload error: {e}")
                    print(f"🔄 Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    print(f"❌ Upload failed: {e}")
                    raise e
    
    def download_chunk(self, account_id: str, file_id: str) -> bytes:
        """
        Download an encrypted chunk from Google Drive
        
        Args:
            account_id: Account to download from
            file_id: Google Drive file ID
            
        Returns:
            Encrypted chunk data (bytes)
        """
        service = self._get_drive_service(account_id)
        
        for attempt in range(self.max_retries):
            try:
                print(f"⬇️ Downloading chunk {file_id} from {account_id} (attempt {attempt + 1}/{self.max_retries})")
                
                # Get file metadata first
                file_metadata = service.files().get(fileId=file_id).execute()
                file_size = int(file_metadata.get('size', 0))
                
                # Download file content
                request = service.files().get_media(fileId=file_id)
                file_io = io.BytesIO()
                
                downloader = MediaIoBaseDownload(file_io, request)
                done = False
                
                while done is False:
                    status, done = downloader.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        print(f"   📊 Download progress: {progress}%")
                
                chunk_data = file_io.getvalue()
                
                # Verify download integrity
                if len(chunk_data) != file_size:
                    print(f"⚠️ Size mismatch: expected {file_size}, got {len(chunk_data)}")
                
                print(f"✅ Chunk downloaded successfully: {len(chunk_data)} bytes")
                return chunk_data
                
            except HttpError as e:
                error_code = e.resp.status
                print(f"⚠️ HTTP Error {error_code}: {e}")
                
                if error_code == 404:  # File not found
                    print("❌ Chunk not found!")
                    raise e
                elif error_code == 401:  # Unauthorized
                    print("❌ Authentication failed!")
                    raise e
                elif attempt < self.max_retries - 1:
                    print(f"🔄 Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    print("❌ Max retries exceeded")
                    raise e
                    
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"⚠️ Download error: {e}")
                    print(f"🔄 Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    print(f"❌ Download failed: {e}")
                    raise e
    
    def delete_chunk(self, account_id: str, file_id: str) -> bool:
        """
        Delete a chunk from Google Drive
        
        Args:
            account_id: Account containing the file
            file_id: Google Drive file ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        service = self._get_drive_service(account_id)
        
        try:
            print(f"🗑️ Deleting chunk {file_id} from {account_id}")
            service.files().delete(fileId=file_id).execute()
            print("✅ Chunk deleted successfully")
            return True
            
        except HttpError as e:
            print(f"⚠️ Delete error: {e}")
            return False
        except Exception as e:
            print(f"❌ Delete failed: {e}")
            return False
    
    def list_chunks(self, account_id: str, sort_by: str = 'name', 
                   search_query: str = None, limit: int = None) -> List[DriveFile]:
        """
        List all BrontoBox chunks in an account with enhanced filtering and sorting
        
        Args:
            account_id: Account to list chunks from
            sort_by: Sort by 'name', 'date', 'size', 'type' (default: 'name')
            search_query: Search term to filter files
            limit: Maximum number of files to return
            
        Returns:
            List of DriveFile objects
        """
        service = self._get_drive_service(account_id)
        
        try:
            # Find BrontoBox folder
            folder_id = self._create_brontobox_folder(account_id)
            
            # Build query
            query = f"'{folder_id}' in parents and trashed=false"
            
            # Add search filter if provided
            if search_query:
                query += f" and name contains '{search_query}'"
            
            # List files in BrontoBox folder with enhanced fields
            results = service.files().list(
                q=query,
                fields='files(id,name,size,createdTime,modifiedTime,mimeType,properties)',
                pageSize=limit or 1000,  # Default to 1000, but respect limit
                orderBy='name' if sort_by == 'name' else 'createdTime desc' if sort_by == 'date' else None
            ).execute()
            
            chunks = []
            for item in results.get('files', []):
                # Check if it's a BrontoBox chunk
                properties = item.get('properties', {})
                is_brontobox = (properties.get('brontobox_chunk') == 'true' or 
                               properties.get('brontobox') == 'true' or
                               item['name'].endswith('.enc'))
                
                if is_brontobox:
                    # Parse metadata (handle both old and new formats)
                    metadata = {}
                    if 'chunk_metadata' in properties:
                        try:
                            metadata = json.loads(properties['chunk_metadata'])
                        except:
                            pass
                    
                    # Add properties as metadata
                    metadata.update(properties)
                    
                    drive_file = DriveFile(
                        file_id=item['id'],
                        name=item['name'],
                        size=int(item.get('size', 0)),
                        created_time=item['createdTime'],
                        modified_time=item.get('modifiedTime'),
                        drive_account=account_id,
                        mime_type=item.get('mimeType')
                    )
                    drive_file.metadata = metadata
                    chunks.append(drive_file)
            
            # Apply sorting if not done by API
            if sort_by == 'size':
                chunks.sort(key=lambda x: x.size, reverse=True)
            elif sort_by == 'type':
                chunks.sort(key=lambda x: x.get_file_type())
            
            # Apply limit if specified and not done by API
            if limit and len(chunks) > limit:
                chunks = chunks[:limit]
            
            print(f"📋 Found {len(chunks)} chunks in {account_id} (sorted by {sort_by})")
            return chunks
            
        except Exception as e:
            print(f"❌ Failed to list chunks: {e}")
            return []
    
    def search_chunks(self, account_id: str, search_term: str, 
                     search_type: str = 'all') -> List[DriveFile]:
        """
        Advanced search functionality for BrontoBox chunks
        
        Args:
            account_id: Account to search in
            search_term: Term to search for
            search_type: 'name', 'content', 'metadata', 'all'
            
        Returns:
            List of matching DriveFile objects
        """
        all_chunks = self.list_chunks(account_id)
        matching_chunks = []
        
        search_term_lower = search_term.lower()
        
        for chunk in all_chunks:
            match_found = False
            
            if search_type in ['name', 'all']:
                if search_term_lower in chunk.name.lower():
                    match_found = True
            
            if search_type in ['metadata', 'all'] and not match_found:
                # Search in metadata
                metadata_str = json.dumps(chunk.metadata).lower()
                if search_term_lower in metadata_str:
                    match_found = True
            
            if match_found:
                matching_chunks.append(chunk)
        
        print(f"🔍 Search '{search_term}' found {len(matching_chunks)} matches")
        return matching_chunks
    
    def get_storage_info(self, account_id: str) -> Dict[str, Any]:
        """
        Get storage quota information for an account
        
        Args:
            account_id: Account to check
            
        Returns:
            Dictionary with storage information
        """
        service = self._get_drive_service(account_id)
        
        try:
            about = service.about().get(fields='storageQuota,user').execute()
            storage_quota = about.get('storageQuota', {})
            user_info = about.get('user', {})
            
            limit = int(storage_quota.get('limit', 0))
            usage = int(storage_quota.get('usage', 0))
            usage_in_drive = int(storage_quota.get('usageInDrive', 0))
            
            return {
                'account_id': account_id,
                'user_email': user_info.get('emailAddress', 'unknown'),
                'total_bytes': limit,
                'used_bytes': usage,
                'used_in_drive_bytes': usage_in_drive,
                'available_bytes': limit - usage,
                'usage_percentage': round((usage / limit * 100), 2) if limit > 0 else 0,
                'total_gb': round(limit / (1024**3), 2),
                'used_gb': round(usage / (1024**3), 2),
                'available_gb': round((limit - usage) / (1024**3), 2)
            }
            
        except Exception as e:
            print(f"❌ Failed to get storage info: {e}")
            return {
                'account_id': account_id,
                'error': str(e)
            }
    
    def get_folder_stats(self, account_id: str) -> Dict[str, Any]:
        """
        Get statistics about the BrontoBox folder
        
        Args:
            account_id: Account to analyze
            
        Returns:
            Dictionary with folder statistics
        """
        chunks = self.list_chunks(account_id)
        
        if not chunks:
            return {
                'total_files': 0,
                'total_size_bytes': 0,
                'total_size_mb': 0,
                'file_types': {},
                'oldest_file': None,
                'newest_file': None
            }
        
        total_size = sum(chunk.size for chunk in chunks)
        file_types = {}
        
        for chunk in chunks:
            file_type = chunk.get_file_type()
            file_types[file_type] = file_types.get(file_type, 0) + 1
        
        # Sort by date to find oldest/newest
        sorted_chunks = sorted(chunks, key=lambda x: x.created_time)
        
        return {
            'total_files': len(chunks),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'file_types': file_types,
            'oldest_file': {
                'name': sorted_chunks[0].name,
                'date': sorted_chunks[0].created_time,
                'size': sorted_chunks[0].get_formatted_size()
            },
            'newest_file': {
                'name': sorted_chunks[-1].name,
                'date': sorted_chunks[-1].created_time,
                'size': sorted_chunks[-1].get_formatted_size()
            }
        }
    
    def cleanup_empty_folders(self, account_id: str) -> int:
        """
        Clean up empty BrontoBox folders (maintenance function)
        
        Args:
            account_id: Account to clean up
            
        Returns:
            Number of folders cleaned up
        """
        service = self._get_drive_service(account_id)
        cleaned_count = 0
        
        try:
            # Find empty BrontoBox folders
            query = f"name='{self.brontobox_folder_name}' and mimeType='application/vnd.google-apps.folder'"
            results = service.files().list(q=query).execute()
            
            for folder in results.get('files', []):
                folder_id = folder['id']
                
                # Check if folder is empty
                files_query = f"'{folder_id}' in parents and trashed=false"
                files_result = service.files().list(q=files_query).execute()
                
                if not files_result.get('files', []):
                    # Folder is empty, but don't delete - it's needed for new uploads
                    print(f"📁 Empty BrontoBox folder found (keeping for future uploads): {folder_id}")
                
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")
        
        return cleaned_count
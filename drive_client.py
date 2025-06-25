# drive_client.py
"""
BrontoBox Google Drive Client
Handles file upload/download operations with Google Drive API
"""

import os
import io
import json
import time
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import mimetypes

# Google Drive API imports
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from google.oauth2.credentials import Credentials

# BrontoBox imports
from google_auth import GoogleAuthManager


class DriveFile:
    """Represents a file stored in Google Drive"""
    def __init__(self, file_id: str, name: str, size: int, 
                 created_time: str, drive_account: str):
        self.file_id = file_id
        self.name = name
        self.size = size
        self.created_time = created_time
        self.drive_account = drive_account
        self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            'file_id': self.file_id,
            'name': self.name,
            'size': self.size,
            'created_time': self.created_time,
            'drive_account': self.drive_account,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DriveFile':
        file_obj = cls(
            file_id=data['file_id'],
            name=data['name'],
            size=data['size'],
            created_time=data['created_time'],
            drive_account=data['drive_account']
        )
        file_obj.metadata = data.get('metadata', {})
        return file_obj


class BrontoBoxDriveClient:
    """
    Google Drive client for BrontoBox encrypted storage
    Handles chunk upload/download with proper error handling and retries
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
                'description': 'BrontoBox encrypted storage - DO NOT DELETE'
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
        
        # Add custom metadata as properties (keep under 124 bytes limit!)
        if metadata:
            # Create compact metadata to stay under Google's 124-byte limit
            compact_metadata = {
                'brontobox': 'true',
                'v': metadata.get('brontobox_version', '1.0')[:10],  # Truncate version
                'test': str(metadata.get('test_file', False))[:5]    # Boolean as short string
            }
            
            # Only add properties if total size is reasonable
            metadata_str = json.dumps(compact_metadata)
            if len(metadata_str.encode('utf-8')) < 100:  # Leave some buffer
                file_metadata['properties'] = compact_metadata
            else:
                print("⚠️ Metadata too large, skipping properties")
        else:
            # Minimal metadata
            file_metadata['properties'] = {'brontobox': 'true'}
        
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
                    fields='id,name,size,createdTime'
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
                    drive_account=account_id
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
    
    def list_chunks(self, account_id: str) -> List[DriveFile]:
        """
        List all BrontoBox chunks in an account
        
        Args:
            account_id: Account to list chunks from
            
        Returns:
            List of DriveFile objects
        """
        service = self._get_drive_service(account_id)
        
        try:
            # Find BrontoBox folder
            folder_id = self._create_brontobox_folder(account_id)
            
            # List files in BrontoBox folder
            query = f"'{folder_id}' in parents and trashed=false"
            results = service.files().list(
                q=query,
                fields='files(id,name,size,createdTime,properties)'
            ).execute()
            
            chunks = []
            for item in results.get('files', []):
                # Check if it's a BrontoBox chunk (check both old and new property formats)
                properties = item.get('properties', {})
                is_brontobox = (properties.get('brontobox_chunk') == 'true' or 
                               properties.get('brontobox') == 'true')
                
                if is_brontobox:
                    # Parse metadata (handle both old and new formats)
                    metadata = {}
                    if 'chunk_metadata' in properties:
                        try:
                            metadata = json.loads(properties['chunk_metadata'])
                        except:
                            pass
                    
                    drive_file = DriveFile(
                        file_id=item['id'],
                        name=item['name'],
                        size=int(item.get('size', 0)),
                        created_time=item['createdTime'],
                        drive_account=account_id
                    )
                    drive_file.metadata = metadata
                    chunks.append(drive_file)
            
            print(f"📋 Found {len(chunks)} chunks in {account_id}")
            return chunks
            
        except Exception as e:
            print(f"❌ Failed to list chunks: {e}")
            return []
    
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
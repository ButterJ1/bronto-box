# brontobox_api.py
"""
BrontoBox FastAPI Server - COMPLETE VERSION WITH FIXES
REST API bridge between Python backend and Electron frontend
Includes registry persistence and download fixes
"""

import os
import json
import asyncio
import hashlib
import base64
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# Import your existing BrontoBox components
from vault_core import VaultCore
from google_auth import GoogleAuthManager
from storage_manager import BrontoBoxStorageManager
from drive_client import BrontoBoxDriveClient

# Pydantic models for API requests/responses
class VaultInitRequest(BaseModel):
    master_password: str

class VaultUnlockRequest(BaseModel):
    master_password: str
    salt: str

class AccountAuthRequest(BaseModel):
    account_name: str
    credentials_file: Optional[str] = "credentials.json"

class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    size: int
    chunks: int
    accounts_used: List[str]
    upload_time: str

class StorageInfo(BaseModel):
    total_accounts: int
    total_capacity_gb: float
    total_used_gb: float
    total_available_gb: float
    usage_percentage: float
    accounts: List[Dict[str, Any]]

class FileInfo(BaseModel):
    file_id: str
    name: str
    size_bytes: int
    size_mb: float
    chunks: int
    accounts_used: List[str]
    created_at: str
    encrypted: bool = True

# Global app state
app_state = {
    "vault": None,
    "auth_manager": None,
    "storage_manager": None,
    "vault_unlocked": False,
    "active_uploads": {},
    "websocket_connections": []
}

# Initialize FastAPI app
app = FastAPI(
    title="BrontoBox API",
    description="Secure Distributed Storage API",
    version="1.0.0"
)

# Enable CORS for Electron frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Electron app origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                # Remove disconnected connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Registry persistence helpers
def save_file_registry_to_disk():
    """Save file registry to disk for persistence"""
    try:
        storage_manager = app_state["storage_manager"]
        if storage_manager and len(storage_manager.stored_files) > 0:
            encrypted_registry = storage_manager.save_file_registry()
            registry_file = "brontobox_file_registry.json"
            with open(registry_file, 'w') as f:
                json.dump(encrypted_registry, f)
            print(f"💾 File registry auto-saved ({len(storage_manager.stored_files)} files)")
            return True
    except Exception as e:
        print(f"⚠️ Could not auto-save registry: {e}")
    return False

def load_file_registry_from_disk():
    """Load file registry from disk"""
    try:
        storage_manager = app_state["storage_manager"]
        if not storage_manager:
            return False
            
        registry_file = "brontobox_file_registry.json"
        if os.path.exists(registry_file):
            with open(registry_file, 'r') as f:
                encrypted_registry = json.load(f)
            
            success = storage_manager.load_file_registry(encrypted_registry)
            if success:
                files_loaded = len(storage_manager.stored_files)
                print(f"📂 Auto-loaded {files_loaded} files from registry")
                return True
    except Exception as e:
        print(f"⚠️ Could not auto-load registry: {e}")
    return False

# API Endpoints

@app.get("/")
async def root():
    """API status endpoint"""
    return {
        "app": "BrontoBox API",
        "version": "1.0.0",
        "status": "running",
        "vault_unlocked": app_state["vault_unlocked"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    auth_manager = app_state.get("auth_manager")
    storage_manager = app_state.get("storage_manager")
    accounts_count = len(auth_manager.accounts) if auth_manager else 0
    files_count = len(storage_manager.stored_files) if storage_manager else 0
    
    return {
        "status": "healthy",
        "vault": app_state["vault"] is not None,
        "vault_unlocked": app_state["vault_unlocked"],
        "accounts_configured": accounts_count,
        "files_stored": files_count
    }

# Vault Management Endpoints

@app.post("/vault/initialize")
async def initialize_vault(request: VaultInitRequest):
    """Initialize a new BrontoBox vault"""
    try:
        # Initialize vault
        vault = VaultCore()
        init_data = vault.initialize_vault(request.master_password)
        
        # Initialize auth manager
        auth_manager = GoogleAuthManager(vault)
        
        # Initialize storage manager (even with no accounts)
        storage_manager = BrontoBoxStorageManager(vault, auth_manager)
        
        # Store in global state
        app_state["vault"] = vault
        app_state["auth_manager"] = auth_manager
        app_state["storage_manager"] = storage_manager
        app_state["vault_unlocked"] = True
        
        # Save vault info for persistence
        vault_info_file = "brontobox_vault_info.json"
        with open(vault_info_file, 'w') as f:
            json.dump(init_data, f)
        
        await manager.broadcast({
            "type": "vault_initialized",
            "data": {"status": "Vault initialized successfully"}
        })
        
        return {
            "success": True,
            "message": "Vault initialized successfully",
            "salt": init_data["salt"],
            "vault_info": init_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize vault: {str(e)}")

@app.post("/vault/unlock")
async def unlock_vault(request: VaultUnlockRequest):
    """Unlock existing vault"""
    try:
        # Initialize vault
        vault = VaultCore()
        success = vault.unlock_vault(request.master_password, request.salt)
        
        if not success:
            raise HTTPException(status_code=401, detail="Invalid master password or salt")
        
        # Initialize auth manager
        auth_manager = GoogleAuthManager(vault)
        
        # Try to load existing accounts
        accounts_file = "brontobox_accounts.json"
        if os.path.exists(accounts_file):
            try:
                with open(accounts_file, 'r') as f:
                    encrypted_accounts = json.load(f)
                success = auth_manager.load_accounts_from_vault(encrypted_accounts)
                if not success:
                    print("Warning: Could not load accounts - they may have been saved with different vault key")
            except Exception as e:
                print(f"Warning: Could not load accounts: {e}")
                # Remove corrupted accounts file
                try:
                    os.remove(accounts_file)
                    print("Removed corrupted accounts file")
                except:
                    pass
        
        # Initialize storage manager
        storage_manager = BrontoBoxStorageManager(vault, auth_manager)
        
        # Store in global state
        app_state["vault"] = vault
        app_state["auth_manager"] = auth_manager
        app_state["storage_manager"] = storage_manager
        app_state["vault_unlocked"] = True
        
        # Auto-load file registry
        load_file_registry_from_disk()
        
        await manager.broadcast({
            "type": "vault_unlocked",
            "data": {"status": "Vault unlocked successfully"}
        })
        
        return {
            "success": True,
            "message": "Vault unlocked successfully",
            "accounts_loaded": len(auth_manager.accounts),
            "files_loaded": len(storage_manager.stored_files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to unlock vault: {str(e)}")

@app.post("/vault/lock")
async def lock_vault():
    """Lock the vault"""
    try:
        # Save registry before locking
        save_file_registry_to_disk()
        
        if app_state["vault"]:
            app_state["vault"].lock_vault()
        
        # Clear global state
        app_state["vault"] = None
        app_state["auth_manager"] = None
        app_state["storage_manager"] = None
        app_state["vault_unlocked"] = False
        
        await manager.broadcast({
            "type": "vault_locked",
            "data": {"status": "Vault locked"}
        })
        
        return {"success": True, "message": "Vault locked successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to lock vault: {str(e)}")

@app.get("/vault/status")
async def get_vault_status():
    """Get current vault status"""
    vault = app_state["vault"]
    auth_manager = app_state["auth_manager"]
    storage_manager = app_state["storage_manager"]
    
    if not vault:
        return {
            "unlocked": False,
            "accounts_configured": 0,
            "files_stored": 0,
            "message": "Vault not initialized"
        }
    
    accounts_count = len(auth_manager.accounts) if auth_manager else 0
    files_count = len(storage_manager.stored_files) if storage_manager else 0
    
    return {
        "unlocked": app_state["vault_unlocked"],
        "accounts_configured": accounts_count,
        "files_stored": files_count,
        "vault_status": vault.get_vault_status() if vault else None
    }

# Account Management Endpoints

@app.post("/accounts/setup-oauth")
async def setup_oauth(credentials_file: str = "credentials.json"):
    """Setup OAuth configuration"""
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        auth_manager = app_state["auth_manager"]
        if not os.path.exists(credentials_file):
            raise HTTPException(status_code=404, detail=f"Credentials file not found: {credentials_file}")
        
        auth_manager.setup_oauth_from_file(credentials_file)
        
        return {
            "success": True,
            "message": "OAuth configured successfully",
            "scopes": auth_manager.SCOPES
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to setup OAuth: {str(e)}")

@app.post("/accounts/authenticate")
async def authenticate_account(request: AccountAuthRequest):
    """Authenticate a new Google account"""
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        auth_manager = app_state["auth_manager"]
        
        # Setup OAuth if not already done
        if not auth_manager.client_config:
            auth_manager.setup_oauth_from_file(request.credentials_file)
        
        # Authenticate account
        account_id = auth_manager.authenticate_new_account(request.account_name)
        
        # Save accounts
        encrypted_accounts = auth_manager.save_accounts_to_vault()
        accounts_file = "brontobox_accounts.json"
        with open(accounts_file, 'w') as f:
            json.dump(encrypted_accounts, f)
        
        # Get account info
        accounts = auth_manager.list_accounts()
        new_account = next((acc for acc in accounts if acc['account_id'] == account_id), None)
        
        await manager.broadcast({
            "type": "account_added",
            "data": {"account": new_account}
        })
        
        return {
            "success": True,
            "message": "Account authenticated successfully",
            "account_id": account_id,
            "account": new_account
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to authenticate account: {str(e)}")

@app.get("/accounts/list")
async def list_accounts():
    """List all configured Google accounts"""
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        auth_manager = app_state["auth_manager"]
        accounts = auth_manager.list_accounts()
        
        # Get storage info for each account
        if app_state["storage_manager"]:
            available_accounts = app_state["storage_manager"].get_available_accounts()
            
            # Merge storage info with account info
            for account in accounts:
                storage_info = next(
                    (acc for acc in available_accounts if acc['account_id'] == account['account_id']), 
                    None
                )
                if storage_info:
                    account['storage_info'] = storage_info['storage_info']
        
        return {
            "success": True,
            "accounts": accounts,
            "total_accounts": len(accounts)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list accounts: {str(e)}")

@app.get("/accounts/{account_id}/test")
async def test_account(account_id: str):
    """Test account access and get storage info"""
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        auth_manager = app_state["auth_manager"]
        test_result = auth_manager.test_account_access(account_id)
        
        return {
            "success": test_result["success"],
            "test_result": test_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test account: {str(e)}")

# Storage Information Endpoints

@app.get("/storage/info", response_model=StorageInfo)
async def get_storage_info():
    """Get comprehensive storage information"""
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        storage_manager = app_state["storage_manager"]
        if not storage_manager:
            raise HTTPException(status_code=500, detail="Storage manager not initialized")
        
        summary = storage_manager.get_storage_summary()
        
        return StorageInfo(
            total_accounts=summary["google_accounts"]["count"],
            total_capacity_gb=summary["google_accounts"]["total_capacity_gb"],
            total_used_gb=summary["google_accounts"]["total_used_gb"],
            total_available_gb=summary["google_accounts"]["total_available_gb"],
            usage_percentage=summary["google_accounts"]["usage_percentage"],
            accounts=summary["accounts"]
        )
        
    except Exception as e:
        # Return empty storage info if no accounts configured
        return StorageInfo(
            total_accounts=0,
            total_capacity_gb=0.0,
            total_used_gb=0.0,
            total_available_gb=0.0,
            usage_percentage=0.0,
            accounts=[]
        )

# File Management Endpoints

@app.post("/files/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...), metadata: str = "{}"):
    """Upload and encrypt a file"""
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        storage_manager = app_state["storage_manager"]
        if not storage_manager:
            raise HTTPException(status_code=500, detail="Storage manager not initialized")
        
        # Parse metadata
        file_metadata = json.loads(metadata) if metadata else {}
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name
        
        try:
            # Store file using BrontoBox
            file_id = storage_manager.store_file(temp_file_path, file_metadata)
            
            # Get file info
            files = storage_manager.list_stored_files()
            stored_file = next((f for f in files if f['file_id'] == file_id), None)
            
            if not stored_file:
                raise HTTPException(status_code=500, detail="File stored but not found in registry")
            
            # Auto-save registry after successful upload
            save_file_registry_to_disk()
            
            await manager.broadcast({
                "type": "file_uploaded",
                "data": {
                    "file_id": file_id,
                    "filename": file.filename,
                    "size": stored_file["size_bytes"]
                }
            })
            
            return FileUploadResponse(
                file_id=file_id,
                filename=file.filename,
                size=stored_file["size_bytes"],
                chunks=stored_file["chunks"],
                accounts_used=stored_file["accounts_used"],
                upload_time=stored_file["created_at"]
            )
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

@app.get("/files/list")
async def list_files():
    """List all stored files"""
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        storage_manager = app_state["storage_manager"]
        if not storage_manager:
            # Return empty list if storage manager not initialized
            return {
                "success": True,
                "files": [],
                "total_files": 0
            }
        
        files = storage_manager.list_stored_files()
        
        return {
            "success": True,
            "files": files,
            "total_files": len(files)
        }
        
    except Exception as e:
        # Return empty list on error instead of failing
        return {
            "success": True,
            "files": [],
            "total_files": 0,
            "note": f"No files found (storage may not be configured): {str(e)}"
        }

@app.get("/files/{file_id}/download")
async def download_file(file_id: str):
    """Download and decrypt a file"""
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        storage_manager = app_state["storage_manager"]
        if not storage_manager:
            raise HTTPException(status_code=500, detail="Storage manager not initialized")
        
        # Get file info
        files = storage_manager.list_stored_files()
        file_info = next((f for f in files if f['file_id'] == file_id), None)
        
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Create temp file for download
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, file_info['name'])
        
        # Retrieve file
        success = storage_manager.retrieve_file(file_id, output_path)
        
        if not success:
            shutil.rmtree(temp_dir)
            raise HTTPException(status_code=500, detail="Failed to retrieve file")
        
        await manager.broadcast({
            "type": "file_downloaded",
            "data": {
                "file_id": file_id,
                "filename": file_info['name']
            }
        })
        
        return FileResponse(
            path=output_path,
            filename=file_info['name'],
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")

@app.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """Delete a file"""
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        storage_manager = app_state["storage_manager"]
        if not storage_manager:
            raise HTTPException(status_code=500, detail="Storage manager not initialized")
        
        # Get file info before deletion
        files = storage_manager.list_stored_files()
        file_info = next((f for f in files if f['file_id'] == file_id), None)
        
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Delete file
        success = storage_manager.delete_file(file_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete file")
        
        # Auto-save registry after successful deletion
        save_file_registry_to_disk()
        
        await manager.broadcast({
            "type": "file_deleted",
            "data": {
                "file_id": file_id,
                "filename": file_info['name']
            }
        })
        
        return {
            "success": True,
            "message": f"File '{file_info['name']}' deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

@app.get("/drive/chunks/{account_id}")
async def list_drive_chunks(
    account_id: str, 
    sort_by: str = "date", 
    order: str = "desc",
    limit: Optional[int] = None,
    search: Optional[str] = None
):
    """List chunks in Google Drive with sorting and filtering"""
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        storage_manager = app_state["storage_manager"]
        if not storage_manager:
            raise HTTPException(status_code=500, detail="Storage manager not initialized")
        
        drive_client = storage_manager.drive_client
        
        # List chunks with parameters
        chunks = drive_client.list_chunks(
            account_id=account_id,
            sort_by=sort_by,
            search_query=search,
            limit=limit
        )
        
        # Convert to dict format
        chunks_data = [chunk.to_dict() for chunk in chunks]
        
        return {
            "success": True,
            "account_id": account_id,
            "chunks": chunks_data,
            "total_chunks": len(chunks_data),
            "sort_by": sort_by,
            "order": order
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list chunks: {str(e)}")

@app.get("/drive/search/{account_id}")
async def search_drive_chunks(
    account_id: str,
    query: str,
    search_type: str = "all"
):
    """Search chunks in Google Drive"""
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        storage_manager = app_state["storage_manager"]
        if not storage_manager:
            raise HTTPException(status_code=500, detail="Storage manager not initialized")
        
        drive_client = storage_manager.drive_client
        
        # Search chunks
        chunks = drive_client.search_chunks(
            account_id=account_id,
            search_term=query,
            search_type=search_type
        )
        
        # Convert to dict format
        chunks_data = [chunk.to_dict() for chunk in chunks]
        
        return {
            "success": True,
            "account_id": account_id,
            "query": query,
            "search_type": search_type,
            "chunks": chunks_data,
            "total_results": len(chunks_data)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search chunks: {str(e)}")

@app.get("/drive/stats/{account_id}")
async def get_drive_folder_stats(account_id: str):
    """Get statistics about the BrontoBox folder in Google Drive"""
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        storage_manager = app_state["storage_manager"]
        if not storage_manager:
            raise HTTPException(status_code=500, detail="Storage manager not initialized")
        
        drive_client = storage_manager.drive_client
        
        # Get folder statistics
        stats = drive_client.get_folder_stats(account_id)
        
        return {
            "success": True,
            "account_id": account_id,
            **stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get folder stats: {str(e)}")

@app.get("/drive/download/{account_id}/{file_id}")
async def download_raw_chunk(account_id: str, file_id: str):
    """Download a raw encrypted chunk from Google Drive"""
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        storage_manager = app_state["storage_manager"]
        if not storage_manager:
            raise HTTPException(status_code=500, detail="Storage manager not initialized")
        
        drive_client = storage_manager.drive_client
        
        # Download the raw chunk
        chunk_data = drive_client.download_chunk(account_id, file_id)
        
        # Get file metadata for filename
        chunks = drive_client.list_chunks(account_id)
        target_chunk = next((c for c in chunks if c.file_id == file_id), None)
        
        filename = target_chunk.name if target_chunk else f"chunk_{file_id}.enc"
        
        # Create temp file for download
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, filename)
        
        with open(temp_path, 'wb') as f:
            f.write(chunk_data)
        
        return FileResponse(
            path=temp_path,
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download chunk: {str(e)}")

@app.delete("/drive/delete/{account_id}/{file_id}")
async def delete_raw_chunk(account_id: str, file_id: str):
    """Delete a raw encrypted chunk from Google Drive"""
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        storage_manager = app_state["storage_manager"]
        if not storage_manager:
            raise HTTPException(status_code=500, detail="Storage manager not initialized")
        
        drive_client = storage_manager.drive_client
        
        # Get file info before deletion
        chunks = drive_client.list_chunks(account_id)
        target_chunk = next((c for c in chunks if c.file_id == file_id), None)
        
        if not target_chunk:
            raise HTTPException(status_code=404, detail="Chunk not found")
        
        # Delete the chunk
        success = drive_client.delete_chunk(account_id, file_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete chunk")
        
        await manager.broadcast({
            "type": "raw_chunk_deleted",
            "data": {
                "account_id": account_id,
                "file_id": file_id,
                "filename": target_chunk.name
            }
        })
        
        return {
            "success": True,
            "message": f"Chunk '{target_chunk.name}' deleted successfully",
            "account_id": account_id,
            "file_id": file_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete chunk: {str(e)}")

@app.get("/drive/folder-info/{account_id}")
async def get_brontobox_folder_info(account_id: str):
    """Get information about the .brontobox_storage folder"""
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        storage_manager = app_state["storage_manager"]
        if not storage_manager:
            raise HTTPException(status_code=500, detail="Storage manager not initialized")
        
        drive_client = storage_manager.drive_client
        
        # Get basic storage info
        storage_info = drive_client.get_storage_info(account_id)
        
        # Get folder stats
        folder_stats = drive_client.get_folder_stats(account_id)
        
        # Get account info
        auth_manager = app_state["auth_manager"]
        accounts = auth_manager.list_accounts()
        account_info = next((acc for acc in accounts if acc['account_id'] == account_id), None)
        
        return {
            "success": True,
            "account_id": account_id,
            "account_email": account_info['email'] if account_info else 'Unknown',
            "folder_name": ".brontobox_storage",
            "storage_info": storage_info,
            "folder_stats": folder_stats,
            "search_enabled": folder_stats.get('total_files', 0) >= 100
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get folder info: {str(e)}")

# Account Persistence Enhancement
@app.post("/accounts/refresh-tokens")
async def refresh_account_tokens():
    """Refresh all account tokens to ensure they stay valid"""
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        auth_manager = app_state["auth_manager"]
        if not auth_manager:
            raise HTTPException(status_code=500, detail="Auth manager not initialized")
        
        refreshed_accounts = []
        failed_accounts = []
        
        for account_id in auth_manager.accounts.keys():
            try:
                # Getting credentials automatically refreshes tokens if needed
                credentials = auth_manager.get_credentials(account_id)
                if credentials:
                    refreshed_accounts.append(account_id)
                else:
                    failed_accounts.append(account_id)
            except Exception as e:
                print(f"Failed to refresh {account_id}: {e}")
                failed_accounts.append(account_id)
        
        # Save updated accounts
        if refreshed_accounts:
            encrypted_accounts = auth_manager.save_accounts_to_vault()
            accounts_file = "brontobox_accounts.json"
            with open(accounts_file, 'w') as f:
                json.dump(encrypted_accounts, f)
        
        return {
            "success": True,
            "message": "Token refresh completed",
            "refreshed_accounts": len(refreshed_accounts),
            "failed_accounts": len(failed_accounts),
            "total_accounts": len(auth_manager.accounts)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh tokens: {str(e)}")

@app.get("/accounts/persistence-status")
async def get_account_persistence_status():
    """Check if accounts are properly persisted and will survive vault lock/unlock"""
    try:
        vault_info_exists = os.path.exists("brontobox_vault_info.json")
        accounts_file_exists = os.path.exists("brontobox_accounts.json")
        registry_file_exists = os.path.exists("brontobox_file_registry.json")
        
        vault_unlocked = app_state["vault_unlocked"]
        accounts_loaded = len(app_state["auth_manager"].accounts) if app_state["auth_manager"] else 0
        files_loaded = len(app_state["storage_manager"].stored_files) if app_state["storage_manager"] else 0
        
        return {
            "success": True,
            "persistence_status": {
                "vault_info_saved": vault_info_exists,
                "accounts_saved": accounts_file_exists,
                "file_registry_saved": registry_file_exists,
                "vault_currently_unlocked": vault_unlocked,
                "accounts_loaded": accounts_loaded,
                "files_loaded": files_loaded
            },
            "ready_for_lock_unlock": vault_info_exists and accounts_file_exists,
            "message": "All components properly persisted" if (vault_info_exists and accounts_file_exists) else "Some components not persisted"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "persistence_status": None
        }

# Registry Management Endpoints

@app.post("/files/save-registry")
async def save_file_registry():
    """Save file registry for persistence"""
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        success = save_file_registry_to_disk()
        
        if success:
            storage_manager = app_state["storage_manager"]
            files_count = len(storage_manager.stored_files) if storage_manager else 0
            
            return {
                "success": True,
                "message": "File registry saved successfully",
                "files_count": files_count
            }
        else:
            return {
                "success": False,
                "message": "No files to save",
                "files_count": 0
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save registry: {str(e)}")

@app.post("/files/load-registry")
async def load_file_registry():
    """Load file registry from persistence"""
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        success = load_file_registry_from_disk()
        
        if success:
            storage_manager = app_state["storage_manager"]
            files_loaded = len(storage_manager.stored_files) if storage_manager else 0
            
            return {
                "success": True,
                "message": "File registry loaded successfully",
                "files_loaded": files_loaded
            }
        else:
            return {
                "success": True,
                "message": "No registry file found or no files to load",
                "files_loaded": 0
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load registry: {str(e)}")

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for testing
            await manager.send_personal_message(f"Echo: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Development endpoints
@app.get("/dev/reset")
async def reset_app_state():
    """Reset application state (development only)"""
    # Save registry before reset
    save_file_registry_to_disk()
    
    app_state["vault"] = None
    app_state["auth_manager"] = None
    app_state["storage_manager"] = None
    app_state["vault_unlocked"] = False
    app_state["active_uploads"] = {}
    
    return {"success": True, "message": "Application state reset"}

# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    print("🦕 Starting BrontoBox API Server...")
    print("🔌 WebSocket: ws://localhost:8000/ws")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🔧 Health Check: http://localhost:8000/health")
    
    uvicorn.run(
        "brontobox_api:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
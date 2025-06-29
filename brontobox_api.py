# brontobox_api.py - COMPLETE SECURE VERSION WITH UNIFIED FILE EXPERIENCE
"""
BrontoBox FastAPI Server - COMPLETE VERSION WITH SECURITY FIXES & AUTO-DISCOVERY
REST API bridge between Python backend and Electron frontend
Includes proper vault authentication, data isolation, and file auto-discovery
"""

import os
import json
import asyncio
import hashlib
import base64
import time
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import tempfile
import shutil


# PRODUCTION FIX: Set UTF-8 encoding for console output
if sys.platform == "win32":
    try:
        # Try to set UTF-8 encoding
        os.environ["PYTHONIOENCODING"] = "utf-8"
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        # Fallback: disable emoji/unicode characters
        pass

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

class RestoreRequest(BaseModel):
    vault_backup_file: str
    registry_backup_file: Optional[str] = None
    master_password: str

class StorageInfo(BaseModel):
    total_accounts: int
    total_capacity_gb: float
    total_used_gb: float
    total_available_gb: float
    usage_percentage: float
    accounts: List[Dict[str, Any]]
    workspace_summary: Optional[Dict[str, Any]] = None  # New field

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

# SECURE VAULT MANAGEMENT FUNCTIONS

def get_vault_registry_path() -> str:
    """Get path to vault registry file"""
    return "brontobox_vault_registry.json"

def save_vault_to_registry(vault_id: str, vault_data: Dict[str, Any]) -> bool:
    """Save vault information to secure registry"""
    try:
        registry_path = get_vault_registry_path()
        
        # Load existing registry or create new
        if os.path.exists(registry_path):
            with open(registry_path, 'r') as f:
                registry = json.load(f)
        else:
            registry = {"vaults": {}, "created_at": datetime.now().isoformat()}
        
        # Add/update vault
        registry["vaults"][vault_id] = {
            "vault_id": vault_id,
            "salt": vault_data["salt"],
            "verification_data": vault_data["verification_data"],
            "created_at": vault_data.get("created_at", datetime.now().isoformat()),
            "version": vault_data.get("version", "1.0"),
            "last_accessed": datetime.now().isoformat()
        }
        
        # Save registry
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)
            
        print(f"Vault {vault_id} saved to registry")
        return True
        
    except Exception as e:
        print(f"Failed to save vault to registry: {e}")
        return False

def load_vault_from_registry(vault_id: str = None) -> Optional[Dict[str, Any]]:
    """Load vault information from registry"""
    try:
        registry_path = get_vault_registry_path()
        
        if not os.path.exists(registry_path):
            return None
            
        with open(registry_path, 'r') as f:
            registry = json.load(f)
        
        vaults = registry.get("vaults", {})
        
        if vault_id:
            return vaults.get(vault_id)
        else:
            # Return most recently accessed vault
            if not vaults:
                return None
            
            latest_vault = max(vaults.values(), 
                             key=lambda v: v.get("last_accessed", ""))
            return latest_vault
            
    except Exception as e:
        print(f"Failed to load vault from registry: {e}")
        return None

def list_vaults_from_registry() -> List[Dict[str, Any]]:
    """List all registered vaults"""
    try:
        registry_path = get_vault_registry_path()
        
        if not os.path.exists(registry_path):
            return []
            
        with open(registry_path, 'r') as f:
            registry = json.load(f)
        
        return list(registry.get("vaults", {}).values())
        
    except Exception as e:
        print(f"Failed to list vaults: {e}")
        return []

def get_accounts_file_path(vault_id: str) -> str:
    """Get account file path for specific vault"""
    return f"brontobox_accounts_{vault_id}.json"

def get_registry_file_path(vault_id: str) -> str:
    """Get file registry path for specific vault"""
    return f"brontobox_file_registry_{vault_id}.json"

# Registry persistence helpers - updated for vault-specific storage
def save_file_registry_to_disk():
    """Save file registry to disk for persistence"""
    try:
        storage_manager = app_state["storage_manager"]
        vault = app_state.get("vault")
        
        if storage_manager and vault and vault.vault_id and len(storage_manager.stored_files) > 0:
            encrypted_registry = storage_manager.save_file_registry()
            registry_file = get_registry_file_path(vault.vault_id)
            with open(registry_file, 'w') as f:
                json.dump(encrypted_registry, f)
            print(f"File registry auto-saved for vault {vault.vault_id} ({len(storage_manager.stored_files)} files)")
            return True
    except Exception as e:
        print(f"Could not auto-save registry: {e}")
    return False

def load_file_registry_from_disk():
    """Load file registry from disk"""
    try:
        storage_manager = app_state["storage_manager"]
        vault = app_state.get("vault")
        
        if not storage_manager or not vault or not vault.vault_id:
            return False
            
        registry_file = get_registry_file_path(vault.vault_id)
        if os.path.exists(registry_file):
            with open(registry_file, 'r') as f:
                encrypted_registry = json.load(f)
            
            success = storage_manager.load_file_registry(encrypted_registry)
            if success:
                files_loaded = len(storage_manager.stored_files)
                print(f"Auto-loaded {files_loaded} files from registry for vault {vault.vault_id}")
                return True
    except Exception as e:
        print(f"Could not auto-load registry: {e}")
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
        "security": "enhanced",
        "features": ["unified_file_experience", "auto_discovery"],
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
    """Initialize a new BrontoBox vault with secure verification"""
    try:
        # Initialize vault
        vault = VaultCore()
        init_data = vault.initialize_vault(request.master_password)
        
        # Initialize auth manager
        auth_manager = GoogleAuthManager(vault)
        
        # Initialize storage manager
        storage_manager = BrontoBoxStorageManager(vault, auth_manager)
        
        # Store in global state
        app_state["vault"] = vault
        app_state["auth_manager"] = auth_manager
        app_state["storage_manager"] = storage_manager
        app_state["vault_unlocked"] = True
        
        # SECURE: Save vault to registry with verification data
        vault_data = {
            "vault_id": init_data["vault_id"],
            "salt": init_data["salt"],
            "verification_data": init_data["verification_data"],
            "created_at": datetime.now().isoformat(),
            "version": init_data.get("version", "1.0")
        }
        
        if not save_vault_to_registry(init_data["vault_id"], vault_data):
            raise HTTPException(status_code=500, detail="Failed to save vault securely")
        
        await manager.broadcast({
            "type": "vault_initialized",
            "data": {"status": "Vault initialized successfully"}
        })
        
        return {
            "success": True,
            "message": "Vault initialized successfully",
            "vault_id": init_data["vault_id"],
            "salt": init_data["salt"],
            "security_notice": "Vault secured with password verification"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize vault: {str(e)}")

@app.post("/vault/unlock")
async def unlock_vault(request: VaultUnlockRequest):
    """Unlock existing vault with SECURE verification"""
    try:
        # Try to find vault by salt (since user only provides salt, not vault_id)
        all_vaults = list_vaults_from_registry()
        matching_vault = None
        
        for vault_info in all_vaults:
            if vault_info["salt"] == request.salt:
                matching_vault = vault_info
                break
        
        if not matching_vault:
            raise HTTPException(status_code=404, detail="No vault found with this salt")
        
        # Initialize vault
        vault = VaultCore()
        
        # SECURE: Unlock with verification data
        success = vault.unlock_vault(
            request.master_password, 
            request.salt,
            matching_vault["verification_data"]
        )
        
        if not success:
            raise HTTPException(status_code=401, detail="Invalid master password or salt")
        
        # Initialize auth manager
        auth_manager = GoogleAuthManager(vault)
        
        # Try to load existing accounts for this specific vault
        accounts_file = get_accounts_file_path(matching_vault["vault_id"])
        if os.path.exists(accounts_file):
            try:
                with open(accounts_file, 'r') as f:
                    encrypted_accounts = json.load(f)
                success = auth_manager.load_accounts_from_vault(encrypted_accounts)
                if not success:
                    print("Warning: Could not load accounts - vault keys may be different")
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
        
        # Auto-load file registry for this vault
        registry_file = get_registry_file_path(matching_vault["vault_id"])
        if os.path.exists(registry_file):
            try:
                with open(registry_file, 'r') as f:
                    encrypted_registry = json.load(f)
                storage_manager.load_file_registry(encrypted_registry)
            except Exception as e:
                print(f"Warning: Could not load file registry: {e}")
        
        # TRIGGER AUTO-DISCOVERY after vault unlock
        if len(auth_manager.accounts) > 0:
            print(f"Triggering file discovery for {len(auth_manager.accounts)} accounts...")
            old_count = len(storage_manager.stored_files)
            storage_manager.refresh_file_discovery()
            new_count = len(storage_manager.stored_files)
            discovered = new_count - old_count
            
            if discovered > 0:
                print(f"Discovered {discovered} existing files across accounts!")
        
        # Update last accessed time
        matching_vault["last_accessed"] = datetime.now().isoformat()
        save_vault_to_registry(matching_vault["vault_id"], matching_vault)
        
        await manager.broadcast({
            "type": "vault_unlocked",
            "data": {"status": "Vault unlocked successfully"}
        })
        
        return {
            "success": True,
            "message": "Vault unlocked successfully",
            "vault_id": matching_vault["vault_id"],
            "accounts_loaded": len(auth_manager.accounts),
            "files_loaded": len(storage_manager.stored_files),
            "files_discovered": discovered if 'discovered' in locals() else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to unlock vault: {str(e)}")

@app.post("/vault/lock")
async def lock_vault():
    """Lock the vault"""
    try:
        vault = app_state.get("vault")
        if not vault:
            return {"success": True, "message": "No vault to lock"}
        
        vault_id = vault.vault_id
        
        # Save data before locking
        if vault_id:
            # Save accounts for this vault
            auth_manager = app_state.get("auth_manager")
            if auth_manager and len(auth_manager.accounts) > 0:
                try:
                    encrypted_accounts = auth_manager.save_accounts_to_vault()
                    accounts_file = get_accounts_file_path(vault_id)
                    with open(accounts_file, 'w') as f:
                        json.dump(encrypted_accounts, f)
                    print(f"Accounts saved for vault {vault_id}")
                except Exception as e:
                    print(f"Could not save accounts: {e}")
            
            # Save file registry for this vault
            storage_manager = app_state.get("storage_manager")
            if storage_manager and len(storage_manager.stored_files) > 0:
                try:
                    encrypted_registry = storage_manager.save_file_registry()
                    registry_file = get_registry_file_path(vault_id)
                    with open(registry_file, 'w') as f:
                        json.dump(encrypted_registry, f)
                    print(f"File registry saved for vault {vault_id}")
                except Exception as e:
                    print(f"Could not save file registry: {e}")
        
        # Lock vault
        vault.lock_vault()
        
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

@app.get("/vault/list")
async def list_vaults():
    """List all registered vaults (for debugging/admin)"""
    try:
        vaults = list_vaults_from_registry()
        
        # Remove sensitive data from response
        safe_vaults = []
        for vault in vaults:
            safe_vaults.append({
                "vault_id": vault["vault_id"],
                "created_at": vault.get("created_at"),
                "last_accessed": vault.get("last_accessed"),
                "version": vault.get("version"),
                "has_verification": "verification_data" in vault
            })
        
        return {
            "success": True,
            "vaults": safe_vaults,
            "total_vaults": len(safe_vaults)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list vaults: {str(e)}")

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
        "vault_id": vault.vault_id if vault else None,
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
    """Authenticate a new Google account and trigger file discovery"""
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        auth_manager = app_state["auth_manager"]
        vault = app_state["vault"]
        storage_manager = app_state["storage_manager"]
        
        # Setup OAuth if not already done
        if not auth_manager.client_config:
            auth_manager.setup_oauth_from_file(request.credentials_file)
        
        # Authenticate account
        account_id = auth_manager.authenticate_new_account(request.account_name)
        
        # Save accounts to vault-specific file
        if vault and vault.vault_id:
            encrypted_accounts = auth_manager.save_accounts_to_vault()
            accounts_file = get_accounts_file_path(vault.vault_id)
            with open(accounts_file, 'w') as f:
                json.dump(encrypted_accounts, f)
        
        # TRIGGER AUTO-DISCOVERY for new account
        discovered = 0
        if storage_manager:
            print(f"Triggering file discovery for new account: {account_id}")
            old_count = len(storage_manager.stored_files)
            storage_manager.refresh_file_discovery()
            new_count = len(storage_manager.stored_files)
            discovered = new_count - old_count
            
            if discovered > 0:
                print(f"Discovered {discovered} existing files in new account!")
        
        # Get account info
        accounts = auth_manager.list_accounts()
        new_account = next((acc for acc in accounts if acc['account_id'] == account_id), None)
        
        await manager.broadcast({
            "type": "account_added",
            "data": {
                "account": new_account,
                "files_discovered": discovered
            }
        })
        
        return {
            "success": True,
            "message": "Account authenticated successfully",
            "account_id": account_id,
            "account": new_account,
            "files_discovered": discovered
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
    """Get comprehensive storage information with workspace account handling"""
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        storage_manager = app_state["storage_manager"]
        if not storage_manager:
            raise HTTPException(status_code=500, detail="Storage manager not initialized")
        
        # Get account information with smart workspace detection
        auth_manager = app_state["auth_manager"]
        accounts = auth_manager.list_accounts()
        
        # Separate personal and workspace accounts
        personal_accounts = []
        workspace_accounts = []
        
        total_personal_capacity = 0
        total_personal_used = 0
        total_workspace_drive_usage = 0
        
        for account in accounts:
            storage_info = account.get('storage_info', {})
            account_type = storage_info.get('account_type', 'personal')
            
            if account_type == 'workspace':
                workspace_accounts.append(account)
                total_workspace_drive_usage += storage_info.get('used_gb', 0)
            else:
                personal_accounts.append(account)
                total_personal_capacity += storage_info.get('total_gb', 0)
                total_personal_used += storage_info.get('used_gb', 0)
        
        total_personal_available = total_personal_capacity - total_personal_used
        
        # Calculate usage percentage for personal accounts only
        personal_usage_percentage = (total_personal_used / total_personal_capacity * 100) if total_personal_capacity > 0 else 0
        
        return StorageInfo(
            total_accounts=len(personal_accounts),  # Only count personal accounts
            total_capacity_gb=total_personal_capacity,
            total_used_gb=total_personal_used,
            total_available_gb=total_personal_available,
            usage_percentage=personal_usage_percentage,
            accounts=accounts,  # Include all accounts but with type distinction
            workspace_summary={
                'count': len(workspace_accounts),
                'drive_usage_gb': total_workspace_drive_usage,
                'accounts': workspace_accounts
            } if workspace_accounts else None
        )
        
    except Exception as e:
        print(f"Storage info error: {e}")
        # Return empty storage info for workspace-only setups
        return StorageInfo(
            total_accounts=0,
            total_capacity_gb=0.0,
            total_used_gb=0.0,
            total_available_gb=0.0,
            usage_percentage=0.0,
            accounts=[],
            workspace_summary=None
        )

# File Management Endpoints - UPDATED FOR UNIFIED EXPERIENCE

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
    """
    ENHANCED: List all BrontoBox files (auto-discovered + uploaded)
    Now shows unified view across all accounts with original filenames
    """
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        storage_manager = app_state["storage_manager"]
        if not storage_manager:
            return {
                "success": True,
                "files": [],
                "total_files": 0,
                "message": "Storage manager not initialized"
            }
        
        # Get unified BrontoBox files (includes auto-discovered ones)
        files = storage_manager.get_unified_brontobox_files()
        
        return {
            "success": True,
            "files": files,
            "total_files": len(files),
            "auto_discovered": sum(1 for f in files if f.get('is_discovered', False)),
            "user_uploaded": sum(1 for f in files if not f.get('is_discovered', False))
        }
        
    except Exception as e:
        # Return empty list on error instead of failing
        return {
            "success": True,
            "files": [],
            "total_files": 0,
            "error": str(e),
            "note": "Could not load files - this may be normal for new vaults"
        }

@app.post("/files/refresh-discovery")
async def refresh_file_discovery():
    """
    NEW ENDPOINT: Manually refresh file discovery across all accounts
    Useful when user wants to refresh the file list
    """
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        storage_manager = app_state["storage_manager"]
        if not storage_manager:
            raise HTTPException(status_code=500, detail="Storage manager not initialized")
        
        # Refresh discovery
        old_count = len(storage_manager.stored_files)
        storage_manager.refresh_file_discovery()
        new_count = len(storage_manager.stored_files)
        
        await manager.broadcast({
            "type": "files_refreshed",
            "data": {
                "old_count": old_count,
                "new_count": new_count,
                "discovered": new_count - old_count
            }
        })
        
        return {
            "success": True,
            "message": "File discovery refreshed",
            "files_before": old_count,
            "files_after": new_count,
            "newly_discovered": max(0, new_count - old_count)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh discovery: {str(e)}")

@app.get("/files/statistics")
async def get_file_statistics():
    """
    NEW ENDPOINT: Get detailed file statistics
    Shows breakdown of discovered vs uploaded files
    """
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        storage_manager = app_state["storage_manager"]
        if not storage_manager:
            raise HTTPException(status_code=500, detail="Storage manager not initialized")
        
        files = storage_manager.get_unified_brontobox_files()
        
        # Calculate statistics
        total_files = len(files)
        discovered_files = [f for f in files if f.get('is_discovered', False)]
        uploaded_files = [f for f in files if not f.get('is_discovered', False)]
        
        total_size = sum(f['size_bytes'] for f in files)
        discovered_size = sum(f['size_bytes'] for f in discovered_files)
        uploaded_size = sum(f['size_bytes'] for f in uploaded_files)
        
        # Account distribution
        account_usage = {}
        for file_info in files:
            for account_id in file_info.get('accounts_used', []):
                if account_id not in account_usage:
                    account_usage[account_id] = {'files': 0, 'size_bytes': 0}
                account_usage[account_id]['files'] += 1
                account_usage[account_id]['size_bytes'] += file_info['size_bytes']
        
        return {
            "success": True,
            "statistics": {
                "total_files": total_files,
                "discovered_files": len(discovered_files),
                "uploaded_files": len(uploaded_files),
                "total_size_bytes": total_size,
                "total_size_gb": round(total_size / (1024**3), 2),
                "discovered_size_bytes": discovered_size,
                "uploaded_size_bytes": uploaded_size,
                "account_distribution": account_usage,
                "accounts_used": len(account_usage)
            },
            "message": f"Found {total_files} BrontoBox files across {len(account_usage)} accounts"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@app.get("/files/{file_id}/download")
async def download_file(file_id: str):
    """
    ENHANCED: Download original decrypted file
    Now works for both uploaded and auto-discovered files
    """
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
        
        # Retrieve file (handles both regular and discovered files)
        success = storage_manager.retrieve_file(file_id, output_path)
        
        if not success:
            shutil.rmtree(temp_dir)
            raise HTTPException(status_code=500, detail="Failed to retrieve file")
        
        # Special handling for discovered files
        if file_info.get('is_discovered'):
            print(f"Downloaded discovered file - may need manual verification")
        
        await manager.broadcast({
            "type": "file_downloaded",
            "data": {
                "file_id": file_id,
                "filename": file_info['name'],
                "is_discovered": file_info.get('is_discovered', False)
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

# Updated Drive Management Endpoints - NOW SHOWS BRONTOBOX FILES

@app.get("/drive/brontobox-files/{account_id}")
async def list_brontobox_files_for_account(account_id: str):
    """
    ENHANCED: List BrontoBox files for specific account
    Shows original filenames, not encrypted chunk names
    """
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        storage_manager = app_state["storage_manager"]
        if not storage_manager:
            raise HTTPException(status_code=500, detail="Storage manager not initialized")
        
        # Get all BrontoBox files
        all_files = storage_manager.get_unified_brontobox_files()
        
        # Filter files that use this account
        account_files = []
        for file_info in all_files:
            accounts_used = file_info.get('accounts_used', [])
            if account_id in accounts_used:
                # Add account-specific info
                file_copy = file_info.copy()
                file_copy['account_id'] = account_id
                file_copy['chunks_in_account'] = sum(
                    1 for chunk in storage_manager.stored_files[file_info['file_id']].chunks
                    if chunk['drive_account'] == account_id
                )
                account_files.append(file_copy)
        
        return {
            "success": True,
            "account_id": account_id,
            "files": account_files,
            "total_files": len(account_files),
            "view_type": "brontobox_files"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list BrontoBox files: {str(e)}")

@app.get("/drive/raw-chunks/{account_id}")
async def list_raw_chunks(account_id: str):
    """
    TECHNICAL VIEW: List raw encrypted chunks (for advanced users)
    This shows the actual encrypted files stored in Google Drive
    """
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        storage_manager = app_state["storage_manager"]
        if not storage_manager:
            raise HTTPException(status_code=500, detail="Storage manager not initialized")
        
        drive_client = storage_manager.drive_client
        
        # List raw chunks
        chunks = drive_client.list_chunks(account_id=account_id)
        chunks_data = [chunk.to_dict() for chunk in chunks]
        
        return {
            "success": True,
            "account_id": account_id,
            "chunks": chunks_data,
            "total_chunks": len(chunks_data),
            "view_type": "raw_chunks",
            "warning": "These are encrypted chunks - use BrontoBox files view for normal operation"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list raw chunks: {str(e)}")

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
        vault = app_state["vault"]
        
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
        
        # Save updated accounts to vault-specific file
        if refreshed_accounts and vault and vault.vault_id:
            encrypted_accounts = auth_manager.save_accounts_to_vault()
            accounts_file = get_accounts_file_path(vault.vault_id)
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
        vault = app_state.get("vault")
        vault_id = vault.vault_id if vault else None
        
        vault_registry_exists = os.path.exists(get_vault_registry_path())
        accounts_file_exists = os.path.exists(get_accounts_file_path(vault_id)) if vault_id else False
        registry_file_exists = os.path.exists(get_registry_file_path(vault_id)) if vault_id else False
        
        vault_unlocked = app_state["vault_unlocked"]
        accounts_loaded = len(app_state["auth_manager"].accounts) if app_state["auth_manager"] else 0
        files_loaded = len(app_state["storage_manager"].stored_files) if app_state["storage_manager"] else 0
        
        return {
            "success": True,
            "persistence_status": {
                "vault_registry_saved": vault_registry_exists,
                "accounts_saved": accounts_file_exists,
                "file_registry_saved": registry_file_exists,
                "vault_currently_unlocked": vault_unlocked,
                "current_vault_id": vault_id,
                "accounts_loaded": accounts_loaded,
                "files_loaded": files_loaded
            },
            "ready_for_lock_unlock": vault_registry_exists and accounts_file_exists,
            "message": "All components properly persisted" if (vault_registry_exists and accounts_file_exists) else "Some components not persisted"
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

# Data Management Endpoints

@app.get("/data/export-registry")
async def export_file_registry():
    """
    Export encrypted file registry for backup
    Returns downloadable file with all file metadata
    """
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        storage_manager = app_state["storage_manager"]
        vault = app_state["vault"]
        
        if not storage_manager or not vault:
            raise HTTPException(status_code=500, detail="Storage manager or vault not initialized")
        
        # Get encrypted registry
        encrypted_registry = storage_manager.save_file_registry()
        
        # Create export data with metadata
        export_data = {
            "export_type": "brontobox_file_registry",
            "vault_id": vault.vault_id,
            "exported_at": datetime.now().isoformat(),
            "brontobox_version": "1.0.0",
            "total_files": len(storage_manager.stored_files),
            "encrypted_registry": encrypted_registry
        }
        
        # Create temporary file for download
        temp_dir = tempfile.mkdtemp()
        filename = f"brontobox_file_registry_{vault.vault_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        file_path = os.path.join(temp_dir, filename)
        
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/json'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export registry: {str(e)}")

@app.get("/data/backup-vault-info")
async def backup_vault_info():
    """
    Export vault information for backup (NO PRIVATE KEYS)
    Returns vault metadata and salt for vault recovery
    """
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        vault = app_state["vault"]
        if not vault:
            raise HTTPException(status_code=500, detail="Vault not initialized")
        
        # Load vault from registry
        vault_info = load_vault_from_registry(vault.vault_id)
        
        if not vault_info:
            raise HTTPException(status_code=404, detail="Vault information not found")
        
        # Create backup data (SAFE - no private keys)
        backup_data = {
            "backup_type": "brontobox_vault_info",
            "vault_id": vault.vault_id,
            "salt": vault_info["salt"],
            "verification_data": vault_info["verification_data"],
            "created_at": vault_info.get("created_at"),
            "version": vault_info.get("version", "1.0"),
            "exported_at": datetime.now().isoformat(),
            "brontobox_version": "1.0.0",
            "instructions": "Keep this file safe! You need the salt and your master password to unlock your vault.",
            "warning": "This file does NOT contain your master password or private keys."
        }
        
        # Create temporary file for download
        temp_dir = tempfile.mkdtemp()
        filename = f"brontobox_vault_backup_{vault.vault_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        file_path = os.path.join(temp_dir, filename)
        
        with open(file_path, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/json'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to backup vault info: {str(e)}")

@app.post("/data/clear-all")
async def clear_all_data():
    """
    DANGER: Clear all BrontoBox data
    Removes all files from Google Drive, deletes accounts, and clears vault
    """
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        storage_manager = app_state["storage_manager"]
        vault = app_state["vault"]
        
        if not storage_manager or not vault:
            raise HTTPException(status_code=500, detail="Storage manager or vault not initialized")
        
        vault_id = vault.vault_id
        deletion_results = {
            "vault_id": vault_id,
            "files_deleted": 0,
            "accounts_cleared": 0,
            "files_failed": 0,
            "errors": []
        }
        
        # Step 1: Delete all files from Google Drive
        print(f"Starting complete data deletion for vault {vault_id}")
        
        for file_id, stored_file in storage_manager.stored_files.items():
            try:
                print(f"Deleting file: {stored_file.original_name}")
                success = storage_manager.delete_file(file_id)
                if success:
                    deletion_results["files_deleted"] += 1
                else:
                    deletion_results["files_failed"] += 1
                    deletion_results["errors"].append(f"Failed to delete file: {stored_file.original_name}")
            except Exception as e:
                deletion_results["files_failed"] += 1
                deletion_results["errors"].append(f"Error deleting {stored_file.original_name}: {str(e)}")
        
        # Step 2: Clear account data
        auth_manager = app_state["auth_manager"]
        if auth_manager:
            deletion_results["accounts_cleared"] = len(auth_manager.accounts)
            auth_manager.accounts.clear()
        
        # Step 3: Remove vault-specific files
        try:
            accounts_file = get_accounts_file_path(vault_id)
            registry_file = get_registry_file_path(vault_id)
            
            if os.path.exists(accounts_file):
                os.remove(accounts_file)
                print(f"Removed accounts file: {accounts_file}")
            
            if os.path.exists(registry_file):
                os.remove(registry_file)
                print(f"Removed registry file: {registry_file}")
                
        except Exception as e:
            deletion_results["errors"].append(f"Error removing vault files: {str(e)}")
        
        # Step 4: Remove vault from registry
        try:
            registry_path = get_vault_registry_path()
            if os.path.exists(registry_path):
                with open(registry_path, 'r') as f:
                    registry = json.load(f)
                
                if vault_id in registry.get("vaults", {}):
                    del registry["vaults"][vault_id]
                    
                    with open(registry_path, 'w') as f:
                        json.dump(registry, f, indent=2)
                    
                    print(f"Removed vault {vault_id} from registry")
                    
        except Exception as e:
            deletion_results["errors"].append(f"Error updating vault registry: {str(e)}")
        
        # Step 5: Lock vault and clear app state
        vault.lock_vault()
        app_state["vault"] = None
        app_state["auth_manager"] = None
        app_state["storage_manager"] = None
        app_state["vault_unlocked"] = False
        
        print(f"Data deletion complete: {deletion_results['files_deleted']} files deleted, {deletion_results['accounts_cleared']} accounts cleared")
        
        await manager.broadcast({
            "type": "data_cleared",
            "data": deletion_results
        })
        
        return {
            "success": True,
            "message": "All data cleared successfully",
            "deletion_results": deletion_results,
            "note": "Vault has been locked. You will need to unlock or create a new vault."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {str(e)}")

@app.post("/data/import-registry")
async def import_file_registry(file: UploadFile = File(...)):
    """
    Import file registry from backup
    Restores file metadata from exported registry file
    """
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        storage_manager = app_state["storage_manager"]
        vault = app_state["vault"]
        
        if not storage_manager or not vault:
            raise HTTPException(status_code=500, detail="Storage manager or vault not initialized")
        
        # Read uploaded file
        content = await file.read()
        import_data = json.loads(content.decode('utf-8'))
        
        # Validate import data
        if import_data.get("export_type") != "brontobox_file_registry":
            raise HTTPException(status_code=400, detail="Invalid registry file format")
        
        # Check if vault ID matches (optional - could be from different vault)
        imported_vault_id = import_data.get("vault_id")
        current_vault_id = vault.vault_id
        
        if imported_vault_id != current_vault_id:
            print(f"Warning: Importing registry from different vault ({imported_vault_id} → {current_vault_id})")
        
        # Load the encrypted registry
        encrypted_registry = import_data["encrypted_registry"]
        success = storage_manager.load_file_registry(encrypted_registry)
        
        if success:
            files_imported = len(storage_manager.stored_files)
            
            # Auto-save the imported registry
            save_file_registry_to_disk()
            
            return {
                "success": True,
                "message": "File registry imported successfully",
                "files_imported": files_imported,
                "imported_from_vault": imported_vault_id,
                "imported_at": import_data.get("exported_at")
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to decrypt imported registry - may be from incompatible vault")
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import registry: {str(e)}")

@app.get("/data/system-info")
async def get_system_info():
    """
    Get comprehensive system information for troubleshooting
    """
    try:
        vault = app_state.get("vault")
        auth_manager = app_state.get("auth_manager")
        storage_manager = app_state.get("storage_manager")
        
        # Count files
        files_count = len(storage_manager.stored_files) if storage_manager else 0
        accounts_count = len(auth_manager.accounts) if auth_manager else 0
        
        # Check file existence
        vault_id = vault.vault_id if vault else None
        files_status = {}
        
        if vault_id:
            files_status = {
                "vault_registry": os.path.exists(get_vault_registry_path()),
                "accounts_file": os.path.exists(get_accounts_file_path(vault_id)),
                "registry_file": os.path.exists(get_registry_file_path(vault_id))
            }
        
        system_info = {
            "brontobox_version": "1.0.0",
            "vault_status": {
                "unlocked": app_state["vault_unlocked"],
                "vault_id": vault_id,
                "has_vault": vault is not None
            },
            "data_status": {
                "files_in_memory": files_count,
                "accounts_configured": accounts_count,
                "persistent_files": files_status
            },
            "api_status": {
                "server_running": True,
                "endpoints_available": [
                    "/files/list", "/files/upload", "/files/download",
                    "/accounts/list", "/accounts/authenticate",
                    "/storage/info", "/vault/status"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "system_info": system_info
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Vault Restore & Import Endpoints

@app.get("/backup/detect")
async def detect_backup_files():
    """
    Auto-detect backup files in the current directory
    """
    try:
        current_dir = os.getcwd()
        detected_backups = {
            "vault_backups": [],
            "registry_backups": [],
            "directory": current_dir
        }
        
        print(f"Scanning directory: {current_dir}")
        
        # Scan for backup files with flexible pattern matching
        for filename in os.listdir(current_dir):
            print(f"Checking file: {filename}")
            
            # Check for vault backup files (both patterns)
            is_vault_backup = (
                filename.startswith("brontobox_vault_backup") and filename.endswith(".json")
            )
            
            # Check for registry backup files (both patterns)  
            is_registry_backup = (
                filename.startswith("brontobox_file_registry") and filename.endswith(".json")
            )
            
            if is_vault_backup:
                try:
                    with open(filename, 'r') as f:
                        backup_data = json.load(f)
                    
                    if backup_data.get("backup_type") == "brontobox_vault_info":
                        detected_backups["vault_backups"].append({
                            "filename": filename,
                            "vault_id": backup_data.get("vault_id"),
                            "created_at": backup_data.get("created_at"),
                            "exported_at": backup_data.get("exported_at"),
                            "file_path": os.path.join(current_dir, filename)
                        })
                        print(f"Detected vault backup: {filename}")
                    else:
                        print(f"File {filename} is not a valid vault backup")
                except Exception as e:
                    print(f"Could not read vault backup file {filename}: {e}")
            
            elif is_registry_backup:
                try:
                    with open(filename, 'r') as f:
                        registry_data = json.load(f)
                    
                    if registry_data.get("export_type") == "brontobox_file_registry":
                        detected_backups["registry_backups"].append({
                            "filename": filename,
                            "vault_id": registry_data.get("vault_id"),
                            "total_files": registry_data.get("total_files"),
                            "exported_at": registry_data.get("exported_at"),
                            "file_path": os.path.join(current_dir, filename)
                        })
                        print(f"Detected registry backup: {filename}")
                    else:
                        print(f"File {filename} is not a valid registry backup")
                except Exception as e:
                    print(f"Could not read registry backup file {filename}: {e}")
        
        print(f"Detection complete: {len(detected_backups['vault_backups'])} vault, {len(detected_backups['registry_backups'])} registry")
        
        return {
            "success": True,
            "detected_backups": detected_backups,
            "vault_count": len(detected_backups["vault_backups"]),
            "registry_count": len(detected_backups["registry_backups"])
        }
        
    except Exception as e:
        print(f"Backup detection failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "detected_backups": {"vault_backups": [], "registry_backups": []}
        }

@app.post("/vault/restore-from-backup")
async def restore_vault_from_backup(backup_file: str, master_password: str):
    """
    Restore vault from backup file
    Uses backup file + master password to recreate vault access
    """
    try:
        # Read backup file
        if not os.path.exists(backup_file):
            raise HTTPException(status_code=404, detail="Backup file not found")
        
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        # Validate backup file
        if backup_data.get("backup_type") != "brontobox_vault_info":
            raise HTTPException(status_code=400, detail="Invalid backup file format")
        
        vault_id = backup_data["vault_id"]
        salt = backup_data["salt"]
        verification_data = backup_data["verification_data"]
        
        print(f"Restoring vault from backup: {vault_id}")
        
        # Initialize vault with backup data
        vault = VaultCore()
        
        # Try to unlock with provided password and backed up salt/verification
        success = vault.unlock_vault(master_password, salt, verification_data)
        
        if not success:
            raise HTTPException(status_code=401, detail="Invalid master password for this vault backup")
        
        # Initialize auth manager and storage manager
        auth_manager = GoogleAuthManager(vault)
        storage_manager = BrontoBoxStorageManager(vault, auth_manager)
        
        # Store in global state
        app_state["vault"] = vault
        app_state["auth_manager"] = auth_manager
        app_state["storage_manager"] = storage_manager
        app_state["vault_unlocked"] = True
        
        # Add vault back to registry
        vault_data = {
            "vault_id": vault_id,
            "salt": salt,
            "verification_data": verification_data,
            "created_at": backup_data.get("created_at", datetime.now().isoformat()),
            "version": backup_data.get("version", "1.0")
        }
        
        save_vault_to_registry(vault_id, vault_data)
        
        print(f"Vault restored successfully: {vault_id}")
        
        await manager.broadcast({
            "type": "vault_restored",
            "data": {"vault_id": vault_id, "status": "Vault restored from backup"}
        })
        
        return {
            "success": True,
            "message": "Vault restored successfully from backup",
            "vault_id": vault_id,
            "created_at": backup_data.get("created_at"),
            "note": "You can now import your file registry to restore your files"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restore vault: {str(e)}")

@app.post("/data/import-registry-from-file")
async def import_registry_from_file(registry_file: str):
    """
    Import file registry from local backup file
    Automatically loads registry from detected backup file
    """
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        # Read registry file
        if not os.path.exists(registry_file):
            raise HTTPException(status_code=404, detail="Registry file not found")
        
        with open(registry_file, 'r') as f:
            import_data = json.load(f)
        
        # Validate registry file
        if import_data.get("export_type") != "brontobox_file_registry":
            raise HTTPException(status_code=400, detail="Invalid registry file format")
        
        storage_manager = app_state["storage_manager"]
        vault = app_state["vault"]
        
        if not storage_manager or not vault:
            raise HTTPException(status_code=500, detail="Storage manager or vault not initialized")
        
        # Check vault compatibility
        imported_vault_id = import_data.get("vault_id")
        current_vault_id = vault.vault_id
        
        if imported_vault_id != current_vault_id:
            print(f"Warning: Importing registry from different vault ({imported_vault_id} → {current_vault_id})")
        
        # Load the encrypted registry
        encrypted_registry = import_data["encrypted_registry"]
        success = storage_manager.load_file_registry(encrypted_registry)
        
        if success:
            files_imported = len(storage_manager.stored_files)
            
            # Auto-save the imported registry to vault-specific file
            save_file_registry_to_disk()
            
            print(f"Registry imported: {files_imported} files loaded")
            
            await manager.broadcast({
                "type": "registry_imported",
                "data": {"files_imported": files_imported}
            })
            
            return {
                "success": True,
                "message": "File registry imported successfully",
                "files_imported": files_imported,
                "imported_from_vault": imported_vault_id,
                "imported_at": import_data.get("exported_at")
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to decrypt imported registry - vault keys may be incompatible")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import registry: {str(e)}")

@app.get("/restore/analyze-missing-accounts")
async def analyze_missing_accounts():
    """
    Analyze which accounts are needed for file access after restore
    """
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        storage_manager = app_state["storage_manager"]
        auth_manager = app_state["auth_manager"]
        
        if not storage_manager:
            raise HTTPException(status_code=500, detail="Storage manager not initialized")
        
        # Get currently connected accounts
        connected_accounts = set()
        if auth_manager:
            accounts = auth_manager.list_accounts()
            connected_accounts = {acc['account_id'] for acc in accounts if acc['is_active']}
        
        # Analyze all files to find required accounts
        required_accounts = set()
        file_account_map = {}
        inaccessible_files = []
        
        for file_id, stored_file in storage_manager.stored_files.items():
            file_accounts = set()
            for chunk in stored_file.chunks:
                account_id = chunk['drive_account']
                required_accounts.add(account_id)
                file_accounts.add(account_id)
            
            file_account_map[file_id] = {
                'file_name': stored_file.original_name,
                'required_accounts': list(file_accounts),
                'accessible_accounts': list(file_accounts & connected_accounts),
                'missing_accounts': list(file_accounts - connected_accounts),
                'is_accessible': file_accounts.issubset(connected_accounts)
            }
            
            if not file_accounts.issubset(connected_accounts):
                inaccessible_files.append({
                    'file_id': file_id,
                    'file_name': stored_file.original_name,
                    'missing_accounts': list(file_accounts - connected_accounts)
                })
        
        missing_accounts = required_accounts - connected_accounts
        
        return {
            "success": True,
            "analysis": {
                "total_files": len(storage_manager.stored_files),
                "total_required_accounts": len(required_accounts),
                "connected_accounts": len(connected_accounts),
                "missing_accounts": len(missing_accounts),
                "inaccessible_files": len(inaccessible_files),
                "accessibility_percentage": round((len(storage_manager.stored_files) - len(inaccessible_files)) / len(storage_manager.stored_files) * 100, 1) if storage_manager.stored_files else 100
            },
            "details": {
                "connected_account_ids": list(connected_accounts),
                "missing_account_ids": list(missing_accounts),
                "inaccessible_files": inaccessible_files[:10],  # Show first 10
                "file_accessibility": file_account_map
            },
            "recommendations": [
                f"Add {len(missing_accounts)} missing Google account(s) to access all files",
                "Use the same Google accounts you used when originally uploading files",
                "Look for existing .brontobox_storage folders in your Google Drives"
            ] if missing_accounts else [
                "All required accounts are connected! Files should be accessible."
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/restore/complete-restoration")
async def complete_restoration(request: RestoreRequest):
    """
    COMPLETE RESTORATION: Restore vault + import registry in one operation
    """
    try:
        print(f"Starting complete restoration...")
        print(f"Vault backup: {request.vault_backup_file}")
        print(f"Registry backup: {request.registry_backup_file}")
        
        # Step 1: Restore vault from backup
        print(f"Step 1: Restoring vault from {request.vault_backup_file}")
        
        # Read and validate vault backup
        if not os.path.exists(request.vault_backup_file):
            raise HTTPException(status_code=404, detail="Vault backup file not found")
        
        with open(request.vault_backup_file, 'r') as f:
            backup_data = json.load(f)
        
        if backup_data.get("backup_type") != "brontobox_vault_info":
            raise HTTPException(status_code=400, detail="Invalid vault backup file")
        
        vault_id = backup_data["vault_id"]
        salt = backup_data["salt"]
        verification_data = backup_data["verification_data"]
        
        # Initialize and unlock vault
        vault = VaultCore()
        success = vault.unlock_vault(request.master_password, salt, verification_data)
        
        if not success:
            raise HTTPException(status_code=401, detail="Invalid master password for vault backup")
        
        # Initialize managers
        auth_manager = GoogleAuthManager(vault)
        storage_manager = BrontoBoxStorageManager(vault, auth_manager)
        
        # Store in global state
        app_state["vault"] = vault
        app_state["auth_manager"] = auth_manager
        app_state["storage_manager"] = storage_manager
        app_state["vault_unlocked"] = True
        
        # Add vault to registry
        vault_data = {
            "vault_id": vault_id,
            "salt": salt,
            "verification_data": verification_data,
            "created_at": backup_data.get("created_at", datetime.now().isoformat()),
            "version": backup_data.get("version", "1.0")
        }
        save_vault_to_registry(vault_id, vault_data)
        
        print(f"Step 1 complete: Vault {vault_id} restored")
        
        # Step 2: Import file registry (if provided)
        files_imported = 0
        if request.registry_backup_file and os.path.exists(request.registry_backup_file):
            print(f"Step 2: Importing registry from {request.registry_backup_file}")
            
            with open(request.registry_backup_file, 'r') as f:
                registry_data = json.load(f)
            
            if registry_data.get("export_type") == "brontobox_file_registry":
                encrypted_registry = registry_data["encrypted_registry"]
                registry_success = storage_manager.load_file_registry(encrypted_registry)
                
                if registry_success:
                    files_imported = len(storage_manager.stored_files)
                    save_file_registry_to_disk()
                    print(f"Step 2 complete: {files_imported} files imported")
                else:
                    print(f"Step 2 warning: Could not decrypt registry (vault mismatch?)")
        
        await manager.broadcast({
            "type": "complete_restoration",
            "data": {
                "vault_id": vault_id,
                "files_imported": files_imported,
                "status": "Complete restoration successful"
            }
        })
        
        return {
            "success": True,
            "message": "Complete restoration successful!",
            "restoration_summary": {
                "vault_id": vault_id,
                "vault_restored": True,
                "files_imported": files_imported,
                "registry_restored": files_imported > 0,
                "ready_to_use": True
            },
            "next_steps": [
                "Add your Google accounts to access files",
                "Run file discovery to find existing files",
                "Your BrontoBox is ready to use!"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Complete restoration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Complete restoration failed: {str(e)}")

@app.get("/restore/check-compatibility") 
async def check_backup_compatibility(vault_backup: str, registry_backup: str = None):
    """
    Check if backup files are compatible with each other
    Validates backup files before attempting restoration
    """
    try:
        compatibility_info = {
            "vault_backup": {"valid": False, "details": {}},
            "registry_backup": {"valid": False, "details": {}},
            "compatible": False,
            "issues": []
        }
        
        # Check vault backup
        if os.path.exists(vault_backup):
            try:
                with open(vault_backup, 'r') as f:
                    vault_data = json.load(f)
                
                if vault_data.get("backup_type") == "brontobox_vault_info":
                    compatibility_info["vault_backup"]["valid"] = True
                    compatibility_info["vault_backup"]["details"] = {
                        "vault_id": vault_data.get("vault_id"),
                        "created_at": vault_data.get("created_at"),
                        "version": vault_data.get("version", "1.0")
                    }
                else:
                    compatibility_info["issues"].append("Vault backup file has invalid format")
            except Exception as e:
                compatibility_info["issues"].append(f"Cannot read vault backup: {str(e)}")
        else:
            compatibility_info["issues"].append("Vault backup file not found")
        
        # Check registry backup (optional)
        if registry_backup and os.path.exists(registry_backup):
            try:
                with open(registry_backup, 'r') as f:
                    registry_data = json.load(f)
                
                if registry_data.get("export_type") == "brontobox_file_registry":
                    compatibility_info["registry_backup"]["valid"] = True
                    compatibility_info["registry_backup"]["details"] = {
                        "vault_id": registry_data.get("vault_id"),
                        "total_files": registry_data.get("total_files"),
                        "exported_at": registry_data.get("exported_at")
                    }
                    
                    # Check if vault IDs match
                    vault_id = compatibility_info["vault_backup"]["details"].get("vault_id")
                    registry_vault_id = registry_data.get("vault_id")
                    
                    if vault_id != registry_vault_id:
                        compatibility_info["issues"].append(f"Vault ID mismatch: vault={vault_id}, registry={registry_vault_id}")
                else:
                    compatibility_info["issues"].append("Registry backup file has invalid format")
            except Exception as e:
                compatibility_info["issues"].append(f"Cannot read registry backup: {str(e)}")
        
        # Determine overall compatibility
        compatibility_info["compatible"] = (
            compatibility_info["vault_backup"]["valid"] and 
            len(compatibility_info["issues"]) == 0
        )
        
        return {
            "success": True,
            "compatibility": compatibility_info
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "compatibility": None
        }

@app.post("/restore/fix-account-mapping")
async def fix_account_mapping():
    """
    Fix account ID mismatches after restore
    Maps old account IDs in file metadata to current account IDs
    """
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        storage_manager = app_state["storage_manager"]
        auth_manager = app_state["auth_manager"]
        
        if not storage_manager or not auth_manager:
            raise HTTPException(status_code=500, detail="Managers not initialized")
        
        # Get current accounts
        current_accounts = auth_manager.list_accounts()
        current_emails = {acc['email']: acc['account_id'] for acc in current_accounts if acc['is_active']}
        
        print(f"Current accounts: {list(current_emails.keys())}")
        
        # Get all old account IDs from file metadata
        old_account_ids = set()
        for stored_file in storage_manager.stored_files.values():
            for chunk in stored_file.chunks:
                old_account_ids.add(chunk['drive_account'])
        
        print(f"Old account IDs in files: {list(old_account_ids)}")
        
        # Try to map old account IDs to current ones
        # Strategy: Check if chunks actually exist in current accounts
        account_mapping = {}
        chunks_remapped = 0
        
        for old_account_id in old_account_ids:
            best_match = None
            
            # Try each current account to see if it has chunks for this old account
            for email, current_account_id in current_emails.items():
                try:
                    # Try to list chunks in this account to see if it has old data
                    chunks = storage_manager.drive_client.list_chunks(current_account_id)
                    
                    # Check if any chunks match what we expect from the old account
                    has_matching_chunks = False
                    for stored_file in storage_manager.stored_files.values():
                        for chunk_info in stored_file.chunks:
                            if chunk_info['drive_account'] == old_account_id:
                                # Look for this chunk in the current account
                                drive_file_id = chunk_info['drive_file_id']
                                matching_chunk = next((c for c in chunks if c.file_id == drive_file_id), None)
                                if matching_chunk:
                                    has_matching_chunks = True
                                    break
                        if has_matching_chunks:
                            break
                    
                    if has_matching_chunks:
                        best_match = current_account_id
                        print(f"Mapped {old_account_id} → {current_account_id} ({email})")
                        break
                        
                except Exception as e:
                    print(f"Could not check account {current_account_id}: {e}")
                    continue
            
            if best_match:
                account_mapping[old_account_id] = best_match
            else:
                print(f"No match found for old account {old_account_id}")
        
        # Apply the mapping to all files
        if account_mapping:
            print(f"Applying account mapping: {account_mapping}")
            
            for stored_file in storage_manager.stored_files.values():
                for chunk in stored_file.chunks:
                    old_id = chunk['drive_account']
                    if old_id in account_mapping:
                        chunk['drive_account'] = account_mapping[old_id]
                        chunks_remapped += 1
                
                # Update metadata
                if 'accounts_used' in stored_file.metadata:
                    new_accounts = []
                    for old_id in stored_file.metadata['accounts_used']:
                        new_accounts.append(account_mapping.get(old_id, old_id))
                    stored_file.metadata['accounts_used'] = new_accounts
            
            # Save the updated file registry
            save_file_registry_to_disk()
            
            print(f"Account mapping complete: {chunks_remapped} chunks remapped")
            
            await manager.broadcast({
                "type": "account_mapping_fixed",
                "data": {"chunks_remapped": chunks_remapped, "mapping": account_mapping}
            })
            
            return {
                "success": True,
                "message": "Account mapping fixed successfully",
                "account_mapping": account_mapping,
                "chunks_remapped": chunks_remapped,
                "old_accounts": list(old_account_ids),
                "current_accounts": list(current_emails.keys())
            }
        else:
            return {
                "success": False,
                "message": "No account mapping could be established",
                "old_accounts": list(old_account_ids),
                "current_accounts": list(current_emails.keys()),
                "suggestion": "Make sure you've added the same Google accounts you used originally"
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Account mapping failed: {str(e)}")

@app.post("/restore/guide-account-recovery")
async def guide_account_recovery():
    """
    Provide step-by-step guidance for account recovery after restore
    """
    try:
        # Get missing account analysis
        analysis_response = await analyze_missing_accounts()
        analysis = analysis_response["analysis"]
        details = analysis_response["details"]
        
        # Generate personalized guidance
        steps = []
        
        if analysis["missing_accounts"] > 0:
            steps.extend([
                {
                    "step": 1,
                    "title": "Add Missing Google Accounts",
                    "description": f"You need to re-authenticate {analysis['missing_accounts']} Google account(s)",
                    "action": "Click 'Add Account' in the sidebar",
                    "details": f"Missing accounts: {', '.join(details['missing_account_ids'][:3])}{'...' if len(details['missing_account_ids']) > 3 else ''}"
                },
                {
                    "step": 2,
                    "title": "Use the Same Google Accounts",
                    "description": "Authenticate the same Google accounts you used originally",
                    "action": "Sign in with the Google accounts that have your files",
                    "details": "Look for accounts that contain .brontobox_storage folders"
                },
                {
                    "step": 3,
                    "title": "Verify File Access",
                    "description": "Once accounts are added, your files should become downloadable",
                    "action": "Try downloading a file to test",
                    "details": f"{analysis['inaccessible_files']} files are currently inaccessible"
                }
            ])
        else:
            steps.append({
                "step": 1,
                "title": "All Accounts Connected!",
                "description": "All required Google accounts are connected",
                "action": "Your files should be accessible for download",
                "details": f"{analysis['total_files']} files are ready to download"
            })
        
        return {
            "success": True,
            "recovery_guide": {
                "current_status": f"{analysis['accessibility_percentage']}% of files are accessible",
                "accounts_needed": analysis["missing_accounts"],
                "files_affected": analysis["inaccessible_files"],
                "steps": steps
            },
            "quick_actions": [
                {
                    "action": "add_account",
                    "label": "Add Google Account",
                    "endpoint": "/accounts/authenticate",
                    "urgent": analysis["missing_accounts"] > 0
                },
                {
                    "action": "test_download",
                    "label": "Test File Download", 
                    "endpoint": "/files/{file_id}/download",
                    "urgent": False
                }
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recovery guide failed: {str(e)}")

@app.get("/restore/status")
async def get_restore_status():
    """
    Get current restoration status including account connectivity
    """
    if not app_state["vault_unlocked"]:
        return {"unlocked": False, "restoration_complete": False}
    
    try:
        # Check if this appears to be a restored vault
        vault = app_state["vault"]
        storage_manager = app_state["storage_manager"]
        auth_manager = app_state["auth_manager"]
        
        is_likely_restored = False
        has_imported_files = False
        
        if storage_manager:
            # Check if we have files marked as imported
            for stored_file in storage_manager.stored_files.values():
                if stored_file.metadata.get('imported_from_registry'):
                    is_likely_restored = True
                    has_imported_files = True
                    break
        
        # Get account analysis if we have imported files
        account_analysis = None
        if has_imported_files:
            try:
                analysis_response = await analyze_missing_accounts()
                account_analysis = analysis_response["analysis"]
            except:
                pass
        
        return {
            "unlocked": True,
            "is_likely_restored": is_likely_restored,
            "has_imported_files": has_imported_files,
            "vault_id": vault.vault_id if vault else None,
            "account_analysis": account_analysis,
            "restoration_complete": account_analysis["accessibility_percentage"] == 100 if account_analysis else True,
            "needs_account_setup": account_analysis["missing_accounts"] > 0 if account_analysis else False
        }
        
    except Exception as e:
        return {
            "unlocked": True,
            "error": str(e),
            "restoration_complete": False
        }

@app.post("/restore/validate-password")
async def validate_restore_password(request: RestoreRequest):
    """
    Validate master password for vault backup WITHOUT doing full restoration
    This prevents misleading users with wrong passwords
    """
    try:
        print(f"Validating password for vault backup: {request.vault_backup_file}")
        
        # Read and validate vault backup
        if not os.path.exists(request.vault_backup_file):
            raise HTTPException(status_code=404, detail="Vault backup file not found")
        
        with open(request.vault_backup_file, 'r') as f:
            backup_data = json.load(f)
        
        if backup_data.get("backup_type") != "brontobox_vault_info":
            raise HTTPException(status_code=400, detail="Invalid vault backup file")
        
        vault_id = backup_data["vault_id"]
        salt = backup_data["salt"]
        verification_data = backup_data["verification_data"]
        
        # Create temporary vault instance for validation only
        temp_vault = VaultCore()
        
        # Try to unlock with provided password and backed up salt/verification
        success = temp_vault.unlock_vault(request.master_password, salt, verification_data)
        
        if not success:
            print(f"Password validation failed for vault {vault_id}")
            raise HTTPException(status_code=401, detail="Invalid master password for this vault backup")
        
        print(f"Password validation successful for vault {vault_id}")
        
        # Immediately lock the temp vault (we don't want to keep it unlocked)
        temp_vault.lock_vault()
        
        return {
            "success": True,
            "message": "Password validated successfully",
            "vault_id": vault_id,
            "validation_timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Password validation error: {e}")
        raise HTTPException(status_code=500, detail=f"Password validation failed: {str(e)}")

@app.get("/debug/file/{file_id}")
async def debug_file_info(file_id: str):
    """Debug endpoint to check file metadata and download capability"""
    if not app_state["vault_unlocked"]:
        return {"error": "Vault not unlocked"}
    
    try:
        storage_manager = app_state["storage_manager"]
        if not storage_manager:
            return {"error": "Storage manager not initialized"}
        
        if file_id not in storage_manager.stored_files:
            return {"error": f"File {file_id} not found"}
        
        stored_file = storage_manager.stored_files[file_id]
        
        # Check chunk accessibility
        accessible_chunks = 0
        chunk_details = []
        
        for chunk_info in stored_file.chunks:
            try:
                # Try to get chunk info without downloading
                drive_account = chunk_info['drive_account']
                drive_file_id = chunk_info['drive_file_id']
                
                # Check if account exists
                auth_manager = app_state["auth_manager"]
                account_exists = drive_account in [acc['account_id'] for acc in auth_manager.list_accounts()]
                
                chunk_details.append({
                    "chunk_index": chunk_info['chunk_index'],
                    "drive_account": drive_account,
                    "drive_file_id": drive_file_id,
                    "account_accessible": account_exists,
                    "chunk_size": chunk_info.get('chunk_size', 'unknown')
                })
                
                if account_exists:
                    accessible_chunks += 1
                    
            except Exception as e:
                chunk_details.append({
                    "chunk_index": chunk_info.get('chunk_index', 'unknown'),
                    "error": str(e)
                })
        
        return {
            "file_id": file_id,
            "file_name": stored_file.original_name,
            "file_size": stored_file.original_size,
            "total_chunks": len(stored_file.chunks),
            "accessible_chunks": accessible_chunks,
            "metadata": {
                "discovered_from_chunks": stored_file.metadata.get('discovered_from_chunks', False),
                "imported_from_registry": stored_file.metadata.get('imported_from_registry', False),
                "has_encrypted_manifest": 'encrypted_manifest' in stored_file.metadata,
                "has_chunk_size": 'chunk_size' in stored_file.metadata,
                "accounts_used": stored_file.metadata.get('accounts_used', [])
            },
            "chunk_details": chunk_details,
            "download_feasible": accessible_chunks == len(stored_file.chunks),
            "recommended_method": "normal" if 'encrypted_manifest' in stored_file.metadata else "reconstruction"
        }
        
    except Exception as e:
        return {"error": f"Debug failed: {str(e)}"}

@app.get("/debug/files")
async def debug_files():
    """Debug endpoint to check file detection"""
    import os
    current_dir = os.getcwd()
    files = os.listdir(current_dir)
    
    vault_files = [f for f in files if f.startswith("brontobox_vault_backup")]
    registry_files = [f for f in files if f.startswith("brontobox_file_registry")]
    
    return {
        "directory": current_dir,
        "all_files": files,
        "vault_files": vault_files,
        "registry_files": registry_files
    }

@app.get("/debug/account-comparison")
async def debug_account_comparison():
    """
    Compare old account IDs vs current account IDs for debugging
    """
    if not app_state["vault_unlocked"]:
        return {"error": "Vault not unlocked"}
    
    try:
        storage_manager = app_state["storage_manager"]
        auth_manager = app_state["auth_manager"]
        
        # Current accounts
        current_accounts = auth_manager.list_accounts() if auth_manager else []
        current_account_info = [
            {
                "account_id": acc['account_id'],
                "email": acc['email'],
                "is_active": acc['is_active']
            }
            for acc in current_accounts
        ]
        
        # Old account IDs from files
        old_account_ids = set()
        file_account_details = {}
        
        if storage_manager:
            for file_id, stored_file in storage_manager.stored_files.items():
                file_accounts = []
                for chunk in stored_file.chunks:
                    old_account_id = chunk['drive_account']
                    old_account_ids.add(old_account_id)
                    file_accounts.append({
                        "chunk_index": chunk['chunk_index'],
                        "old_account_id": old_account_id,
                        "drive_file_id": chunk['drive_file_id']
                    })
                
                file_account_details[file_id] = {
                    "file_name": stored_file.original_name,
                    "chunks": file_accounts
                }
        
        return {
            "current_accounts": current_account_info,
            "old_account_ids": list(old_account_ids),
            "file_account_details": file_account_details,
            "mismatch_detected": len(old_account_ids) > 0 and not any(
                acc['account_id'] in old_account_ids for acc in current_accounts
            )
        }
        
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/accounts/{account_id}/storage-debug")
async def debug_account_storage(account_id: str):
    """
    Debug endpoint to analyze storage quota for any account type
    """
    if not app_state["vault_unlocked"]:
        raise HTTPException(status_code=401, detail="Vault must be unlocked first")
    
    try:
        auth_manager = app_state["auth_manager"]
        
        # Get debug storage info
        debug_info = auth_manager.debug_storage_quota(account_id)
        
        return {
            "success": True,
            "debug_info": debug_info,
            "recommendations": {
                "workspace_account": [
                    "Google Workspace accounts show organization storage, not individual quotas",
                    "BrontoBox will use Drive usage only for workspace accounts",
                    "Consider adding personal Google accounts for predictable 15GB quotas",
                    "Workspace accounts are still useful for BrontoBox storage"
                ],
                "personal_account": [
                    "Personal accounts provide reliable 15GB storage quotas", 
                    "Perfect for BrontoBox distributed storage strategy",
                    "Add up to 4 personal accounts for 60GB total capacity"
                ]
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "account_id": account_id
        }

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
    print("Starting BrontoBox API Server with Enhanced Security & Unified File Experience...")
    print("Vault authentication: SECURE")
    print("File discovery: AUTO-ENABLED")
    print("Unified file view: ACTIVE")
    print("WebSocket: ws://localhost:8000/ws")
    print("API Docs: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )
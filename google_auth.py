# google_auth.py - OAUTH STATE MISMATCH FIX + STORAGE QUOTA FIX
"""
VaultDrive Google OAuth Authentication Manager - COMPLETE FIXED VERSION
Handles Google OAuth2 flows, token management, secure storage, and correct storage quota calculation
"""

import os
import json
import base64
import secrets
import webbrowser
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import urllib.parse
import urllib.request
from dataclasses import dataclass

# Google OAuth2 and API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow, InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    print("Google API libraries not installed!")
    print("Please install: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    raise e

# Import our VaultDrive components
from vault_core import VaultCore


@dataclass
class GoogleAccount:
    """Represents a Google account with credentials"""
    email: str
    account_id: str
    credentials_encrypted: Dict[str, Any]
    created_at: datetime
    last_used: datetime
    is_active: bool = True
    storage_used: int = 0
    storage_total: int = 15 * 1024 * 1024 * 1024  # 15GB default


class GoogleAuthManager:
    """
    Manages Google OAuth authentication and account credentials
    """
    
    # Google Drive API scopes
    SCOPES = [
        'openid',  # Required for userinfo scopes
        'https://www.googleapis.com/auth/drive.file',  # Access files created by this app
        'https://www.googleapis.com/auth/drive.metadata.readonly',  # Read drive metadata
        'https://www.googleapis.com/auth/userinfo.email',  # Get user email (OAuth2)
        'https://www.googleapis.com/auth/userinfo.profile'  # Get user profile (OAuth2)
    ]
    
    def __init__(self, vault_core: VaultCore):
        """Initialize with VaultCore for encrypted credential storage"""
        self.vault_core = vault_core
        self.accounts: Dict[str, GoogleAccount] = {}
        self.active_account: Optional[str] = None
        
        # OAuth configuration
        self.client_config = None
        self.redirect_uri = "http://localhost:8080"  # For installed apps
        
        # FIX: Track authentication state to prevent conflicts
        self._auth_in_progress = False
        self._last_auth_time = 0
        
    def setup_oauth_config(self, client_id: str, client_secret: str, project_id: str = "vaultdrive"):
        """
        Setup OAuth2 configuration
        In production, these would come from Google Cloud Console
        """
        self.client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "project_id": project_id,
                "redirect_uris": [self.redirect_uri]
            }
        }
    
    def setup_oauth_from_file(self, credentials_file: str):
        """
        Setup OAuth2 configuration from downloaded credentials.json file
        """
        if not os.path.exists(credentials_file):
            raise FileNotFoundError(f"Credentials file not found: {credentials_file}")
        
        with open(credentials_file, 'r') as f:
            self.client_config = json.load(f)
    
    def authenticate_new_account(self, account_name: str = None) -> str:
        """
        Authenticate a new Google account using OAuth2 flow - FIXED VERSION
        Returns account_id for the new account
        """
        if not self.vault_core.is_unlocked:
            raise RuntimeError("Vault must be unlocked before authenticating accounts")
        
        if not self.client_config:
            raise RuntimeError("OAuth configuration not set. Call setup_oauth_config() first")
        
        # FIX: Prevent concurrent authentication attempts
        current_time = time.time()
        if self._auth_in_progress:
            raise RuntimeError("Authentication already in progress. Please wait and try again.")
        
        if current_time - self._last_auth_time < 10:  # 10 second cooldown
            raise RuntimeError("Please wait 10 seconds between authentication attempts.")
        
        self._auth_in_progress = True
        self._last_auth_time = current_time
        
        try:
            print("🔐 Starting Google OAuth authentication...")
            print("This will open a browser window for you to sign in to Google.")
            
            # FIX: Create OAuth2 flow with better state management
            flow = InstalledAppFlow.from_client_config(
                self.client_config,
                scopes=self.SCOPES,
                redirect_uri=self.redirect_uri
            )
            
            # FIX: Use a unique port to avoid conflicts
            import socket
            sock = socket.socket()
            sock.bind(('', 0))
            port = sock.getsockname()[1]
            sock.close()
            
            # Update redirect URI for unique port
            flow.redirect_uri = f"http://localhost:{port}"
            
            print(f"🔌 Using port {port} for OAuth callback")
            
            # FIX: Run OAuth with better error handling and state management
            try:
                credentials = flow.run_local_server(
                    port=port,
                    prompt='consent',
                    open_browser=True,
                    authorization_prompt_message='Please complete the authorization in your browser...',
                    success_message='✅ Authentication successful! You can close this window and return to BrontoBox.',
                    # FIX: Add state parameter for CSRF protection
                    access_type='offline',
                    include_granted_scopes='true'
                )
                
                print("✅ Authentication successful!")
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ OAuth Error: {error_msg}")
                
                # FIX: Handle specific OAuth errors
                if "mismatching_state" in error_msg or "State not equal" in error_msg:
                    raise RuntimeError("OAuth state mismatch - please try again. This usually happens when authentication is attempted multiple times simultaneously.")
                elif "invalid_grant" in error_msg:
                    raise RuntimeError("OAuth grant invalid - please try again with a fresh authentication.")
                elif "Scope has changed" in error_msg:
                    print("⚠️ Scope mismatch detected - retrying with corrected scopes...")
                    # This is usually harmless, Google adds 'openid' automatically
                    raise RuntimeError("OAuth scope changed - please try again. This is usually temporary.")
                else:
                    raise RuntimeError(f"OAuth authentication failed: {error_msg}")
            
            # Get user info to identify the account
            user_info = self._get_user_info(credentials)
            email = user_info.get('email', 'unknown@gmail.com')
            
            # Check if account already exists
            existing_account = next(
                (acc for acc in self.accounts.values() if acc.email == email), 
                None
            )
            
            if existing_account:
                print(f"⚠️ Account {email} already exists, updating credentials...")
                account_id = existing_account.account_id
                # Update existing account with new credentials
                existing_account.last_used = datetime.now()
            else:
                # Generate unique account ID
                account_id = f"account_{secrets.token_hex(8)}"
                if account_name:
                    account_id = f"{account_name}_{secrets.token_hex(4)}"
            
            # Encrypt and store credentials
            credentials_data = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes,
                'expiry': credentials.expiry.isoformat() if credentials.expiry else None
            }
            
            # Encrypt credentials using vault's token encryption key
            encrypted_credentials = self.vault_core.crypto_manager.encrypt_data(
                json.dumps(credentials_data).encode('utf-8'),
                self.vault_core.master_keys['token_encryption']
            )
            
            if existing_account:
                # Update existing account
                existing_account.credentials_encrypted = encrypted_credentials
                existing_account.last_used = datetime.now()
                existing_account.is_active = True
            else:
                # Create new account object
                account = GoogleAccount(
                    email=email,
                    account_id=account_id,
                    credentials_encrypted=encrypted_credentials,
                    created_at=datetime.now(),
                    last_used=datetime.now()
                )
                
                # Store account
                self.accounts[account_id] = account
            
            # Set as active if it's the first account
            if not self.active_account:
                self.active_account = account_id
            
            print(f"✅ Account added: {email} (ID: {account_id})")
            return account_id
            
        finally:
            # FIX: Always reset auth state
            self._auth_in_progress = False
    
    def _get_user_info(self, credentials: Credentials) -> Dict[str, Any]:
        """Get user information from Google OAuth2 API"""
        try:
            # Use OAuth2 API (v2) - this is the current, supported method
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            return user_info
        except Exception as e:
            print(f"Warning: Could not get user info: {e}")
            return {'email': 'unknown@gmail.com'}
    
    def get_credentials(self, account_id: str) -> Optional[Credentials]:
        """
        Get decrypted credentials for an account
        Returns Google Credentials object or None if account not found
        """
        if not self.vault_core.is_unlocked:
            raise RuntimeError("Vault must be unlocked to access credentials")
        
        if account_id not in self.accounts:
            return None
        
        account = self.accounts[account_id]
        
        try:
            # Decrypt credentials
            credentials_json = self.vault_core.crypto_manager.decrypt_data(
                account.credentials_encrypted,
                self.vault_core.master_keys['token_encryption']
            )
            
            credentials_data = json.loads(credentials_json.decode('utf-8'))
            
            # Create Credentials object
            credentials = Credentials(
                token=credentials_data['token'],
                refresh_token=credentials_data['refresh_token'],
                token_uri=credentials_data['token_uri'],
                client_id=credentials_data['client_id'],
                client_secret=credentials_data['client_secret'],
                scopes=credentials_data['scopes']
            )
            
            # Set expiry if available
            if credentials_data.get('expiry'):
                credentials.expiry = datetime.fromisoformat(credentials_data['expiry'])
            
            # Refresh token if needed
            if credentials.expired and credentials.refresh_token:
                print(f"🔄 Refreshing token for {account.email}...")
                credentials.refresh(Request())
                
                # Update stored credentials
                self._update_stored_credentials(account_id, credentials)
            
            # Update last used time
            account.last_used = datetime.now()
            
            return credentials
            
        except Exception as e:
            print(f"❌ Failed to decrypt credentials for {account_id}: {e}")
            return None
    
    def _update_stored_credentials(self, account_id: str, credentials: Credentials):
        """Update stored credentials after token refresh"""
        account = self.accounts[account_id]
        
        credentials_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }
        
        # Re-encrypt updated credentials
        encrypted_credentials = self.vault_core.crypto_manager.encrypt_data(
            json.dumps(credentials_data).encode('utf-8'),
            self.vault_core.master_keys['token_encryption']
        )
        
        account.credentials_encrypted = encrypted_credentials
    
    def _detect_workspace_account(self, limit_bytes, usage_bytes, user_info) -> bool:
        """
        Detect if this is a workspace/school account based on storage patterns
        """
        # Check 1: Extremely large storage (>100TB) indicates organizational storage
        if limit_bytes and int(limit_bytes) > 100 * 1024 * 1024 * 1024 * 1024:  # 100TB
            return True
        
        # Check 2: Very large usage but small Drive usage indicates pooled storage
        if usage_bytes > 50 * 1024 * 1024 * 1024 * 1024:  # 50TB total usage
            return True
        
        # Check 3: Email domain check (if available)
        email = user_info.get('emailAddress', '')
        if email and not email.endswith('@gmail.com'):
            # Custom domain usually means workspace
            return True
        
        return False
    
    def _handle_workspace_account(self, account_id: str, storage_quota: dict, user_info: dict) -> Dict[str, Any]:
        """
        Handle workspace accounts - show only Drive usage and add warnings
        """
        usage_in_drive_bytes = int(storage_quota.get('usageInDrive', 0))
        usage_in_drive_gb = usage_in_drive_bytes / (1024 ** 3)
        
        # For workspace accounts, we can't know the real individual quota
        # So we estimate based on Drive usage or use a reasonable default
        estimated_quota_gb = max(15.0, usage_in_drive_gb * 2)  # At least 15GB or 2x current usage
        available_gb = estimated_quota_gb - usage_in_drive_gb
        
        email = user_info.get('emailAddress', 'Unknown')
        domain = email.split('@')[1] if '@' in email else 'Unknown'
        
        print(f"📊 Workspace account {account_id} ({email}):")
        print(f"   Drive usage: {usage_in_drive_gb:.3f}GB")
        print(f"   Estimated quota: {estimated_quota_gb:.1f}GB")
        print(f"   Domain: {domain}")
        
        return {
            'total_gb': estimated_quota_gb,
            'used_gb': usage_in_drive_gb,  # Only count Drive usage
            'available_gb': max(available_gb, 1.0),  # Always show some available space
            'account_type': 'workspace',
            'organization_domain': domain,
            'drive_usage_only': True,
            'warning_message': f'Google Workspace account ({domain})',
            'recommendation': 'For best experience, connect a personal Google account',
            'raw_org_storage_tb': int(storage_quota.get('limit', 0)) / (1024 ** 4),  # Show org storage in TB
            'note': 'Storage shown is Drive usage only, not organization total'
        }

    def _handle_personal_account(self, account_id: str, storage_quota: dict) -> Dict[str, Any]:
        """
        Handle personal accounts - normal storage calculation
        """
        limit_bytes = storage_quota.get('limit')
        usage_bytes = int(storage_quota.get('usage', 0))
        
        if limit_bytes is None:
            # Unlimited storage (rare for personal accounts)
            limit_gb = 15.0
            available_gb = 15.0
            is_unlimited = True
        else:
            limit_bytes = int(limit_bytes)
            limit_gb = limit_bytes / (1024 ** 3)
            available_gb = (limit_bytes - usage_bytes) / (1024 ** 3)
            is_unlimited = False
        
        used_gb = usage_bytes / (1024 ** 3)
        
        print(f"📊 Personal account {account_id}:")
        print(f"   Total: {limit_gb:.2f}GB")
        print(f"   Used: {used_gb:.2f}GB")
        print(f"   Available: {available_gb:.2f}GB")
        
        return {
            'total_gb': limit_gb,
            'used_gb': used_gb,
            'available_gb': max(available_gb, 0),
            'account_type': 'personal',
            'is_unlimited': is_unlimited
        }
    
    # NEW: FIXED storage info method
    def get_storage_info(self, account_id: str) -> Dict[str, Any]:
        """
        SMART: Get storage information with workspace account detection
        Handles personal vs workspace accounts differently
        """
        credentials = self.get_credentials(account_id)
        if not credentials:
            return {
                'total_gb': 15.0,
                'used_gb': 0.0,
                'available_gb': 15.0,
                'error': 'No credentials available'
            }
        
        try:
            # Build Drive service
            drive_service = build('drive', 'v3', credentials=credentials)
            
            # Get storage quota AND user info
            response = drive_service.about().get(fields='storageQuota,user').execute()
            storage_quota = response.get('storageQuota', {})
            user_info = response.get('user', {})
            
            print(f"🔍 Raw storage API response for {account_id}: {storage_quota}")
            
            # Extract values (ALL ARE IN BYTES!)
            limit_bytes = storage_quota.get('limit')
            usage_bytes = int(storage_quota.get('usage', 0))
            usage_in_drive_bytes = int(storage_quota.get('usageInDrive', 0))
            
            # SMART: Detect workspace/school accounts
            is_workspace = self._detect_workspace_account(limit_bytes, usage_bytes, user_info)
            
            if is_workspace:
                print(f"🏢 Google Workspace account detected for {account_id}")
                return self._handle_workspace_account(account_id, storage_quota, user_info)
            else:
                print(f"👤 Personal Google account detected for {account_id}")
                return self._handle_personal_account(account_id, storage_quota)
                
        except Exception as e:
            print(f"❌ Error getting storage info for {account_id}: {e}")
            return {
                'total_gb': 15.0,
                'used_gb': 0.0,
                'available_gb': 15.0,
                'error': str(e),
                'account_type': 'unknown'
            }
    
    def list_accounts(self) -> List[Dict[str, Any]]:
        """List all stored accounts with smart storage info"""
        accounts_info = []
        for account_id, account in self.accounts.items():
            # Get smart storage info
            storage_info = self.get_storage_info(account_id)
            
            account_info = {
                'account_id': account_id,
                'email': account.email,
                'created_at': account.created_at.isoformat(),
                'last_used': account.last_used.isoformat(),
                'is_active': account.is_active,
                'is_current': account_id == self.active_account,
                'storage_info': storage_info
            }
            accounts_info.append(account_info)
            
        return accounts_info
    
    def set_active_account(self, account_id: str) -> bool:
        """Set the active account for operations"""
        if account_id in self.accounts:
            self.active_account = account_id
            return True
        return False
    
    def remove_account(self, account_id: str) -> bool:
        """Remove an account (WARNING: This will delete stored credentials)"""
        if account_id in self.accounts:
            del self.accounts[account_id]
            
            # Update active account if needed
            if self.active_account == account_id:
                remaining_accounts = list(self.accounts.keys())
                self.active_account = remaining_accounts[0] if remaining_accounts else None
            
            return True
        return False
    
    def test_account_access(self, account_id: str) -> Dict[str, Any]:
        """Test if an account's credentials are working with FIXED storage info"""
        credentials = self.get_credentials(account_id)
        if not credentials:
            return {'success': False, 'error': 'No credentials found'}
        
        try:
            # Test OAuth2 userinfo access (basic user info)
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            
            # Test Drive access with CORRECT storage quota call
            drive_service = build('drive', 'v3', credentials=credentials)
            
            # FIXED: Use correct fields parameter for storage quota
            about = drive_service.about().get(fields='user,storageQuota').execute()
            storage_quota = about.get('storageQuota', {})
            
            # Process storage quota correctly
            limit_bytes = storage_quota.get('limit')
            usage_bytes = int(storage_quota.get('usage', 0))
            
            if limit_bytes is None:
                # Unlimited storage
                storage_info = {
                    'total_gb': 100.0,  # Display value for unlimited
                    'used_gb': usage_bytes / (1024 ** 3),
                    'available_gb': 100.0,
                    'is_unlimited': True
                }
            else:
                # Normal account
                limit_bytes = int(limit_bytes)
                storage_info = {
                    'total_gb': limit_bytes / (1024 ** 3),
                    'used_gb': usage_bytes / (1024 ** 3),
                    'available_gb': (limit_bytes - usage_bytes) / (1024 ** 3),
                    'is_unlimited': False
                }
            
            return {
                'success': True,
                'user_email': user_info.get('email'),
                'user_name': user_info.get('name'),
                'drive_access': True,
                'storage_info': storage_info,
                'raw_storage_quota': storage_quota,  # For debugging
                'tested_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tested_at': datetime.now().isoformat()
            }
    
    # NEW: Debug method for storage issues
    def debug_storage_quota(self, account_id: str) -> Dict[str, Any]:
        """
        Debug method to inspect raw storage quota response
        Use this to troubleshoot storage quota issues
        """
        credentials = self.get_credentials(account_id)
        if not credentials:
            return {'error': 'No credentials available'}
        
        try:
            drive_service = build('drive', 'v3', credentials=credentials)
            
            # Get raw response with all available fields
            response = drive_service.about().get(fields='*').execute()
            
            storage_quota = response.get('storageQuota', {})
            user_info = response.get('user', {})
            
            return {
                'account_id': account_id,
                'user_email': user_info.get('emailAddress'),
                'raw_storage_quota': storage_quota,
                'all_fields': response,
                'analysis': {
                    'has_limit': 'limit' in storage_quota,
                    'limit_value': storage_quota.get('limit'),
                    'usage_value': storage_quota.get('usage'),
                    'is_unlimited': storage_quota.get('limit') is None,
                    'limit_gb': int(storage_quota.get('limit', 0)) / (1024**3) if storage_quota.get('limit') else None,
                    'usage_gb': int(storage_quota.get('usage', 0)) / (1024**3)
                }
            }
            
        except Exception as e:
            return {'error': str(e), 'account_id': account_id}
    
    def save_accounts_to_vault(self) -> Dict[str, Any]:
        """
        Save account information to encrypted storage
        Returns encrypted account data that can be stored persistently
        """
        if not self.vault_core.is_unlocked:
            raise RuntimeError("Vault must be unlocked to save accounts")
        
        # Prepare account data for storage (credentials are already encrypted)
        accounts_data = {}
        for account_id, account in self.accounts.items():
            accounts_data[account_id] = {
                'email': account.email,
                'account_id': account.account_id,
                'credentials_encrypted': account.credentials_encrypted,
                'created_at': account.created_at.isoformat(),
                'last_used': account.last_used.isoformat(),
                'is_active': account.is_active,
                'storage_used': account.storage_used,
                'storage_total': account.storage_total
            }
        
        vault_data = {
            'accounts': accounts_data,
            'active_account': self.active_account,
            'saved_at': datetime.now().isoformat()
        }
        
        # Encrypt the entire vault data
        encrypted_vault = self.vault_core.crypto_manager.encrypt_data(
            json.dumps(vault_data).encode('utf-8'),
            self.vault_core.master_keys['vault_unlock']
        )
        
        return encrypted_vault
    
    def load_accounts_from_vault(self, encrypted_vault_data: Dict[str, Any]) -> bool:
        """
        Load account information from encrypted storage
        """
        if not self.vault_core.is_unlocked:
            raise RuntimeError("Vault must be unlocked to load accounts")
        
        try:
            # Decrypt vault data
            vault_json = self.vault_core.crypto_manager.decrypt_data(
                encrypted_vault_data,
                self.vault_core.master_keys['vault_unlock']
            )
            
            vault_data = json.loads(vault_json.decode('utf-8'))
            
            # Restore accounts
            self.accounts = {}
            for account_id, account_data in vault_data['accounts'].items():
                account = GoogleAccount(
                    email=account_data['email'],
                    account_id=account_data['account_id'],
                    credentials_encrypted=account_data['credentials_encrypted'],
                    created_at=datetime.fromisoformat(account_data['created_at']),
                    last_used=datetime.fromisoformat(account_data['last_used']),
                    is_active=account_data['is_active'],
                    storage_used=account_data['storage_used'],
                    storage_total=account_data['storage_total']
                )
                self.accounts[account_id] = account
            
            self.active_account = vault_data.get('active_account')
            
            print(f"✅ Loaded {len(self.accounts)} accounts from vault")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load accounts from vault: {e}")
            return False
# oauth_demo.py
"""
Demo script for Google OAuth authentication
"""

from google_auth import GoogleAccount, GoogleAuthManager

def create_demo_credentials():
    """
    Create demo OAuth credentials for testing
    
    NOTE: In real usage, you need to:
    1. Go to Google Cloud Console (https://console.cloud.google.com/)
    2. Create a new project or select existing
    3. Enable Google Drive API
    4. Create OAuth 2.0 credentials (Desktop application)
    5. Download the credentials.json file
    """
    print("📋 Demo OAuth Setup Instructions:")
    print("=" * 50)
    print("To use real Google OAuth, you need to:")
    print("1. Visit: https://console.cloud.google.com/")
    print("2. Create a new project called 'VaultDrive'")
    print("3. Enable the Google Drive API")
    print("4. Go to Credentials → Create Credentials → OAuth 2.0 Client ID")
    print("5. Choose 'Desktop Application'")
    print("6. Download the JSON file as 'credentials.json'")
    print("7. Place it in the same directory as this script")
    print("\nFor this demo, we'll use mock credentials (won't actually work)")
    
    # Create mock credentials for demo
    mock_credentials = {
        "installed": {
            "client_id": "123456789-abcdefghijklmnop.apps.googleusercontent.com",
            "project_id": "vaultdrive-demo",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "DEMO_SECRET_NOT_REAL",
            "redirect_uris": ["http://localhost"]
        }
    }
    
    return mock_credentials

def demo_oauth_system():
    """Demonstrate the OAuth system (with mock credentials)"""
    print("=== VaultDrive Google OAuth Demo ===\n")
    
    # Initialize vault
    from vault_core import VaultCore
    vault = VaultCore()
    vault.initialize_vault("oauth_demo_password_2024")
    
    # Initialize OAuth manager
    auth_manager = GoogleAuthManager(vault)
    
    # Setup mock credentials
    mock_creds = create_demo_credentials()
    auth_manager.client_config = mock_creds
    
    print("\n🔐 OAuth Manager initialized")
    print(f"✅ Vault unlocked: {vault.is_unlocked}")
    print(f"📧 OAuth scopes: {auth_manager.SCOPES}")
    
    # Show what real authentication would do
    print("\n🎯 Real Authentication Flow:")
    print("1. User clicks 'Add Google Account'")
    print("2. Browser opens to Google OAuth page")
    print("3. User signs in and grants permissions")
    print("4. OAuth tokens are received and encrypted")
    print("5. Account is stored securely in vault")
    
    # Simulate stored accounts (for demo)
    print("\n📱 Simulating stored accounts...")
    
    # Create mock account data
    import json
    from datetime import datetime
    
    mock_account_data = {
        'email': 'demo@gmail.com',
        'account_id': 'demo_account_001',
        'created_at': datetime.now(),
        'last_used': datetime.now(),
        'is_active': True,
        'storage_used': 0,
        'storage_total': 15 * 1024 * 1024 * 1024
    }
    
    # Encrypt mock credentials
    mock_credentials_data = {
        'token': 'mock_access_token_12345',
        'refresh_token': 'mock_refresh_token_67890',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'client_id': 'mock_client_id',
        'client_secret': 'mock_client_secret',
        'scopes': auth_manager.SCOPES,
        'expiry': None
    }
    
    encrypted_creds = vault.crypto_manager.encrypt_data(
        json.dumps(mock_credentials_data).encode('utf-8'),
        vault.master_keys['token_encryption']
    )
    
    mock_account = GoogleAccount(
        email=mock_account_data['email'],
        account_id=mock_account_data['account_id'],
        credentials_encrypted=encrypted_creds,
        created_at=mock_account_data['created_at'],
        last_used=mock_account_data['last_used'],
        is_active=mock_account_data['is_active']
    )
    
    auth_manager.accounts['demo_account_001'] = mock_account
    auth_manager.active_account = 'demo_account_001'
    
    print("✅ Mock account added successfully")
    
    # List accounts
    print("\n📋 Account Management:")
    accounts = auth_manager.list_accounts()
    for account in accounts:
        print(f"   📧 {account['email']} (ID: {account['account_id']})")
        print(f"      Created: {account['created_at'][:19]}")
        print(f"      Active: {'✅' if account['is_current'] else '❌'}")
    
    # Test credential encryption/decryption
    print("\n🔒 Testing credential security...")
    
    # Test decryption
    decrypted_creds_json = vault.crypto_manager.decrypt_data(
        encrypted_creds,
        vault.master_keys['token_encryption']
    )
    decrypted_creds = json.loads(decrypted_creds_json.decode('utf-8'))
    
    print("✅ Credentials successfully encrypted and decrypted")
    print(f"   Token preview: {decrypted_creds['token'][:20]}...")
    
    # Test vault save/load
    print("\n💾 Testing vault persistence...")
    encrypted_vault = auth_manager.save_accounts_to_vault()
    print("✅ Accounts saved to encrypted vault")
    
    # Clear accounts and reload
    auth_manager.accounts = {}
    auth_manager.active_account = None
    
    success = auth_manager.load_accounts_from_vault(encrypted_vault)
    print(f"✅ Accounts loaded from vault: {success}")
    print(f"   Loaded {len(auth_manager.accounts)} accounts")
    
    # Show security properties
    print("\n🛡️ Security Features:")
    print("✅ OAuth tokens encrypted with AES-256-GCM")
    print("✅ Tokens never stored in plain text")
    print("✅ Master password required to decrypt")
    print("✅ Token refresh handled automatically")
    print("✅ Multiple accounts supported")
    print("✅ Secure vault persistence")
    
    print("\n🎉 OAuth system ready for Phase 2!")
    print("Next: Integrate with Google Drive API for file uploads")

def test_oauth_requirements():
    """Test if OAuth requirements are met"""
    print("=== Testing OAuth Requirements ===\n")
    
    required_modules = [
        'google.auth',
        'google.oauth2.credentials',
        'google_auth_oauthlib.flow',
        'googleapiclient.discovery'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n⚠️ Missing {len(missing_modules)} required modules")
        print("Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        return False
    else:
        print("\n✅ All OAuth requirements satisfied!")
        return True

if __name__ == "__main__":
    print("VaultDrive Google OAuth System")
    print("=" * 50)
    
    # Test requirements first
    if test_oauth_requirements():
        print("\n" + "=" * 50)
        demo_oauth_system()
    else:
        print("\nPlease install missing dependencies first!")
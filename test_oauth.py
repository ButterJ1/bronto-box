# # test_oauth.py
# """
# Quick test for VaultDrive OAuth system
# Tests the authentication infrastructure without requiring real Google credentials
# """

# import json
# import os
# from datetime import datetime
# from vault_core import VaultCore
# from google_auth import GoogleAccount

# def test_oauth_installation():
#     """Test if OAuth dependencies are installed correctly"""
#     print("🔍 Testing OAuth Dependencies...")
    
#     required_modules = {
#         'google.auth': 'Google Auth Library',
#         'google.oauth2.credentials': 'OAuth2 Credentials',
#         'google_auth_oauthlib.flow': 'OAuth Flow Manager',
#         'googleapiclient.discovery': 'Google API Client'
#     }
    
#     results = {}
#     for module, description in required_modules.items():
#         try:
#             __import__(module)
#             print(f"✅ {description}")
#             results[module] = True
#         except ImportError as e:
#             print(f"❌ {description} - {e}")
#             results[module] = False
    
#     if all(results.values()):
#         print("\n🎉 All OAuth dependencies installed correctly!")
#         return True
#     else:
#         print("\n⚠️ Some dependencies missing. Install with:")
#         print("pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
#         return False

# def test_vault_integration():
#     """Test OAuth integration with VaultCore"""
#     print("\n🔐 Testing Vault Integration...")
    
#     # Test importing our OAuth system
#     try:
#         from google_auth import GoogleAuthManager, GoogleAccount
#         print("✅ OAuth system imports successfully")
#     except ImportError as e:
#         print(f"❌ OAuth system import failed: {e}")
#         return False
    
#     # Test vault creation and OAuth manager initialization
#     try:
#         vault = VaultCore()
#         vault.initialize_vault("test_password_oauth_2024")
#         print("✅ Vault initialized successfully")
        
#         auth_manager = GoogleAuthManager(vault)
#         print("✅ OAuth manager created successfully")
#         print(f"📋 OAuth scopes: {len(auth_manager.SCOPES)} configured")
        
#         return True, vault, auth_manager
#     except Exception as e:
#         print(f"❌ Vault integration failed: {e}")
#         return False, None, None

# def test_credential_encryption():
#     """Test credential encryption and storage"""
#     print("\n🔒 Testing Credential Encryption...")
    
#     success, vault, auth_manager = test_vault_integration()
#     if not success:
#         return False
    
#     # Create mock credential data
#     mock_credentials = {
#         'access_token': 'ya29.mock_access_token_abcdef123456',
#         'refresh_token': '1//mock_refresh_token_789xyz',
#         'token_uri': 'https://oauth2.googleapis.com/token',
#         'client_id': '123456789-mock.apps.googleusercontent.com',
#         'client_secret': 'mock_client_secret_abc123',
#         'scopes': ['https://www.googleapis.com/auth/drive.file'],
#         'expiry': '2024-12-31T23:59:59Z'
#     }
    
#     try:
#         # Test encryption
#         credentials_json = json.dumps(mock_credentials)
#         encrypted_creds = vault.crypto_manager.encrypt_data(
#             credentials_json.encode('utf-8'),
#             vault.master_keys['token_encryption']
#         )
#         print("✅ Credentials encrypted successfully")
        
#         # Test decryption
#         decrypted_json = vault.crypto_manager.decrypt_data(
#             encrypted_creds,
#             vault.master_keys['token_encryption']
#         )
#         decrypted_creds = json.loads(decrypted_json.decode('utf-8'))
        
#         # Verify data integrity
#         if decrypted_creds == mock_credentials:
#             print("✅ Credentials decrypted successfully")
#             print("✅ Data integrity verified")
#         else:
#             print("❌ Data integrity check failed")
#             return False
        
#         return True
        
#     except Exception as e:
#         print(f"❌ Credential encryption test failed: {e}")
#         return False

# def test_account_management():
#     """Test account creation and management"""
#     print("\n📱 Testing Account Management...")
    
#     success, vault, auth_manager = test_vault_integration()
#     if not success:
#         return False
    
#     try:
#         # Create mock accounts manually (simulating OAuth flow results)
#         mock_accounts = [
#             {
#                 'email': 'user1@gmail.com',
#                 'account_id': 'account_001',
#                 'credentials': {
#                     'access_token': 'mock_token_user1',
#                     'refresh_token': 'mock_refresh_user1',
#                     'token_uri': 'https://oauth2.googleapis.com/token',
#                     'client_id': 'mock_client_id',
#                     'client_secret': 'mock_client_secret',
#                     'scopes': auth_manager.SCOPES
#                 }
#             },
#             {
#                 'email': 'user2@gmail.com',
#                 'account_id': 'account_002',
#                 'credentials': {
#                     'access_token': 'mock_token_user2',
#                     'refresh_token': 'mock_refresh_user2',
#                     'token_uri': 'https://oauth2.googleapis.com/token',
#                     'client_id': 'mock_client_id',
#                     'client_secret': 'mock_client_secret',
#                     'scopes': auth_manager.SCOPES
#                 }
#             }
#         ]
        
#         # Add accounts to auth manager
#         for account_data in mock_accounts:
#             # Encrypt credentials
#             credentials_json = json.dumps(account_data['credentials'])
#             encrypted_creds = vault.crypto_manager.encrypt_data(
#                 credentials_json.encode('utf-8'),
#                 vault.master_keys['token_encryption']
#             )
            
#             # Create account object
#             account = GoogleAccount(
#                 email=account_data['email'],
#                 account_id=account_data['account_id'],
#                 credentials_encrypted=encrypted_creds,
#                 created_at=datetime.now(),
#                 last_used=datetime.now()
#             )
            
#             auth_manager.accounts[account_data['account_id']] = account
        
#         # Set active account
#         auth_manager.active_account = 'account_001'
        
#         print(f"✅ Created {len(auth_manager.accounts)} test accounts")
        
#         # Test account listing
#         accounts = auth_manager.list_accounts()
#         print("📋 Account List:")
#         for account in accounts:
#             print(f"   📧 {account['email']} ({'ACTIVE' if account['is_current'] else 'inactive'})")
        
#         # Test credential retrieval (this will work with mock data)
#         print("\n🔓 Testing credential retrieval...")
#         for account_id in auth_manager.accounts.keys():
#             # We can't actually create Google Credentials objects with mock data,
#             # but we can test the decryption part
#             account = auth_manager.accounts[account_id]
            
#             decrypted_json = vault.crypto_manager.decrypt_data(
#                 account.credentials_encrypted,
#                 vault.master_keys['token_encryption']
#             )
#             decrypted_creds = json.loads(decrypted_json.decode('utf-8'))
            
#             print(f"   ✅ {account.email}: Token retrieval successful")
        
#         return True
        
#     except Exception as e:
#         print(f"❌ Account management test failed: {e}")
#         return False

# def test_vault_persistence():
#     """Test saving and loading accounts from vault"""
#     print("\n💾 Testing Vault Persistence...")
    
#     success, vault, auth_manager = test_vault_integration()
#     if not success:
#         return False
    
#     # First create some test accounts (reuse from previous test)
#     test_account_management()
    
#     try:
#         # Test saving accounts
#         encrypted_vault = auth_manager.save_accounts_to_vault()
#         print("✅ Accounts saved to encrypted vault")
        
#         # Save to file for inspection
#         vault_file = "test_oauth_vault.json"
#         with open(vault_file, 'w') as f:
#             json.dump(encrypted_vault, f, indent=2)
#         print(f"✅ Vault data saved to {vault_file}")
        
#         # Clear accounts and test loading
#         original_account_count = len(auth_manager.accounts)
#         auth_manager.accounts = {}
#         auth_manager.active_account = None
        
#         print("🔄 Cleared accounts from memory")
        
#         # Load accounts back
#         success = auth_manager.load_accounts_from_vault(encrypted_vault)
#         if success and len(auth_manager.accounts) == original_account_count:
#             print("✅ Accounts loaded successfully from vault")
#             print(f"✅ Account count matches: {len(auth_manager.accounts)}")
#         else:
#             print("❌ Account loading failed")
#             return False
        
#         # Cleanup
#         if os.path.exists(vault_file):
#             os.remove(vault_file)
#             print("🧹 Cleaned up test files")
        
#         return True
        
#     except Exception as e:
#         print(f"❌ Vault persistence test failed: {e}")
#         return False

# def run_comprehensive_test():
#     """Run all OAuth system tests"""
#     print("=== VaultDrive OAuth System Test Suite ===\n")
    
#     tests = [
#         ("Dependencies", test_oauth_installation),
#         ("Vault Integration", lambda: test_vault_integration()[0]),
#         ("Credential Encryption", test_credential_encryption),
#         ("Account Management", test_account_management),
#         ("Vault Persistence", test_vault_persistence)
#     ]
    
#     results = {}
    
#     for test_name, test_func in tests:
#         try:
#             result = test_func()
#             results[test_name] = result
#             if result:
#                 print(f"\n✅ {test_name} test PASSED")
#             else:
#                 print(f"\n❌ {test_name} test FAILED")
#         except Exception as e:
#             print(f"\n❌ {test_name} test ERROR: {e}")
#             results[test_name] = False
        
#         print("-" * 50)
    
#     # Summary
#     passed = sum(results.values())
#     total = len(results)
    
#     print(f"\n🎯 Test Results: {passed}/{total} tests passed")
    
#     if passed == total:
#         print("🎉 ALL TESTS PASSED!")
#         print("\nOAuth system is ready! Next steps:")
#         print("1. Set up Google Cloud Console credentials")
#         print("2. Test with real Google authentication")
#         print("3. Move to Google Drive integration")
#     else:
#         print("⚠️ Some tests failed. Check the errors above.")
#         print("Common issues:")
#         print("- Missing dependencies: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
#         print("- File permissions or imports")
    
#     return passed == total

# if __name__ == "__main__":
#     run_comprehensive_test()

from vault_core import VaultCore
from google_auth import GoogleAuthManager

# Initialize vault
vault = VaultCore()
vault.initialize_vault("your_password")

# Initialize OAuth manager
auth_manager = GoogleAuthManager(vault)
auth_manager.setup_oauth_from_file("credentials.json")

# Authenticate new account (opens browser)
account_id = auth_manager.authenticate_new_account("main_account")

# Test the account
test_result = auth_manager.test_account_access(account_id)
print(test_result)
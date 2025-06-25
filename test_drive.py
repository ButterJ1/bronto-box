# test_drive.py
"""
Quick test for BrontoBox Google Drive integration
Tests upload/download with your authenticated Google account
"""

import os
import sys
import time
import json
import base64
import hashlib

def test_drive_operations():
    """Test BrontoBox Drive operations step by step"""
    print("🦕📦 === BrontoBox Drive Test === 📦🦕\n")
    
    # Check if we have the required files
    required_files = ['vault_core.py', 'google_auth.py', 'drive_client.py', 'credentials.json']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        if 'credentials.json' in missing_files:
            print("\n📋 To get credentials.json:")
            print("1. Go to Google Cloud Console")
            print("2. Create OAuth 2.0 Desktop credentials")
            print("3. Download as credentials.json")
        return False
    
    print("✅ All required files present")
    
    # Import BrontoBox components
    try:
        from vault_core import VaultCore
        from google_auth import GoogleAuthManager
        from drive_client import BrontoBoxDriveClient
        print("✅ BrontoBox components imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Step 1: Initialize vault
    print("\n🔐 Step 1: Initialize BrontoBox vault...")
    vault = VaultCore()
    
    # Check if we have existing vault info
    vault_info_file = "brontobox_vault_info.json"
    if os.path.exists(vault_info_file):
        print("📂 Loading existing vault...")
        try:
            with open(vault_info_file, 'r') as f:
                vault_info = json.load(f)
            
            success = vault.unlock_vault("brontobox_shared_vault_2024", vault_info['salt'])
            if success:
                print("✅ Vault unlocked with existing key")
            else:
                print("⚠️ Failed to unlock with existing key, creating new vault")
                vault_info = vault.initialize_vault("brontobox_shared_vault_2024")
        except Exception as e:
            print(f"⚠️ Error loading vault info: {e}")
            vault_info = vault.initialize_vault("brontobox_shared_vault_2024")
    else:
        print("🔐 Creating new vault...")
        vault_info = vault.initialize_vault("brontobox_shared_vault_2024")
    
    # Save vault info for future use
    try:
        with open(vault_info_file, 'w') as f:
            json.dump(vault_info, f)
        print("💾 Vault info saved for future sessions")
    except Exception as e:
        print(f"⚠️ Warning: Could not save vault info: {e}")
    
    print("✅ Vault ready")
    
    # Step 2: Setup OAuth
    print("\n📧 Step 2: Setup OAuth authentication...")
    auth_manager = GoogleAuthManager(vault)
    auth_manager.setup_oauth_from_file("credentials.json")
    
    # Try to load existing accounts first
    accounts_file = "brontobox_accounts.json"
    if os.path.exists(accounts_file):
        print("📂 Loading existing accounts...")
        try:
            with open(accounts_file, 'r') as f:
                encrypted_accounts = json.load(f)
            auth_manager.load_accounts_from_vault(encrypted_accounts)
        except Exception as e:
            print(f"⚠️ Error loading accounts: {e}")
    
    # Check for existing accounts
    accounts = auth_manager.list_accounts()
    if not accounts:
        print("📱 No Google accounts found. Please authenticate:")
        try:
            account_id = auth_manager.authenticate_new_account("test_account")
            print(f"✅ Account authenticated: {account_id}")
            
            # Save accounts for future use
            encrypted_accounts = auth_manager.save_accounts_to_vault()
            with open(accounts_file, 'w') as f:
                json.dump(encrypted_accounts, f)
            print(f"💾 Accounts saved to {accounts_file}")
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    else:
        account_id = accounts[0]['account_id']
        account_email = accounts[0]['email']
        print(f"✅ Using existing account: {account_email}")
    
    # Step 3: Initialize Drive client
    print("\n☁️ Step 3: Initialize Google Drive client...")
    drive_client = BrontoBoxDriveClient(auth_manager)
    
    # Test storage info
    storage_info = drive_client.get_storage_info(account_id)
    if 'error' in storage_info:
        print(f"❌ Storage info error: {storage_info['error']}")
        return False
    
    print(f"✅ Drive access confirmed")
    print(f"   📧 Account: {storage_info['user_email']}")
    print(f"   💾 Available: {storage_info['available_gb']:.2f} GB")
    print(f"   📊 Usage: {storage_info['usage_percentage']:.1f}%")
    
    if storage_info['available_gb'] < 0.1:  # Less than 100MB
        print("⚠️ Warning: Very low storage space available")
    
    # Step 4: Create test data
    print("\n📄 Step 4: Creating test data...")
    test_content = f"""
🦕 BrontoBox Drive Test File 🦕

This is a test file to verify Google Drive integration.
Created: {time.ctime()}
Random ID: {hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]}

Content:
{"=" * 50}
BrontoBox provides secure, distributed storage using multiple
Google Drive accounts with client-side encryption.

Your files are:
✅ Encrypted before upload
✅ Split into chunks
✅ Distributed across accounts  
✅ Completely private (even from Google)

Brontosaurus = Massive storage capacity
Box = Secure container
BrontoBox = Your personal secure cloud! 🦕📦
{"=" * 50}

End of test file.
""".strip()
    
    test_data_bytes = test_content.encode('utf-8')
    
    # 🔒 IMPORTANT: Encrypt the test data first!
    print("🔒 Encrypting test data...")
    encrypted_test_data = vault.crypto_manager.encrypt_data(
        test_data_bytes,
        vault.master_keys['file_encryption']
    )
    
    # Convert encrypted data to bytes for upload
    encrypted_bytes = base64.b64decode(encrypted_test_data['ciphertext'])
    
    chunk_name = f"brontobox_test_{int(time.time())}.enc"  # .enc extension for encrypted
    
    print(f"✅ Test data encrypted: {len(test_data_bytes)} → {len(encrypted_bytes)} bytes")
    print(f"   📄 Chunk name: {chunk_name}")
    print(f"   🔒 Now Google will see encrypted gibberish, not plain text!")
    
    # Step 5: Test upload
    print(f"\n⬆️ Step 5: Testing encrypted chunk upload...")
    try:
        drive_file = drive_client.upload_chunk(
            account_id=account_id,
            chunk_data=encrypted_bytes,  # Upload encrypted data
            chunk_name=chunk_name,
            metadata={
                'test_file': True,
                'brontobox_version': '1.0',
                'encrypted': True
            }  # Reduced metadata to stay under 124-byte limit
        )
        
        print(f"✅ Encrypted upload successful!")
        print(f"   📁 Drive File ID: {drive_file.file_id}")
        print(f"   📏 Encrypted size: {drive_file.size} bytes")
        print(f"   📅 Created: {drive_file.created_time}")
        print(f"   🔒 Google sees: Encrypted gibberish (not readable)")
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False
    
    # Step 6: Test download and decryption
    print(f"\n⬇️ Step 6: Testing chunk download and decryption...")
    try:
        downloaded_encrypted_data = drive_client.download_chunk(account_id, drive_file.file_id)
        
        # Verify encrypted data matches
        if downloaded_encrypted_data == encrypted_bytes:
            print("✅ Encrypted download successful - encrypted data matches!")
        else:
            print("❌ Encrypted download data mismatch!")
            return False
        
        # Now decrypt the downloaded data
        print("🔓 Decrypting downloaded data...")
        
        # Reconstruct the encrypted data structure
        decrypted_data = vault.crypto_manager.decrypt_data(
            {
                'ciphertext': base64.b64encode(downloaded_encrypted_data).decode('utf-8'),
                'nonce': encrypted_test_data['nonce'],
                'algorithm': encrypted_test_data['algorithm'],
                'key_id': encrypted_test_data['key_id']
            },
            vault.master_keys['file_encryption']
        )
        
        # Verify decrypted content matches original
        if decrypted_data == test_data_bytes:
            print("✅ Decryption successful - original content recovered!")
            print("✅ End-to-end encryption test PASSED!")
        else:
            print("❌ Decryption failed - content doesn't match!")
            return False
            
    except Exception as e:
        print(f"❌ Download/decryption failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 7: Test file listing
    print(f"\n📋 Step 7: Testing chunk listing...")
    try:
        chunks = drive_client.list_chunks(account_id)
        print(f"✅ Found {len(chunks)} BrontoBox chunks in account")
        
        # Show recent chunks
        recent_chunks = sorted(chunks, key=lambda x: x.created_time, reverse=True)[:3]
        for chunk in recent_chunks:
            print(f"   📄 {chunk.name} ({chunk.size} bytes)")
            
    except Exception as e:
        print(f"❌ Listing failed: {e}")
        return False
    
    # Step 8: Optional cleanup
    print(f"\n🗑️ Step 8: Cleanup test file...")
    cleanup = input("Delete test file from Google Drive? (y/n): ").lower().strip()
    
    if cleanup == 'y':
        try:
            success = drive_client.delete_chunk(account_id, drive_file.file_id)
            if success:
                print("✅ Test file deleted successfully")
            else:
                print("⚠️ Deletion may have failed")
        except Exception as e:
            print(f"❌ Cleanup error: {e}")
    else:
        print("📁 Test file kept in Google Drive")
    
    # Summary
    print(f"\n🎉 BrontoBox Drive Test Complete!")
    print("=" * 50)
    print("✅ Google Drive authentication working")
    print("✅ File upload to Drive working")
    print("✅ File download from Drive working")
    print("✅ File listing working")
    print("✅ Storage quota monitoring working")
    print("✅ Ready for full BrontoBox storage system!")
    print("🦕📦 BrontoBox Drive integration successful! 📦🦕")
    
    return True

def quick_storage_check():
    """Quick check of available storage across accounts"""
    print("🦕 BrontoBox Storage Check 🦕\n")
    
    try:
        from vault_core import VaultCore
        from google_auth import GoogleAuthManager
        from drive_client import BrontoBoxDriveClient
        
        # Check if we have saved vault and account info
        vault_info_file = "brontobox_vault_info.json"
        accounts_file = "brontobox_accounts.json"
        
        if not os.path.exists(vault_info_file) or not os.path.exists(accounts_file):
            print("📧 No saved accounts found")
            print("💡 Run 'python test_drive.py' (option 1) first to set up accounts")
            return
        
        # Load vault with existing salt
        with open(vault_info_file, 'r') as f:
            vault_info = json.load(f)
        
        vault = VaultCore()
        success = vault.unlock_vault("brontobox_shared_vault_2024", vault_info['salt'])
        
        if not success:
            print("❌ Failed to unlock vault")
            print("💡 Run 'python test_drive.py' (option 1) to reset accounts")
            return
        
        # Load accounts
        auth_manager = GoogleAuthManager(vault)
        auth_manager.setup_oauth_from_file("credentials.json")
        
        with open(accounts_file, 'r') as f:
            encrypted_accounts = json.load(f)
        
        success = auth_manager.load_accounts_from_vault(encrypted_accounts)
        if not success:
            print("❌ Failed to load accounts")
            print("💡 Run 'python test_drive.py' (option 1) to reset accounts")
            return
        
        accounts = auth_manager.list_accounts()
        if not accounts:
            print("📧 No active accounts found")
            return
        
        print(f"✅ Found {len(accounts)} BrontoBox account(s)")
        
        drive_client = BrontoBoxDriveClient(auth_manager)
        total_available = 0
        
        print("\n📊 Storage Summary:")
        print("-" * 40)
        
        for account in accounts:
            if account['is_active']:
                account_id = account['account_id']
                try:
                    storage_info = drive_client.get_storage_info(account_id)
                    
                    if 'error' not in storage_info:
                        total_available += storage_info['available_gb']
                        print(f"📧 {storage_info['user_email']}")
                        print(f"   💾 {storage_info['available_gb']:.2f} GB available")
                        print(f"   📊 {storage_info['usage_percentage']:.1f}% used")
                        print(f"   🗂️ Total: {storage_info['total_gb']:.2f} GB")
                        
                        # Check for BrontoBox files
                        chunks = drive_client.list_chunks(account_id)
                        if chunks:
                            total_size_mb = sum(chunk.size for chunk in chunks) / (1024**2)
                            print(f"   📦 BrontoBox chunks: {len(chunks)} files ({total_size_mb:.2f} MB)")
                        print()
                    else:
                        print(f"📧 {account['email']}")
                        print(f"   ❌ Error: {storage_info['error']}")
                        print()
                        
                except Exception as e:
                    print(f"📧 {account['email']}")
                    print(f"   ❌ Storage check failed: {e}")
                    print()
        
        if total_available > 0:
            print("=" * 40)
            print(f"🦕 Total BrontoBox Capacity: {total_available:.2f} GB")
            print(f"📦 Estimated files you can store:")
            print(f"   📄 ~{int(total_available * 1000)} documents (1MB each)")
            print(f"   📸 ~{int(total_available * 200)} photos (5MB each)")
            print(f"   🎵 ~{int(total_available * 250)} songs (4MB each)")
            print(f"   🎬 ~{int(total_available)} movies (1GB each)")
        
    except Exception as e:
        print(f"❌ Storage check failed: {e}")
        print("💡 Try running the full drive test first: python test_drive.py (option 1)")

if __name__ == "__main__":
    print("Choose test mode:")
    print("1. Full drive test (recommended)")
    print("2. Quick storage check")
    
    choice = input("\nEnter choice (1-2): ").strip()
    
    if choice == "2":
        quick_storage_check()
    else:
        success = test_drive_operations()
        if success:
            print("\n🚀 Ready for Phase 3: Multi-Account Distribution!")
        else:
            print("\n🔧 Please fix the issues above and try again.")
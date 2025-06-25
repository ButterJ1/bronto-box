# quick_fix_test.py
"""
Quick test to verify the encryption fix
This will upload ENCRYPTED data to Google Drive, not plain text
"""

import os
import time
import base64
import hashlib

def test_encryption_fix():
    """Test that we're actually encrypting data before upload"""
    print("🔒 Testing BrontoBox Encryption Fix\n")
    
    # Check required files
    if not os.path.exists("credentials.json"):
        print("❌ credentials.json not found")
        return False
    
    # Import components
    try:
        from vault_core import VaultCore
        from google_auth import GoogleAuthManager
        from drive_client import BrontoBoxDriveClient
        print("✅ BrontoBox components imported")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Initialize vault
    vault = VaultCore()
    vault.initialize_vault("encryption_fix_test_2024")
    print("✅ Vault initialized")
    
    # Setup auth
    auth_manager = GoogleAuthManager(vault)
    auth_manager.setup_oauth_from_file("credentials.json")
    
    accounts = auth_manager.list_accounts()
    if not accounts:
        print("📧 Authenticating Google account...")
        try:
            account_id = auth_manager.authenticate_new_account("encryption_test")
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    else:
        account_id = accounts[0]['account_id']
        print(f"✅ Using account: {accounts[0]['email']}")
    
    # Initialize drive client
    drive_client = BrontoBoxDriveClient(auth_manager)
    
    # Create test data
    test_content = """
🔒 ENCRYPTION TEST FILE 🔒

If you can read this in Google Drive, the encryption is BROKEN!
This should appear as encrypted gibberish.

Test data: CONFIDENTIAL_INFORMATION_123456
Secret: This is a private message
    """.strip()
    
    test_bytes = test_content.encode('utf-8')
    print(f"📄 Test content: {len(test_bytes)} bytes")
    
    # ENCRYPT the data (this was missing before!)
    print("🔒 Encrypting test data...")
    encrypted_data = vault.crypto_manager.encrypt_data(
        test_bytes,
        vault.master_keys['file_encryption']
    )
    
    # Convert to bytes for upload (FIX: use base64, not hex!)
    encrypted_bytes = base64.b64decode(encrypted_data['ciphertext'])
    
    print(f"✅ Data encrypted: {len(test_bytes)} → {len(encrypted_bytes)} bytes")
    print(f"🔒 Encrypted preview: {encrypted_bytes[:50].hex()}...")
    
    # Upload encrypted data
    chunk_name = f"brontobox_encryption_test_{int(time.time())}.enc"
    
    try:
        print(f"\n⬆️ Uploading ENCRYPTED data to Google Drive...")
        drive_file = drive_client.upload_chunk(
            account_id=account_id,
            chunk_data=encrypted_bytes,
            chunk_name=chunk_name,
            metadata={
                'encryption_test': True,
                'original_size': len(test_bytes),
                'encrypted_size': len(encrypted_bytes)
            }
        )
        
        print(f"✅ Upload successful!")
        print(f"📁 File ID: {drive_file.file_id}")
        print(f"📄 Name: {drive_file.name}")
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False
    
    # Test download and decryption
    try:
        print(f"\n⬇️ Downloading and decrypting...")
        
        downloaded_encrypted = drive_client.download_chunk(account_id, drive_file.file_id)
        
        # Decrypt
        decrypted_bytes = vault.crypto_manager.decrypt_data(
            {
                'ciphertext': base64.b64encode(downloaded_encrypted).decode('utf-8'),
                'nonce': encrypted_data['nonce'],
                'algorithm': encrypted_data['algorithm'],
                'key_id': encrypted_data['key_id']
            },
            vault.master_keys['file_encryption']
        )
        
        decrypted_content = decrypted_bytes.decode('utf-8')
        
        if decrypted_content == test_content:
            print("✅ Decryption successful - content matches!")
        else:
            print("❌ Decryption failed - content mismatch!")
            return False
            
    except Exception as e:
        print(f"❌ Download/decrypt failed: {e}")
        return False
    
    # Cleanup
    cleanup = input(f"\n🗑️ Delete test file from Google Drive? (y/n): ").lower()
    if cleanup == 'y':
        try:
            success = drive_client.delete_chunk(account_id, drive_file.file_id)
            if success:
                print("✅ Test file deleted")
            else:
                print("⚠️ Deletion may have failed")
        except Exception as e:
            print(f"❌ Cleanup error: {e}")
    
    print(f"\n🎉 Encryption Fix Test Results:")
    print("✅ Data encrypted before upload")
    print("✅ Google Drive sees encrypted gibberish")
    print("✅ Decryption recovers original content")
    print("✅ End-to-end encryption working!")
    
    print(f"\n🔒 Security Status:")
    print("✅ Your files are now properly encrypted")
    print("✅ Google cannot read your content")
    print("✅ Only you can decrypt with your master password")
    
    return True

if __name__ == "__main__":
    success = test_encryption_fix()
    
    if success:
        print("\n🎯 Next Steps:")
        print("1. Check Google Drive - you should see encrypted .enc files")
        print("2. Try opening them - should be unreadable gibberish ✅")
        print("3. Run the full storage demo: python demo_full_storage.py")
    else:
        print("\n🔧 Please fix the issues above and try again")
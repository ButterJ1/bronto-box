# demo_drive.py
"""
Demo script for BrontoBox Google Drive operations
Tests real file upload/download with your authenticated account
"""

import os
import hashlib
import time
from drive_client import BrontoBoxDriveClient

def test_drive_client():
    """Test the BrontoBox Drive client with real Google Drive"""
    print("=== BrontoBox Google Drive Client Demo ===\n")
    
    # Initialize system
    from vault_core import VaultCore
    from google_auth import GoogleAuthManager
    
    vault = VaultCore()
    
    # Use your existing vault or create new one
    try:
        # Try to unlock with a password (modify as needed)
        vault.initialize_vault("brontobox_demo_password_2024")
        print("🔐 Vault initialized")
    except Exception as e:
        print(f"Vault error: {e}")
        return
    
    # Initialize auth manager
    auth_manager = GoogleAuthManager(vault)
    
    # Setup OAuth (assumes you have credentials.json)
    if os.path.exists("credentials.json"):
        auth_manager.setup_oauth_from_file("credentials.json")
        print("✅ OAuth configured from credentials.json")
    else:
        print("❌ credentials.json not found")
        print("Please download OAuth credentials from Google Cloud Console")
        return
    
    # List existing accounts or authenticate new one
    accounts = auth_manager.list_accounts()
    if not accounts:
        print("📱 No accounts found. Authenticating new account...")
        account_id = auth_manager.authenticate_new_account("demo_account")
    else:
        account_id = accounts[0]['account_id']
        account_email = accounts[0]['email']
        print(f"📧 Using existing account: {account_email}")
    
    # Initialize Drive client
    drive_client = BrontoBoxDriveClient(auth_manager)
    
    # Test storage info
    print("\n📊 Testing storage information...")
    storage_info = drive_client.get_storage_info(account_id)
    if 'error' not in storage_info:
        print(f"   📧 Account: {storage_info['user_email']}")
        print(f"   💾 Total: {storage_info['total_gb']:.2f} GB")
        print(f"   📈 Used: {storage_info['used_gb']:.2f} GB ({storage_info['usage_percentage']:.1f}%)")
        print(f"   🆓 Available: {storage_info['available_gb']:.2f} GB")
    else:
        print(f"   ❌ Error: {storage_info['error']}")
        return
    
    # Create test data
    print("\n📄 Creating test encrypted chunk...")
    test_data = f"This is a BrontoBox encrypted chunk test! 🦕📦\n" * 100  # ~5KB
    chunk_name = f"brontobox_test_chunk_{int(time.time())}.enc"
    
    chunk_metadata = {
        'original_filename': 'test_document.txt',
        'chunk_index': 0,
        'total_chunks': 1,
        'file_hash': hashlib.sha256(test_data).hexdigest(),
        'created_by': 'BrontoBox Demo'
    }
    
    # Test upload
    print(f"\n⬆️ Testing chunk upload...")
    try:
        drive_file = drive_client.upload_chunk(
            account_id=account_id,
            chunk_data=test_data,
            chunk_name=chunk_name,
            metadata=chunk_metadata
        )
        
        print(f"✅ Upload successful!")
        print(f"   📁 File ID: {drive_file.file_id}")
        print(f"   📄 Name: {drive_file.name}")
        print(f"   📏 Size: {drive_file.size} bytes")
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return
    
    # Test download
    print(f"\n⬇️ Testing chunk download...")
    try:
        downloaded_data = drive_client.download_chunk(account_id, drive_file.file_id)
        
        if downloaded_data == test_data:
            print("✅ Download successful - data matches!")
        else:
            print("❌ Download data mismatch!")
            return
            
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return
    
    # Test listing chunks
    print(f"\n📋 Testing chunk listing...")
    try:
        chunks = drive_client.list_chunks(account_id)
        print(f"✅ Found {len(chunks)} chunks in account")
        
        for chunk in chunks[-3:]:  # Show last 3 chunks
            print(f"   📄 {chunk.name} ({chunk.size} bytes)")
            
    except Exception as e:
        print(f"❌ Listing failed: {e}")
    
    # Test cleanup (optional - uncomment to test deletion)
    print(f"\n🗑️ Testing chunk deletion...")
    try:
        success = drive_client.delete_chunk(account_id, drive_file.file_id)
        if success:
            print("✅ Test chunk deleted successfully")
        else:
            print("⚠️ Deletion failed (but chunk still uploaded)")
    except Exception as e:
        print(f"❌ Deletion error: {e}")
    
    print(f"\n🎉 BrontoBox Drive Client test complete!")
    print("✅ Upload/download operations working")
    print("✅ Storage quota monitoring working")
    print("✅ Chunk management working")
    print("✅ Ready for full file storage system!")

if __name__ == "__main__":
    test_drive_client()
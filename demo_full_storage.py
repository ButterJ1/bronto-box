# demo_full_storage.py
"""
Demo script for complete BrontoBox storage system
Tests the full flow: encrypt → chunk → upload → download → decrypt
"""

import os
import json
import secrets
from datetime import datetime
from storage_manager import BrontoBoxStorageManager

def demo_full_storage():
    """Demo the complete BrontoBox storage system"""
    print("🦕📦 === BrontoBox Complete Storage Demo === 🦕📦\n")
    
    # Initialize all components
    from vault_core import VaultCore
    from google_auth import GoogleAuthManager
    
    # Initialize vault
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
    
    print("🔐 BrontoBox vault initialized")
    
    # Save vault info for consistency
    try:
        with open(vault_info_file, 'w') as f:
            json.dump(vault_info, f)
    except Exception as e:
        print(f"⚠️ Warning: Could not save vault info: {e}")
    
    # Initialize auth manager
    auth_manager = GoogleAuthManager(vault)
    if os.path.exists("credentials.json"):
        auth_manager.setup_oauth_from_file("credentials.json")
        print("✅ OAuth configured")
        
        # Try to load existing accounts first
        accounts_file = "brontobox_accounts.json"
        if os.path.exists(accounts_file):
            print("📂 Loading existing accounts...")
            try:
                with open(accounts_file, 'r') as f:
                    encrypted_accounts = json.load(f)
                
                success = auth_manager.load_accounts_from_vault(encrypted_accounts)
                if success:
                    accounts = auth_manager.list_accounts()
                    if accounts:
                        print(f"📧 Loaded existing account: {accounts[0]['email']}")
                    else:
                        print("⚠️ No active accounts found in saved file")
                else:
                    print("❌ Failed to load accounts from file")
            except Exception as e:
                print(f"⚠️ Error loading accounts: {e}")
        
        # Check for existing accounts
        accounts = auth_manager.list_accounts()
        if not accounts:
            print("📱 No accounts found. Let's authenticate a new account...")
            try:
                account_id = auth_manager.authenticate_new_account("main_account")
                print(f"✅ Account authenticated: {account_id}")
            except Exception as e:
                print(f"❌ Authentication failed: {e}")
                print("Please run 'python test_drive.py' first to set up authentication")
                return
        else:
            account_email = accounts[0]['email']
            print(f"📧 Using existing account: {account_email}")
    else:
        print("❌ credentials.json not found")
        print("Please download OAuth credentials from Google Cloud Console")
        return
    
    # Initialize storage manager
    storage_manager = BrontoBoxStorageManager(vault, auth_manager)
    
    # Show storage summary
    print("\n📊 Storage Summary:")
    summary = storage_manager.get_storage_summary()
    print(f"   🦕 BrontoBox Files: {summary['brontobox_files']['count']}")
    print(f"   📧 Google Accounts: {summary['google_accounts']['count']}")
    print(f"   💾 Available Space: {summary['google_accounts']['total_available_gb']:.2f} GB")
    
    # Create test file
    print("\n📄 Creating test file...")
    test_content = f"""
BrontoBox Test Document

This is a test document to demonstrate BrontoBox's
secure, distributed storage capabilities!

Features:
- Client-side encryption (AES-256-GCM)
- File chunking for optimal storage
- Distributed across multiple Google accounts
- Zero-knowledge security

Created: {datetime.now().isoformat()}
Random data: {secrets.token_hex(32)}

{("BrontoBox rocks! " * 50)}
""".strip()
    
    test_file_path = "brontobox_test_document.txt"
    with open(test_file_path, 'w', encoding='utf-8') as f:  # Fix: UTF-8 encoding
        f.write(test_content)
    
    file_size = os.path.getsize(test_file_path)
    print(f"✅ Test file created: {test_file_path} ({file_size:,} bytes)")
    
    try:
        # Store file
        print(f"\n🦕 Storing file in BrontoBox...")
        file_id = storage_manager.store_file(
            file_path=test_file_path,
            metadata={
                'description': 'BrontoBox demo test file',
                'demo_version': '1.0',
                'test_run': True
            }
        )
        
        # List stored files
        print(f"\n📋 Files in BrontoBox:")
        files = storage_manager.list_stored_files()
        for file_info in files:
            print(f"   📄 {file_info['name']} ({file_info['size_mb']:.2f} MB)")
            print(f"      📦 {file_info['chunks']} chunks across {len(file_info['accounts_used'])} accounts")
        
        # Retrieve file
        print(f"\n🦕 Retrieving file from BrontoBox...")
        output_path = "brontobox_retrieved_document.txt"
        success = storage_manager.retrieve_file(file_id, output_path)
        
        if success:
            # Compare original and retrieved
            with open(test_file_path, 'r') as f:
                original_content = f.read()
            with open(output_path, 'r') as f:
                retrieved_content = f.read()
            
            if original_content == retrieved_content:
                print("✅ File integrity verified - content matches perfectly!")
            else:
                print("❌ File integrity check failed!")
        
        # Show updated storage summary
        print(f"\n📊 Updated Storage Summary:")
        summary = storage_manager.get_storage_summary()
        print(f"   🦕 BrontoBox Files: {summary['brontobox_files']['count']}")
        print(f"   📦 Total Chunks: {summary['brontobox_files']['total_chunks']}")
        print(f"   💾 BrontoBox Data: {summary['brontobox_files']['total_size_gb']:.3f} GB")
        
        # Test file registry save/load
        print(f"\n💾 Testing file registry persistence...")
        encrypted_registry = storage_manager.save_file_registry()
        
        # Clear and reload
        storage_manager.stored_files = {}
        success = storage_manager.load_file_registry(encrypted_registry)
        
        if success:
            reloaded_files = storage_manager.list_stored_files()
            print(f"✅ Registry persistence working: {len(reloaded_files)} files reloaded")
        
        # Save accounts for future use
        print(f"\n💾 Saving accounts for future sessions...")
        encrypted_accounts = auth_manager.save_accounts_to_vault()
        
        # Save to file for persistence
        accounts_file = "brontobox_accounts.json"
        with open(accounts_file, 'w') as f:
            json.dump(encrypted_accounts, f)
        print(f"✅ Accounts saved to {accounts_file}")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup test files
        for cleanup_file in [test_file_path, "brontobox_retrieved_document.txt"]:
            if os.path.exists(cleanup_file):
                os.remove(cleanup_file)
                print(f"🧹 Cleaned up: {cleanup_file}")
    
    print(f"\n🎉 BrontoBox Complete Storage Demo Finished!")
    print("✅ Encryption ↔ Chunking ↔ Google Drive ↔ Decryption")
    print("✅ Ready for multi-account distribution!")
    print("🦕 BrontoBox: Massive storage, maximum security! 📦")

if __name__ == "__main__":
    demo_full_storage()
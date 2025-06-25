# quick_storage_check.py
"""
Fixed storage check that handles vault key consistency
"""

import os
import json
import base64

def quick_storage_check():
    """Quick check of available storage across accounts with proper key handling"""
    print("🦕 BrontoBox Storage Check 🦕\n")
    
    try:
        from vault_core import VaultCore
        from google_auth import GoogleAuthManager
        from drive_client import BrontoBoxDriveClient
        
        # Check if we have saved vault info
        vault_info_file = "brontobox_vault_info.json"
        accounts_file = "brontobox_accounts.json"
        
        if os.path.exists(vault_info_file) and os.path.exists(accounts_file):
            print("📂 Loading existing vault and accounts...")
            
            # Load vault info
            with open(vault_info_file, 'r') as f:
                vault_info = json.load(f)
            
            # Initialize vault with saved salt
            vault = VaultCore()
            success = vault.unlock_vault(
                "brontobox_shared_vault_2024", 
                vault_info['salt']
            )
            
            if not success:
                print("❌ Failed to unlock vault with saved info")
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
                
        else:
            print("📧 No saved accounts found")
            print("💡 Run 'python test_drive.py' (option 1) first to set up accounts")
            return
        
        accounts = auth_manager.list_accounts()
        if not accounts:
            print("📧 No active accounts found")
            return
        
        print(f"✅ Loaded {len(accounts)} account(s)")
        
        # Check storage for each account
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
                        
                        # Show BrontoBox chunks if any
                        chunks = drive_client.list_chunks(account_id)
                        if chunks:
                            total_chunk_size = sum(chunk.size for chunk in chunks) / (1024**2)  # MB
                            print(f"   📦 BrontoBox chunks: {len(chunks)} files ({total_chunk_size:.2f} MB)")
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
            
            # Show storage distribution strategy
            if len([a for a in accounts if a['is_active']]) > 1:
                print(f"\n🔄 Multi-Account Distribution:")
                print(f"   📦 Files will be split across {len([a for a in accounts if a['is_active']])} accounts")
                print(f"   🔒 Each account stores encrypted chunks only")
                print(f"   🛡️ Maximum privacy and security")
        
    except Exception as e:
        print(f"❌ Storage check failed: {e}")
        print("💡 Try running: python test_drive.py (option 1)")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    quick_storage_check()
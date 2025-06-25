# test_vault_fix.py
"""
Quick test to verify vault key consistency fix
"""

import os
import json

def test_vault_consistency():
    """Test that vault keys remain consistent across sessions"""
    print("🔐 Testing BrontoBox Vault Consistency Fix\n")
    
    try:
        from vault_core import VaultCore
        
        vault_info_file = "test_vault_info.json"
        
        # Test 1: Create vault and save info
        print("1️⃣ Creating new vault...")
        vault1 = VaultCore()
        vault_info = vault1.initialize_vault("test_password_123")
        
        # Save vault info
        with open(vault_info_file, 'w') as f:
            json.dump(vault_info, f)
        
        # Create test data
        test_data = b"This is a test message for vault consistency"
        encrypted_data = vault1.crypto_manager.encrypt_data(
            test_data,
            vault1.master_keys['file_encryption']
        )
        
        print(f"✅ Vault created and test data encrypted")
        print(f"   Salt: {vault_info['salt'][:20]}...")
        
        # Test 2: Load vault with same info
        print("\n2️⃣ Loading vault with saved info...")
        vault2 = VaultCore()
        
        success = vault2.unlock_vault("test_password_123", vault_info['salt'])
        if not success:
            print("❌ Failed to unlock vault with saved salt")
            return False
        
        # Try to decrypt the data
        try:
            decrypted_data = vault2.crypto_manager.decrypt_data(
                encrypted_data,
                vault2.master_keys['file_encryption']
            )
            
            if decrypted_data == test_data:
                print("✅ Successfully decrypted data with loaded vault")
                print("✅ Vault key consistency working!")
            else:
                print("❌ Decrypted data doesn't match original")
                return False
                
        except Exception as e:
            print(f"❌ Failed to decrypt data: {e}")
            return False
        
        # Test 3: Simulate multiple sessions
        print("\n3️⃣ Testing multiple session simulation...")
        for i in range(3):
            vault_session = VaultCore()
            success = vault_session.unlock_vault("test_password_123", vault_info['salt'])
            
            if success:
                print(f"   ✅ Session {i+1}: Vault unlocked successfully")
            else:
                print(f"   ❌ Session {i+1}: Failed to unlock vault")
                return False
        
        print("\n🎉 Vault Consistency Test Results:")
        print("✅ Vault salt persistence working")
        print("✅ Key derivation consistent across sessions")
        print("✅ Account encryption/decryption will work")
        print("✅ Storage check should now work properly")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        if os.path.exists(vault_info_file):
            os.remove(vault_info_file)
            print("🧹 Cleaned up test files")

if __name__ == "__main__":
    success = test_vault_consistency()
    
    if success:
        print("\n✅ Fix verified! Now try:")
        print("1. python test_drive.py (option 1) - to set up accounts")
        print("2. python test_drive.py (option 2) - should show storage info!")
    else:
        print("\n❌ Fix needs more work")
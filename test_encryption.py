# test_encryption.py
"""
Test suite for VaultDrive encryption system
"""

import tempfile
import os
import secrets
from crypto_manager import CryptoManager
from file_chunker import FileChunker
from vault_core import VaultCore

def test_crypto_manager():
    """Test basic crypto operations"""
    print("Testing CryptoManager...")
    
    crypto = CryptoManager()
    test_data = b"Hello, VaultDrive! This is test data for encryption."
    
    # Test key derivation
    salt = crypto.generate_salt()
    keys = crypto.derive_master_keys("test_password_123", salt)
    
    assert len(keys) == 4
    assert len(keys['file_encryption']) == 32
    print("✓ Key derivation successful")
    
    # Test encryption/decryption
    encrypted = crypto.encrypt_data(test_data, keys['file_encryption'])
    decrypted = crypto.decrypt_data(encrypted, keys['file_encryption'])
    
    assert decrypted == test_data
    print("✓ Encryption/decryption successful")

def test_file_chunker():
    """Test file chunking operations"""
    print("\nTesting FileChunker...")
    
    crypto = CryptoManager()
    chunker = FileChunker(crypto, max_chunk_size=1024)  # Small chunks for testing
    
    # Create test file
    test_data = secrets.token_bytes(3000)  # 3KB file, should create 3 chunks
    
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(test_data)
        temp_file_path = temp_file.name
    
    try:
        # Test chunking
        salt = crypto.generate_salt()
        keys = crypto.derive_master_keys("test_password", salt)
        
        manifest = chunker.chunk_file(temp_file_path, keys['file_encryption'])
        
        assert manifest['num_chunks'] == 3
        assert manifest['file_size'] == 3000
        print("✓ File chunking successful")
        
        # Test reconstruction
        output_path = temp_file_path + "_reconstructed"
        success = chunker.reconstruct_file(manifest, output_path, keys['file_encryption'])
        
        assert success
        
        # Verify reconstructed file
        with open(output_path, 'rb') as f:
            reconstructed_data = f.read()
        
        assert reconstructed_data == test_data
        print("✓ File reconstruction successful")
        
    finally:
        # Cleanup
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)

def test_vault_core():
    """Test main VaultCore functionality"""
    print("\nTesting VaultCore...")
    
    vault = VaultCore()
    
    # Test vault initialization
    init_data = vault.initialize_vault("my_secure_password_123")
    assert vault.is_unlocked
    print("✓ Vault initialization successful")
    
    # Test vault lock/unlock
    salt = init_data['salt']
    vault.lock_vault()
    assert not vault.is_unlocked
    
    unlock_success = vault.unlock_vault("my_secure_password_123", salt)
    assert unlock_success
    assert vault.is_unlocked
    print("✓ Vault lock/unlock successful")
    
    # Test file encryption
    test_data = b"This is a test file for VaultDrive encryption!"
    
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(test_data)
        temp_file_path = temp_file.name
    
    try:
        encrypted_result = vault.encrypt_file(temp_file_path)
        assert 'file_manifest' in encrypted_result
        assert encrypted_result['total_chunks'] >= 1
        print("✓ File encryption successful")
        
        # Test file decryption
        output_path = temp_file_path + "_decrypted"
        decrypt_success = vault.decrypt_file(encrypted_result, output_path)
        assert decrypt_success
        
        # Verify decrypted file
        with open(output_path, 'rb') as f:
            decrypted_data = f.read()
        
        assert decrypted_data == test_data
        print("✓ File decryption successful")
        
    finally:
        # Cleanup
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)

def run_all_tests():
    """Run all tests"""
    print("=== VaultDrive Encryption System Tests ===\n")
    
    try:
        test_crypto_manager()
        test_file_chunker()
        test_vault_core()
        
        print("\n=== All Tests Passed! ===")
        print("✓ Core encryption system is working correctly")
        print("✓ File chunking and reconstruction work properly") 
        print("✓ Vault management is functional")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()
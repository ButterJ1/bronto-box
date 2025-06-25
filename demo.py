# demo.py
"""
VaultDrive Demo Script
Demonstrates basic usage of the encryption system
"""

import os
import tempfile
import json
import base64
import hashlib
import secrets

# Import our VaultDrive components
# Note: In a real setup, these would be in separate files
# For this demo, we assume the classes are available
try:
    from vault_core import VaultCore, CryptoManager, FileChunker
except ImportError:
    print("Error: Make sure all VaultDrive core files are in the same directory")
    print("Required files: crypto_manager.py, file_chunker.py, vault_core.py")
    exit(1)

def create_demo_file(content: str, filename: str = "demo.txt") -> str:
    """Create a demo file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix=f"_{filename}", delete=False) as f:
        f.write(content)
        return f.name

def demo_basic_encryption():
    """Demonstrate basic file encryption and decryption"""
    print("=== VaultDrive Basic Encryption Demo ===\n")
    
    # Initialize vault
    vault = VaultCore()
    
    # Step 1: Create a new vault
    print("1. Creating new vault...")
    master_password = "my_super_secure_password_2024"
    init_data = vault.initialize_vault(master_password)
    print(f"   ✓ Vault initialized with salt: {init_data['salt'][:20]}...")
    
    # Step 2: Create a demo file
    print("\n2. Creating demo file...")
    demo_content = """
    This is a confidential document for VaultDrive testing.
    
    It contains:
    - Personal information
    - Financial data  
    - Private communications
    - Business secrets
    
    This file will be encrypted and split into chunks,
    then distributed across multiple Google Drive accounts
    for maximum security and privacy.
    
    Even Google won't be able to read this content!
    """
    
    demo_file_path = create_demo_file(demo_content, "confidential_document.txt")
    file_size = os.path.getsize(demo_file_path)
    print(f"   ✓ Created demo file: {os.path.basename(demo_file_path)} ({file_size} bytes)")
    
    try:
        # Step 3: Encrypt the file
        print("\n3. Encrypting and chunking file...")
        encrypted_result = vault.encrypt_file(demo_file_path)
        
        print(f"   ✓ File encrypted successfully!")
        print(f"   ✓ Created {encrypted_result['total_chunks']} encrypted chunks")
        print(f"   ✓ Total size: {encrypted_result['total_size']} bytes")
        
        # Show chunk information
        manifest = encrypted_result['file_manifest']
        print(f"   ✓ File hash: {manifest['file_hash'][:16]}...")
        
        # Step 4: Simulate vault lock/unlock (like app restart)
        print("\n4. Simulating vault lock and unlock...")
        salt = init_data['salt']
        vault.lock_vault()
        print("   ✓ Vault locked (all keys cleared from memory)")
        
        unlock_success = vault.unlock_vault(master_password, salt)
        if unlock_success:
            print("   ✓ Vault unlocked successfully")
        else:
            print("   ❌ Vault unlock failed!")
            return
        
        # Step 5: Decrypt and reconstruct the file
        print("\n5. Decrypting and reconstructing file...")
        output_path = demo_file_path + "_decrypted"
        
        decrypt_success = vault.decrypt_file(encrypted_result, output_path)
        
        if decrypt_success:
            print("   ✓ File decrypted successfully!")
            
            # Verify the content
            with open(output_path, 'r') as f:
                decrypted_content = f.read()
            
            if decrypted_content == demo_content:
                print("   ✓ File integrity verified - content matches original!")
            else:
                print("   ❌ File integrity check failed!")
        else:
            print("   ❌ File decryption failed!")
        
        # Step 6: Show what the encrypted chunks look like
        print("\n6. Examining encrypted chunks...")
        chunks = manifest['chunks']
        for i, chunk in enumerate(chunks[:2]):  # Show first 2 chunks
            encrypted_data = chunk['encrypted_data']['ciphertext'][:50]
            print(f"   Chunk {i+1}: {encrypted_data}... ({chunk['chunk_size']} bytes)")
        
        if len(chunks) > 2:
            print(f"   ... and {len(chunks) - 2} more chunks")
        
    finally:
        # Cleanup
        if os.path.exists(demo_file_path):
            os.remove(demo_file_path)
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)
    
    print("\n=== Demo Complete ===")
    print("This demonstrates how VaultDrive will:")
    print("• Encrypt files locally before any upload")
    print("• Split files into secure, unidentifiable chunks") 
    print("• Distribute chunks across multiple accounts")
    print("• Reconstruct files seamlessly when needed")
    print("• Maintain perfect privacy - even from Google!")

def demo_large_file():
    """Demonstrate chunking with a larger file"""
    print("\n=== Large File Chunking Demo ===\n")
    
    vault = VaultCore()
    vault.initialize_vault("demo_password_large_file")
    
    # Create a larger demo file (1MB of data)
    print("1. Creating large demo file (1MB)...")
    large_content = "VaultDrive Test Data " * 52428  # ~1MB
    large_file_path = create_demo_file(large_content, "large_file.txt")
    
    file_size = os.path.getsize(large_file_path)
    print(f"   ✓ Created file: {file_size:,} bytes")
    
    try:
        # Encrypt with smaller chunk size for demo
        print("\n2. Encrypting with 256KB chunks...")
        vault.file_chunker.max_chunk_size = 256 * 1024  # 256KB chunks
        
        encrypted_result = vault.encrypt_file(large_file_path)
        
        print(f"   ✓ Created {encrypted_result['total_chunks']} chunks")
        
        # Show chunk distribution
        manifest = encrypted_result['file_manifest']
        total_encrypted_size = sum(len(chunk['encrypted_data']['ciphertext']) for chunk in manifest['chunks'])
        
        print(f"   ✓ Original size: {file_size:,} bytes")
        print(f"   ✓ Encrypted size: {total_encrypted_size:,} bytes")
        print(f"   ✓ Overhead: {((total_encrypted_size - file_size) / file_size * 100):.2f}%")
        
    finally:
        if os.path.exists(large_file_path):
            os.remove(large_file_path)
    
    print("\nThis shows how VaultDrive handles large files efficiently!")

def demo_security_features():
    """Demonstrate security features"""
    print("\n=== Security Features Demo ===\n")
    
    # Show what happens with wrong password
    print("1. Testing wrong password protection...")
    vault = VaultCore()
    init_data = vault.initialize_vault("correct_password")
    salt = init_data['salt']
    
    vault.lock_vault()
    
    # Try wrong password
    wrong_unlock = vault.unlock_vault("wrong_password", salt)
    print(f"   ✓ Wrong password rejected: {not wrong_unlock}")
    
    # Try correct password
    correct_unlock = vault.unlock_vault("correct_password", salt)
    print(f"   ✓ Correct password accepted: {correct_unlock}")
    
    # Show key derivation
    print("\n2. Key derivation system...")
    keys = vault.master_keys
    print(f"   ✓ File encryption key: {keys['file_encryption'].hex()[:32]}...")
    print(f"   ✓ Metadata encryption key: {keys['metadata_encryption'].hex()[:32]}...")
    print(f"   ✓ Vault unlock key: {keys['vault_unlock'].hex()[:32]}...")
    print(f"   ✓ Token encryption key: {keys['token_encryption'].hex()[:32]}...")
    print("   (Each key is unique and serves a different purpose)")

if __name__ == "__main__":
    print("VaultDrive Core Encryption System Demo")
    print("=" * 50)
    
    demo_basic_encryption()
    demo_large_file()
    demo_security_features()
    
    print("\n" + "=" * 50)
    print("Ready for Phase 2: Google Drive Integration! 🚀")
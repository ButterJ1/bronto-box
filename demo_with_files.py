# demo_with_files.py
"""
VaultDrive Demo Script - Creates actual files you can examine
Demonstrates the encryption system and leaves files for inspection
"""

import os
import json
import base64
import hashlib
import secrets
from datetime import datetime

# Import our VaultDrive components
try:
    from vault_core import VaultCore, CryptoManager, FileChunker
except ImportError:
    print("Error: Make sure all VaultDrive core files are in the same directory")
    print("Required files: crypto_manager.py, file_chunker.py, vault_core.py")
    exit(1)

def create_demo_directory():
    """Create a demo directory with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    demo_dir = f"vaultdrive_demo_{timestamp}"
    os.makedirs(demo_dir, exist_ok=True)
    return demo_dir

def create_sample_files(demo_dir):
    """Create various sample files for testing"""
    files_created = []
    
    # 1. Text document
    text_content = """CONFIDENTIAL DOCUMENT
===================

This is a secret document that will be encrypted and stored securely.

Personal Information:
- Name: Sarah Johnson
- SSN: 123-45-6789
- Account: 9876543210
- PIN: 1234

Business Secrets:
- Product launch date: March 2025
- Market strategy: Target millennials with premium pricing
- Competitor analysis: Company X is our biggest threat

Financial Data:
- Revenue projection: $2.5M
- Budget allocation: 40% marketing, 30% R&D, 30% operations
- Investment fund: $500K available

This information must be kept secure and encrypted!
"""
    
    text_file = os.path.join(demo_dir, "confidential_document.txt")
    with open(text_file, 'w') as f:
        f.write(text_content)
    files_created.append(text_file)
    
    # 2. JSON data file
    json_data = {
        "user_profile": {
            "name": "Sarah Johnson",
            "email": "sarah@example.com",
            "preferences": {
                "theme": "dark",
                "notifications": True,
                "backup_frequency": "daily"
            }
        },
        "financial_records": [
            {"date": "2025-01-01", "amount": 5000.00, "category": "salary"},
            {"date": "2025-01-15", "amount": -1200.00, "category": "rent"},
            {"date": "2025-01-20", "amount": -300.00, "category": "groceries"}
        ],
        "passwords": {
            "banking": "encrypted_password_123",
            "email": "super_secure_pass_456",
            "social_media": "private_key_789"
        }
    }
    
    json_file = os.path.join(demo_dir, "personal_data.json")
    with open(json_file, 'w') as f:
        json.dump(json_data, f, indent=2)
    files_created.append(json_file)
    
    # 3. Large file (to demonstrate chunking)
    large_content = "VaultDrive Test Data - " + "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" * 1000  # ~36KB
    large_file = os.path.join(demo_dir, "large_test_file.txt")
    with open(large_file, 'w') as f:
        f.write(large_content)
    files_created.append(large_file)
    
    # 4. Binary-like file (simulated)
    binary_content = secrets.token_bytes(5000)  # 5KB of random binary data
    binary_file = os.path.join(demo_dir, "binary_data.bin")
    with open(binary_file, 'wb') as f:
        f.write(binary_content)
    files_created.append(binary_file)
    
    return files_created

def save_encrypted_chunks(demo_dir, filename, encrypted_result):
    """Save encrypted chunks to individual files"""
    chunks_dir = os.path.join(demo_dir, f"encrypted_chunks_{os.path.splitext(filename)[0]}")
    os.makedirs(chunks_dir, exist_ok=True)
    
    manifest = encrypted_result['file_manifest']
    
    # Save each chunk as a separate file
    chunk_files = []
    for i, chunk in enumerate(manifest['chunks']):
        chunk_filename = f"chunk_{i:03d}_{chunk['chunk_id']}.enc"
        chunk_path = os.path.join(chunks_dir, chunk_filename)
        
        # Write the encrypted chunk data
        with open(chunk_path, 'w') as f:
            f.write(chunk['encrypted_data']['ciphertext'])
        
        chunk_files.append(chunk_path)
    
    # Save the manifest
    manifest_path = os.path.join(chunks_dir, "file_manifest.json")
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    # Save the encrypted manifest
    encrypted_manifest_path = os.path.join(chunks_dir, "encrypted_manifest.json")
    with open(encrypted_manifest_path, 'w') as f:
        json.dump(encrypted_result['encrypted_manifest'], f, indent=2)
    
    return chunks_dir, chunk_files, manifest_path

def demonstrate_encryption_process():
    """Run the complete encryption demonstration with file outputs"""
    print("=== VaultDrive File Encryption Demo (with file output) ===\n")
    
    # Create demo directory
    demo_dir = create_demo_directory()
    print(f"📁 Created demo directory: {demo_dir}")
    
    # Initialize vault
    vault = VaultCore()
    master_password = "demo_password_2024!"
    init_data = vault.initialize_vault(master_password)
    
    # Save vault initialization data
    vault_info = {
        "master_password": master_password,
        "salt": init_data['salt'],
        "created_at": datetime.now().isoformat(),
        "key_derivation": init_data['key_derivation'],
        "iterations": init_data['iterations']
    }
    
    vault_info_path = os.path.join(demo_dir, "vault_info.json")
    with open(vault_info_path, 'w') as f:
        json.dump(vault_info, f, indent=2)
    
    print(f"🔐 Vault initialized - info saved to: {vault_info_path}")
    
    # Create sample files
    print("\n📄 Creating sample files...")
    sample_files = create_sample_files(demo_dir)
    
    for file_path in sample_files:
        file_size = os.path.getsize(file_path)
        print(f"   ✓ {os.path.basename(file_path)} ({file_size:,} bytes)")
    
    # Encrypt each file
    print("\n🔒 Encrypting files...")
    encryption_results = {}
    
    for file_path in sample_files:
        filename = os.path.basename(file_path)
        print(f"\n   Processing: {filename}")
        
        # Encrypt the file
        encrypted_result = vault.encrypt_file(file_path)
        encryption_results[filename] = encrypted_result
        
        # Save encrypted chunks
        chunks_dir, chunk_files, manifest_path = save_encrypted_chunks(demo_dir, filename, encrypted_result)
        
        print(f"   ✓ Encrypted into {encrypted_result['total_chunks']} chunks")
        print(f"   ✓ Chunks saved to: {chunks_dir}")
        print(f"   ✓ Manifest saved to: {manifest_path}")
    
    # Demonstrate decryption
    print("\n🔓 Decrypting files...")
    decrypted_dir = os.path.join(demo_dir, "decrypted_files")
    os.makedirs(decrypted_dir, exist_ok=True)
    
    for filename, encrypted_result in encryption_results.items():
        original_path = os.path.join(demo_dir, filename)
        decrypted_path = os.path.join(decrypted_dir, f"decrypted_{filename}")
        
        success = vault.decrypt_file(encrypted_result, decrypted_path)
        
        if success:
            # Verify the file is identical
            if filename.endswith('.bin'):
                # Binary comparison
                with open(original_path, 'rb') as f1, open(decrypted_path, 'rb') as f2:
                    original_content = f1.read()
                    decrypted_content = f2.read()
                    identical = original_content == decrypted_content
            else:
                # Text comparison
                with open(original_path, 'r') as f1, open(decrypted_path, 'r') as f2:
                    original_content = f1.read()
                    decrypted_content = f2.read()
                    identical = original_content == decrypted_content
            
            print(f"   ✓ {filename} decrypted successfully (identical: {identical})")
        else:
            print(f"   ❌ {filename} decryption failed")
    
    # Generate summary report
    print("\n📊 Generating encryption report...")
    report = {
        "demo_info": {
            "created_at": datetime.now().isoformat(),
            "demo_directory": demo_dir,
            "vault_password": master_password,
            "total_files_processed": len(sample_files)
        },
        "encryption_results": {},
        "security_features": {
            "encryption_algorithm": "AES-256-GCM",
            "key_derivation": "PBKDF2-SHA256",
            "iterations": 100000,
            "chunk_size": "100MB (adjustable)"
        }
    }
    
    for filename, encrypted_result in encryption_results.items():
        original_size = os.path.getsize(os.path.join(demo_dir, filename))
        manifest = encrypted_result['file_manifest']
        
        report["encryption_results"][filename] = {
            "original_size": original_size,
            "num_chunks": encrypted_result['total_chunks'],
            "file_hash": manifest['file_hash'],
            "chunks_created": len(manifest['chunks'])
        }
    
    report_path = os.path.join(demo_dir, "encryption_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"📋 Encryption report saved to: {report_path}")
    
    # Show what to examine
    print(f"\n🔍 Files created in: {os.path.abspath(demo_dir)}")
    print("\nYou can now examine:")
    print("📁 Original files (unencrypted)")
    print("📁 encrypted_chunks_* directories (encrypted chunks)")  
    print("📁 decrypted_files directory (reconstructed files)")
    print("📄 vault_info.json (vault configuration)")
    print("📄 encryption_report.json (detailed results)")
    print("📄 *_manifest.json files (chunk metadata)")
    
    print(f"\n🎉 Demo complete! Check the '{demo_dir}' directory to see all generated files.")
    
    return demo_dir

def create_pdf_like_file(demo_dir):
    """Create a file that simulates a PDF structure"""
    pdf_content = """%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj

4 0 obj
<<
/Length 56
>>
stream
BT
/F1 12 Tf
100 700 Td
(This is a confidential PDF document!) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000274 00000 n 
0000000379 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
456
%%EOF"""
    
    pdf_file = os.path.join(demo_dir, "confidential_document.pdf")
    with open(pdf_file, 'w') as f:
        f.write(pdf_content)
    
    return pdf_file

def extended_demo():
    """Extended demo with more file types"""
    print("=== Extended VaultDrive Demo ===\n")
    
    demo_dir = create_demo_directory()
    print(f"📁 Demo directory: {os.path.abspath(demo_dir)}")
    
    # Create additional file types
    pdf_file = create_pdf_like_file(demo_dir)
    print(f"📄 Created PDF-like file: {os.path.basename(pdf_file)}")
    
    # Run the main demo
    demonstrate_encryption_process()

if __name__ == "__main__":
    print("VaultDrive File Encryption Demo")
    print("=" * 50)
    
    # Ask user what they want to do
    print("\nChoose demo mode:")
    print("1. Standard demo (creates files to examine)")
    print("2. Extended demo (includes PDF-like files)")
    print("3. Both")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        demo_dir = demonstrate_encryption_process()
    elif choice == "2":
        extended_demo()
    elif choice == "3":
        demo_dir = demonstrate_encryption_process()
        print("\n" + "="*50)
        extended_demo()
    else:
        print("Invalid choice, running standard demo...")
        demo_dir = demonstrate_encryption_process()
    
    print("\n" + "="*50)
    print("🎯 Demo complete!")
    print("\nNext steps:")
    print("1. Examine the generated files")
    print("2. Try opening the encrypted chunks (they should be unreadable)")
    print("3. Compare original vs decrypted files (should be identical)")
    print("4. Ready for Phase 2: Google Drive Integration! 🚀")
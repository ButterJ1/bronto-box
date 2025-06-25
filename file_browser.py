# file_browser.py
"""
VaultDrive File Browser
Browse and examine files created by the demo
"""

import os
import json
from datetime import datetime

def find_demo_directories():
    """Find all demo directories in current path"""
    demo_dirs = []
    for item in os.listdir('.'):
        if os.path.isdir(item) and item.startswith('vaultdrive_demo_'):
            demo_dirs.append(item)
    return sorted(demo_dirs, reverse=True)  # Most recent first

def show_file_tree(directory, prefix="", max_depth=3, current_depth=0):
    """Display a tree view of files and directories"""
    if current_depth >= max_depth:
        return
    
    try:
        items = sorted(os.listdir(directory))
    except PermissionError:
        print(f"{prefix}[Permission Denied]")
        return
    
    for i, item in enumerate(items):
        item_path = os.path.join(directory, item)
        is_last = i == len(items) - 1
        
        # Choose the right tree characters
        if is_last:
            print(f"{prefix}└── {item}")
            new_prefix = prefix + "    "
        else:
            print(f"{prefix}├── {item}")
            new_prefix = prefix + "│   "
        
        # Add file size for files
        if os.path.isfile(item_path):
            size = os.path.getsize(item_path)
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size/1024:.1f} KB"
            else:
                size_str = f"{size/(1024*1024):.1f} MB"
            print(f"{new_prefix[:-4]}    ({size_str})")
        
        # Recurse into directories
        if os.path.isdir(item_path) and current_depth < max_depth - 1:
            show_file_tree(item_path, new_prefix, max_depth, current_depth + 1)

def show_file_content(file_path, max_lines=20):
    """Display file content with smart handling of different file types"""
    try:
        file_size = os.path.getsize(file_path)
        
        if file_path.endswith('.json'):
            # Pretty print JSON files
            with open(file_path, 'r') as f:
                data = json.load(f)
            print(json.dumps(data, indent=2))
            
        elif file_path.endswith('.bin') or file_size > 100000:
            # Show hex dump for binary files or very large files
            with open(file_path, 'rb') as f:
                data = f.read(200)  # First 200 bytes
            
            print("Binary/Large file - showing first 200 bytes as hex:")
            for i in range(0, len(data), 16):
                hex_part = ' '.join(f'{b:02x}' for b in data[i:i+16])
                ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data[i:i+16])
                print(f"{i:04x}: {hex_part:<48} {ascii_part}")
            
            if file_size > 200:
                print(f"... ({file_size - 200} more bytes)")
                
        elif file_path.endswith('.enc'):
            # Encrypted files - show as hex
            with open(file_path, 'r') as f:
                content = f.read(500)  # First 500 characters
            print("Encrypted chunk (base64 encoded):")
            print(content[:200] + "..." if len(content) > 200 else content)
            
        else:
            # Regular text files
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines[:max_lines]):
                print(f"{i+1:3}: {line.rstrip()}")
            
            if len(lines) > max_lines:
                print(f"... ({len(lines) - max_lines} more lines)")
                
    except Exception as e:
        print(f"Error reading file: {e}")

def compare_files(file1, file2):
    """Compare two files and show if they're identical"""
    try:
        # Get file sizes
        size1 = os.path.getsize(file1)
        size2 = os.path.getsize(file2)
        
        print(f"File 1: {os.path.basename(file1)} ({size1} bytes)")
        print(f"File 2: {os.path.basename(file2)} ({size2} bytes)")
        
        if size1 != size2:
            print("❌ Files are different sizes!")
            return False
        
        # Compare content
        with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
            content1 = f1.read()
            content2 = f2.read()
        
        if content1 == content2:
            print("✅ Files are identical!")
            return True
        else:
            print("❌ Files have different content!")
            return False
            
    except Exception as e:
        print(f"Error comparing files: {e}")
        return False

def interactive_browser():
    """Interactive file browser for demo directories"""
    print("=== VaultDrive File Browser ===\n")
    
    # Find demo directories
    demo_dirs = find_demo_directories()
    
    if not demo_dirs:
        print("No demo directories found.")
        print("Run 'python demo_with_files.py' first to create demo files.")
        return
    
    print("Available demo directories:")
    for i, dir_name in enumerate(demo_dirs):
        timestamp = dir_name.replace('vaultdrive_demo_', '')
        print(f"{i+1}. {dir_name} ({timestamp})")
    
    # Select directory
    while True:
        try:
            choice = input(f"\nSelect directory (1-{len(demo_dirs)}) or 'q' to quit: ").strip()
            if choice.lower() == 'q':
                return
            
            dir_index = int(choice) - 1
            if 0 <= dir_index < len(demo_dirs):
                selected_dir = demo_dirs[dir_index]
                break
            else:
                print("Invalid selection!")
        except ValueError:
            print("Please enter a number!")
    
    print(f"\n📁 Browsing: {selected_dir}")
    print("=" * 50)
    
    # Show file tree
    print("\nFile structure:")
    show_file_tree(selected_dir)
    
    # Interactive commands
    while True:
        print(f"\nCommands:")
        print("1. View file content")
        print("2. Compare original vs decrypted file")
        print("3. Show encryption report")
        print("4. Show vault info")
        print("5. List all encrypted chunks")
        print("6. Switch to different demo directory")
        print("7. Quit")
        
        cmd = input("\nEnter command (1-7): ").strip()
        
        if cmd == '1':
            filename = input("Enter filename to view: ").strip()
            file_path = os.path.join(selected_dir, filename)
            
            if os.path.exists(file_path):
                print(f"\n--- Content of {filename} ---")
                show_file_content(file_path)
            else:
                # Try to find the file in subdirectories
                found = False
                for root, dirs, files in os.walk(selected_dir):
                    if filename in files:
                        file_path = os.path.join(root, filename)
                        print(f"\n--- Content of {filename} (found in {os.path.relpath(root, selected_dir)}) ---")
                        show_file_content(file_path)
                        found = True
                        break
                
                if not found:
                    print(f"File '{filename}' not found!")
        
        elif cmd == '2':
            print("\nAvailable files for comparison:")
            original_files = [f for f in os.listdir(selected_dir) if os.path.isfile(os.path.join(selected_dir, f))]
            for f in original_files:
                print(f"  - {f}")
            
            filename = input("Enter original filename: ").strip()
            original_path = os.path.join(selected_dir, filename)
            decrypted_path = os.path.join(selected_dir, "decrypted_files", f"decrypted_{filename}")
            
            if os.path.exists(original_path) and os.path.exists(decrypted_path):
                print(f"\nComparing {filename}:")
                compare_files(original_path, decrypted_path)
            else:
                print("One or both files not found!")
        
        elif cmd == '3':
            report_path = os.path.join(selected_dir, "encryption_report.json")
            if os.path.exists(report_path):
                print("\n--- Encryption Report ---")
                show_file_content(report_path)
            else:
                print("Encryption report not found!")
        
        elif cmd == '4':
            vault_path = os.path.join(selected_dir, "vault_info.json")
            if os.path.exists(vault_path):
                print("\n--- Vault Information ---")
                show_file_content(vault_path)
            else:
                print("Vault info not found!")
        
        elif cmd == '5':
            print("\nEncrypted chunks:")
            for root, dirs, files in os.walk(selected_dir):
                for file in files:
                    if file.endswith('.enc'):
                        file_path = os.path.join(root, file)
                        size = os.path.getsize(file_path)
                        rel_path = os.path.relpath(file_path, selected_dir)
                        print(f"  {rel_path} ({size} bytes)")
        
        elif cmd == '6':
            interactive_browser()  # Restart browser
            return
        
        elif cmd == '7':
            print("Goodbye!")
            return
        
        else:
            print("Invalid command!")

if __name__ == "__main__":
    interactive_browser()
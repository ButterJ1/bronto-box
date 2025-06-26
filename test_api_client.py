# test_api_client.py
"""
BrontoBox API Test Client
Test the FastAPI server endpoints
"""

import requests
import json
import os
import time
import websocket
import threading
import sys
from typing import Dict, Any

# Fix Windows terminal encoding issues
if sys.platform == "win32":
    import locale
    # Set UTF-8 encoding for Windows
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except:
        pass
    
    # Configure stdout encoding
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    elif hasattr(sys.stdout, 'encoding'):
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

# Safe print function for cross-platform compatibility
def safe_print(text):
    """Print text with emoji fallback for Windows terminals"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Replace emojis with text equivalents for problematic terminals
        emoji_map = {
            '🦕': '[DINO]',
            '📡': '[ANTENNA]',
            '📚': '[BOOKS]',
            '🔧': '[WRENCH]',
            '✅': '[OK]',
            '❌': '[ERROR]',
            '⚠️': '[WARNING]',
            '📄': '[FILE]',
            '⬇️': '[DOWN]',
            '🔌': '[PLUG]',
            '📨': '[MESSAGE]',
            '🎮': '[GAME]',
            '🎉': '[PARTY]',
            '📦': '[BOX]'
        }
        
        safe_text = text
        for emoji, replacement in emoji_map.items():
            safe_text = safe_text.replace(emoji, replacement)
        
        print(safe_text)

class BrontoBoxAPIClient:
    """Client for testing BrontoBox API"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def get(self, endpoint: str) -> Dict[str, Any]:
        """GET request"""
        response = self.session.get(f"{self.base_url}{endpoint}")
        return response.json()
    
    def post(self, endpoint: str, data: Dict[str, Any] = None, files: Dict = None) -> Dict[str, Any]:
        """POST request"""
        if files:
            response = self.session.post(f"{self.base_url}{endpoint}", data=data, files=files)
        else:
            response = self.session.post(f"{self.base_url}{endpoint}", json=data)
        return response.json()
    
    def delete(self, endpoint: str) -> Dict[str, Any]:
        """DELETE request"""
        response = self.session.delete(f"{self.base_url}{endpoint}")
        return response.json()

def test_api_endpoints():
    """Test all BrontoBox API endpoints"""
    safe_print("[DINO] Testing BrontoBox API Server\n")
    
    client = BrontoBoxAPIClient()
    
    # Test 1: Health check
    safe_print("1. Testing Health Check...")
    try:
        health = client.get("/health")
        safe_print(f"[OK] Health: {health}")
    except Exception as e:
        safe_print(f"[ERROR] Health check failed: {e}")
        return False
    
    # Test 2: Initialize vault
    safe_print("\n2. Testing Vault Initialization...")
    try:
        vault_init = client.post("/vault/initialize", {
            "master_password": "test_password_api_2024"
        })
        
        if vault_init.get("success"):
            safe_print(f"[OK] Vault initialized: {vault_init['message']}")
            vault_salt = vault_init["salt"]
        else:
            safe_print(f"[ERROR] Vault initialization failed: {vault_init}")
            return False
            
    except Exception as e:
        safe_print(f"[ERROR] Vault initialization error: {e}")
        return False
    
    # Test 3: Vault status
    safe_print("\n3. Testing Vault Status...")
    try:
        status = client.get("/vault/status")
        safe_print(f"[OK] Vault status: {status}")
    except Exception as e:
        safe_print(f"[ERROR] Vault status error: {e}")
    
    # Test 4: Setup OAuth (if credentials.json exists)
    safe_print("\n4. Testing OAuth Setup...")
    try:
        if os.path.exists("credentials.json"):
            oauth_setup = client.post("/accounts/setup-oauth", {
                "credentials_file": "credentials.json"
            })
            safe_print(f"[OK] OAuth setup: {oauth_setup}")
        else:
            safe_print("[WARNING] Skipping OAuth - credentials.json not found")
    except Exception as e:
        safe_print(f"[ERROR] OAuth setup error: {e}")
    
    # Test 5: List accounts
    safe_print("\n5. Testing Account List...")
    try:
        accounts = client.get("/accounts/list")
        safe_print(f"[OK] Accounts: {accounts}")
    except Exception as e:
        safe_print(f"[ERROR] Account list error: {e}")
    
    # Test 6: Storage info
    safe_print("\n6. Testing Storage Info...")
    try:
        storage = client.get("/storage/info")
        safe_print(f"[OK] Storage: {storage}")
    except Exception as e:
        safe_print(f"[ERROR] Storage info error: {e}")
    
    # Test 7: File list
    safe_print("\n7. Testing File List...")
    try:
        files = client.get("/files/list")
        safe_print(f"[OK] Files: {files}")
    except Exception as e:
        safe_print(f"[ERROR] File list error: {e}")
    
    # Test 8: Lock vault
    safe_print("\n8. Testing Vault Lock...")
    try:
        lock_result = client.post("/vault/lock")
        safe_print(f"[OK] Vault locked: {lock_result}")
    except Exception as e:
        safe_print(f"[ERROR] Vault lock error: {e}")
    
    # Test 9: Unlock vault
    safe_print("\n9. Testing Vault Unlock...")
    try:
        unlock_result = client.post("/vault/unlock", {
            "master_password": "test_password_api_2024",
            "salt": vault_salt
        })
        safe_print(f"[OK] Vault unlocked: {unlock_result}")
    except Exception as e:
        safe_print(f"[ERROR] Vault unlock error: {e}")
    
    safe_print("\n[PARTY] API Test Complete!")
    return True

def test_file_upload():
    """Test file upload functionality"""
    safe_print("\n[FILE] Testing File Upload...")
    
    client = BrontoBoxAPIClient()
    
    # Create a test file
    test_content = """
[DINO] BrontoBox API Test File

This is a test file for the API upload functionality.
Created: """ + str(time.time()) + """

Content includes:
- API testing data
- Encryption verification
- Upload/download workflow

BrontoBox rocks! [BOX]
    """.strip()
    
    test_file_path = "api_test_file.txt"
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    try:
        # Upload file
        with open(test_file_path, 'rb') as f:
            upload_response = client.post(
                "/files/upload",
                data={"metadata": json.dumps({"test": True, "api_upload": True})},
                files={"file": f}
            )
        
        safe_print(f"[OK] File upload: {upload_response}")
        
        if upload_response.get("file_id"):
            file_id = upload_response["file_id"]
            
            # Test download
            safe_print("[DOWN] Testing file download...")
            download_url = f"{client.base_url}/files/{file_id}/download"
            download_response = client.session.get(download_url)
            
            if download_response.status_code == 200:
                safe_print("[OK] File download successful")
                safe_print(f"   Downloaded {len(download_response.content)} bytes")
                
                # Verify content
                downloaded_content = download_response.content.decode('utf-8')
                if downloaded_content == test_content:
                    safe_print("[OK] File integrity verified - content matches!")
                else:
                    safe_print("[ERROR] File integrity check failed")
            else:
                safe_print(f"[ERROR] File download failed: {download_response.status_code}")
        
    except Exception as e:
        safe_print(f"[ERROR] File upload test error: {e}")
    
    finally:
        # Cleanup
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

def test_websocket():
    """Test WebSocket connection"""
    safe_print("\n[PLUG] Testing WebSocket Connection...")
    
    def on_message(ws, message):
        safe_print(f"[MESSAGE] WebSocket message: {message}")
    
    def on_error(ws, error):
        safe_print(f"[ERROR] WebSocket error: {error}")
    
    def on_close(ws, close_status_code, close_msg):
        safe_print("[PLUG] WebSocket connection closed")
    
    def on_open(ws):
        safe_print("[OK] WebSocket connected")
        # Send test message
        ws.send("Hello BrontoBox API!")
        
        # Close after 3 seconds
        def close_connection():
            time.sleep(3)
            ws.close()
        
        thread = threading.Thread(target=close_connection)
        thread.start()
    
    try:
        ws = websocket.WebSocketApp("ws://127.0.0.1:8000/ws",
                                    on_open=on_open,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)
        
        ws.run_forever()
        
    except Exception as e:
        safe_print(f"[ERROR] WebSocket test error: {e}")

def interactive_test():
    """Interactive API testing"""
    safe_print("\n[GAME] Interactive API Testing")
    safe_print("Available commands:")
    safe_print("1. health - Check API health")
    safe_print("2. init - Initialize vault")
    safe_print("3. status - Check vault status")
    safe_print("4. accounts - List accounts")
    safe_print("5. storage - Get storage info")
    safe_print("6. files - List files")
    safe_print("7. upload - Upload test file")
    safe_print("8. ws - Test WebSocket")
    safe_print("9. quit - Exit")
    
    client = BrontoBoxAPIClient()
    
    while True:
        command = input("\n> ").strip().lower()
        
        if command == "quit":
            break
        elif command == "health":
            try:
                result = client.get("/health")
                safe_print(json.dumps(result, indent=2))
            except Exception as e:
                safe_print(f"Error: {e}")
        elif command == "init":
            try:
                password = input("Master password: ")
                result = client.post("/vault/initialize", {"master_password": password})
                safe_print(json.dumps(result, indent=2))
            except Exception as e:
                safe_print(f"Error: {e}")
        elif command == "status":
            try:
                result = client.get("/vault/status")
                safe_print(json.dumps(result, indent=2))
            except Exception as e:
                safe_print(f"Error: {e}")
        elif command == "accounts":
            try:
                result = client.get("/accounts/list")
                safe_print(json.dumps(result, indent=2))
            except Exception as e:
                safe_print(f"Error: {e}")
        elif command == "storage":
            try:
                result = client.get("/storage/info")
                safe_print(json.dumps(result, indent=2))
            except Exception as e:
                safe_print(f"Error: {e}")
        elif command == "files":
            try:
                result = client.get("/files/list")
                safe_print(json.dumps(result, indent=2))
            except Exception as e:
                safe_print(f"Error: {e}")
        elif command == "upload":
            test_file_upload()
        elif command == "ws":
            test_websocket()
        else:
            safe_print("Unknown command. Type 'quit' to exit.")

if __name__ == "__main__":
    safe_print("[DINO] BrontoBox API Test Client")
    safe_print("=" * 40)
    
    # Check if server is running
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if response.status_code == 200:
            safe_print("[OK] API Server is running!")
        else:
            safe_print("[ERROR] API Server returned error")
            exit(1)
    except requests.exceptions.RequestException:
        safe_print("[ERROR] API Server is not running!")
        safe_print("Please start the server first: python brontobox_api.py")
        exit(1)
    
    safe_print("\nChoose test mode:")
    safe_print("1. Run all tests")
    safe_print("2. Test file upload only")
    safe_print("3. Test WebSocket only")
    safe_print("4. Interactive testing")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        test_api_endpoints()
        test_file_upload()
        test_websocket()
    elif choice == "2":
        test_file_upload()
    elif choice == "3":
        test_websocket()
    elif choice == "4":
        interactive_test()
    else:
        safe_print("Invalid choice, running all tests...")
        test_api_endpoints()
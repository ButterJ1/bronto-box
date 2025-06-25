from vault_core import VaultCore

# Initialize vault
vault = VaultCore()
init_data = vault.initialize_vault("my_secure_password")

# Encrypt a file  
encrypted_result = vault.encrypt_file("confidential.pdf")

# Later: decrypt the file
vault.decrypt_file(encrypted_result, "restored_confidential.pdf")
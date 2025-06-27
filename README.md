# BrontoBox

**Secure Distributed Storage System**

BrontoBox is a privacy-focused distributed storage solution that transforms multiple Google Drive accounts into a unified, encrypted storage network. By distributing encrypted file chunks across multiple cloud accounts, BrontoBox provides enhanced security, redundancy, and storage capacity while maintaining complete user control over data.

## Overview

Traditional cloud storage services require users to trust third-party providers with their sensitive data. BrontoBox takes a different approach by implementing client-side encryption and distributing encrypted chunks across multiple user-controlled Google Drive accounts. This architecture ensures that no single service provider has access to complete files, while providing users with significantly expanded storage capacity.

The system operates on the principle of security through distribution. Files are encrypted locally using AES-256-GCM encryption before being split into chunks and distributed across multiple Google Drive accounts. Each chunk is individually encrypted and stored with randomized naming, making it impossible for external observers to reconstruct original files without access to the master vault.

## Core Capabilities

### Distributed Encryption
BrontoBox employs military-grade encryption standards to protect user data. Files are encrypted using AES-256-GCM with PBKDF2-SHA256 key derivation, ensuring that even if individual storage accounts are compromised, the underlying data remains secure. The encryption process occurs entirely on the user's device, meaning sensitive data never leaves the local environment in an unencrypted state.

### Multi-Account Storage Aggregation
The system can utilize up to four Google Drive accounts simultaneously, effectively creating a storage pool of up to 60GB of free cloud storage. Files are intelligently distributed across available accounts based on space availability and redundancy requirements. This approach not only maximizes storage capacity but also provides built-in backup protection through geographic and service distribution.

### Vault-Based Security Model
User data is protected by a secure vault system that requires both a master password and a cryptographic salt for access. This dual-authentication approach ensures that even with access to vault files, attackers cannot decrypt user data without the correct credentials. The vault system supports multiple independent vaults, allowing users to maintain separate encrypted environments for different purposes.

### Intelligent File Recovery
BrontoBox includes sophisticated file discovery mechanisms that can automatically detect and recover files from previous sessions. When connecting storage accounts, the system scans for existing encrypted chunks and reconstructs file manifests, ensuring that users never lose access to their data even when switching devices or reinstalling the application.

### Comprehensive Backup and Restore
The system provides enterprise-grade backup and restore capabilities. Users can export encrypted vault configurations and file registries, enabling complete system recovery on new devices. The restore process includes automatic account mapping and intelligent chunk reconstruction, making data migration seamless and reliable.

## Technical Architecture

### Encryption Pipeline
The BrontoBox encryption pipeline implements a multi-layered security model. Master passwords are processed through PBKDF2-SHA256 with 100,000 iterations to generate encryption keys. Files are encrypted using AES-256-GCM, which provides both confidentiality and authentication. Each encrypted chunk includes integrity verification to detect tampering or corruption.

### Distributed Storage Logic
File distribution follows an intelligent algorithm that considers account capacity, availability, and redundancy requirements. Large files are split into chunks of configurable size, with each chunk encrypted independently. The system maintains detailed manifests that track chunk locations, enabling efficient reconstruction while preserving security through distribution.

### Account Management
Google Drive integration utilizes OAuth 2.0 authentication with restricted scope permissions. BrontoBox only requests access to files it creates, ensuring that existing Google Drive content remains private and unaffected. Account credentials are stored using the operating system's secure credential management APIs.

### Vault System
The vault architecture implements a secure key derivation and storage system. Master keys are derived from user passwords and used to encrypt file manifests, account information, and system metadata. Vault verification ensures that only authorized users can access encrypted data, with built-in protection against brute force attacks.

## Security Model

BrontoBox implements a zero-knowledge security architecture where the application never has access to unencrypted user data outside of the local environment. All cryptographic operations occur on the user's device, and encrypted chunks are distributed without revealing file structure or content to storage providers.

The system employs defense in depth through multiple security layers. Even if an attacker gains access to all storage accounts, the distributed nature of chunk storage and individual chunk encryption make data reconstruction computationally infeasible without the master vault credentials.

Vault verification mechanisms prevent unauthorized access even with physical access to vault files. The combination of master password and cryptographic salt creates a two-factor authentication system that significantly increases security against credential-based attacks.

## Getting Started

### System Requirements
BrontoBox requires a modern operating system with Python 3.8 or higher and Node.js 14 or higher. The application supports Windows, macOS, and Linux environments. Users need access to Google accounts with Google Drive enabled for storage functionality.

### Initial Setup
Installation begins with configuring the Python backend environment and installing required dependencies. The Electron frontend provides a user-friendly interface for vault creation and account management. Users create a master vault by providing a strong password, which generates the cryptographic infrastructure for secure storage.

### Account Configuration
Google Drive accounts are connected through a secure OAuth flow that grants BrontoBox limited access to create and manage its own files. The system automatically creates hidden storage folders in each connected account and begins distributing encrypted chunks according to availability and redundancy requirements.

### File Operations
Users interact with BrontoBox through an intuitive file management interface that handles encryption and distribution transparently. File uploads are automatically encrypted, chunked, and distributed across connected accounts. Downloads reconstruct files from distributed chunks and decrypt them locally before presenting them to the user.

## Advanced Features

### Multiple Vault Support
BrontoBox supports multiple independent vaults, each with its own encryption keys and storage allocation. This capability enables users to maintain separate encrypted environments for different security domains, such as personal files, business documents, or shared family storage.

### File Discovery and Recovery
The system includes intelligent algorithms that can detect and recover files from previous installations or different devices. When connecting storage accounts, BrontoBox scans for existing encrypted chunks and reconstructs file manifests, ensuring continuity across device changes or system migrations.

### Backup and Migration
Comprehensive backup functionality enables users to export vault configurations and file registries for disaster recovery or device migration. The restore process includes automatic account mapping and chunk verification, ensuring reliable data recovery even when moving between different Google accounts or devices.

### Account Mapping and Recovery
Advanced account recovery mechanisms can automatically map old account identifiers to new authentication sessions, resolving common issues that occur when re-authenticating Google accounts. This functionality ensures that existing encrypted chunks remain accessible even when account credentials change.

## Development and Architecture

BrontoBox is built using a hybrid architecture that combines a Python backend for cryptographic operations with an Electron frontend for cross-platform compatibility. The backend implements the core encryption, chunking, and storage logic, while the frontend provides an intuitive user interface and integrates with operating system file management.

The system follows security-first design principles with comprehensive input validation, secure memory management, and protection against common attack vectors. Code architecture emphasizes modularity and testability, with clear separation between cryptographic functions, storage management, and user interface components.

API design follows RESTful principles with comprehensive error handling and logging. The WebSocket integration provides real-time updates for file operations and system status, enhancing user experience during long-running operations like large file uploads or account synchronization.

## Contributing and Support

BrontoBox is designed as a secure, self-hosted solution that prioritizes user privacy and data sovereignty. The modular architecture enables customization and extension while maintaining security guarantees through well-defined interfaces and comprehensive testing.

System logs provide detailed information for troubleshooting and optimization. The application includes diagnostic tools for verifying vault integrity, account connectivity, and chunk distribution, enabling users to maintain optimal system performance and security.

---

**BrontoBox Version 1.0** - Secure Distributed Storage with Enhanced Vault Verification and Unified File Experience
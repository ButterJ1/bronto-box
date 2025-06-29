// src/services/APIService.js - COMPATIBLE VERSION FOR YOUR SETUP
// Based on your original structure with comprehensive enhancements
// netstat -ano | findstr :8000
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

// Enhanced axios instance with better production configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 seconds default
  headers: {
    'Content-Type': 'application/json',
  },
});

// Global state for backend monitoring
let backendReady = false;
let healthCheckInterval = null;
let connectionRetries = 0;
const MAX_RETRIES = 3;

// Enhanced request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Enhanced response interceptor with comprehensive error handling
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    backendReady = true;
    connectionRetries = 0; // Reset on successful response
    return response;
  },
  async (error) => {
    // Enhanced error logging with null checks
    const status = error.response?.status || 'No Status';
    const data = error.response?.data || 'No Response Data';
    const message = error.message || 'Unknown Error';
    
    console.error(`API Response Error: ${status}`, data);
    console.error(`Error Type: ${error.code || 'Unknown'} - ${message}`);
    
    // Handle specific error cases
    if (error.code === 'ECONNREFUSED') {
      backendReady = false;
      
      // Auto-retry for connection refused (backend not ready)
      if (connectionRetries < MAX_RETRIES) {
        connectionRetries++;
        console.log(`Retrying request (${connectionRetries}/${MAX_RETRIES})...`);
        
        // Wait for backend to be ready
        await waitForBackend(10000); // 10 seconds
        
        // Retry the original request
        return api.request(error.config);
      }
      
      throw new Error('Cannot connect to BrontoBox API server. Please ensure it is running.');
    }
    
    if (error.code === 'ECONNABORTED') {
      // Handle timeout specifically for OAuth which can take time
      if (error.config?.url?.includes('/accounts/authenticate')) {
        throw new Error('Google authentication timed out. This is normal - please try again and complete the authentication quickly.');
      }
      throw new Error(`Request timed out after ${error.config?.timeout || 60000}ms`);
    }
    
    if (error.response?.status === 401) {
      throw new Error('Vault must be unlocked first.');
    }
    
    if (error.response?.status === 500) {
      throw new Error(error.response?.data?.detail || 'Internal server error');
    }
    
    // Re-throw the original error with better context
    throw error;
  }
);

// Backend health monitoring functions
async function checkBackendHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, { 
      method: 'GET',
      signal: AbortSignal.timeout ? AbortSignal.timeout(5000) : undefined
    });
    
    if (response.ok) {
      const data = await response.json();
      if (data.status === 'healthy') {
        if (!backendReady) {
          console.log('Backend is now ready and healthy!');
          backendReady = true;
          
          // Dispatch custom event
          if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('backendReady', {
              detail: { status: 'ready', health: data }
            }));
          }
        }
        return true;
      }
    }
  } catch (error) {
    if (backendReady) {
      console.log('Backend became unresponsive');
      backendReady = false;
      
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('backendDisconnected', {
          detail: { error: error.message }
        }));
      }
    }
  }
  return false;
}

async function waitForBackend(timeout = 30000) {
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    if (await checkBackendHealth()) {
      return true;
    }
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  return false;
}

function startHealthMonitoring() {
  // Initial check
  checkBackendHealth();
  
  // Set up periodic monitoring
  if (!healthCheckInterval) {
    healthCheckInterval = setInterval(checkBackendHealth, 5000); // Check every 5 seconds
  }
}

function stopHealthMonitoring() {
  if (healthCheckInterval) {
    clearInterval(healthCheckInterval);
    healthCheckInterval = null;
  }
}

// Enhanced APIService class with all endpoints from your Python API
export class APIService {
  // Health and status endpoints
  static async getHealth() {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      console.warn('Health check failed, API may be starting up');
      throw error;
    }
  }

  static async getVaultStatus() {
    const response = await api.get('/vault/status');
    return response.data;
  }

  // Vault management
  static async initializeVault(masterPassword) {
    const response = await api.post('/vault/initialize', {
      master_password: masterPassword
    });
    return response.data;
  }

  static async unlockVault(masterPassword, salt) {
    const response = await api.post('/vault/unlock', {
      master_password: masterPassword,
      salt: salt
    });
    return response.data;
  }

  static async lockVault() {
    const response = await api.post('/vault/lock');
    return response.data;
  }

  static async listVaults() {
    const response = await api.get('/vault/list');
    return response.data;
  }

  // Account management
  static async setupOAuth(credentialsFile = 'credentials.json') {
    const response = await api.post('/accounts/setup-oauth', {}, {
      params: { credentials_file: credentialsFile }
    });
    return response.data;
  }

  // Enhanced OAuth with better timeout handling
  static async authenticateAccount(accountName, credentialsFile = 'credentials.json') {
    try {
      const response = await api.post('/accounts/authenticate', {
        account_name: accountName,
        credentials_file: credentialsFile
      }, {
        timeout: 120000 // 2 minutes for OAuth flow
      });
      return response.data;
    } catch (error) {
      if (error.code === 'ECONNABORTED') {
        throw new Error('Authentication timed out. Please try again and complete Google OAuth quickly.');
      }
      throw error;
    }
  }

  static async listAccounts() {
    const response = await api.get('/accounts/list');
    return response.data;
  }

  static async testAccount(accountId) {
    const response = await api.get(`/accounts/${accountId}/test`);
    return response.data;
  }

  static async refreshTokens() {
    const response = await api.post('/accounts/refresh-tokens');
    return response.data;
  }

  static async getPersistenceStatus() {
    const response = await api.get('/accounts/persistence-status');
    return response.data;
  }

  // Storage information
  static async getStorageInfo() {
    const response = await api.get('/storage/info');
    return response.data;
  }

  // Enhanced file management with better error handling
  static async uploadFile(file, metadata = {}) {
    console.log(`Starting upload: ${file.name} (${this.formatFileSize(file.size)})`);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('metadata', JSON.stringify(metadata));

      const response = await api.post('/files/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 300000, // 5 minutes for large files
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          console.log(`Upload progress: ${percentCompleted}% - ${file.name}`);
          
          // Dispatch progress event
          if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('uploadProgress', {
              detail: { fileName: file.name, percent: percentCompleted }
            }));
          }
        },
      });
      
      console.log(`Upload completed: ${file.name}`);
      return response.data;
    } catch (error) {
      console.error(`Upload failed: ${file.name}`, error);
      
      // Provide more specific error messages
      if (error.code === 'ECONNABORTED') {
        throw new Error(`Upload timeout: ${file.name} took too long to upload`);
      } else if (error.response?.status === 413) {
        throw new Error(`File too large: ${file.name} exceeds size limit`);
      } else if (error.response?.status === 507) {
        throw new Error(`Storage full: Not enough space to upload ${file.name}`);
      } else {
        throw new Error(`Upload failed: ${file.name} - ${error.message}`);
      }
    }
  }

  static async listFiles() {
    const response = await api.get('/files/list');
    return response.data;
  }

  static async downloadFile(fileId) {
    const response = await api.get(`/files/${fileId}/download`, {
      responseType: 'blob',
      timeout: 300000, // 5 minutes for large downloads
    });
    return response;
  }

  static async deleteFile(fileId) {
    const response = await api.delete(`/files/${fileId}`);
    return response.data;
  }

  // NEW: Enhanced file discovery and statistics
  static async refreshFileDiscovery() {
    const response = await api.post('/files/refresh-discovery');
    return response.data;
  }

  static async getFileStatistics() {
    const response = await api.get('/files/statistics');
    return response.data;
  }

  // NEW: Drive management endpoints
  static async listBrontoBoxFilesForAccount(accountId) {
    const response = await api.get(`/drive/brontobox-files/${accountId}`);
    return response.data;
  }

  static async listRawChunks(accountId) {
    const response = await api.get(`/drive/raw-chunks/${accountId}`);
    return response.data;
  }

  static async listDriveChunks(accountId, sortBy = 'date', order = 'desc', limit = null, search = null) {
    const params = { sort_by: sortBy, order, limit, search };
    const response = await api.get(`/drive/chunks/${accountId}`, { params });
    return response.data;
  }

  static async searchDriveChunks(accountId, query, searchType = 'all') {
    const response = await api.get(`/drive/search/${accountId}`, {
      params: { query, search_type: searchType }
    });
    return response.data;
  }

  static async getDriveStats(accountId) {
    const response = await api.get(`/drive/stats/${accountId}`);
    return response.data;
  }

  static async downloadRawChunk(accountId, fileId) {
    const response = await api.get(`/drive/download/${accountId}/${fileId}`, {
      responseType: 'blob'
    });
    return response;
  }

  static async deleteRawChunk(accountId, fileId) {
    const response = await api.delete(`/drive/delete/${accountId}/${fileId}`);
    return response.data;
  }

  static async getBrontoBoxFolderInfo(accountId) {
    const response = await api.get(`/drive/folder-info/${accountId}`);
    return response.data;
  }

  // Registry management
  static async saveFileRegistry() {
    const response = await api.post('/files/save-registry');
    return response.data;
  }

  static async loadFileRegistry() {
    const response = await api.post('/files/load-registry');
    return response.data;
  }

  // NEW: Data management endpoints
  static async exportFileRegistry() {
    const response = await api.get('/data/export-registry', {
      responseType: 'blob'
    });
    return response;
  }

  static async backupVaultInfo() {
    const response = await api.get('/data/backup-vault-info', {
      responseType: 'blob'
    });
    return response;
  }

  static async clearAllData() {
    const response = await api.post('/data/clear-all');
    return response.data;
  }

  static async importFileRegistry(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/data/import-registry', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  static async getSystemInfo() {
    const response = await api.get('/data/system-info');
    return response.data;
  }

  // NEW: Backup and restore endpoints
  static async detectBackupFiles() {
    const response = await api.get('/backup/detect');
    return response.data;
  }

  static async restoreVaultFromBackup(backupFile, masterPassword) {
    const response = await api.post('/vault/restore-from-backup', {
      backup_file: backupFile,
      master_password: masterPassword
    });
    return response.data;
  }

  static async importRegistryFromFile(registryFile) {
    const response = await api.post('/data/import-registry-from-file', {
      registry_file: registryFile
    });
    return response.data;
  }

  static async analyzeMissingAccounts() {
    const response = await api.get('/restore/analyze-missing-accounts');
    return response.data;
  }

  static async completeRestoration(vaultBackupFile, registryBackupFile, masterPassword) {
    const response = await api.post('/restore/complete-restoration', {
      vault_backup_file: vaultBackupFile,
      registry_backup_file: registryBackupFile,
      master_password: masterPassword
    });
    return response.data;
  }

  static async checkBackupCompatibility(vaultBackup, registryBackup = null) {
    const response = await api.get('/restore/check-compatibility', {
      params: { vault_backup: vaultBackup, registry_backup: registryBackup }
    });
    return response.data;
  }

  static async fixAccountMapping() {
    const response = await api.post('/restore/fix-account-mapping');
    return response.data;
  }

  static async guideAccountRecovery() {
    const response = await api.get('/restore/guide-account-recovery');
    return response.data;
  }

  static async getRestoreStatus() {
    const response = await api.get('/restore/status');
    return response.data;
  }

  static async validateRestorePassword(vaultBackupFile, masterPassword) {
    const response = await api.post('/restore/validate-password', {
      vault_backup_file: vaultBackupFile,
      master_password: masterPassword
    });
    return response.data;
  }

  // NEW: Debug endpoints
  static async debugFileInfo(fileId) {
    const response = await api.get(`/debug/file/${fileId}`);
    return response.data;
  }

  static async debugFiles() {
    const response = await api.get('/debug/files');
    return response.data;
  }

  static async debugAccountComparison() {
    const response = await api.get('/debug/account-comparison');
    return response.data;
  }

  // Enhanced WebSocket connection with better error handling and reconnection
  static createWebSocket(onMessage, onError, onClose) {
    let ws = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    const reconnectDelay = 3000; // 3 seconds
    let reconnectTimer = null;
    
    const connect = () => {
      try {
        console.log('Attempting WebSocket connection...');
        ws = new WebSocket('ws://127.0.0.1:8000/ws');
        
        ws.onopen = () => {
          console.log('WebSocket connected successfully');
          reconnectAttempts = 0; // Reset on successful connection
          
          // Clear any pending reconnection timer
          if (reconnectTimer) {
            clearTimeout(reconnectTimer);
            reconnectTimer = null;
          }
          
          // Dispatch connection event
          if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('websocketConnected'));
          }
        };
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('WebSocket message:', data);
            if (onMessage) onMessage(data);
          } catch (error) {
            console.error('WebSocket message parse error:', error);
            if (onMessage) onMessage({ type: 'echo', data: event.data });
          }
        };
        
        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          if (onError) onError(error);
        };
        
        ws.onclose = (event) => {
          console.log(`WebSocket closed: ${event.code} - ${event.reason}`);
          
          // Dispatch disconnection event
          if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('websocketDisconnected', {
              detail: { code: event.code, reason: event.reason }
            }));
          }
          
          // Only attempt reconnection if it wasn't a clean close and we haven't exceeded max attempts
          if (event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            console.log(`Reconnecting WebSocket (attempt ${reconnectAttempts}/${maxReconnectAttempts})...`);
            
            reconnectTimer = setTimeout(connect, reconnectDelay * reconnectAttempts);
          } else if (reconnectAttempts >= maxReconnectAttempts) {
            console.warn('Max WebSocket reconnection attempts reached. Giving up.');
            if (onError) onError(new Error('WebSocket connection failed after multiple attempts'));
          }
          
          if (onClose) onClose(event);
        };
        
      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        if (onError) onError(error);
      }
    };
    
    // Initial connection
    connect();
    
    // Return an object with control methods
    return {
      close: () => { 
        if (reconnectTimer) {
          clearTimeout(reconnectTimer);
          reconnectTimer = null;
        }
        if (ws) {
          reconnectAttempts = maxReconnectAttempts; // Prevent reconnection
          ws.close(1000, 'Manual close');
        }
      },
      readyState: () => ws ? ws.readyState : WebSocket.CLOSED,
      send: (data) => {
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(typeof data === 'string' ? data : JSON.stringify(data));
        } else {
          console.warn('WebSocket not ready, message not sent:', data);
        }
      }
    };
  }

  // Backend connection utilities
  static async checkBackendConnection() {
    return await checkBackendHealth();
  }

  static getBackendStatus() {
    return {
      ready: backendReady,
      baseURL: API_BASE_URL,
      retries: connectionRetries
    };
  }

  static async waitForBackend(timeout = 30000) {
    return await waitForBackend(timeout);
  }

  // Utility methods
  static formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  static formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  }

  static calculateStoragePercentage(used, total) {
    if (total === 0) return 0;
    return Math.round((used / total) * 100);
  }

  // Cleanup method
  static cleanup() {
    stopHealthMonitoring();
  }

  // Initialize health monitoring when first method is called
  static ensureInitialized() {
    if (!healthCheckInterval) {
      startHealthMonitoring();
    }
  }
}

// Initialize health monitoring when module loads
startHealthMonitoring();

// Export both class and default for compatibility
export default APIService;
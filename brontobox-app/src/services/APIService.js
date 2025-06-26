// src/services/APIService.js - FIXED ERROR HANDLING
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // Increased to 60 seconds for file uploads
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
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

// Response interceptor for error handling - FIXED VERSION
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    // FIXED: Better error logging with null checks
    const status = error.response?.status || 'No Status';
    const data = error.response?.data || 'No Response Data';
    const message = error.message || 'Unknown Error';
    
    console.error(`API Response Error: ${status}`, data);
    console.error(`Error Type: ${error.code || 'Unknown'} - ${message}`);
    
    // Handle specific error cases
    if (error.code === 'ECONNREFUSED') {
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

export class APIService {
  // Health and status endpoints
  static async getHealth() {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      // Graceful fallback for health checks
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

  // Account management
  static async setupOAuth(credentialsFile = 'credentials.json') {
    const response = await api.post('/accounts/setup-oauth', {
      credentials_file: credentialsFile
    });
    return response.data;
  }

  // FIXED: Better timeout handling for OAuth
  static async authenticateAccount(accountName) {
    try {
      const response = await api.post('/accounts/authenticate', {
        account_name: accountName
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

  // Storage information
  static async getStorageInfo() {
    const response = await api.get('/storage/info');
    return response.data;
  }

  // File management with better error handling
  static async uploadFile(file, metadata = {}) {
    console.log(`📤 Starting upload: ${file.name} (${this.formatFileSize(file.size)})`);
    
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
          console.log(`📤 Upload progress: ${percentCompleted}% - ${file.name}`);
        },
      });
      
      console.log(`✅ Upload completed: ${file.name}`);
      return response.data;
    } catch (error) {
      console.error(`❌ Upload failed: ${file.name}`, error);
      
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

  // Registry management
  static async saveFileRegistry() {
    const response = await api.post('/files/save-registry');
    return response.data;
  }

  static async loadFileRegistry() {
    const response = await api.post('/files/load-registry');
    return response.data;
  }

  // Improved WebSocket connection with better error handling
  static createWebSocket(onMessage, onError, onClose) {
    let ws = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    const reconnectDelay = 3000; // 3 seconds
    
    const connect = () => {
      try {
        console.log('🔌 Attempting WebSocket connection...');
        ws = new WebSocket('ws://127.0.0.1:8000/ws');
        
        ws.onopen = () => {
          console.log('🔌 WebSocket connected successfully');
          reconnectAttempts = 0; // Reset on successful connection
        };
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('📨 WebSocket message:', data);
            if (onMessage) onMessage(data);
          } catch (error) {
            console.error('❌ WebSocket message parse error:', error);
            if (onMessage) onMessage({ type: 'echo', data: event.data });
          }
        };
        
        ws.onerror = (error) => {
          console.error('❌ WebSocket error:', error);
          if (onError) onError(error);
        };
        
        ws.onclose = (event) => {
          console.log(`🔌 WebSocket closed: ${event.code} - ${event.reason}`);
          
          // Only attempt reconnection if it wasn't a clean close and we haven't exceeded max attempts
          if (event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            console.log(`🔄 Reconnecting WebSocket (attempt ${reconnectAttempts}/${maxReconnectAttempts})...`);
            setTimeout(connect, reconnectDelay);
          } else if (reconnectAttempts >= maxReconnectAttempts) {
            console.warn('⚠️ Max WebSocket reconnection attempts reached. Giving up.');
            if (onError) onError(new Error('WebSocket connection failed after multiple attempts'));
          }
          
          if (onClose) onClose(event);
        };
        
      } catch (error) {
        console.error('❌ Failed to create WebSocket:', error);
        if (onError) onError(error);
      }
    };
    
    // Initial connection
    connect();
    
    // Return an object with a close method for cleanup
    return {
      close: () => {
        if (ws) {
          reconnectAttempts = maxReconnectAttempts; // Prevent reconnection
          ws.close(1000, 'Manual close');
        }
      },
      readyState: () => ws ? ws.readyState : WebSocket.CLOSED
    };
  }

  // Check if backend is reachable
  static async checkBackendConnection() {
    try {
      const response = await fetch(`${API_BASE_URL}/health`, { 
        method: 'GET',
        timeout: 5000 
      });
      return response.ok;
    } catch (error) {
      console.error('❌ Backend connection check failed:', error);
      return false;
    }
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
}

// Export singleton instance for convenience
export default APIService;
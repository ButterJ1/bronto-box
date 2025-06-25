// src/services/APIService.js
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout
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

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.status, error.response?.data);
    
    // Handle specific error cases
    if (error.code === 'ECONNREFUSED') {
      throw new Error('Cannot connect to BrontoBox API server. Please ensure it is running.');
    }
    
    if (error.response?.status === 401) {
      throw new Error('Vault must be unlocked first.');
    }
    
    if (error.response?.status === 500) {
      throw new Error(error.response?.data?.detail || 'Internal server error');
    }
    
    throw error;
  }
);

export class APIService {
  // Health and status endpoints
  static async getHealth() {
    const response = await api.get('/health');
    return response.data;
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

  static async authenticateAccount(accountName) {
    const response = await api.post('/accounts/authenticate', {
      account_name: accountName
    });
    return response.data;
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

  // File management
  static async uploadFile(file, metadata = {}) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('metadata', JSON.stringify(metadata));

    const response = await api.post('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        console.log(`Upload progress: ${percentCompleted}%`);
      },
    });
    return response.data;
  }

  static async listFiles() {
    const response = await api.get('/files/list');
    return response.data;
  }

  static async downloadFile(fileId) {
    const response = await api.get(`/files/${fileId}/download`, {
      responseType: 'blob'
    });
    return response;
  }

  static async deleteFile(fileId) {
    const response = await api.delete(`/files/${fileId}`);
    return response.data;
  }

  // WebSocket connection for real-time updates
  static createWebSocket(onMessage, onError, onClose) {
    const ws = new WebSocket('ws://127.0.0.1:8000/ws');
    
    ws.onopen = () => {
      console.log('WebSocket connected');
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
      console.log('WebSocket closed:', event.code, event.reason);
      if (onClose) onClose(event);
    };
    
    return ws;
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
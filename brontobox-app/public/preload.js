// public/preload.js
const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // File operations
  selectFiles: () => ipcRenderer.invoke('select-files'),
  selectDownloadLocation: (fileName) => ipcRenderer.invoke('select-download-location', fileName),
  showItemInFolder: (fullPath) => ipcRenderer.invoke('show-item-in-folder', fullPath),
  
  // Dialog operations
  showMessageBox: (options) => ipcRenderer.invoke('show-message-box', options),
  
  // App info
  getAppVersion: () => ipcRenderer.invoke('app-version'),
  
  // Menu event listeners
  onMenuAddFiles: (callback) => {
    ipcRenderer.on('menu-add-files', callback);
  },
  onMenuNewVault: (callback) => {
    ipcRenderer.on('menu-new-vault', callback);
  },
  onMenuLockVault: (callback) => {
    ipcRenderer.on('menu-lock-vault', callback);
  },
  onMenuAddAccount: (callback) => {
    ipcRenderer.on('menu-add-account', callback);
  },
  onMenuManageAccounts: (callback) => {
    ipcRenderer.on('menu-manage-accounts', callback);
  },
  
  // Remove listeners
  removeAllListeners: (channel) => {
    ipcRenderer.removeAllListeners(channel);
  }
});

// Expose a limited API for security
contextBridge.exposeInMainWorld('brontoboxAPI', {
  // Platform info
  platform: process.platform,
  
  // Version info
  versions: {
    node: process.versions.node,
    chrome: process.versions.chrome,
    electron: process.versions.electron
  },
  
  // Environment
  isDevelopment: process.env.NODE_ENV === 'development'
});

// Log that preload script has loaded
console.log('BrontoBox preload script loaded');
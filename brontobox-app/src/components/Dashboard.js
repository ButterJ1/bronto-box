// src/components/Dashboard.js
import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Header from './Header';
import Sidebar from './Sidebar';
import FileArea from './FileArea';
import StorageOverview from './StorageOverview';
import UploadProgress from './UploadProgress';
import { APIService } from '../services/APIService';
import { useNotification } from './NotificationContext';

const Dashboard = ({ onVaultLock }) => {
  const [storageInfo, setStorageInfo] = useState({
    total_accounts: 0,
    total_capacity_gb: 0,
    total_used_gb: 0,
    total_available_gb: 0,
    usage_percentage: 0,
    accounts: []
  });

  const [files, setFiles] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [uploadProgress, setUploadProgress] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [websocket, setWebsocket] = useState(null);

  const { showNotification } = useNotification();

  // Load initial data
  const loadData = useCallback(async (showLoadingState = true) => {
    if (showLoadingState) {
      setLoading(true);
    } else {
      setRefreshing(true);
    }

    try {
      // Load storage info and files in parallel
      const [storageResponse, filesResponse] = await Promise.all([
        APIService.getStorageInfo(),
        APIService.listFiles()
      ]);

      setStorageInfo(storageResponse);
      setFiles(filesResponse.files || []);

      // Set default selected account
      if (storageResponse.accounts && storageResponse.accounts.length > 0 && !selectedAccount) {
        setSelectedAccount(storageResponse.accounts[0].account_id);
      }

    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      showNotification('Failed to load data: ' + error.message, 'error');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedAccount, showNotification]);

  // Setup WebSocket for real-time updates
  useEffect(() => {
    const ws = APIService.createWebSocket(
      (message) => {
        console.log('WebSocket update:', message);
        
        switch (message.type) {
          case 'file_uploaded':
            showNotification(`File uploaded: ${message.data.filename}`, 'success');
            loadData(false);
            break;
          case 'file_deleted':
            showNotification(`File deleted: ${message.data.filename}`, 'info');
            loadData(false);
            break;
          case 'account_added':
            showNotification(`Account added: ${message.data.account.email}`, 'success');
            loadData(false);
            break;
          case 'vault_locked':
            showNotification('Vault locked', 'info');
            onVaultLock();
            break;
          default:
            console.log('Unknown message type:', message.type);
        }
      },
      (error) => {
        console.error('WebSocket error:', error);
      },
      (event) => {
        console.log('WebSocket closed:', event);
        // Attempt to reconnect after 5 seconds
        setTimeout(() => {
          if (!websocket || websocket.readyState === WebSocket.CLOSED) {
            console.log('Attempting to reconnect WebSocket...');
            loadData(false);
          }
        }, 5000);
      }
    );

    setWebsocket(ws);

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [loadData, onVaultLock, showNotification]);

  // Load data on mount
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Handle file upload
  const handleFileUpload = async (files) => {
    const uploads = files.map(file => ({
      id: Date.now() + Math.random(),
      file,
      progress: 0,
      status: 'uploading',
      error: null
    }));

    setUploadProgress(prev => [...prev, ...uploads]);

    for (const upload of uploads) {
      try {
        // Update progress to show started
        setUploadProgress(prev => 
          prev.map(u => u.id === upload.id ? { ...u, progress: 10 } : u)
        );

        const metadata = {
          uploaded_at: new Date().toISOString(),
          original_name: upload.file.name,
          size: upload.file.size
        };

        // Simulate progress updates
        const progressInterval = setInterval(() => {
          setUploadProgress(prev => 
            prev.map(u => {
              if (u.id === upload.id && u.progress < 90) {
                return { ...u, progress: u.progress + Math.random() * 10 };
              }
              return u;
            })
          );
        }, 500);

        const result = await APIService.uploadFile(upload.file, metadata);

        clearInterval(progressInterval);

        // Mark as complete
        setUploadProgress(prev => 
          prev.map(u => u.id === upload.id ? 
            { ...u, progress: 100, status: 'completed' } : u
          )
        );

        showNotification(`File uploaded successfully: ${upload.file.name}`, 'success');

      } catch (error) {
        console.error('Upload failed:', error);
        
        setUploadProgress(prev => 
          prev.map(u => u.id === upload.id ? 
            { ...u, status: 'error', error: error.message } : u
          )
        );

        showNotification(`Upload failed: ${upload.file.name} - ${error.message}`, 'error');
      }
    }

    // Remove completed uploads after 3 seconds
    setTimeout(() => {
      setUploadProgress(prev => 
        prev.filter(u => uploads.find(up => up.id === u.id) ? u.status === 'error' : true)
      );
    }, 3000);

    // Refresh data
    setTimeout(() => loadData(false), 1000);
  };

  // Handle file download
  const handleFileDownload = async (file) => {
    try {
      showNotification(`Downloading ${file.name}...`, 'info');
      
      const response = await APIService.downloadFile(file.file_id);
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', file.name);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      showNotification(`Downloaded ${file.name}`, 'success');
    } catch (error) {
      console.error('Download failed:', error);
      showNotification(`Download failed: ${error.message}`, 'error');
    }
  };

  // Handle file delete
  const handleFileDelete = async (file) => {
    try {
      const confirmed = await window.electronAPI?.showMessageBox({
        type: 'warning',
        buttons: ['Delete', 'Cancel'],
        defaultId: 1,
        title: 'Delete File',
        message: `Are you sure you want to delete "${file.name}"?`,
        detail: 'This action cannot be undone. The file will be permanently removed from all Google Drive accounts.'
      });

      if (confirmed?.response === 0) {
        await APIService.deleteFile(file.file_id);
        showNotification(`Deleted ${file.name}`, 'success');
        loadData(false);
      }
    } catch (error) {
      console.error('Delete failed:', error);
      showNotification(`Delete failed: ${error.message}`, 'error');
    }
  };

  // Handle account selection
  const handleAccountSelect = (accountId) => {
    setSelectedAccount(accountId);
  };

  // Handle add account
  const handleAddAccount = async () => {
    try {
      showNotification('Starting account authentication...', 'info');
      
      const accountName = `account_${Date.now()}`;
      const result = await APIService.authenticateAccount(accountName);
      
      if (result.success) {
        showNotification(`Account added successfully: ${result.account.email}`, 'success');
        loadData(false);
      } else {
        throw new Error(result.message || 'Authentication failed');
      }
    } catch (error) {
      console.error('Add account failed:', error);
      showNotification(`Failed to add account: ${error.message}`, 'error');
    }
  };

  // Handle vault lock
  const handleVaultLock = async () => {
    try {
      await APIService.lockVault();
      showNotification('Vault locked successfully', 'info');
      onVaultLock();
    } catch (error) {
      console.error('Failed to lock vault:', error);
      showNotification(`Failed to lock vault: ${error.message}`, 'error');
    }
  };

  // Handle refresh
  const handleRefresh = () => {
    loadData(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-5xl mb-4">🦕</div>
          <h2 className="text-xl font-semibold text-gray-700 mb-2">Loading BrontoBox</h2>
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <Header 
        storageInfo={storageInfo}
        onVaultLock={handleVaultLock}
        onRefresh={handleRefresh}
        refreshing={refreshing}
      />

      {/* Main Content */}
      <div className="flex h-screen pt-16">
        {/* Sidebar */}
        <Sidebar 
          accounts={storageInfo.accounts}
          selectedAccount={selectedAccount}
          onAccountSelect={handleAccountSelect}
          onAddAccount={handleAddAccount}
        />

        {/* Main Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Storage Overview */}
          <StorageOverview storageInfo={storageInfo} />

          {/* File Area */}
          <div className="flex-1 overflow-auto">
            <FileArea 
              files={files}
              onFileUpload={handleFileUpload}
              onFileDownload={handleFileDownload}
              onFileDelete={handleFileDelete}
              storageInfo={storageInfo}
            />
          </div>
        </div>
      </div>

      {/* Upload Progress */}
      <AnimatePresence>
        {uploadProgress.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 100 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 100 }}
            className="fixed bottom-4 right-4 w-96 max-h-64 overflow-y-auto"
          >
            <UploadProgress uploads={uploadProgress} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Dashboard;
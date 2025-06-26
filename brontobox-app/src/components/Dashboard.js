// src/components/Dashboard.js - UPDATED FOR UNIFIED FILE EXPERIENCE
import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
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
  const [fileStatistics, setFileStatistics] = useState(null);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [uploadProgress, setUploadProgress] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const { showNotification } = useNotification();
  const navigate = useNavigate();

  // Load initial data
  const loadData = useCallback(async (showLoadingState = true) => {
    console.log('🔄 Loading dashboard data with unified file experience...');

    if (showLoadingState) {
      setLoading(true);
    } else {
      setRefreshing(true);
    }

    try {
      // Load storage info, files, and statistics in parallel
      console.log('📡 Fetching storage info, files, and statistics...');
      const [storageResponse, filesResponse, statsResponse] = await Promise.all([
        APIService.getStorageInfo(),
        fetch('http://127.0.0.1:8000/files/list').then(r => r.json()),
        fetch('http://127.0.0.1:8000/files/statistics').then(r => r.json()).catch(() => ({ statistics: null }))
      ]);

      console.log('✅ Data loaded successfully:', {
        accounts: storageResponse.total_accounts,
        files: filesResponse.files?.length || 0,
        discovered: statsResponse.statistics?.discovered_files || 0,
        uploaded: statsResponse.statistics?.uploaded_files || 0
      });

      setStorageInfo(storageResponse);
      setFiles(filesResponse.files || []);
      setFileStatistics(statsResponse.statistics);

      // Show notification about discovered files
      if (statsResponse.statistics?.discovered_files > 0) {
        const discoveredCount = statsResponse.statistics.discovered_files;
        showNotification(
          `Found ${discoveredCount} existing BrontoBox file${discoveredCount > 1 ? 's' : ''} from previous sessions!`,
          'info'
        );
      }

      // Set default selected account
      if (storageResponse.accounts && storageResponse.accounts.length > 0 && !selectedAccount) {
        setSelectedAccount(storageResponse.accounts[0].account_id);
        console.log('📧 Selected default account:', storageResponse.accounts[0].email);
      }

    } catch (error) {
      console.error('❌ Failed to load dashboard data:', error);
      showNotification('Failed to load data: ' + error.message, 'error');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [selectedAccount, showNotification]);

  // Load data on mount
  useEffect(() => {
    console.log('🚀 Dashboard mounting - loading initial data with file discovery');
    loadData();
  }, []);

  // Handle file upload with enhanced logging
  const handleFileUpload = async (files) => {
    console.log('📤 handleFileUpload called with:', files);

    if (!files || files.length === 0) {
      console.warn('⚠️ No files provided to handleFileUpload');
      showNotification('No files selected', 'warning');
      return;
    }

    // Log each file
    files.forEach((file, index) => {
      console.log(`📄 File ${index + 1}:`, {
        name: file.name,
        size: file.size,
        type: file.type,
        lastModified: new Date(file.lastModified).toISOString()
      });
    });

    // Check if vault is unlocked and accounts are available
    if (storageInfo.total_accounts === 0) {
      console.warn('⚠️ No Google accounts available for upload');
      showNotification('Please add a Google account before uploading files', 'warning');
      return;
    }

    console.log(`📤 Starting upload of ${files.length} file(s) to ${storageInfo.total_accounts} account(s)`);

    const uploads = files.map(file => ({
      id: Date.now() + Math.random(),
      file,
      progress: 0,
      status: 'uploading',
      error: null
    }));

    console.log('📊 Created upload tracking objects:', uploads.map(u => ({ id: u.id, name: u.file.name })));
    setUploadProgress(prev => {
      const newProgress = [...prev, ...uploads];
      console.log('📈 Updated upload progress state:', newProgress.length, 'total uploads');
      return newProgress;
    });

    for (const upload of uploads) {
      try {
        console.log(`⬆️ Processing upload: ${upload.file.name} (${APIService.formatFileSize(upload.file.size)})`);

        // Update progress to show started
        setUploadProgress(prev =>
          prev.map(u => u.id === upload.id ? {
            ...u,
            progress: 10,
            status: 'uploading'
          } : u)
        );

        const metadata = {
          uploaded_at: new Date().toISOString(),
          original_name: upload.file.name,
          size: upload.file.size,
          type: upload.file.type || 'application/octet-stream'
        };

        console.log('📋 Upload metadata:', metadata);

        // Simulate progress updates for user feedback
        const progressInterval = setInterval(() => {
          setUploadProgress(prev =>
            prev.map(u => {
              if (u.id === upload.id && u.progress < 90 && u.status === 'uploading') {
                const newProgress = Math.min(90, u.progress + Math.random() * 15);
                console.log(`📊 Progress update: ${upload.file.name} - ${newProgress.toFixed(1)}%`);
                return { ...u, progress: newProgress };
              }
              return u;
            })
          );
        }, 1000);

        console.log('🚀 Starting actual upload...');

        // Actual upload
        const result = await APIService.uploadFile(upload.file, metadata);

        console.log('✅ Upload API response:', result);

        clearInterval(progressInterval);

        // Mark as complete
        setUploadProgress(prev =>
          prev.map(u => u.id === upload.id ?
            { ...u, progress: 100, status: 'completed' } : u
          )
        );

        console.log(`🎉 Upload completed successfully: ${upload.file.name}`);
        showNotification(`File uploaded successfully: ${upload.file.name}`, 'success');

      } catch (error) {
        console.error(`💥 Upload failed: ${upload.file.name}`, error);

        setUploadProgress(prev =>
          prev.map(u => u.id === upload.id ?
            { ...u, status: 'error', error: error.message, progress: 0 } : u
          )
        );

        showNotification(`Upload failed: ${upload.file.name} - ${error.message}`, 'error');
      }
    }

    // Remove completed uploads after 5 seconds
    setTimeout(() => {
      console.log('🧹 Cleaning up completed uploads...');
      setUploadProgress(prev =>
        prev.filter(u => {
          const uploadItem = uploads.find(up => up.id === u.id);
          return uploadItem ? u.status === 'error' : true;
        })
      );
    }, 5000);

    // Refresh data after all uploads to show new files
    setTimeout(() => {
      console.log('🔄 Refreshing data after uploads completed');
      loadData(false);
    }, 2000);
  };

  // Handle file download
  const handleFileDownload = async (file) => {
    console.log('⬇️ Starting download:', file.name);
    try {
      showNotification(`Downloading ${file.name}...`, 'info');

      // Download using the unified file endpoint (always returns decrypted file)
      const response = await fetch(`http://127.0.0.1:8000/files/${file.file_id}/download`);

      if (!response.ok) {
        throw new Error(`Download failed: ${response.statusText}`);
      }

      // Create download link
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', file.name);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      console.log('✅ Download completed:', file.name);

      // Show different message for discovered vs uploaded files
      if (file.is_discovered) {
        showNotification(`Downloaded discovered file: ${file.name}`, 'success');
      } else {
        showNotification(`Downloaded ${file.name}`, 'success');
      }

    } catch (error) {
      console.error('❌ Download failed:', error);
      showNotification(`Download failed: ${error.message}`, 'error');
    }
  };

  // Handle file delete
  const handleFileDelete = async (file) => {
    console.log('🗑️ Delete requested for:', file.name);
    try {
      const confirmed = await window.electronAPI?.showMessageBox({
        type: 'warning',
        buttons: ['Delete', 'Cancel'],
        defaultId: 1,
        title: 'Delete File',
        message: `Are you sure you want to delete "${file.name}"?`,
        detail: file.is_discovered
          ? 'This file was discovered from existing chunks. Deleting it will remove all chunks from Google Drive.'
          : 'This action cannot be undone. The file will be permanently removed from all Google Drive accounts.'
      });

      if (confirmed?.response === 0) {
        console.log('🗑️ User confirmed deletion');

        const response = await fetch(`http://127.0.0.1:8000/files/${file.file_id}`, {
          method: 'DELETE'
        });

        if (!response.ok) {
          throw new Error(`Delete failed: ${response.statusText}`);
        }

        showNotification(`Deleted ${file.name}`, 'success');
        console.log('🔄 Refreshing after deletion');
        loadData(false);
      } else {
        console.log('❌ User cancelled deletion');
      }
    } catch (error) {
      console.error('❌ Delete failed:', error);
      showNotification(`Delete failed: ${error.message}`, 'error');
    }
  };

  // Handle account selection
  const handleAccountSelect = (accountId) => {
    console.log('📧 Account selected:', accountId);
    setSelectedAccount(accountId);
  };

  // Handle add account with auto file discovery
  const handleAddAccount = async () => {
    console.log('➕ Add account requested');
    try {
      showNotification('Starting account authentication...', 'info');

      const accountName = `account_${Date.now()}`;
      console.log('🔐 Authenticating account:', accountName);

      const response = await fetch('http://127.0.0.1:8000/accounts/authenticate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ account_name: accountName })
      });

      if (!response.ok) {
        throw new Error(`Authentication failed: ${response.statusText}`);
      }

      const result = await response.json();

      if (result.success) {
        console.log('✅ Account authenticated:', result.account.email);

        // Show notification about discovered files
        const discoveredCount = result.files_discovered || 0;
        if (discoveredCount > 0) {
          showNotification(
            `Account added successfully: ${result.account.email}. Found ${discoveredCount} existing file${discoveredCount > 1 ? 's' : ''}!`,
            'success'
          );
        } else {
          showNotification(`Account added successfully: ${result.account.email}`, 'success');
        }

        // Refresh all data to show new account and any discovered files
        loadData(false);
      } else {
        throw new Error(result.message || 'Authentication failed');
      }
    } catch (error) {
      console.error('❌ Add account failed:', error);
      showNotification(`Failed to add account: ${error.message}`, 'error');
    }
  };

  // Handle vault lock
  const handleVaultLock = async () => {
    console.log('🔒 Vault lock requested');
    try {
      await APIService.lockVault();
      showNotification('Vault locked successfully', 'info');
      onVaultLock();
    } catch (error) {
      console.error('❌ Failed to lock vault:', error);
      showNotification(`Failed to lock vault: ${error.message}`, 'error');
    }
  };

  // Handle MANUAL refresh with file discovery
  const handleRefresh = async () => {
    console.log('🔄 MANUAL refresh button clicked - triggering file discovery');

    try {
      setRefreshing(true);

      // Trigger file discovery refresh
      const discoveryResponse = await fetch('http://127.0.0.1:8000/files/refresh-discovery', {
        method: 'POST'
      });

      if (discoveryResponse.ok) {
        const discoveryResult = await discoveryResponse.json();
        if (discoveryResult.newly_discovered > 0) {
          showNotification(
            `Refresh complete! Found ${discoveryResult.newly_discovered} new file${discoveryResult.newly_discovered > 1 ? 's' : ''}`,
            'success'
          );
        }
      }

      // Load all data
      loadData(false);

    } catch (error) {
      console.error('❌ Refresh failed:', error);
      showNotification(`Refresh failed: ${error.message}`, 'error');
    }
  };

  const handleSettingsClick = () => {
    console.log('📱 Navigating to Settings page...');
    navigate('/settings');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-5xl mb-4">🦕</div>
          <h2 className="text-xl font-semibold text-gray-700 mb-2">Loading BrontoBox</h2>
          <p className="text-sm text-gray-500 mb-4">Discovering existing files...</p>
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
        OnSettingsClick={handleSettingsClick}
      />

      {/* Main Content */}
      <div className="flex h-screen pt-16">
        {/* Sidebar */}
        <Sidebar
          accounts={storageInfo.accounts}
          selectedAccount={selectedAccount}
          onAccountSelect={handleAccountSelect}
          onAddAccount={handleAddAccount}
          fileStatistics={fileStatistics}
        />

        {/* Main Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Storage Overview */}
          <StorageOverview storageInfo={storageInfo} />

          {/* File Area with Enhanced Info */}
          <div className="flex-1 overflow-auto">
            <FileArea
              files={files}
              fileStatistics={fileStatistics}
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
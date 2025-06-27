// src/components/Settings.js - ENHANCED FOR UNIFIED FILE EXPERIENCE
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Shield, Database, Users, Info, Trash2, Download, Lock, RefreshCw, Clock, Upload } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { APIService } from '../services/APIService';
import { useNotification } from './NotificationContext';
import BrontoBoxLogo, { BrontoBoxFavicon, BrontoBoxSmall, BrontoBoxMedium, BrontoBoxLarge, BrontoBoxXL } from './BrontoBoxLogo';


const Settings = ({ onVaultLock }) => {
  const navigate = useNavigate();
  const { showNotification } = useNotification();
  const [accounts, setAccounts] = useState([]);
  const [storageInfo, setStorageInfo] = useState({});
  const [fileStatistics, setFileStatistics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [accountsResponse, storageResponse, statsResponse] = await Promise.all([
        APIService.listAccounts(),
        APIService.getStorageInfo(),
        fetch('http://127.0.0.1:8000/files/statistics').then(r => r.json()).catch(() => ({ statistics: null }))
      ]);

      setAccounts(accountsResponse.accounts || []);
      setStorageInfo(storageResponse);
      setFileStatistics(statsResponse.statistics);
    } catch (error) {
      console.error('Failed to load settings data:', error);
      showNotification('Failed to load settings data', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleLockVault = async () => {
    try {
      await APIService.lockVault();
      showNotification('Vault locked successfully', 'info');
      onVaultLock();
    } catch (error) {
      console.error('Failed to lock vault:', error);
      showNotification('Failed to lock vault', 'error');
    }
  };

  const handleAddAccount = async () => {
    try {
      showNotification('Starting account authentication...', 'info');
      const accountName = `account_${Date.now()}`;
      const result = await APIService.authenticateAccount(accountName);

      if (result.success) {
        showNotification(`Account added: ${result.account.email}`, 'success');
        loadData(); // Refresh data
      } else {
        throw new Error(result.message || 'Authentication failed');
      }
    } catch (error) {
      console.error('Add account failed:', error);
      showNotification(`Failed to add account: ${error.message}`, 'error');
    }
  };

  const handleRefreshDiscovery = async () => {
    try {
      showNotification('Refreshing file discovery...', 'info');

      const response = await fetch('http://127.0.0.1:8000/files/refresh-discovery', {
        method: 'POST'
      });

      if (response.ok) {
        const result = await response.json();
        if (result.newly_discovered > 0) {
          showNotification(`Found ${result.newly_discovered} new files!`, 'success');
        } else {
          showNotification('No new files found', 'info');
        }
        loadData(); // Refresh statistics
      } else {
        throw new Error('Refresh failed');
      }
    } catch (error) {
      console.error('Refresh discovery failed:', error);
      showNotification(`Refresh failed: ${error.message}`, 'error');
    }
  };

  const handleExportRegistry = async () => {
    try {
      showNotification('Exporting file registry...', 'info');

      const response = await fetch('http://127.0.0.1:8000/data/export-registry');

      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`);
      }

      // Download the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      // Get filename from response headers or create default with timestamp
      const contentDisposition = response.headers.get('content-disposition');
      let filename = `brontobox_file_registry_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;

      if (contentDisposition) {
        const matches = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (matches && matches[1]) {
          filename = matches[1].replace(/['"]/g, '');
        }
      }

      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      showNotification(`File registry exported: ${filename}`, 'success');

    } catch (error) {
      console.error('Export registry failed:', error);
      showNotification(`Export failed: ${error.message}`, 'error');
    }
  };

  const handleBackupVaultKeys = async () => {
    try {
      showNotification('Creating vault backup...', 'info');

      const response = await fetch('http://127.0.0.1:8000/data/backup-vault-info');

      if (!response.ok) {
        throw new Error(`Backup failed: ${response.statusText}`);
      }

      // Download the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      // Get filename from response headers or create default with timestamp
      const contentDisposition = response.headers.get('content-disposition');
      let filename = `brontobox_vault_backup_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;

      if (contentDisposition) {
        const matches = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (matches && matches[1]) {
          filename = matches[1].replace(/['"]/g, '');
        }
      }

      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      showNotification(`Vault backup created: ${filename}`, 'success');

      // Show important warning
      setTimeout(() => {
        alert('🔐 IMPORTANT: This backup contains your vault salt and verification data.\n\n✅ SAFE: No private keys or passwords are included\n⚠️ KEEP SECURE: You need this + your master password to recover your vault\n📁 STORE SAFELY: Save this file in a secure location');
      }, 1000);

    } catch (error) {
      console.error('Backup vault failed:', error);
      showNotification(`Backup failed: ${error.message}`, 'error');
    }
  };

  const handleClearAllData = async () => {
    // Show multiple confirmation dialogs for safety
    const firstConfirm = window.confirm(
      '⚠️ WARNING: Clear ALL BrontoBox Data?\n\n' +
      'This will:\n' +
      '• Delete ALL files from Google Drive\n' +
      '• Remove ALL connected accounts\n' +
      '• Clear vault and file registry\n' +
      '• Lock the vault\n\n' +
      'This action CANNOT be undone!\n\n' +
      'Are you absolutely sure?'
    );

    if (!firstConfirm) return;

    const secondConfirm = window.confirm(
      '🚨 FINAL WARNING!\n\n' +
      'You are about to PERMANENTLY DELETE all your BrontoBox data.\n\n' +
      'Files will be removed from Google Drive and cannot be recovered.\n\n' +
      'Type "DELETE" in the next prompt to confirm.'
    );

    if (!secondConfirm) return;

    const finalConfirm = prompt(
      'Type "DELETE" (in capital letters) to confirm permanent data deletion:'
    );

    if (finalConfirm !== 'DELETE') {
      showNotification('Data deletion cancelled', 'info');
      return;
    }

    try {
      showNotification('Clearing all data... This may take a while.', 'warning');

      const response = await fetch('http://127.0.0.1:8000/data/clear-all', {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error(`Clear data failed: ${response.statusText}`);
      }

      const result = await response.json();

      showNotification(
        `Data cleared: ${result.deletion_results.files_deleted} files deleted, ${result.deletion_results.accounts_cleared} accounts removed`,
        'success'
      );

      // Show results
      setTimeout(() => {
        alert(
          `🗑️ DATA DELETION COMPLETE\n\n` +
          `✅ Files deleted: ${result.deletion_results.files_deleted}\n` +
          `✅ Accounts cleared: ${result.deletion_results.accounts_cleared}\n` +
          `❌ Failed deletions: ${result.deletion_results.files_failed}\n\n` +
          `The vault has been locked. You can create a new vault or unlock an existing one.`
        );

        // Redirect to main page (vault will be locked)
        navigate('/');
      }, 2000);

    } catch (error) {
      console.error('Clear all data failed:', error);
      showNotification(`Clear data failed: ${error.message}`, 'error');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-5xl mb-4">⚙️</div>
          <h2 className="text-xl font-semibold text-gray-700 mb-2">Loading Settings</h2>
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/')}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-800">Settings</h1>
                <p className="text-sm text-gray-600">Manage your BrontoBox configuration</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">
                <BrontoBoxSmall className="mr-2" />
                BrontoBox v1.0.0
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* Security Settings */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-lg shadow-lg p-6"
          >
            <div className="flex items-center mb-4">
              <Shield className="w-6 h-6 text-blue-500 mr-3" />
              <h2 className="text-lg font-semibold text-gray-800">Security</h2>
            </div>

            <div className="space-y-4">
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-green-800">Vault Status</p>
                    <p className="text-sm text-green-600">Unlocked & Secure</p>
                  </div>
                  <div className="text-green-500">🔓</div>
                </div>
              </div>

              <button
                onClick={handleLockVault}
                className="w-full bg-orange-500 hover:bg-orange-600 text-white px-4 py-3 rounded-lg transition-colors flex items-center justify-center space-x-2"
              >
                <Lock className="w-4 h-4" />
                <span>Lock Vault</span>
              </button>

              <div className="text-sm text-gray-600 space-y-2">
                <p><strong>Encryption:</strong> AES-256-GCM</p>
                <p><strong>Key Derivation:</strong> PBKDF2-SHA256</p>
                <p><strong>Iterations:</strong> 100,000</p>
                <p><strong>Security:</strong> Enhanced vault verification</p>
              </div>
            </div>
          </motion.div>

          {/* Enhanced Storage Overview */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-lg shadow-lg p-6"
          >
            <div className="flex items-center mb-4">
              <Database className="w-6 h-6 text-green-500 mr-3" />
              <h2 className="text-lg font-semibold text-gray-800">Storage & Files</h2>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <div className="text-xl font-bold text-blue-600">
                    {(storageInfo.total_available_gb || 0).toFixed(1)}GB
                  </div>
                  <div className="text-xs text-blue-600">Available</div>
                </div>
                <div className="text-center p-3 bg-purple-50 rounded-lg">
                  <div className="text-xl font-bold text-purple-600">
                    {(storageInfo.usage_percentage || 0).toFixed(1)}%
                  </div>
                  <div className="text-xs text-purple-600">Used</div>
                </div>
              </div>

              {/* File Statistics */}
              {fileStatistics && (
                <div className="space-y-3">
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <h3 className="font-medium text-gray-800 mb-2">📁 File Overview</h3>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div className="flex items-center">
                        <Clock className="w-4 h-4 text-blue-500 mr-2" />
                        <span>{fileStatistics.discovered_files} Discovered</span>
                      </div>
                      <div className="flex items-center">
                        <Upload className="w-4 h-4 text-green-500 mr-2" />
                        <span>{fileStatistics.uploaded_files} Uploaded</span>
                      </div>
                    </div>
                    <div className="mt-2 text-sm text-gray-600">
                      <p>📊 Total: {fileStatistics.total_files} files ({fileStatistics.total_size_gb}GB)</p>
                      <p>📧 Across {fileStatistics.accounts_used} account{fileStatistics.accounts_used !== 1 ? 's' : ''}</p>
                    </div>
                  </div>

                  <button
                    onClick={handleRefreshDiscovery}
                    className="w-full bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors flex items-center justify-center space-x-2"
                  >
                    <RefreshCw className="w-4 h-4" />
                    <span>Refresh File Discovery</span>
                  </button>
                </div>
              )}

              <div className="p-4 bg-gray-50 rounded-lg">
                <h3 className="font-medium text-gray-800 mb-2">Distribution</h3>
                <p className="text-sm text-gray-600">
                  Files are encrypted and distributed across {storageInfo.total_accounts || 0} Google account{storageInfo.total_accounts !== 1 ? 's' : ''} for maximum security.
                </p>
              </div>

              {storageInfo.total_accounts < 4 && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-blue-800">
                    💡 Add {4 - storageInfo.total_accounts} more account{4 - storageInfo.total_accounts > 1 ? 's' : ''} to unlock {(4 - storageInfo.total_accounts) * 15}GB additional space!
                  </p>
                </div>
              )}
            </div>
          </motion.div>

          {/* Enhanced Account Management */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-lg shadow-lg p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <Users className="w-6 h-6 text-orange-500 mr-3" />
                <h2 className="text-lg font-semibold text-gray-800">Accounts</h2>
              </div>
              <button
                onClick={handleAddAccount}
                className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-sm transition-colors"
              >
                + Add
              </button>
            </div>

            <div className="space-y-3">
              {accounts.length > 0 ? (
                accounts.map((account, index) => (
                  <div key={account.account_id} className="p-3 border border-gray-200 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-gray-800 text-sm truncate">
                          {account.email}
                        </p>
                        <p className="text-xs text-gray-500">
                          Added {new Date(account.created_at).toLocaleDateString()}
                        </p>
                        {account.storage_info && (
                          <p className="text-xs text-blue-600 mt-1">
                            {account.storage_info.available_gb.toFixed(1)}GB available
                          </p>
                        )}
                      </div>
                      <div className={`w-3 h-3 rounded-full ${account.is_active ? 'bg-green-400' : 'bg-gray-400'}`}></div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8">
                  <div className="text-4xl mb-2">📧</div>
                  <p className="text-sm text-gray-600 mb-4">No accounts connected</p>
                  <button
                    onClick={handleAddAccount}
                    className="text-blue-500 hover:text-blue-600 text-sm font-medium"
                  >
                    Add your first account
                  </button>
                </div>
              )}
            </div>
          </motion.div>
        </div>

        {/* Additional Settings */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-8">

          {/* About Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-lg shadow-lg p-6"
          >
            <div className="flex items-center mb-4">
              <Info className="w-6 h-6 text-blue-500 mr-3" />
              <h2 className="text-lg font-semibold text-gray-800">About BrontoBox</h2>
            </div>

            <div className="space-y-3 text-sm text-gray-600">
              <p><strong>Version:</strong> 1.0.0 (Unified File Experience)</p>
              <p><strong>Build:</strong> Enhanced Security + Auto-Discovery</p>
              <p><strong>Description:</strong> Secure distributed storage using multiple Google Drive accounts with client-side encryption and unified file management.</p>

              <div className="pt-4 border-t border-gray-200">
                <h3 className="font-medium text-gray-800 mb-2">Enhanced Features</h3>
                <ul className="space-y-1 text-sm">
                  <li>✅ AES-256-GCM encryption with secure vault verification</li>
                  <li>✅ Multi-account distribution with auto-discovery</li>
                  <li>✅ Zero-knowledge security with multiple vault support</li>
                  <li>✅ Original quality preservation with unified file view</li>
                  <li>🆕 Auto-discovery of existing files across accounts</li>
                  <li>🆕 Enhanced file statistics and management</li>
                </ul>
              </div>
            </div>
          </motion.div>

          {/* Data Management */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-white rounded-lg shadow-lg p-6"
          >
            <div className="flex items-center mb-4">
              <Database className="w-6 h-6 text-red-500 mr-3" />
              <h2 className="text-lg font-semibold text-gray-800">Data Management</h2>
            </div>

            <div className="space-y-4">
              <button
                onClick={handleExportRegistry}
                className="w-full bg-blue-500 hover:bg-blue-600 text-white px-4 py-3 rounded-lg transition-colors flex items-center justify-center space-x-2"
              >
                <Download className="w-4 h-4" />
                <span>Export File Registry</span>
              </button>

              <button
                onClick={handleBackupVaultKeys}
                className="w-full bg-gray-500 hover:bg-gray-600 text-white px-4 py-3 rounded-lg transition-colors flex items-center justify-center space-x-2"
              >
                <Download className="w-4 h-4" />
                <span>Backup Vault Keys</span>
              </button>

              <button
                onClick={handleRefreshDiscovery}
                className="w-full bg-green-500 hover:bg-green-600 text-white px-4 py-3 rounded-lg transition-colors flex items-center justify-center space-x-2"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Rescan All Accounts</span>
              </button>

              <div className="border-t border-gray-200 pt-4">
                <button
                  onClick={handleClearAllData}
                  className="w-full bg-red-500 hover:bg-red-600 text-white px-4 py-3 rounded-lg transition-colors flex items-center justify-center space-x-2"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>Clear All Data</span>
                </button>
                <p className="text-xs text-gray-500 mt-2 text-center">
                  ⚠️ This will permanently delete all files and accounts
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
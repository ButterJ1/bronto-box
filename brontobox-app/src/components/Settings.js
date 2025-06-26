// src/components/Settings.js
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Shield, Database, Users, Info, Trash2, Download, Lock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { APIService } from '../services/APIService';
import { useNotification } from './NotificationContext';

const Settings = ({ onVaultLock }) => {
  const navigate = useNavigate();
  const { showNotification } = useNotification();
  const [accounts, setAccounts] = useState([]);
  const [storageInfo, setStorageInfo] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [accountsResponse, storageResponse] = await Promise.all([
        APIService.listAccounts(),
        APIService.getStorageInfo()
      ]);
      
      setAccounts(accountsResponse.accounts || []);
      setStorageInfo(storageResponse);
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
              <span className="text-sm text-gray-500">🦕 BrontoBox</span>
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
              </div>
            </div>
          </motion.div>

          {/* Storage Overview */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-lg shadow-lg p-6"
          >
            <div className="flex items-center mb-4">
              <Database className="w-6 h-6 text-green-500 mr-3" />
              <h2 className="text-lg font-semibold text-gray-800">Storage</h2>
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

          {/* Account Management */}
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
              <p><strong>Version:</strong> 1.0.0</p>
              <p><strong>Build:</strong> Phase 3 MVP</p>
              <p><strong>Description:</strong> Secure distributed storage using multiple Google Drive accounts with client-side encryption.</p>
              
              <div className="pt-4 border-t border-gray-200">
                <h3 className="font-medium text-gray-800 mb-2">Features</h3>
                <ul className="space-y-1 text-sm">
                  <li>✅ AES-256-GCM encryption</li>
                  <li>✅ Multi-account distribution</li>
                  <li>✅ Zero-knowledge security</li>
                  <li>✅ Original quality preservation</li>
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
              <button className="w-full bg-blue-500 hover:bg-blue-600 text-white px-4 py-3 rounded-lg transition-colors flex items-center justify-center space-x-2">
                <Download className="w-4 h-4" />
                <span>Export Data</span>
              </button>
              
              <button className="w-full bg-gray-500 hover:bg-gray-600 text-white px-4 py-3 rounded-lg transition-colors flex items-center justify-center space-x-2">
                <Download className="w-4 h-4" />
                <span>Backup Keys</span>
              </button>
              
              <div className="border-t border-gray-200 pt-4">
                <button className="w-full bg-red-500 hover:bg-red-600 text-white px-4 py-3 rounded-lg transition-colors flex items-center justify-center space-x-2">
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
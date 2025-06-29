// src/components/Sidebar.js - ENHANCED WITH FILE STATISTICS
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Plus, Settings, Folder, Search, HardDrive, Eye, Clock, Upload, RefreshCw } from 'lucide-react';
import FileManager from './FileManager';

const AccountCard = ({ account, isSelected, onSelect, onViewFiles }) => {
  const storage_info = account.storage_info || {};
  const isWorkspace = storage_info.account_type === 'workspace';
  
  const storageUsed = storage_info.used_gb || 0;
  const storageTotal = storage_info.total_gb || 15;
  const storageAvailable = storageTotal - storageUsed;
  const usagePercentage = Math.min((storageUsed / storageTotal) * 100, 100);

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={() => onSelect(account.account_id)}
      className={`
        bg-white rounded-lg p-4 mb-3 shadow-md cursor-pointer transition-all
        ${isSelected
          ? isWorkspace ? 'ring-2 ring-orange-500 bg-gradient-to-br from-orange-50 to-orange-100' : 'ring-2 ring-green-500 bg-gradient-to-br from-green-50 to-green-100'
          : 'hover:shadow-lg'
        }
        ${isWorkspace ? 'border-l-4 border-orange-400' : 'border-l-4 border-green-400'}
      `}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="text-xs text-gray-600 truncate flex-1" title={account.email}>
          {account.email}
          {isWorkspace && (
            <span className="ml-1 text-orange-600" title="Google Workspace Account">🏢</span>
          )}
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onViewFiles(account);
          }}
          className="p-1 rounded hover:bg-gray-200 transition-colors"
          title="Browse Files in This Account"
        >
          <Folder className="w-4 h-4 text-blue-500" />
        </button>
      </div>

      {/* Workspace Warning */}
      {isWorkspace && (
        <div className="mb-2 p-2 bg-orange-50 border border-orange-200 rounded text-xs">
          <div className="flex items-center text-orange-700">
            <span className="mr-1">🏢</span>
            <span className="font-medium">Workspace Account</span>
          </div>
          <div className="text-orange-600 mt-1">
            {storage_info.note || 'Drive usage only'}
          </div>
        </div>
      )}

      {/* Storage Bar */}
      <div className="bg-gray-200 h-2 rounded-full overflow-hidden mb-2">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${usagePercentage}%` }}
          transition={{ duration: 1 }}
          className={`h-full ${isWorkspace 
            ? 'bg-gradient-to-r from-orange-400 to-orange-600' 
            : 'bg-gradient-to-r from-green-400 to-green-600'
          }`}
        />
      </div>

      {/* Storage Info */}
      <div className="flex justify-between text-xs text-gray-600">
        <span>
          {storageAvailable.toFixed(1)}GB {isWorkspace ? 'est.' : 'free'}
        </span>
        <span>
          {storageTotal.toFixed(1)}GB {isWorkspace ? 'est.' : ''}
        </span>
      </div>

      {/* Enhanced Info */}
      <div className="mt-2 flex items-center justify-between text-xs">
        <span className={isWorkspace ? "text-orange-600" : "text-green-600"}>
          {isWorkspace ? '🏢 Workspace Ready' : '📦 BrontoBox Ready'}
        </span>
        <span className="text-gray-500">
          💾 {usagePercentage.toFixed(1)}% used
          {isWorkspace && (
            <span className="ml-1 text-orange-600" title="Drive usage only">📁</span>
          )}
        </span>
      </div>

      {/* Organization Info for Workspace */}
      {isWorkspace && storage_info.organization_domain && (
        <div className="mt-1 text-xs text-gray-500">
          📍 {storage_info.organization_domain}
        </div>
      )}
    </motion.div>
  );
};

// const AccountCard = ({ account, isSelected, onSelect, onViewFiles }) => {
//   const storageUsed = account.storage_info?.used_gb || 0;
//   const storageTotal = account.storage_info?.total_gb || 15;
//   const storageAvailable = storageTotal - storageUsed;
//   const usagePercentage = (storageUsed / storageTotal) * 100;

//   return (
//     <motion.div
//       whileHover={{ scale: 1.02 }}
//       whileTap={{ scale: 0.98 }}
//       onClick={() => onSelect(account.account_id)}
//       className={`
//         bg-white rounded-lg p-4 mb-3 shadow-md cursor-pointer transition-all
//         ${isSelected
//           ? 'ring-2 ring-green-500 bg-gradient-to-br from-green-50 to-green-100'
//           : 'hover:shadow-lg'
//         }
//       `}
//     >
//       <div className="flex items-center justify-between mb-2">
//         <div className="text-xs text-gray-600 truncate flex-1" title={account.email}>
//           {account.email}
//         </div>
//         <button
//           onClick={(e) => {
//             e.stopPropagation();
//             onViewFiles(account);
//           }}
//           className="p-1 rounded hover:bg-gray-200 transition-colors"
//           title="Browse Files in This Account"
//         >
//           <Folder className="w-4 h-4 text-blue-500" />
//         </button>
//       </div>

//       {/* Storage Bar */}
//       <div className="bg-gray-200 h-2 rounded-full overflow-hidden mb-2">
//         <motion.div
//           initial={{ width: 0 }}
//           animate={{ width: `${usagePercentage}%` }}
//           transition={{ duration: 1 }}
//           className="h-full bg-gradient-to-r from-green-400 to-green-600"
//         />
//       </div>

//       {/* Storage Info */}
//       <div className="flex justify-between text-xs text-gray-600">
//         <span>{storageAvailable.toFixed(1)}GB free</span>
//         <span>{storageTotal.toFixed(1)}GB</span>
//       </div>

//       {/* Enhanced Info */}
//       <div className="mt-2 flex items-center justify-between text-xs">
//         <span className="text-green-600">
//           📦 BrontoBox Ready
//         </span>
//         <span className="text-gray-500">
//           💾 {usagePercentage.toFixed(1)}% used
//         </span>
//       </div>
//     </motion.div>
//   );
// };

const Sidebar = ({ accounts, selectedAccount, onAccountSelect, onAddAccount, fileStatistics }) => {
  const [showFileManager, setShowFileManager] = useState(false);
  const [selectedAccountForFiles, setSelectedAccountForFiles] = useState(null);
  const navigate = useNavigate();

  const handleViewFiles = (account) => {
    setSelectedAccountForFiles(account);
    setShowFileManager(true);
  };

  const closeFileManager = () => {
    setShowFileManager(false);
    setSelectedAccountForFiles(null);
  };

  const handleSettingsClick = () => {
    console.log('📱 Navigating to Settings page...');
    navigate('/settings');
  };

  // // Calculate total BrontoBox capacity
  // const totalCapacity = accounts.reduce((total, acc) => {
  //   return total + (acc.storage_info?.total_gb || 15);
  // }, 0);

  // const totalUsed = accounts.reduce((total, acc) => {
  //   return total + (acc.storage_info?.used_gb || 0);
  // }, 0);

  // const totalAvailable = totalCapacity - totalUsed;

  return (
    <>
      <div className="w-80 bg-gray-50 border-r border-gray-200 p-6 overflow-y-auto">
        {/* Google Accounts Section */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
            📧 Google Accounts
            {accounts.length > 0 && (
              <span className="ml-2 text-sm bg-green-100 text-green-800 px-2 py-1 rounded-full">
                {accounts.length}
              </span>
            )}
          </h3>

          {accounts && accounts.length > 0 ? (
            accounts.map((account) => (
              <AccountCard
                key={account.account_id}
                account={account}
                isSelected={selectedAccount === account.account_id}
                onSelect={onAccountSelect}
                onViewFiles={handleViewFiles}
              />
            ))
          ) : (
            <div className="text-center py-8">
              <div className="text-4xl mb-2">📧</div>
              <p className="text-sm text-gray-600 mb-4">
                No Google accounts connected yet
              </p>
              <button
                onClick={onAddAccount}
                className="text-blue-500 hover:text-blue-600 text-sm font-medium"
              >
                Add your first account
              </button>
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
            ⚙️ Quick Actions
          </h3>

          <button
            onClick={onAddAccount}
            className="w-full bg-green-500 hover:bg-green-600 text-white px-4 py-3 rounded-lg transition-colors flex items-center justify-center space-x-2 mb-3"
          >
            <Plus className="w-4 h-4" />
            <span>Add Account</span>
          </button>

          <button
            onClick={() => {
              if (accounts.length > 0) {
                handleViewFiles(accounts[0]);
              }
            }}
            className="w-full bg-blue-100 hover:bg-blue-200 text-blue-700 px-4 py-3 rounded-lg transition-colors flex items-center justify-center space-x-2 mb-3"
          >
            <Folder className="w-4 h-4" />
            <span>Browse BrontoBox Files</span>
          </button>

          <button
            onClick={() => {
              // Trigger refresh discovery
              fetch('http://127.0.0.1:8000/files/refresh-discovery', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                  if (data.success && data.newly_discovered > 0) {
                    alert(`Found ${data.newly_discovered} new files!`);
                    window.location.reload(); // Simple refresh for now
                  }
                })
                .catch(console.error);
            }}
            className="w-full bg-purple-100 hover:bg-purple-200 text-purple-700 px-4 py-3 rounded-lg transition-colors flex items-center justify-center space-x-2 mb-3"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh File Discovery</span>
          </button>

          <button
            onClick={handleSettingsClick}
            className="w-full bg-gray-200 hover:bg-gray-300 text-gray-700 px-4 py-3 rounded-lg transition-colors flex items-center justify-center space-x-2"
          >
            <Settings className="w-4 h-4" />
            <span>Settings</span>
          </button>
        </div>

        {/* Enhanced File Statistics Section */}
        {fileStatistics && accounts.length > 0 && (
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
              📊 File Overview
            </h3>

            <div className="bg-white rounded-lg shadow-sm p-4 space-y-4">
              {/* Total Files */}
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-800">
                  {fileStatistics.total_files}
                </div>
                <div className="text-sm text-gray-600">Total Files</div>
              </div>

              {/* File Type Breakdown */}
              <div className="grid grid-cols-2 gap-3">
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <div className="flex items-center justify-center mb-1">
                    <Clock className="w-4 h-4 text-blue-600 mr-1" />
                    <span className="text-lg font-bold text-blue-600">
                      {fileStatistics.discovered_files}
                    </span>
                  </div>
                  <div className="text-xs text-blue-600">Discovered</div>
                </div>
                <div className="text-center p-3 bg-green-50 rounded-lg">
                  <div className="flex items-center justify-center mb-1">
                    <Upload className="w-4 h-4 text-green-600 mr-1" />
                    <span className="text-lg font-bold text-green-600">
                      {fileStatistics.uploaded_files}
                    </span>
                  </div>
                  <div className="text-xs text-green-600">Uploaded</div>
                </div>
              </div>

              {/* Storage Used by Files */}
              <div className="pt-3 border-t border-gray-200">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Files using:</span>
                  <span className="font-medium">{fileStatistics.total_size_gb}GB</span>
                </div>
                <div className="flex justify-between text-sm mt-1">
                  <span className="text-gray-600">Across accounts:</span>
                  <span className="font-medium">{fileStatistics.accounts_used}</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Discovery Status */}
        {accounts.length > 0 && fileStatistics && (
          <div className="mt-4 p-3 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
            <div className="flex items-center justify-between mb-2">
              <h5 className="text-sm font-medium text-gray-800">🔍 File Discovery</h5>
              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                Active
              </span>
            </div>
            <p className="text-xs text-gray-600 mb-2">
              {fileStatistics.discovered_files > 0
                ? `Found ${fileStatistics.discovered_files} existing files from previous sessions`
                : 'Auto-discovering files when you add accounts'
              }
            </p>
            <div className="flex items-center justify-between text-xs">
              <span className="text-blue-600">
                📊 {fileStatistics.total_files} total files tracked
              </span>
              <button
                onClick={() => {
                  fetch('http://127.0.0.1:8000/files/refresh-discovery', { method: 'POST' });
                }}
                className="text-blue-600 hover:text-blue-800"
              >
                Refresh
              </button>
            </div>
          </div>
        )}
      </div>

      {/* File Manager Modal */}
      {showFileManager && selectedAccountForFiles && (
        <FileManager
          account={selectedAccountForFiles}
          onClose={closeFileManager}
        />
      )}
    </>
  );
};

export default Sidebar;
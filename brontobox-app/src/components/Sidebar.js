// src/components/Sidebar.js - ENHANCED WITH FILE MANAGER
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Plus, Settings, Folder, Search, HardDrive, Eye } from 'lucide-react';
import FileManager from './FileManager';

const AccountCard = ({ account, isSelected, onSelect, onViewFiles }) => {
  const storageUsed = account.storage_info?.used_gb || 0;
  const storageTotal = account.storage_info?.total_gb || 15;
  const storageAvailable = storageTotal - storageUsed;
  const usagePercentage = (storageUsed / storageTotal) * 100;

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={() => onSelect(account.account_id)}
      className={`
        bg-white rounded-lg p-4 mb-3 shadow-md cursor-pointer transition-all
        ${isSelected 
          ? 'ring-2 ring-green-500 bg-gradient-to-br from-green-50 to-green-100' 
          : 'hover:shadow-lg'
        }
      `}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="text-xs text-gray-600 truncate flex-1" title={account.email}>
          {account.email}
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onViewFiles(account);
          }}
          className="p-1 rounded hover:bg-gray-200 transition-colors"
          title="View Google Drive Files"
        >
          <Folder className="w-4 h-4 text-blue-500" />
        </button>
      </div>
      
      {/* Storage Bar */}
      <div className="bg-gray-200 h-2 rounded-full overflow-hidden mb-2">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${usagePercentage}%` }}
          transition={{ duration: 1 }}
          className="h-full bg-gradient-to-r from-green-400 to-green-600"
        />
      </div>
      
      {/* Storage Info */}
      <div className="flex justify-between text-xs text-gray-600">
        <span>{storageAvailable.toFixed(1)}GB free</span>
        <span>{storageTotal.toFixed(1)}GB</span>
      </div>

      {/* Enhanced Info */}
      <div className="mt-2 flex items-center justify-between text-xs">
        <span className="text-green-600">
          📦 BrontoBox Ready
        </span>
        <span className="text-gray-500">
          🔍 Files: ~{Math.floor(storageUsed * 50)} chunks
        </span>
      </div>
    </motion.div>
  );
};

const Sidebar = ({ accounts, selectedAccount, onAccountSelect, onAddAccount }) => {
  const [showFileManager, setShowFileManager] = useState(false);
  const [selectedAccountForFiles, setSelectedAccountForFiles] = useState(null);

  const handleViewFiles = (account) => {
    setSelectedAccountForFiles(account);
    setShowFileManager(true);
  };

  const closeFileManager = () => {
    setShowFileManager(false);
    setSelectedAccountForFiles(null);
  };

  // Calculate total BrontoBox capacity
  const totalCapacity = accounts.reduce((total, acc) => {
    return total + (acc.storage_info?.total_gb || 15);
  }, 0);

  const totalUsed = accounts.reduce((total, acc) => {
    return total + (acc.storage_info?.used_gb || 0);
  }, 0);

  const totalAvailable = totalCapacity - totalUsed;

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

        {/* Drive Management Section */}
        {accounts.length > 0 && (
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
              🗂️ Drive Management
            </h3>
            
            <div className="space-y-2">
              <button
                onClick={() => {
                  if (accounts.length > 0) {
                    handleViewFiles(accounts[0]);
                  }
                }}
                className="w-full bg-blue-100 hover:bg-blue-200 text-blue-700 px-4 py-3 rounded-lg transition-colors flex items-center justify-center space-x-2"
              >
                <Search className="w-4 h-4" />
                <span>Browse Drive Files</span>
              </button>
              
              <button
                className="w-full bg-purple-100 hover:bg-purple-200 text-purple-700 px-4 py-3 rounded-lg transition-colors flex items-center justify-center space-x-2"
              >
                <HardDrive className="w-4 h-4" />
                <span>Storage Analytics</span>
              </button>
            </div>
          </div>
        )}

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
            className="w-full bg-gray-200 hover:bg-gray-300 text-gray-700 px-4 py-3 rounded-lg transition-colors flex items-center justify-center space-x-2"
          >
            <Settings className="w-4 h-4" />
            <span>Settings</span>
          </button>
        </div>

        {/* Storage Summary */}
        {accounts && accounts.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm p-4">
            <h4 className="font-medium text-gray-800 mb-3 flex items-center">
              📊 BrontoBox Capacity
              {totalCapacity >= 60 && (
                <span className="ml-2 text-xs bg-gold-100 text-yellow-800 px-2 py-1 rounded">
                  🏆 MAX
                </span>
              )}
            </h4>
            
            <div className="space-y-3">
              {/* Capacity Bar */}
              <div className="bg-gray-200 h-3 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${(totalUsed / totalCapacity) * 100}%` }}
                  transition={{ duration: 1.5 }}
                  className="h-full bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500"
                />
              </div>
              
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Accounts:</span>
                  <span className="font-medium">{accounts.length}/4</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Capacity:</span>
                  <span className="font-medium">{totalCapacity.toFixed(1)}GB</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Available:</span>
                  <span className="font-medium text-green-600">{totalAvailable.toFixed(1)}GB</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Usage:</span>
                  <span className="font-medium">{((totalUsed / totalCapacity) * 100).toFixed(1)}%</span>
                </div>
              </div>

              {/* Estimated Storage */}
              <div className="pt-2 border-t border-gray-200">
                <p className="text-xs text-gray-600 mb-1">📦 Estimated Storage:</p>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="text-center p-2 bg-blue-50 rounded">
                    <div className="font-medium text-blue-700">
                      {Math.floor(totalAvailable * 200)}
                    </div>
                    <div className="text-blue-600">Photos</div>
                  </div>
                  <div className="text-center p-2 bg-green-50 rounded">
                    <div className="font-medium text-green-700">
                      {Math.floor(totalAvailable)}
                    </div>
                    <div className="text-green-600">Movies</div>
                  </div>
                </div>
              </div>

              {/* Expansion Tip */}
              {accounts.length < 4 && (
                <div className="pt-2 border-t border-gray-200">
                  <p className="text-xs text-blue-600">
                    💡 Add {4 - accounts.length} more account{4 - accounts.length > 1 ? 's' : ''} for 
                    +{(4 - accounts.length) * 15}GB capacity!
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Search Feature Status */}
        {accounts.length > 0 && (
          <div className="mt-4 p-3 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
            <div className="flex items-center justify-between mb-2">
              <h5 className="text-sm font-medium text-gray-800">🔍 Search Engine</h5>
              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                Beta
              </span>
            </div>
            <p className="text-xs text-gray-600 mb-2">
              Advanced file search activates at 100+ files per account
            </p>
            <div className="flex items-center space-x-2">
              <div className="flex-1 bg-gray-200 h-1 rounded-full">
                <div 
                  className="bg-blue-500 h-1 rounded-full transition-all duration-1000"
                  style={{ width: '45%' }} // This would be calculated based on actual file count
                ></div>
              </div>
              <span className="text-xs text-gray-500">45/100</span>
            </div>
            <p className="text-xs text-blue-600 mt-1">
              55 more files to unlock advanced search
            </p>
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
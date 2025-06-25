// src/components/Sidebar.js
import React from 'react';
import { motion } from 'framer-motion';
import { Plus, Settings } from 'lucide-react';

const AccountCard = ({ account, isSelected, onSelect }) => {
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
      <div className="text-xs text-gray-600 mb-2 truncate" title={account.email}>
        {account.email}
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
    </motion.div>
  );
};

const Sidebar = ({ accounts, selectedAccount, onAccountSelect, onAddAccount }) => {
  return (
    <div className="w-80 bg-gray-50 border-r border-gray-200 p-6 overflow-y-auto">
      {/* Google Accounts Section */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
          📧 Google Accounts
        </h3>
        
        {accounts && accounts.length > 0 ? (
          accounts.map((account) => (
            <AccountCard
              key={account.account_id}
              account={account}
              isSelected={selectedAccount === account.account_id}
              onSelect={onAccountSelect}
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
      <div>
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
        <div className="mt-8 p-4 bg-white rounded-lg shadow-sm">
          <h4 className="font-medium text-gray-800 mb-2">Storage Summary</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Total Accounts:</span>
              <span className="font-medium">{accounts.length}/4</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Capacity:</span>
              <span className="font-medium">{(accounts.length * 15).toFixed(1)}GB</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

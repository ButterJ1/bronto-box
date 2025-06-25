// src/components/StorageOverview.js
import React from 'react';
import { motion } from 'framer-motion';

const StorageOverview = ({ storageInfo }) => {
  const getStorageSegments = () => {
    if (!storageInfo.accounts || storageInfo.accounts.length === 0) {
      return [
        { label: 'No accounts', percentage: 100, color: 'bg-gray-200', textColor: 'text-gray-600' }
      ];
    }

    const segments = [];
    let totalCapacity = 0;

    // Calculate segments for each account
    storageInfo.accounts.forEach((account, index) => {
      const accountCapacity = account.storage_info?.total_gb || 15;
      const accountUsed = account.storage_info?.used_gb || 0;
      const accountAvailable = accountCapacity - accountUsed;
      
      totalCapacity += accountCapacity;

      // Used storage segment
      if (accountUsed > 0) {
        segments.push({
          label: `${account.email} (Used)`,
          value: accountUsed,
          percentage: (accountUsed / (storageInfo.total_capacity_gb || 45)) * 100,
          color: index === 0 ? 'bg-red-400' : index === 1 ? 'bg-orange-400' : 'bg-yellow-400',
          textColor: 'text-white'
        });
      }

      // Available storage segment
      if (accountAvailable > 0) {
        segments.push({
          label: `${account.email} (Available)`,
          value: accountAvailable,
          percentage: (accountAvailable / (storageInfo.total_capacity_gb || 45)) * 100,
          color: index === 0 ? 'bg-green-500' : index === 1 ? 'bg-blue-500' : 'bg-purple-500',
          textColor: 'text-white'
        });
      }
    });

    // Add potential 4th account space
    const currentAccounts = storageInfo.accounts.length;
    if (currentAccounts < 4) {
      const potentialSpace = (4 - currentAccounts) * 15; // 15GB per additional account
      segments.push({
        label: `Potential (+${4 - currentAccounts} account${4 - currentAccounts > 1 ? 's' : ''})`,
        value: potentialSpace,
        percentage: (potentialSpace / (totalCapacity + potentialSpace)) * 100,
        color: 'bg-gray-300',
        textColor: 'text-gray-600'
      });
    }

    return segments;
  };

  const segments = getStorageSegments();

  return (
    <div className="bg-white mx-6 mt-6 rounded-lg shadow-lg p-6">
      <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
        🦕 BrontoBox Storage Distribution
      </h2>
      
      {/* Storage Chart */}
      <div className="flex h-20 bg-gray-100 rounded-lg overflow-hidden mb-4">
        {segments.map((segment, index) => (
          <motion.div
            key={index}
            initial={{ width: 0 }}
            animate={{ width: `${segment.percentage}%` }}
            transition={{ duration: 1, delay: index * 0.1 }}
            className={`${segment.color} ${segment.textColor} flex items-center justify-center text-xs font-medium px-2 cursor-pointer hover:brightness-110 transition-all`}
            title={`${segment.label}: ${segment.value?.toFixed(1) || 0}GB`}
            style={{ minWidth: segment.percentage > 5 ? 'auto' : '0' }}
          >
            {segment.percentage > 10 && (
              <span className="truncate">
                {segment.value?.toFixed(1) || 0}GB
              </span>
            )}
          </motion.div>
        ))}
      </div>

      {/* Storage Summary */}
      <div className="grid grid-cols-4 gap-4 text-center">
        <div>
          <div className="text-2xl font-bold text-gray-800">
            {storageInfo.total_accounts || 0}
          </div>
          <div className="text-sm text-gray-600">Accounts</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-green-600">
            {(storageInfo.total_available_gb || 0).toFixed(1)}GB
          </div>
          <div className="text-sm text-gray-600">Available</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-blue-600">
            {(storageInfo.total_capacity_gb || 0).toFixed(1)}GB
          </div>
          <div className="text-sm text-gray-600">Total Capacity</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-purple-600">
            {(storageInfo.usage_percentage || 0).toFixed(1)}%
          </div>
          <div className="text-sm text-gray-600">Used</div>
        </div>
      </div>

      {/* Potential Expansion */}
      {storageInfo.total_accounts < 4 && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            💡 <strong>Tip:</strong> Add {4 - storageInfo.total_accounts} more Google account{4 - storageInfo.total_accounts > 1 ? 's' : ''} 
            to unlock {(4 - storageInfo.total_accounts) * 15}GB additional storage capacity!
          </p>
        </div>
      )}
    </div>
  );
};
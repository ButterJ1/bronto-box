// src/components/StorageOverview.js
import React from 'react';
import { motion } from 'framer-motion';
import BrontoBoxLogo, { BrontoBoxFavicon, BrontoBoxSmall, BrontoBoxMedium, BrontoBoxLarge, BrontoBoxXL } from './BrontoBoxLogo';

const StorageOverview = ({ storageInfo }) => {
  // Separate workspace and personal accounts
  const accounts = storageInfo.accounts || [];
  const personalAccounts = accounts.filter(acc => acc.storage_info?.account_type !== 'workspace');
  const workspaceAccounts = accounts.filter(acc => acc.storage_info?.account_type === 'workspace');
  
  // Calculate totals - only count personal accounts for main storage
  const personalTotal = personalAccounts.reduce((sum, acc) => sum + (acc.storage_info?.total_gb || 0), 0);
  const personalUsed = personalAccounts.reduce((sum, acc) => sum + (acc.storage_info?.used_gb || 0), 0);
  const personalAvailable = personalTotal - personalUsed;
  
  // Workspace totals (for display only)
  const workspaceUsed = workspaceAccounts.reduce((sum, acc) => sum + (acc.storage_info?.used_gb || 0), 0);

  return (
    <div className="bg-white mx-6 mt-6 rounded-lg shadow-lg p-6">
      <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
        <BrontoBoxMedium className="mr-2" />
        BrontoBox Storage Distribution
        {workspaceAccounts.length > 0 && (
          <span className="ml-2 text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded-full">
            {workspaceAccounts.length} Workspace
          </span>
        )}
      </h2>

      {/* Workspace Account Notice */}
      {workspaceAccounts.length > 0 && (
        <div className="mb-4 p-3 bg-orange-50 border border-orange-200 rounded-lg">
          <div className="flex items-start space-x-2">
            <span className="text-orange-600 mt-1">🏢</span>
            <div>
              <p className="text-sm font-medium text-orange-800">
                Google Workspace Account{workspaceAccounts.length > 1 ? 's' : ''} Connected
              </p>
              <p className="text-xs text-orange-700 mt-1">
                Workspace accounts show Drive usage only. For maximum storage capacity, 
                connect personal Google accounts (15GB each).
              </p>
              {workspaceAccounts.length > 0 && (
                <div className="text-xs text-orange-600 mt-2">
                  📁 Workspace Drive usage: {workspaceUsed.toFixed(2)}GB across {workspaceAccounts.length} account{workspaceAccounts.length > 1 ? 's' : ''}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Main Storage Stats - Personal Accounts Only */}
      <div className="grid grid-cols-4 gap-4 text-center mb-4">
        <div>
          <div className="text-2xl font-bold text-gray-800">
            {personalAccounts.length}
          </div>
          <div className="text-sm text-gray-600">Personal Accounts</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-green-600">
            {personalAvailable.toFixed(1)}GB
          </div>
          <div className="text-sm text-gray-600">Available</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-blue-600">
            {personalTotal.toFixed(1)}GB
          </div>
          <div className="text-sm text-gray-600">Personal Capacity</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-purple-600">
            {personalTotal > 0 ? ((personalUsed / personalTotal) * 100).toFixed(1) : 0}%
          </div>
          <div className="text-sm text-gray-600">Personal Used</div>
        </div>
      </div>

      {/* Recommendation for More Storage */}
      {personalAccounts.length < 4 && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            💡 <strong>Maximize your storage:</strong> Add {4 - personalAccounts.length} more personal Google account{4 - personalAccounts.length > 1 ? 's' : ''} to unlock {(4 - personalAccounts.length) * 15}GB additional space!
          </p>
          <p className="text-xs text-blue-700 mt-1">
            Personal accounts provide 15GB each for BrontoBox storage.
          </p>
        </div>
      )}

      {/* Account Type Breakdown */}
      {accounts.length > 0 && (
        <div className="mt-4">
          <h3 className="text-sm font-medium text-gray-700 mb-2">Account Breakdown</h3>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-green-50 p-2 rounded border border-green-200">
              <div className="font-medium text-green-800">
                👤 Personal: {personalAccounts.length}
              </div>
              <div className="text-green-600">
                {personalTotal.toFixed(1)}GB total capacity
              </div>
            </div>
            <div className="bg-orange-50 p-2 rounded border border-orange-200">
              <div className="font-medium text-orange-800">
                🏢 Workspace: {workspaceAccounts.length}
              </div>
              <div className="text-orange-600">
                {workspaceUsed.toFixed(2)}GB Drive usage
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Add this notice component for the main dashboard
const WorkspaceAccountNotice = ({ workspaceAccounts, onAddPersonalAccount }) => {
  if (workspaceAccounts.length === 0) return null;

  return (
    <div className="mx-6 mt-4 p-4 bg-gradient-to-r from-orange-50 to-yellow-50 border border-orange-200 rounded-lg">
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3">
          <span className="text-2xl">🏢</span>
          <div>
            <h3 className="font-semibold text-orange-800">
              Google Workspace Account{workspaceAccounts.length > 1 ? 's' : ''} Connected
            </h3>
            <p className="text-sm text-orange-700 mt-1">
              You're connected to {workspaceAccounts.length} workspace account{workspaceAccounts.length > 1 ? 's' : ''}. 
              These show Drive usage only and may have organization storage limits.
            </p>
            <div className="mt-2 text-xs text-orange-600">
              <p>📝 Workspace accounts are great for BrontoBox, but for maximum storage:</p>
              <p>• Add personal Google accounts (15GB each)</p>
              <p>• Workspace accounts supplement but don't count toward the 60GB goal</p>
            </div>
          </div>
        </div>
        <button
          onClick={onAddPersonalAccount}
          className="bg-orange-500 hover:bg-orange-600 text-white px-3 py-2 rounded text-sm transition-colors"
        >
          Add Personal Account
        </button>
      </div>
    </div>
  );
};

// const StorageOverview = ({ storageInfo }) => {
//   const getStorageSegments = () => {
//     if (!storageInfo.accounts || storageInfo.accounts.length === 0) {
//       return [
//         { label: 'No accounts', percentage: 100, color: 'bg-gray-200', textColor: 'text-gray-600' }
//       ];
//     }

//     const segments = [];
//     let totalCapacity = 0;

//     // Calculate segments for each account
//     storageInfo.accounts.forEach((account, index) => {
//       const accountCapacity = account.storage_info?.total_gb || 15;
//       const accountUsed = account.storage_info?.used_gb || 0;
//       const accountAvailable = accountCapacity - accountUsed;

//       totalCapacity += accountCapacity;

//       // Used storage segment
//       if (accountUsed > 0) {
//         segments.push({
//           label: `${account.email} (Used)`,
//           value: accountUsed,
//           percentage: (accountUsed / (storageInfo.total_capacity_gb || 45)) * 100,
//           color: index === 0 ? 'bg-red-400' : index === 1 ? 'bg-orange-400' : 'bg-yellow-400',
//           textColor: 'text-white'
//         });
//       }

//       // Available storage segment
//       if (accountAvailable > 0) {
//         segments.push({
//           label: `${account.email} (Available)`,
//           value: accountAvailable,
//           percentage: (accountAvailable / (storageInfo.total_capacity_gb || 45)) * 100,
//           color: index === 0 ? 'bg-green-500' : index === 1 ? 'bg-blue-500' : 'bg-purple-500',
//           textColor: 'text-white'
//         });
//       }
//     });

//     // Add potential 4th account space
//     const currentAccounts = storageInfo.accounts.length;
//     if (currentAccounts < 4) {
//       const potentialSpace = (4 - currentAccounts) * 15; // 15GB per additional account
//       segments.push({
//         label: `Potential (+${4 - currentAccounts} account${4 - currentAccounts > 1 ? 's' : ''})`,
//         value: potentialSpace,
//         percentage: (potentialSpace / (totalCapacity + potentialSpace)) * 100,
//         color: 'bg-gray-300',
//         textColor: 'text-gray-600'
//       });
//     }

//     return segments;
//   };

//   const segments = getStorageSegments();

//   return (
//     <div className="bg-white mx-6 mt-6 rounded-lg shadow-lg p-6">
//       <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
//         <BrontoBoxMedium className="mr-2" />
//         BrontoBox Storage Distribution
//       </h2>

//       {/* Storage Chart */}
//       <div className="flex h-20 bg-gray-100 rounded-lg overflow-hidden mb-4">
//         {segments.map((segment, index) => (
//           <motion.div
//             key={index}
//             initial={{ width: 0 }}
//             animate={{ width: `${segment.percentage}%` }}
//             transition={{ duration: 1, delay: index * 0.1 }}
//             className={`${segment.color} ${segment.textColor} flex items-center justify-center text-xs font-medium px-2 cursor-pointer hover:brightness-110 transition-all`}
//             title={`${segment.label}: ${segment.value?.toFixed(1) || 0}GB`}
//             style={{ minWidth: segment.percentage > 5 ? 'auto' : '0' }}
//           >
//             {segment.percentage > 10 && (
//               <span className="truncate">
//                 {segment.value?.toFixed(1) || 0}GB
//               </span>
//             )}
//           </motion.div>
//         ))}
//       </div>

//       {/* Storage Summary */}
//       <div className="grid grid-cols-4 gap-4 text-center">
//         <div>
//           <div className="text-2xl font-bold text-gray-800">
//             {storageInfo.total_accounts || 0}
//           </div>
//           <div className="text-sm text-gray-600">Accounts</div>
//         </div>
//         <div>
//           <div className="text-2xl font-bold text-green-600">
//             {(storageInfo.total_available_gb || 0).toFixed(1)}GB
//           </div>
//           <div className="text-sm text-gray-600">Available</div>
//         </div>
//         <div>
//           <div className="text-2xl font-bold text-blue-600">
//             {(storageInfo.total_capacity_gb || 0).toFixed(1)}GB
//           </div>
//           <div className="text-sm text-gray-600">Total Capacity</div>
//         </div>
//         <div>
//           <div className="text-2xl font-bold text-purple-600">
//             {(storageInfo.usage_percentage || 0).toFixed(1)}%
//           </div>
//           <div className="text-sm text-gray-600">Used</div>
//         </div>
//       </div>

//       {/* Potential Expansion */}
//       {storageInfo.total_accounts < 4 && (
//         <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
//           <p className="text-sm text-blue-800">
//             💡 <strong>Tip:</strong> Add {4 - storageInfo.total_accounts} more Google account{4 - storageInfo.total_accounts > 1 ? 's' : ''}
//             to unlock {(4 - storageInfo.total_accounts) * 15}GB additional storage capacity!
//           </p>
//         </div>
//       )}
//     </div>
//   );
// };

export default StorageOverview;
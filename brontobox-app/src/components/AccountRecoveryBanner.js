// src/components/AccountRecoveryBanner.js - Guide users to add accounts after restore
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, Users, Download, Loader, X } from 'lucide-react';

const AccountRecoveryBanner = ({ onAddAccount, onDismiss }) => {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dismissed, setDismissed] = useState(false);
  const [fixing, setFixing] = useState(false);

  useEffect(() => {
    checkAccountStatus();
  }, []);

  const checkAccountStatus = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/restore/analyze-missing-accounts');
      
      if (response.ok) {
        const data = await response.json();
        setAnalysis(data);
        
        // Auto-dismiss if no missing accounts
        if (data.analysis.missing_accounts === 0) {
          setTimeout(() => setDismissed(true), 3000);
        }
      }
    } catch (error) {
      console.error('Failed to check account status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFixAccountMapping = async () => {
    try {
      setFixing(true);
      console.log('🔧 Attempting to fix account mapping...');
      
      const response = await fetch('http://127.0.0.1:8000/restore/fix-account-mapping', {
        method: 'POST'
      });
      
      if (response.ok) {
        const result = await response.json();
        
        if (result.success) {
          console.log('✅ Account mapping fixed:', result);
          
          // Refresh status after fix
          setTimeout(() => {
            checkAccountStatus();
            // Refresh the whole page to update file accessibility
            window.location.reload();
          }, 1000);
          
          alert(`🎉 Account mapping fixed!\n\n✅ Remapped ${result.chunks_remapped} chunks\n✅ Check your file downloads now!`);
        } else {
          alert(`⚠️ Account mapping failed:\n\n${result.message}\n\nSuggestion: ${result.suggestion || 'Make sure you have added all your original Google accounts'}`);
        }
      } else {
        throw new Error('Fix account mapping request failed');
      }
      
    } catch (error) {
      console.error('❌ Fix account mapping failed:', error);
      alert(`❌ Failed to fix account mapping: ${error.message}`);
    } finally {
      setFixing(false);
    }
  };

  const handleDismiss = () => {
    setDismissed(true);
    if (onDismiss) onDismiss();
  };

  const handleAddAccount = () => {
    if (onAddAccount) onAddAccount();
  };

  // Don't show if dismissed or no issues
  if (dismissed || loading) return null;
  if (!analysis || analysis.analysis.missing_accounts === 0) return null;

  const { analysis: accountAnalysis, details } = analysis;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, height: 0 }}
        animate={{ opacity: 1, height: 'auto' }}
        exit={{ opacity: 0, height: 0 }}
        className="bg-gradient-to-r from-orange-50 to-red-50 border border-orange-200 rounded-lg p-4 mb-6 overflow-hidden"
      >
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3 flex-1">
            <div className="flex-shrink-0 mt-1">
              <AlertCircle className="w-5 h-5 text-orange-600" />
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-2">
                <h3 className="font-semibold text-orange-800">Account Setup Required</h3>
                <span className="bg-orange-100 text-orange-700 text-xs px-2 py-1 rounded-full">
                  {accountAnalysis.accessibility_percentage}% Accessible
                </span>
              </div>
              
              <p className="text-orange-700 text-sm mb-3">
                Your vault was restored successfully, but you need to re-add your Google accounts to download files.
              </p>
              
              {/* Account Status */}
              <div className="bg-white bg-opacity-50 rounded-lg p-3 mb-3">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div className="text-center">
                    <div className="text-lg font-bold text-gray-800">{accountAnalysis.total_files}</div>
                    <div className="text-gray-600">Total Files</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-orange-600">{accountAnalysis.missing_accounts}</div>
                    <div className="text-gray-600">Missing Accounts</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-red-600">{accountAnalysis.inaccessible_files}</div>
                    <div className="text-gray-600">Inaccessible Files</div>
                  </div>
                </div>
              </div>

              {/* Missing Account IDs - Limit height and add scroll */}
              {details.missing_account_ids.length > 0 && (
                <div className="mb-3">
                  <p className="text-xs text-orange-600 mb-1">Required Account IDs:</p>
                  <div className="text-xs text-gray-600 font-mono bg-gray-100 p-2 rounded max-h-16 overflow-y-auto">
                    {details.missing_account_ids.slice(0, 2).map((accountId, index) => (
                      <div key={index} className="truncate">{accountId}</div>
                    ))}
                    {details.missing_account_ids.length > 2 && (
                      <div>... and {details.missing_account_ids.length - 2} more</div>
                    )}
                  </div>
                </div>
              )}

              {/* Action Buttons - FIXED: Remove useless Refresh Status */}
              <div className="flex flex-wrap items-center gap-2">
                <button
                  onClick={handleAddAccount}
                  className="bg-orange-500 hover:bg-orange-600 text-white px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-2"
                >
                  <Users className="w-4 h-4" />
                  <span>Add Google Account</span>
                </button>
                
                <button
                  onClick={handleFixAccountMapping}
                  disabled={fixing}
                  className="bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 text-gray-700 px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-2"
                >
                  {fixing ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  ) : (
                    <Loader className="w-4 h-4" />
                  )}
                  <span>{fixing ? 'Refreshing...' : 'Refresh Status'}</span>
                </button>
                
                {/* Removed the broken Refresh Status button */}
              </div>
            </div>
          </div>
          
          <button
            onClick={handleDismiss}
            className="flex-shrink-0 p-1 rounded-lg hover:bg-orange-100 transition-colors ml-2"
          >
            <X className="w-4 h-4 text-orange-600" />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="mt-4">
          <div className="flex items-center justify-between text-xs text-orange-600 mb-1">
            <span>File Accessibility</span>
            <span>{accountAnalysis.accessibility_percentage}%</span>
          </div>
          <div className="bg-orange-200 rounded-full h-2 overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${accountAnalysis.accessibility_percentage}%` }}
              transition={{ duration: 1 }}
              className="bg-orange-500 h-full"
            />
          </div>
        </div>

        {/* Helpful Tips - UPDATED */}
        <div className="mt-3 p-2 bg-blue-50 border border-blue-200 rounded">
          <p className="text-xs text-blue-700">
            💡 <strong>Try "Refresh Status" first</strong> - it automatically maps your current accounts to your files. 
            If that doesn't work, you might need to add more Google accounts.
          </p>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default AccountRecoveryBanner;
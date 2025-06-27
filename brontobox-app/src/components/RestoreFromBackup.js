// src/components/RestoreFromBackup.js - AUTO-DETECT & RESTORE FUNCTIONALITY
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, Upload, AlertCircle, CheckCircle, Key, FileText, ArrowRight, RefreshCw } from 'lucide-react';

const RestoreFromBackup = ({ onRestoreSuccess, onSkip }) => {
  const [detectedBackups, setDetectedBackups] = useState({ vault_backups: [], registry_backups: [] });
  const [selectedVaultBackup, setSelectedVaultBackup] = useState(null);
  const [selectedRegistryBackup, setSelectedRegistryBackup] = useState(null);
  const [masterPassword, setMasterPassword] = useState('');
  const [loading, setLoading] = useState(true);
  const [restoring, setRestoring] = useState(false);
  const [step, setStep] = useState(1); // 1: detect, 2: select, 3: password, 4: restore
  const [error, setError] = useState('');
  const [compatibility, setCompatibility] = useState(null);

  useEffect(() => {
    detectBackupFiles();
  }, []);

  const detectBackupFiles = async () => {
    try {
      console.log('🔍 Detecting backup files...');
      setLoading(true);
      
      const response = await fetch('http://127.0.0.1:8000/backup/detect');
      const data = await response.json();
      
      if (data.success) {
        setDetectedBackups(data.detected_backups);
        console.log(`📁 Detected: ${data.vault_count} vault backups, ${data.registry_count} registry backups`);
        
        // Auto-select if only one of each
        if (data.detected_backups.vault_backups.length === 1) {
          setSelectedVaultBackup(data.detected_backups.vault_backups[0]);
        }
        if (data.detected_backups.registry_backups.length === 1) {
          setSelectedRegistryBackup(data.detected_backups.registry_backups[0]);
        }
        
        setStep(data.vault_count > 0 ? 2 : 1);
      } else {
        setError('Failed to detect backup files');
      }
    } catch (error) {
      console.error('❌ Failed to detect backups:', error);
      setError('Failed to scan for backup files');
    } finally {
      setLoading(false);
    }
  };

  const checkCompatibility = async () => {
    if (!selectedVaultBackup) return;
    
    try {
      const params = new URLSearchParams({
        vault_backup: selectedVaultBackup.file_path
      });
      
      if (selectedRegistryBackup) {
        params.append('registry_backup', selectedRegistryBackup.file_path);
      }
      
      const response = await fetch(`http://127.0.0.1:8000/restore/check-compatibility?${params}`);
      const data = await response.json();
      
      if (data.success) {
        setCompatibility(data.compatibility);
        return data.compatibility.compatible;
      }
      return false;
    } catch (error) {
      console.error('❌ Compatibility check failed:', error);
      return false;
    }
  };

  const handleNext = async () => {
    if (step === 2) {
      // Check compatibility before proceeding
      const isCompatible = await checkCompatibility();
      if (isCompatible) {
        setStep(3);
      } else {
        setError('Selected backup files are not compatible');
      }
    } else if (step === 3) {
      // FIXED: Validate password BEFORE proceeding to step 4
      if (!masterPassword.trim()) {
        setError('Please enter your master password');
        return;
      }
      
      // Lightweight password validation first
      setError('');
      console.log('🔐 Validating master password...');
      
      try {
        const validationData = {
          vault_backup_file: selectedVaultBackup.file_path,
          registry_backup_file: selectedRegistryBackup?.file_path || '',
          master_password: masterPassword
        };
        
        // Use lightweight validation endpoint
        const response = await fetch('http://127.0.0.1:8000/restore/validate-password', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(validationData)
        });
        
        if (!response.ok) {
          let errorMessage = `Password validation failed`;
          try {
            const errorData = await response.json();
            if (errorData.detail && errorData.detail.includes('Invalid master password')) {
              errorMessage = 'Invalid master password for this vault backup';
            } else {
              errorMessage = errorData.detail || errorData.message || errorMessage;
            }
          } catch (e) {
            console.warn('Could not parse validation error response');
          }
          throw new Error(errorMessage);
        }
        
        const result = await response.json();
        
        if (result.success) {
          console.log('✅ Password validated successfully');
          setStep(4);
          handleRestore(); // Now do the actual restoration
        } else {
          throw new Error(result.message || 'Password validation failed');
        }
        
      } catch (error) {
        console.error('❌ Password validation failed:', error);
        setError(`${error.message}`);
        return;
      }
    }
  };

  const handleRestore = async () => {
    try {
      setRestoring(true);
      setError('');
      console.log('🚀 Starting complete restoration (password already validated)...');
      
      const restoreData = {
        vault_backup_file: selectedVaultBackup.file_path,
        registry_backup_file: selectedRegistryBackup?.file_path || '',
        master_password: masterPassword
      };
      
      const response = await fetch('http://127.0.0.1:8000/restore/complete-restoration', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(restoreData)
      });
      
      if (!response.ok) {
        let errorMessage = `Restoration failed with status ${response.status}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch (e) {
          console.warn('Could not parse restoration error response');
        }
        throw new Error(errorMessage);
      }
      
      const result = await response.json();
      console.log('✅ Restoration response:', result);
      
      if (result.success) {
        console.log('✅ Restoration successful:', result.restoration_summary);
        
        // Show success message briefly then redirect
        setTimeout(() => {
          onRestoreSuccess(result.restoration_summary);
        }, 2000);
        
      } else {
        throw new Error(result.message || 'Restoration failed');
      }
      
    } catch (error) {
      console.error('❌ Restoration failed:', error);
      setError(`Restoration failed: ${error.message}`);
      setRestoring(false);
      // Go back to password step to let user try again
      setStep(3);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">🔍</div>
          <h2 className="text-xl font-semibold text-gray-700 mb-2">Scanning for Backups</h2>
          <p className="text-gray-500 mb-4">Looking for BrontoBox backup files...</p>
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
        </div>
      </div>
    );
  }

  // No backups detected
  if (detectedBackups.vault_backups.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md text-center">
          <div className="text-5xl mb-4">📁</div>
          <h2 className="text-xl font-semibold text-gray-700 mb-2">No Backup Files Found</h2>
          <p className="text-gray-500 mb-6">
            No BrontoBox backup files were detected in the current directory.
          </p>
          <div className="space-y-3 text-sm text-gray-600 mb-6">
            <p>To restore from backup:</p>
            <p>• Place <code>brontobox_vault_backup_*.json</code> in this folder</p>
            <p>• Place <code>brontobox_file_registry_*.json</code> in this folder</p>
            <p>• Restart BrontoBox</p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={detectBackupFiles}
              className="flex-1 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors flex items-center justify-center space-x-2"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Rescan</span>
            </button>
            <button
              onClick={onSkip}
              className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-700 px-4 py-2 rounded-lg transition-colors"
            >
              Continue
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-lg shadow-xl max-w-2xl w-full overflow-hidden"
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-500 to-blue-500 text-white p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Restore from Backup</h1>
              <p className="text-blue-100">Found backup files! Restore your BrontoBox vault</p>
            </div>
            <div className="text-4xl">🔄</div>
          </div>
          
          {/* Progress Steps */}
          <div className="flex items-center mt-4 space-x-4">
            {[1, 2, 3, 4].map((stepNum) => (
              <div key={stepNum} className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  stepNum <= step ? 'bg-white text-blue-500' : 'bg-blue-400 text-blue-200'
                }`}>
                  {stepNum < step ? '✓' : stepNum}
                </div>
                {stepNum < 4 && <div className="w-8 h-0.5 bg-blue-400 mx-2"></div>}
              </div>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          <AnimatePresence mode="wait">
            {/* Step 2: Select Backup Files */}
            {step === 2 && (
              <motion.div
                key="select"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                  <FileText className="w-5 h-5 mr-2" />
                  Select Backup Files
                </h2>
                
                {/* Vault Backup Selection */}
                <div className="mb-6">
                  <h3 className="font-medium text-gray-700 mb-2">Vault Backup (Required)</h3>
                  <div className="space-y-2">
                    {detectedBackups.vault_backups.map((backup, index) => (
                      <div
                        key={index}
                        onClick={() => setSelectedVaultBackup(backup)}
                        className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                          selectedVaultBackup?.filename === backup.filename
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium text-gray-800">{backup.filename}</p>
                            <p className="text-sm text-gray-500">Vault ID: {backup.vault_id}</p>
                            <p className="text-xs text-gray-400">Created: {formatDate(backup.created_at)}</p>
                          </div>
                          <Key className="w-5 h-5 text-blue-500" />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Registry Backup Selection */}
                <div className="mb-6">
                  <h3 className="font-medium text-gray-700 mb-2">File Registry (Optional)</h3>
                  {detectedBackups.registry_backups.length > 0 ? (
                    <div className="space-y-2">
                      <div
                        onClick={() => setSelectedRegistryBackup(null)}
                        className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                          !selectedRegistryBackup ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <p className="font-medium text-gray-600">Skip registry import</p>
                        <p className="text-sm text-gray-500">Start with empty file list</p>
                      </div>
                      {detectedBackups.registry_backups.map((backup, index) => (
                        <div
                          key={index}
                          onClick={() => setSelectedRegistryBackup(backup)}
                          className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                            selectedRegistryBackup?.filename === backup.filename
                              ? 'border-blue-500 bg-blue-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="font-medium text-gray-800">{backup.filename}</p>
                              <p className="text-sm text-gray-500">{backup.total_files} files</p>
                              <p className="text-xs text-gray-400">Exported: {formatDate(backup.exported_at)}</p>
                            </div>
                            <Download className="w-5 h-5 text-green-500" />
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-3 border border-gray-200 rounded-lg bg-gray-50">
                      <p className="text-gray-600">No file registry backups found</p>
                      <p className="text-sm text-gray-500">You can add accounts and files will auto-discover</p>
                    </div>
                  )}
                </div>

                {/* Compatibility Check Results */}
                {compatibility && (
                  <div className="mb-4 p-3 rounded-lg bg-gray-50">
                    <h4 className="font-medium text-gray-700 mb-2">Compatibility Check</h4>
                    {compatibility.compatible ? (
                      <div className="flex items-center text-green-600">
                        <CheckCircle className="w-4 h-4 mr-2" />
                        <span>Backup files are compatible</span>
                      </div>
                    ) : (
                      <div>
                        <div className="flex items-center text-red-600 mb-2">
                          <AlertCircle className="w-4 h-4 mr-2" />
                          <span>Compatibility issues found</span>
                        </div>
                        <ul className="text-sm text-red-600 ml-6">
                          {compatibility.issues.map((issue, index) => (
                            <li key={index}>• {issue}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </motion.div>
            )}

            {/* Step 3: Enter Password */}
            {step === 3 && (
              <motion.div
                key="password"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                  <Key className="w-5 h-5 mr-2" />
                  Enter Master Password
                </h2>
                
                <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-blue-800 font-medium">Selected Files:</p>
                  <p className="text-sm text-blue-600">🔑 Vault: {selectedVaultBackup?.filename}</p>
                  {selectedRegistryBackup && (
                    <p className="text-sm text-blue-600">📁 Registry: {selectedRegistryBackup.filename}</p>
                  )}
                </div>
                
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Master Password
                  </label>
                  <input
                    type="password"
                    value={masterPassword}
                    onChange={(e) => setMasterPassword(e.target.value)}
                    placeholder="Enter your vault master password"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    onKeyPress={(e) => e.key === 'Enter' && handleNext()}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    This is the same password you used when creating the vault
                  </p>
                </div>
              </motion.div>
            )}

            {/* Step 4: Restoring */}
            {step === 4 && (
              <motion.div
                key="restoring"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="text-center"
              >
                <div className="text-6xl mb-4">🔄</div>
                <h2 className="text-lg font-semibold text-gray-800 mb-2">
                  {restoring ? 'Restoring Your Vault...' : 'Restoration Complete!'}
                </h2>
                {restoring ? (
                  <div>
                    <p className="text-gray-600 mb-4">
                      Please wait while we restore your vault and files
                    </p>
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                  </div>
                ) : (
                  <div>
                    <div className="text-4xl mb-4">✅</div>
                    <p className="text-gray-600 mb-4">
                      Your BrontoBox vault has been successfully restored!
                    </p>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Error Display */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center text-red-600">
                <AlertCircle className="w-4 h-4 mr-2" />
                <span>{error}</span>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          {step < 4 && (
            <div className="flex justify-between pt-4">
              <button
                onClick={onSkip}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
              >
                Skip & Create New Vault
              </button>
              
              <div className="flex space-x-3">
                {step > 2 && (
                  <button
                    onClick={() => setStep(step - 1)}
                    className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg transition-colors"
                  >
                    Back
                  </button>
                )}
                <button
                  onClick={handleNext}
                  disabled={
                    (step === 2 && !selectedVaultBackup) ||
                    (step === 3 && !masterPassword.trim())
                  }
                  className="px-6 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white rounded-lg transition-colors flex items-center space-x-2"
                >
                  <span>{step === 3 ? 'Restore' : 'Next'}</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
};

export default RestoreFromBackup;
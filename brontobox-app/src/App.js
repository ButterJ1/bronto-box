// src/App.js - UPDATED WITH RESTORE FUNCTIONALITY
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';

// Components
import VaultLogin from './components/VaultLogin';
import Dashboard from './components/Dashboard';
import Settings from './components/Settings';
import RestoreFromBackup from './components/RestoreFromBackup';
import { NotificationProvider } from './components/NotificationContext';

// Services
import { APIService } from './services/APIService';

// Logo
import BrontoBoxLogo, { BrontoBoxFavicon, BrontoBoxSmall, BrontoBoxMedium, BrontoBoxLarge, BrontoBoxXL } from './components/BrontoBoxLogo';

const App = () => {
  const [appState, setAppState] = useState('loading'); // 'loading', 'restore_check', 'login', 'dashboard'
  const [vaultStatus, setVaultStatus] = useState(null);
  const [hasBackupFiles, setHasBackupFiles] = useState(false);
  const [showRestore, setShowRestore] = useState(false);
  const [debugInfo, setDebugInfo] = useState({ backups: false, vault: 'Unknown' });

  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    console.log('🚀 BrontoBox starting up...');

    try {
      // Step 1: Check if vault is already unlocked
      console.log('🔍 Checking vault status...');
      const status = await APIService.getVaultStatus();
      setVaultStatus(status);
      setDebugInfo(prev => ({ ...prev, vault: status.unlocked ? 'Unlocked' : 'Locked' }));

      if (status.unlocked) {
        console.log('✅ Vault already unlocked, proceeding to dashboard');
        setAppState('dashboard');
        return;
      }

      // Step 2: Check for backup files in directory
      console.log('🔍 Checking for backup files...');
      const backupResponse = await fetch('http://127.0.0.1:8000/backup/detect');

      if (backupResponse.ok) {
        const backupData = await backupResponse.json();
        const hasBackups = backupData.success && backupData.vault_count > 0;

        setHasBackupFiles(hasBackups);
        setDebugInfo(prev => ({ ...prev, backups: hasBackups }));

        if (hasBackups) {
          console.log(`📁 Found ${backupData.vault_count} vault backup(s) and ${backupData.registry_count} registry backup(s)`);
          setAppState('restore_check');
          return;
        }
      } else {
        setDebugInfo(prev => ({ ...prev, backups: false }));
      }

      // Step 3: No backups found, show normal login
      console.log('🔐 No backups found, showing vault login');
      setAppState('login');

    } catch (error) {
      console.error('❌ App initialization failed:', error);
      setDebugInfo(prev => ({ ...prev, vault: 'Error', backups: false }));
      // Fallback to login screen
      setAppState('login');
    }
  };

  const handleRestoreSuccess = (restorationSummary) => {
    console.log('✅ Vault restored successfully:', restorationSummary);
    setShowRestore(false);
    setAppState('dashboard');
  };

  const handleSkipRestore = () => {
    console.log('⏭️ User skipped restore, showing login');
    setShowRestore(false);
    setAppState('login');
  };

  const handleVaultUnlock = () => {
    console.log('🔓 Vault unlocked, switching to dashboard');
    setAppState('dashboard');
  };

  const handleVaultLock = () => {
    console.log('🔒 Vault locked, switching to login');
    setAppState('login');
    setVaultStatus(null);
  };

  // Show restore option if backups detected
  const handleShowRestore = () => {
    setShowRestore(true);
  };

  // Loading screen
  if (appState === 'loading') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="mb-6">
            <BrontoBoxLogo size={128} />
          </div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">BrontoBox</h1>
          <p className="text-gray-600 mb-6">Secure Distributed Storage</p>
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-sm text-gray-500">Initializing secure storage...</p>
        </div>
      </div>
    );
  }

  // Restore from backup screen
  if (appState === 'restore_check' || showRestore) {
    return (
      <NotificationProvider>
        <RestoreFromBackup
          onRestoreSuccess={handleRestoreSuccess}
          onSkip={handleSkipRestore}
        />
      </NotificationProvider>
    );
  }

  // Main app with router
  return (
    <NotificationProvider>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <AnimatePresence mode="wait">
            <Routes>
              {/* Main Dashboard Route */}
              <Route
                path="/"
                element={
                  appState === 'dashboard' ? (
                    <Dashboard onVaultLock={handleVaultLock} />
                  ) : (
                    <VaultLogin
                      onVaultUnlock={handleVaultUnlock}
                      hasBackupFiles={hasBackupFiles}
                      onShowRestore={handleShowRestore}
                    />
                  )
                }
              />

              {/* Settings Route */}
              <Route
                path="/settings"
                element={
                  appState === 'dashboard' ? (
                    <Settings onVaultLock={handleVaultLock} />
                  ) : (
                    <Navigate to="/" replace />
                  )
                }
              />

              {/* Catch all - redirect to home */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </AnimatePresence>

          {/* Debug info in development */}
          {process.env.NODE_ENV === 'development' && (
            <div className="fixed bottom-4 left-4 bg-black bg-opacity-75 text-white text-xs p-2 rounded">
              App State: {appState} | Vault: {debugInfo.vault} | Backups: {debugInfo.backups ? 'Yes' : 'No'}
            </div>
          )}
        </div>
      </Router>
    </NotificationProvider>
  );
};

export default App;
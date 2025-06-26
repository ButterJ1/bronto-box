// src/App.js
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import VaultSetup from './components/VaultSetup';
import Settings from './components/Settings';
import { APIService } from './services/APIService';
import { NotificationProvider } from './components/NotificationContext';
import './App.css';

function App() {
  const [vaultStatus, setVaultStatus] = useState({
    unlocked: false,
    loading: true,
    error: null
  });

  const [apiConnected, setApiConnected] = useState(false);

  // Check API connection and vault status on startup
  useEffect(() => {
    let mounted = true;

    const checkStatus = async () => {
      try {
        // Check if API server is running
        const health = await APIService.getHealth();
        
        if (mounted) {
          setApiConnected(true);
          
          // Check vault status
          const status = await APIService.getVaultStatus();
          setVaultStatus({
            unlocked: status.unlocked,
            loading: false,
            error: null
          });
        }
      } catch (error) {
        if (mounted) {
          setApiConnected(false);
          setVaultStatus({
            unlocked: false,
            loading: false,
            error: 'Cannot connect to BrontoBox API. Please ensure the backend server is running.'
          });
        }
      }
    };

    checkStatus();

    // Check status every 5 seconds
    const interval = setInterval(checkStatus, 5000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  // Handle vault unlock
  const handleVaultUnlock = () => {
    setVaultStatus(prev => ({ ...prev, unlocked: true }));
  };

  // Handle vault lock
  const handleVaultLock = () => {
    setVaultStatus(prev => ({ ...prev, unlocked: false }));
  };

  // Loading screen
  if (vaultStatus.loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-amber-100 via-amber-200 to-amber-200 flex items-center justify-center">
        <div className="text-center text-white">
          <div className="text-6xl mb-4">🦕</div>
          <h1 className="text-3xl font-bold mb-2">BrontoBox</h1>
          <p className="text-lg opacity-80">Loading secure storage...</p>
          <div className="mt-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto"></div>
          </div>
        </div>
      </div>
    );
  }

  // API connection error
  if (!apiConnected) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full mx-4">
          <div className="text-center">
            <div className="text-red-500 text-5xl mb-4">⚠️</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Connection Error</h2>
            <p className="text-gray-600 mb-6">
              Cannot connect to the BrontoBox API server.
            </p>
            <div className="bg-gray-50 rounded-lg p-4 mb-6 text-left">
              <p className="text-sm text-gray-700 mb-2">
                <strong>To fix this:</strong>
              </p>
              <ol className="text-sm text-gray-600 space-y-1">
                <li>1. Open a terminal in your BrontoBox directory</li>
                <li>2. Run: <code className="bg-gray-200 px-1 rounded">python brontobox_api.py</code></li>
                <li>3. Wait for "Application startup complete"</li>
                <li>4. Restart BrontoBox</li>
              </ol>
            </div>
            <button 
              onClick={() => window.location.reload()}
              className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg transition-colors"
            >
              Retry Connection
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <NotificationProvider>
      <Router>
        <div className="App">
          <Routes>
            <Route 
              path="/" 
              element={
                vaultStatus.unlocked ? (
                  <Dashboard onVaultLock={handleVaultLock} />
                ) : (
                  <VaultSetup onVaultUnlock={handleVaultUnlock} />
                )
              } 
            />
            <Route 
              path="/settings" 
              element={
                vaultStatus.unlocked ? (
                  <Settings onVaultLock={handleVaultLock} />
                ) : (
                  <Navigate to="/" replace />
                )
              } 
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </Router>
    </NotificationProvider>
  );
}

export default App;
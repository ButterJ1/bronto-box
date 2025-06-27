// src/components/Header.js
import React from 'react';
import { Lock, RefreshCw, Settings, Shield } from 'lucide-react';
import BrontoBoxLogo, { BrontoBoxFavicon, BrontoBoxSmall, BrontoBoxMedium, BrontoBoxLarge, BrontoBoxXL } from './BrontoBoxLogo';

const Header = ({ storageInfo, onVaultLock, onRefresh, refreshing, OnSettingsClick }) => {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-gradient-to-r from-green-600 to-green-700 text-white shadow-lg">
      <div className="flex items-center justify-between px-6 py-3">
        {/* Logo and Title */}
        <div className="flex items-center space-x-3">
          <div>
            <BrontoBoxMedium />
          </div>
          <h1 className="text-xl font-bold">BrontoBox</h1>
        </div>

        {/* Status Bar */}
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-2 bg-white/20 rounded-lg px-3 py-1">
            <Shield className="w-4 h-4" />
            <span className="text-sm">Encrypted</span>
          </div>

          <div className="flex items-center space-x-2 bg-white/20 rounded-lg px-3 py-1">
            <span className="text-sm">📧 {storageInfo.total_accounts} Accounts</span>
          </div>

          <div className="flex items-center space-x-2 bg-white/20 rounded-lg px-3 py-1">
            <span className="text-sm">💾 {storageInfo.total_available_gb?.toFixed(1) || 0} GB Available</span>
          </div>

          <div className="flex items-center space-x-2 bg-white/20 rounded-lg px-3 py-1">
            <span className="text-sm">🔄 Synced</span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-2">
          <button
            onClick={onRefresh}
            disabled={refreshing}
            className="p-2 rounded-lg bg-white/20 hover:bg-white/30 transition-colors disabled:opacity-50"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>

          <button
            onClick={OnSettingsClick}
            className="p-2 rounded-lg bg-white/20 hover:bg-white/30 transition-colors"
            title="Settings"
          >
            <Settings className="w-4 h-4" />
          </button>

          <button
            onClick={onVaultLock}
            className="p-2 rounded-lg bg-white/20 hover:bg-white/30 transition-colors"
            title="Lock Vault"
          >
            <Lock className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
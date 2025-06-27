// src/components/VaultLogin.js - UPDATED WITH RESTORE OPTION
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Lock, Unlock, Eye, EyeOff, Shield, Key, Upload } from 'lucide-react';
import { APIService } from '../services/APIService';
import { useNotification } from './NotificationContext';
import BrontoBoxLogo, { BrontoBoxFavicon, BrontoBoxSmall, BrontoBoxMedium, BrontoBoxLarge, BrontoBoxXL } from './BrontoBoxLogo';


const VaultLogin = ({ onVaultUnlock, hasBackupFiles, onShowRestore }) => {
    const [mode, setMode] = useState('unlock'); // 'unlock' or 'create'
    const [formData, setFormData] = useState({
        masterPassword: '',
        salt: ''
    });
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [existingVaults, setExistingVaults] = useState([]);

    const { showNotification } = useNotification();

    useEffect(() => {
        loadExistingVaults();
    }, []);

    const loadExistingVaults = async () => {
        try {
            const response = await fetch('http://127.0.0.1:8000/vault/list');
            if (response.ok) {
                const data = await response.json();
                setExistingVaults(data.vaults || []);

                // Auto-set mode based on existing vaults
                if (data.vaults && data.vaults.length > 0) {
                    setMode('unlock');
                } else {
                    setMode('create');
                }
            }
        } catch (error) {
            console.error('Failed to load existing vaults:', error);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!formData.masterPassword.trim()) {
            showNotification('Please enter a master password', 'warning');
            return;
        }

        if (mode === 'unlock' && !formData.salt.trim()) {
            showNotification('Please enter your vault salt', 'warning');
            return;
        }

        setLoading(true);

        try {
            let result;

            if (mode === 'create') {
                console.log('🔐 Creating new vault...');
                result = await APIService.initializeVault(formData.masterPassword);

                if (result.success) {
                    showNotification('Vault created successfully!', 'success');
                    console.log('✅ New vault created:', result.vault_id);
                    console.log('🔑 Salt:', result.salt);

                    // Show salt to user for safekeeping
                    setTimeout(() => {
                        alert(`🔑 IMPORTANT: Save your vault salt!\n\nSalt: ${result.salt}\n\nYou need both your password AND this salt to unlock your vault. Store it safely!`);
                    }, 1000);

                    onVaultUnlock();
                } else {
                    throw new Error(result.message || 'Failed to create vault');
                }
            } else {
                console.log('🔓 Unlocking existing vault...');
                result = await APIService.unlockVault(formData.masterPassword, formData.salt);

                if (result.success) {
                    showNotification('Vault unlocked successfully!', 'success');
                    console.log('✅ Vault unlocked:', result.vault_id);
                    console.log('📁 Files loaded:', result.files_loaded);
                    console.log('📧 Accounts loaded:', result.accounts_loaded);

                    // Show discovery info if files were found
                    if (result.files_loaded > 0) {
                        setTimeout(() => {
                            showNotification(`Welcome back! Found ${result.files_loaded} files and ${result.accounts_loaded} accounts`, 'info');
                        }, 1000);
                    }

                    onVaultUnlock();
                } else {
                    throw new Error(result.message || 'Failed to unlock vault');
                }
            }
        } catch (error) {
            console.error(`❌ ${mode} failed:`, error);
            showNotification(error.message, 'error');
        } finally {
            setLoading(false);
        }
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleVaultSelect = (vault) => {
        setFormData(prev => ({
            ...prev,
            salt: vault.vault_id // For simplicity, but in real app you'd extract the actual salt
        }));
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden"
            >
                {/* Header */}
                <div className="bg-gradient-to-r from-blue-500 to-blue-500 text-white p-8 text-center">
                    <div className="mb-4">
                        <BrontoBoxLarge />
                    </div>

                    <h1 className="text-2xl font-bold mb-2">BrontoBox</h1>
                    <p className="text-blue-100">Secure Distributed Storage</p>
                </div>

                {/* Backup Files Banner */}
                {hasBackupFiles && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        className="bg-green-50 border-b border-green-200 p-4"
                    >
                        <div className="flex items-center justify-between">
                            <div className="flex items-center">
                                <Upload className="w-5 h-5 text-green-600 mr-2" />
                                <div>
                                    <p className="text-sm font-medium text-green-800">Backup Files Detected!</p>
                                    <p className="text-xs text-green-600">Restore your existing vault</p>
                                </div>
                            </div>
                            <button
                                onClick={onShowRestore}
                                className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-sm transition-colors"
                            >
                                Restore
                            </button>
                        </div>
                    </motion.div>
                )}

                {/* Mode Tabs */}
                <div className="flex border-b border-gray-200">
                    <button
                        onClick={() => setMode('unlock')}
                        className={`flex-1 py-4 px-6 text-center font-medium transition-colors ${mode === 'unlock'
                                ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                                : 'text-gray-600 hover:text-gray-800'
                            }`}
                    >
                        <Unlock className="w-5 h-5 mx-auto mb-1" />
                        Unlock Vault
                    </button>
                    <button
                        onClick={() => setMode('create')}
                        className={`flex-1 py-4 px-6 text-center font-medium transition-colors ${mode === 'create'
                                ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                                : 'text-gray-600 hover:text-gray-800'
                            }`}
                    >
                        <Lock className="w-5 h-5 mx-auto mb-1" />
                        Create Vault
                    </button>
                </div>

                {/* Form Content */}
                <div className="p-8">
                    <AnimatePresence mode="wait">
                        {mode === 'unlock' ? (
                            <motion.div
                                key="unlock"
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 20 }}
                            >
                                <h2 className="text-xl font-semibold text-gray-800 mb-6 text-center">
                                    Unlock Your Vault
                                </h2>

                                {/* Existing Vaults */}
                                {existingVaults.length > 0 && (
                                    <div className="mb-6">
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Recent Vaults
                                        </label>
                                        <div className="space-y-2">
                                            {existingVaults.slice(0, 3).map((vault, index) => (
                                                <button
                                                    key={vault.vault_id}
                                                    onClick={() => handleVaultSelect(vault)}
                                                    className="w-full p-3 text-left border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors"
                                                >
                                                    <div className="flex items-center justify-between">
                                                        <div>
                                                            <p className="font-medium text-gray-800">Vault {index + 1}</p>
                                                            <p className="text-xs text-gray-500">
                                                                Last accessed: {new Date(vault.last_accessed).toLocaleDateString()}
                                                            </p>
                                                        </div>
                                                        <Shield className="w-4 h-4 text-blue-500" />
                                                    </div>
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                <form onSubmit={handleSubmit} className="space-y-4">
                                    {/* Salt Input */}
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Vault Salt
                                        </label>
                                        <input
                                            type="text"
                                            name="salt"
                                            value={formData.salt}
                                            onChange={handleInputChange}
                                            placeholder="Enter your vault salt"
                                            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                            required
                                        />
                                        <p className="text-xs text-gray-500 mt-1">
                                            The salt you received when creating your vault
                                        </p>
                                    </div>

                                    {/* Password Input */}
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Master Password
                                        </label>
                                        <div className="relative">
                                            <input
                                                type={showPassword ? 'text' : 'password'}
                                                name="masterPassword"
                                                value={formData.masterPassword}
                                                onChange={handleInputChange}
                                                placeholder="Enter your master password"
                                                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-12"
                                                required
                                            />
                                            <button
                                                type="button"
                                                onClick={() => setShowPassword(!showPassword)}
                                                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                                            >
                                                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                            </button>
                                        </div>
                                    </div>

                                    <button
                                        type="submit"
                                        disabled={loading}
                                        className="w-full bg-blue-500 hover:bg-blue-600 disabled:bg-blue-300 text-white py-3 px-4 rounded-lg font-medium transition-colors flex items-center justify-center space-x-2"
                                    >
                                        {loading ? (
                                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                                        ) : (
                                            <>
                                                <Unlock className="w-5 h-5" />
                                                <span>Unlock Vault</span>
                                            </>
                                        )}
                                    </button>
                                </form>
                            </motion.div>
                        ) : (
                            <motion.div
                                key="create"
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                            >
                                <h2 className="text-xl font-semibold text-gray-800 mb-6 text-center">
                                    Create New Vault
                                </h2>

                                <form onSubmit={handleSubmit} className="space-y-4">
                                    {/* Password Input */}
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Master Password
                                        </label>
                                        <div className="relative">
                                            <input
                                                type={showPassword ? 'text' : 'password'}
                                                name="masterPassword"
                                                value={formData.masterPassword}
                                                onChange={handleInputChange}
                                                placeholder="Choose a strong master password"
                                                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-12"
                                                required
                                            />
                                            <button
                                                type="button"
                                                onClick={() => setShowPassword(!showPassword)}
                                                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                                            >
                                                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                            </button>
                                        </div>
                                        <p className="text-xs text-gray-500 mt-1">
                                            Choose a strong password - you cannot recover it if lost!
                                        </p>
                                    </div>

                                    {/* Security Notice */}
                                    <div className="bg-amber-50 border border-amber-200 p-4 rounded-lg">
                                        <div className="flex items-start">
                                            <Key className="w-5 h-5 text-amber-600 mr-2 mt-0.5" />
                                            <div>
                                                <h4 className="font-medium text-amber-800">Important Security Notice</h4>
                                                <p className="text-sm text-amber-700 mt-1">
                                                    Your master password and vault salt are the ONLY way to access your encrypted files.
                                                    Store them securely - they cannot be recovered if lost.
                                                </p>
                                            </div>
                                        </div>
                                    </div>

                                    <button
                                        type="submit"
                                        disabled={loading}
                                        className="w-full bg-green-500 hover:bg-green-600 disabled:bg-green-300 text-white py-3 px-4 rounded-lg font-medium transition-colors flex items-center justify-center space-x-2"
                                    >
                                        {loading ? (
                                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                                        ) : (
                                            <>
                                                <Lock className="w-5 h-5" />
                                                <span>Create Vault</span>
                                            </>
                                        )}
                                    </button>
                                </form>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* Footer */}
                <div className="bg-gray-50 px-8 py-4 text-center">
                    <p className="text-xs text-gray-500">
                        🔐 Enhanced security with vault verification
                    </p>
                    {hasBackupFiles && (
                        <p className="text-xs text-green-600 mt-1">
                            💡 Backup files detected - use "Restore" to recover your vault
                        </p>
                    )}
                </div>
            </motion.div>
        </div>
    );
};

export default VaultLogin;
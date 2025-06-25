
// src/components/UploadProgress.js
import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, AlertCircle, X } from 'lucide-react';
import { APIService } from '../services/APIService';

const UploadItem = ({ upload }) => {
  const getStatusIcon = () => {
    switch (upload.status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return (
          <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        );
    }
  };

  const getStatusColor = () => {
    switch (upload.status) {
      case 'completed':
        return 'bg-green-100 border-green-200';
      case 'error':
        return 'bg-red-100 border-red-200';
      default:
        return 'bg-blue-100 border-blue-200';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className={`p-4 rounded-lg border ${getStatusColor()} mb-2`}
    >
      <div className="flex items-center space-x-3">
        {getStatusIcon()}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-800 truncate">
            {upload.file.name}
          </p>
          <p className="text-xs text-gray-600">
            {APIService.formatFileSize(upload.file.size)}
          </p>
        </div>
        <div className="text-xs text-gray-600">
          {upload.status === 'error' && upload.error ? (
            <span className="text-red-600">{upload.error}</span>
          ) : (
            <span>{Math.round(upload.progress)}%</span>
          )}
        </div>
      </div>
      
      {/* Progress Bar */}
      {upload.status === 'uploading' && (
        <div className="mt-2 bg-gray-200 rounded-full h-2">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${upload.progress}%` }}
            className="bg-blue-500 h-2 rounded-full"
          />
        </div>
      )}
    </motion.div>
  );
};

const UploadProgress = ({ uploads }) => {
  return (
    <div className="bg-white rounded-lg shadow-lg border p-4 max-w-sm">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-medium text-gray-800">Upload Progress</h3>
        <span className="text-xs text-gray-500">
          {uploads.filter(u => u.status === 'uploading').length} active
        </span>
      </div>
      
      <div className="max-h-64 overflow-y-auto">
        <AnimatePresence>
          {uploads.map((upload) => (
            <UploadItem key={upload.id} upload={upload} />
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};

export { FileArea, StorageOverview, Sidebar, UploadProgress };
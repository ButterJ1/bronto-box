// src/components/FileArea.js - ENHANCED FOR UNIFIED FILE EXPERIENCE
import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion } from 'framer-motion';
import { Upload, Download, Trash2, Info, ShieldAlert, FileText, Image, Video, Archive, Clock, HardDrive } from 'lucide-react';
import { APIService } from '../services/APIService';

const FileCard = ({ file, onDownload, onDelete, storageInfo }) => {
  const getFileIcon = (fileName) => {
    const ext = fileName.toLowerCase().split('.').pop();
    
    if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg'].includes(ext)) {
      return <Image className="w-8 h-8 text-blue-500" />;
    } else if (['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv'].includes(ext)) {
      return <Video className="w-8 h-8 text-purple-500" />;
    } else if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) {
      return <Archive className="w-8 h-8 text-orange-500" />;
    } else {
      return <FileText className="w-8 h-8 text-gray-500" />;
    }
  };

  const getChunkVisualization = () => {
    // Use actual accounts from file metadata
    const accountsUsed = file.accounts_used || [];
    const chunkCount = file.chunks || 1;
    const accountColors = ['bg-green-500', 'bg-blue-500', 'bg-orange-500', 'bg-purple-500'];
    
    return Array.from({ length: Math.min(chunkCount, 12) }, (_, i) => {
      const accountIndex = i % accountsUsed.length;
      const colorClass = accountColors[accountIndex] || 'bg-gray-400';
      
      // Find account email for tooltip
      const accountId = accountsUsed[accountIndex];
      const account = storageInfo.accounts?.find(acc => acc.account_id === accountId);
      const accountEmail = account?.email || 'Unknown Account';
      
      return (
        <div
          key={i}
          className={`w-3 h-3 rounded-sm ${colorClass} hover:scale-125 transition-transform cursor-pointer`}
          title={`Chunk ${i + 1} → ${accountEmail}`}
        />
      );
    });
  };

  // Determine file type badge
  const getFileTypeBadge = () => {
    if (file.is_discovered) {
      return (
        <div className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full font-medium flex items-center">
          <Clock className="w-4 h-4 mr-1" />
          Discovered
        </div>
      );
    } else {
      return (
        <div className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full font-medium">
          <ShieldAlert className="w-4 h-4 mr-0" />
          {/* Encrypted */}
        </div>
      );
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow border-l-4 border-green-500"
    >
      {/* File Header */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center space-x-3">
          {getFileIcon(file.name)}
          <div>
            <h3 className="font-semibold text-gray-800 truncate max-w-48" title={file.name}>
              {file.name}
            </h3>
            <p className="text-sm text-gray-500">
              {APIService.formatFileSize(file.size_bytes)}
            </p>
          </div>
        </div>
        {getFileTypeBadge()}
      </div>

      {/* Enhanced File Info */}
      <div className="mb-4 space-y-2">
        <div className="flex items-center justify-between text-xs text-gray-600">
          <span className="flex items-center">
            <HardDrive className="w-3 h-3 mr-1" />
            {file.chunks} chunk{file.chunks !== 1 ? 's' : ''}
          </span>
          <span>{file.accounts_used?.length || 0} account{(file.accounts_used?.length || 0) !== 1 ? 's' : ''}</span>
        </div>
        
        {/* Upload date */}
        <div className="text-xs text-gray-500">
          📅 {new Date(file.created_at).toLocaleDateString()} {new Date(file.created_at).toLocaleTimeString()}
        </div>
        
        {/* Discovery indicator for discovered files */}
        {file.is_discovered && (
          <div className="text-xs text-blue-600 bg-blue-50 p-2 rounded">
            💡 This file was found in your Google Drive from a previous session
          </div>
        )}
      </div>

      {/* Storage Distribution Visualization */}
      <div className="mb-4">
        <p className="text-xs text-gray-600 mb-2">Storage Distribution:</p>
        <div className="flex flex-wrap gap-1">
          {getChunkVisualization()}
        </div>
      </div>

      {/* File Actions */}
      <div className="flex space-x-2">
        <button
          onClick={() => onDownload(file)}
          className="flex-1 bg-blue-500 hover:bg-blue-600 text-white text-sm px-3 py-2 rounded-lg transition-colors flex items-center justify-center space-x-1"
        >
          <Download className="w-4 h-4" />
          <span>Download</span>
        </button>
        <button
          className="bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm px-3 py-2 rounded-lg transition-colors flex items-center justify-center"
          title="File Info"
        >
          <Info className="w-4 h-4" />
        </button>
        <button
          onClick={() => onDelete(file)}
          className="bg-red-100 hover:bg-red-200 text-red-700 text-sm px-3 py-2 rounded-lg transition-colors flex items-center justify-center"
          title="Delete"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </motion.div>
  );
};

const FileArea = ({ files, fileStatistics, onFileUpload, onFileDownload, onFileDelete, storageInfo }) => {
  const onDrop = useCallback((acceptedFiles) => {
    onFileUpload(acceptedFiles);
  }, [onFileUpload]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    multiple: true,
    accept: {
      '*/*': []
    }
  });

  return (
    <div className="p-6">
      {/* Drop Zone */}
      <div
        {...getRootProps()}
        className={`
          border-3 border-dashed rounded-xl p-12 text-center transition-all cursor-pointer mb-8
          ${isDragActive && !isDragReject 
            ? 'border-green-400 bg-green-50 scale-105' 
            : isDragReject 
            ? 'border-red-400 bg-red-50' 
            : 'border-gray-300 bg-gray-50 hover:border-green-400 hover:bg-green-50'
          }
        `}
      >
        <input {...getInputProps()} />
        <div className="text-5xl mb-4">📦</div>
        <h3 className="text-xl font-semibold text-gray-700 mb-2">
          {isDragActive 
            ? isDragReject 
              ? 'File type not supported' 
              : 'Drop files here...'
            : 'Drop files here to encrypt and store securely'
          }
        </h3>
        <p className="text-gray-500 mb-4">
          Your files will be encrypted, chunked, and distributed across your Google accounts
        </p>
        <p className="text-sm text-gray-400">
          Click to browse files or drag & drop
        </p>
      </div>

      {/* Enhanced Files Section */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-800 flex items-center">
            📁 My Secure Files
          </h2>
          <div className="flex items-center space-x-4 text-sm text-gray-500">
            {fileStatistics && (
              <>
                <span className="flex items-center bg-blue-50 px-2 py-1 rounded">
                  <Clock className="w-4 h-4 mr-1" />
                  {fileStatistics.discovered_files} discovered
                </span>
                <span className="flex items-center bg-green-50 px-2 py-1 rounded">
                  <Upload className="w-4 h-4 mr-1" />
                  {fileStatistics.uploaded_files} uploaded
                </span>
              </>
            )}
            <span>
              {files.length} file{files.length !== 1 ? 's' : ''} total
            </span>
          </div>
        </div>

        {/* File Statistics Summary */}
        {fileStatistics && files.length > 0 && (
          <div className="bg-gradient-to-r from-blue-50 to-green-50 p-4 rounded-lg mb-6 border border-blue-200">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-lg font-bold text-blue-600">
                  {fileStatistics.total_size_gb}GB
                </div>
                <div className="text-xs text-blue-600">Total Storage</div>
              </div>
              <div>
                <div className="text-lg font-bold text-green-600">
                  {fileStatistics.accounts_used}
                </div>
                <div className="text-xs text-green-600">Accounts Used</div>
              </div>
              <div>
                <div className="text-lg font-bold text-purple-600">
                  {fileStatistics.discovered_files}
                </div>
                <div className="text-xs text-purple-600">Auto-Discovered</div>
              </div>
              <div>
                <div className="text-lg font-bold text-orange-600">
                  {fileStatistics.uploaded_files}
                </div>
                <div className="text-xs text-orange-600">Newly Uploaded</div>
              </div>
            </div>
          </div>
        )}

        {/* Files Grid */}
        {files.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {files.map((file, index) => (
              <FileCard
                key={file.file_id || index}
                file={file}
                onDownload={onFileDownload}
                onDelete={onFileDelete}
                storageInfo={storageInfo}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📂</div>
            <h3 className="text-xl font-semibold text-gray-600 mb-2">No files yet</h3>
            <p className="text-gray-500 mb-4">
              Upload your first file to get started with secure storage
            </p>
            {storageInfo.total_accounts === 0 && (
              <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 p-4 rounded-lg max-w-md mx-auto">
                <p className="text-sm">
                  💡 <strong>Tip:</strong> Add a Google account from the sidebar to start uploading files
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Help Section for New Users */}
      {files.length === 0 && storageInfo.total_accounts > 0 && (
        <div className="bg-blue-50 border border-blue-200 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-blue-800 mb-3">🎯 Getting Started</h3>
          <div className="space-y-2 text-sm text-blue-700">
            <p>• <strong>Drag & drop</strong> files into the upload area above</p>
            <p>• <strong>Files are automatically encrypted</strong> with AES-256-GCM</p>
            <p>• <strong>Chunks are distributed</strong> across your Google accounts for security</p>
            <p>• <strong>Original files are preserved</strong> - downloads give you the exact same file</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileArea;
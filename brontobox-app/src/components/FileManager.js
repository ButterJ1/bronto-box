// src/components/FileManager.js - UPDATED FOR BRONTOBOX FILES VIEW
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, Filter, SortAsc, SortDesc, Grid, List, 
  Folder, File, Calendar, HardDrive, Eye, Trash2,
  Download, RefreshCw, Settings, ArrowLeft, Clock,
  Upload, FileText, Image, Video, Archive
} from 'lucide-react';
import { APIService } from '../services/APIService';
import { useNotification } from './NotificationContext';

const FileTypeIcon = ({ fileName, fileType }) => {
  const ext = fileName.toLowerCase().split('.').pop();
  
  if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg'].includes(ext)) {
    return <Image className="w-5 h-5 text-blue-500" />;
  } else if (['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv'].includes(ext)) {
    return <Video className="w-5 h-5 text-purple-500" />;
  } else if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) {
    return <Archive className="w-5 h-5 text-orange-500" />;
  } else {
    return <FileText className="w-5 h-5 text-gray-500" />;
  }
};

const FileCard = ({ file, viewMode, onDelete, onDownload }) => {
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const isListView = viewMode === 'list';

  if (isListView) {
    return (
      <motion.tr
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="hover:bg-gray-50 border-b border-gray-200"
      >
        <td className="px-4 py-3">
          <div className="flex items-center space-x-3">
            <FileTypeIcon fileName={file.name} />
            <div>
              <p className="font-medium text-gray-800 truncate max-w-xs" title={file.name}>
                {file.name}
              </p>
              <div className="flex items-center space-x-2 text-xs text-gray-500">
                {file.is_discovered ? (
                  <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded">
                    <Clock className="w-3 h-3 inline mr-1" />
                    Discovered
                  </span>
                ) : (
                  <span className="bg-green-100 text-green-700 px-2 py-1 rounded">
                    <Upload className="w-3 h-3 inline mr-1" />
                    Uploaded
                  </span>
                )}
              </div>
            </div>
          </div>
        </td>
        <td className="px-4 py-3 text-sm text-gray-600">
          {APIService.formatFileSize(file.size_bytes)}
        </td>
        <td className="px-4 py-3 text-sm text-gray-600">
          {file.chunks} chunk{file.chunks !== 1 ? 's' : ''}
        </td>
        <td className="px-4 py-3 text-sm text-gray-600">
          {formatDate(file.created_at)}
        </td>
        <td className="px-4 py-3 text-sm text-gray-600">
          {file.accounts_used?.length || 0} account{(file.accounts_used?.length || 0) !== 1 ? 's' : ''}
        </td>
        <td className="px-4 py-3">
          <div className="flex space-x-2">
            <button
              onClick={() => onDownload(file)}
              className="p-1 rounded-lg hover:bg-blue-100 text-blue-600"
              title="Download Original File"
            >
              <Download className="w-4 h-4" />
            </button>
            <button
              className="p-1 rounded-lg hover:bg-gray-100 text-gray-600"
              title="View Details"
            >
              <Eye className="w-4 h-4" />
            </button>
            <button
              onClick={() => onDelete(file)}
              className="p-1 rounded-lg hover:bg-red-100 text-red-600"
              title="Delete File"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </td>
      </motion.tr>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-4 border"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-3">
          <FileTypeIcon fileName={file.name} />
          <div>
            <h3 className="font-medium text-gray-800 truncate max-w-40" title={file.name}>
              {file.name}
            </h3>
            <div className="flex items-center space-x-2 text-xs text-gray-500 mt-1">
              {file.is_discovered ? (
                <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded">
                  <Clock className="w-3 h-3 inline mr-1" />
                  Discovered
                </span>
              ) : (
                <span className="bg-green-100 text-green-700 px-2 py-1 rounded">
                  <Upload className="w-3 h-3 inline mr-1" />
                  Uploaded
                </span>
              )}
            </div>
          </div>
        </div>
        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
          {APIService.formatFileSize(file.size_bytes)}
        </span>
      </div>

      <div className="text-xs text-gray-600 mb-3 space-y-1">
        <p>📦 {file.chunks} chunk{file.chunks !== 1 ? 's' : ''}</p>
        <p>📧 {file.accounts_used?.length || 0} account{(file.accounts_used?.length || 0) !== 1 ? 's' : ''}</p>
        <p>📅 {formatDate(file.created_at)}</p>
      </div>

      <div className="flex justify-between items-center">
        <div className="flex space-x-2">
          <button
            onClick={() => onDownload(file)}
            className="text-xs bg-blue-100 hover:bg-blue-200 text-blue-700 px-2 py-1 rounded transition-colors"
          >
            Download
          </button>
          <button
            className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-2 py-1 rounded transition-colors"
          >
            Details
          </button>
        </div>
        <button
          onClick={() => onDelete(file)}
          className="text-xs bg-red-100 hover:bg-red-200 text-red-700 px-2 py-1 rounded transition-colors"
        >
          Delete
        </button>
      </div>
    </motion.div>
  );
};

const SearchBar = ({ searchTerm, onSearchChange, onSearchSubmit, isSearching }) => {
  return (
    <div className="relative">
      <form onSubmit={onSearchSubmit} className="flex">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search files by name..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-l-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <button
          type="submit"
          disabled={isSearching}
          className="bg-blue-500 hover:bg-blue-600 disabled:bg-blue-300 text-white px-4 py-2 rounded-r-lg transition-colors"
        >
          {isSearching ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            'Search'
          )}
        </button>
      </form>
    </div>
  );
};

const FileManager = ({ account, onClose }) => {
  const [files, setFiles] = useState([]);
  const [allFiles, setAllFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');
  const [viewMode, setViewMode] = useState('grid');
  const [folderStats, setFolderStats] = useState(null);
  const [searchActive, setSearchActive] = useState(false);
  const [viewType, setViewType] = useState('brontobox'); // 'brontobox' or 'raw'

  const { showNotification } = useNotification();

  useEffect(() => {
    loadFiles();
    loadFolderStats();
  }, [account, viewType]);

  const loadFiles = async () => {
    try {
      setLoading(true);
      
      if (viewType === 'brontobox') {
        // Load BrontoBox files for this account
        const response = await fetch(`http://127.0.0.1:8000/drive/brontobox-files/${account.account_id}`);
        
        if (response.ok) {
          const data = await response.json();
          const accountFiles = data.files || [];
          setFiles(accountFiles);
          setAllFiles(accountFiles);
          console.log(`📁 Loaded ${accountFiles.length} BrontoBox files for account ${account.email}`);
        } else {
          throw new Error('Failed to load BrontoBox files');
        }
      } else {
        // Load raw chunks (technical view)
        const response = await fetch(`http://127.0.0.1:8000/drive/raw-chunks/${account.account_id}`);
        
        if (response.ok) {
          const data = await response.json();
          const chunks = data.chunks || [];
          setFiles(chunks);
          setAllFiles(chunks);
          console.log(`🔧 Loaded ${chunks.length} raw chunks for account ${account.email}`);
        } else {
          throw new Error('Failed to load raw chunks');
        }
      }
      
    } catch (error) {
      console.error('Error loading files:', error);
      showNotification(`Failed to load files: ${error.message}`, 'error');
      setFiles([]);
      setAllFiles([]);
    } finally {
      setLoading(false);
    }
  };

  const loadFolderStats = async () => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/drive/stats/${account.account_id}`);
      
      if (response.ok) {
        const data = await response.json();
        setFolderStats(data);
      }
    } catch (error) {
      console.error('Error loading folder stats:', error);
      // Mock stats for demonstration
      setFolderStats({
        total_files: files.length,
        total_size_mb: 15.5,
        file_types: {
          'BrontoBox Files': files.filter(f => viewType === 'brontobox').length,
          'Raw Chunks': files.length
        }
      });
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchTerm.trim()) {
      setSearchActive(false);
      setFiles(allFiles);
      return;
    }

    try {
      setIsSearching(true);
      setSearchActive(true);
      
      // Filter locally for BrontoBox files
      const filtered = allFiles.filter(file => 
        file.name.toLowerCase().includes(searchTerm.toLowerCase())
      );
      
      setFiles(filtered);
      showNotification(`Found ${filtered.length} matching files`, 'info');
      
    } catch (error) {
      console.error('Search error:', error);
      showNotification('Search failed', 'error');
    } finally {
      setIsSearching(false);
    }
  };

  const clearSearch = () => {
    setSearchTerm('');
    setSearchActive(false);
    setFiles(allFiles);
  };

  const handleSort = (newSortBy) => {
    if (sortBy === newSortBy) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(newSortBy);
      setSortOrder('desc');
    }
    
    // Sort files locally
    const sorted = [...files].sort((a, b) => {
      let aVal, bVal;
      
      switch (newSortBy) {
        case 'name':
          aVal = a.name.toLowerCase();
          bVal = b.name.toLowerCase();
          break;
        case 'size':
          aVal = a.size_bytes || a.size || 0;
          bVal = b.size_bytes || b.size || 0;
          break;
        case 'date':
          aVal = new Date(a.created_at || a.created_time);
          bVal = new Date(b.created_at || b.created_time);
          break;
        default:
          return 0;
      }
      
      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
    
    setFiles(sorted);
  };

  const handleDownload = async (file) => {
    try {
      showNotification(`Downloading ${file.name}...`, 'info');
      
      if (viewType === 'brontobox') {
        // Download original decrypted file
        const response = await fetch(`http://127.0.0.1:8000/files/${file.file_id}/download`);
        
        if (!response.ok) {
          throw new Error('Download failed');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = file.name;
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
        
        showNotification(`Downloaded ${file.name}`, 'success');
      } else {
        // Download raw chunk (technical view)
        const response = await fetch(`http://127.0.0.1:8000/drive/download/${account.account_id}/${file.file_id}`);
        
        if (!response.ok) {
          throw new Error('Download failed');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = file.name;
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
        
        showNotification(`Downloaded raw chunk: ${file.name}`, 'success');
      }
      
    } catch (error) {
      console.error('Download error:', error);
      showNotification(`Download failed: ${error.message}`, 'error');
    }
  };

  const handleDelete = async (file) => {
    const isRawChunk = viewType === 'raw';
    const confirmMessage = isRawChunk 
      ? `Delete raw chunk "${file.name}"?\n\nThis will permanently remove this encrypted chunk from Google Drive.`
      : `Delete file "${file.name}"?\n\nThis will permanently remove the file and all its chunks from Google Drive.`;
    
    const confirmed = window.confirm(confirmMessage);
    
    if (confirmed) {
      try {
        showNotification(`Deleting ${file.name}...`, 'info');
        
        let response;
        if (isRawChunk) {
          response = await fetch(`http://127.0.0.1:8000/drive/delete/${account.account_id}/${file.file_id}`, {
            method: 'DELETE'
          });
        } else {
          response = await fetch(`http://127.0.0.1:8000/files/${file.file_id}`, {
            method: 'DELETE'
          });
        }
        
        if (!response.ok) {
          throw new Error('Delete failed');
        }
        
        // Remove from local state
        setFiles(files.filter(f => f.file_id !== file.file_id));
        setAllFiles(allFiles.filter(f => f.file_id !== file.file_id));
        
        showNotification(`Deleted ${file.name}`, 'success');
        loadFolderStats(); // Refresh stats
        
      } catch (error) {
        console.error('Delete error:', error);
        showNotification(`Delete failed: ${error.message}`, 'error');
      }
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">Loading Files</h3>
            <p className="text-gray-600">
              {viewType === 'brontobox' ? 'Loading BrontoBox files...' : 'Loading raw chunks...'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-2xl max-w-6xl w-full mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h2 className="text-xl font-bold text-gray-800 flex items-center">
                <Folder className="w-6 h-6 mr-2 text-blue-500" />
                {viewType === 'brontobox' ? 'BrontoBox Files' : 'Raw Google Drive Files'}
              </h2>
              <p className="text-sm text-gray-600">{account.email}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* View Type Toggle */}
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewType('brontobox')}
                className={`px-3 py-1 rounded text-xs transition-colors ${
                  viewType === 'brontobox' 
                    ? 'bg-blue-500 text-white' 
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                📁 BrontoBox Files
              </button>
              <button
                onClick={() => setViewType('raw')}
                className={`px-3 py-1 rounded text-xs transition-colors ${
                  viewType === 'raw' 
                    ? 'bg-blue-500 text-white' 
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                🔧 Raw Chunks
              </button>
            </div>
            
            <button
              onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="Toggle view mode"
            >
              {viewMode === 'grid' ? <List className="w-5 h-5" /> : <Grid className="w-5 h-5" />}
            </button>
            <button
              onClick={loadFiles}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="Refresh"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Stats Bar */}
        {folderStats && (
          <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center space-x-6">
                <span className="text-gray-600">
                  📁 {files.length} {viewType === 'brontobox' ? 'files' : 'chunks'}
                </span>
                <span className="text-gray-600">
                  💾 {folderStats.total_size_mb} MB total
                </span>
                {viewType === 'brontobox' && (
                  <span className="text-gray-600">
                    🔍 Original filenames shown
                  </span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Search and Controls */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center space-x-4 mb-4">
            <div className="flex-1">
              <SearchBar
                searchTerm={searchTerm}
                onSearchChange={setSearchTerm}
                onSearchSubmit={handleSearch}
                isSearching={isSearching}
              />
            </div>
            {searchActive && (
              <button
                onClick={clearSearch}
                className="text-gray-500 hover:text-gray-700 px-3 py-2"
              >
                Clear
              </button>
            )}
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">Sort by:</span>
              {['name', 'date', 'size'].map((option) => (
                <button
                  key={option}
                  onClick={() => handleSort(option)}
                  className={`px-3 py-1 rounded text-sm transition-colors ${
                    sortBy === option
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                  }`}
                >
                  {option.charAt(0).toUpperCase() + option.slice(1)}
                  {sortBy === option && (
                    sortOrder === 'asc' ? 
                    <SortAsc className="w-3 h-3 inline ml-1" /> : 
                    <SortDesc className="w-3 h-3 inline ml-1" />
                  )}
                </button>
              ))}
            </div>

            <div className="text-sm text-gray-600">
              {searchActive ? `${files.length} search results` : `${files.length} files total`}
            </div>
          </div>
        </div>

        {/* File List */}
        <div className="flex-1 overflow-auto p-6">
          {files.length === 0 ? (
            <div className="text-center py-12">
              <Folder className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-600 mb-2">
                {searchActive ? 'No files match your search' : 'No files found'}
              </h3>
              <p className="text-gray-500">
                {searchActive 
                  ? 'Try adjusting your search terms' 
                  : viewType === 'brontobox'
                  ? 'No BrontoBox files found in this account'
                  : 'No raw chunks found in this account'
                }
              </p>
            </div>
          ) : viewMode === 'list' ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Name</th>
                    <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Size</th>
                    <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Chunks</th>
                    <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Created</th>
                    <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Accounts</th>
                    <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <AnimatePresence>
                    {files.map((file) => (
                      <FileCard
                        key={file.file_id}
                        file={file}
                        viewMode={viewMode}
                        onDelete={handleDelete}
                        onDownload={handleDownload}
                      />
                    ))}
                  </AnimatePresence>
                </tbody>
              </table>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              <AnimatePresence>
                {files.map((file) => (
                  <FileCard
                    key={file.file_id}
                    file={file}
                    viewMode={viewMode}
                    onDelete={handleDelete}
                    onDownload={handleDownload}
                  />
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div>
              <span className="font-medium">
                {viewType === 'brontobox' ? 'BrontoBox Files' : 'Raw Encrypted Chunks'}
              </span> 
              {viewType === 'brontobox' && ' - Original filenames and decrypted downloads'}
            </div>
            <div>
              {files.length} {viewType === 'brontobox' ? 'files' : 'chunks'} in {account.email}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileManager;
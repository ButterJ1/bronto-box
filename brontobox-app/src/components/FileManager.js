// src/components/FileManager.js
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, Filter, SortAsc, SortDesc, Grid, List, 
  Folder, File, Calendar, HardDrive, Eye, Trash2,
  Download, RefreshCw, Settings, ArrowLeft
} from 'lucide-react';
import { APIService } from '../services/APIService';
import { useNotification } from './NotificationContext';

const FileTypeIcon = ({ fileName, fileType }) => {
  if (fileType === 'Encrypted Chunk') {
    return <File className="w-5 h-5 text-blue-500" />;
  } else if (fileType === 'Metadata') {
    return <Settings className="w-5 h-5 text-purple-500" />;
  } else {
    return <File className="w-5 h-5 text-gray-500" />;
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
            <FileTypeIcon fileName={file.name} fileType={file.file_type} />
            <div>
              <p className="font-medium text-gray-800 truncate max-w-xs" title={file.name}>
                {file.name}
              </p>
              <p className="text-xs text-gray-500">{file.file_type}</p>
            </div>
          </div>
        </td>
        <td className="px-4 py-3 text-sm text-gray-600">
          {file.size_formatted}
        </td>
        <td className="px-4 py-3 text-sm text-gray-600">
          {formatDate(file.created_time)}
        </td>
        <td className="px-4 py-3 text-sm text-gray-600">
          {file.drive_account.substring(0, 8)}...
        </td>
        <td className="px-4 py-3">
          <div className="flex space-x-2">
            <button
              onClick={() => onDownload(file)}
              className="p-1 rounded-lg hover:bg-blue-100 text-blue-600"
              title="Download Raw Chunk"
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
              title="Delete Chunk"
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
          <FileTypeIcon fileName={file.name} fileType={file.file_type} />
          <div>
            <h3 className="font-medium text-gray-800 truncate max-w-40" title={file.name}>
              {file.name}
            </h3>
            <p className="text-xs text-gray-500">{file.file_type}</p>
          </div>
        </div>
        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
          {file.size_formatted}
        </span>
      </div>

      <div className="text-xs text-gray-600 mb-3">
        <p>📅 {formatDate(file.created_time)}</p>
        <p>💾 Account: {file.drive_account.substring(0, 12)}...</p>
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
            placeholder="Search chunks by name, metadata..."
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
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');
  const [viewMode, setViewMode] = useState('grid');
  const [folderStats, setFolderStats] = useState(null);
  const [searchActive, setSearchActive] = useState(false);

  const { showNotification } = useNotification();

  useEffect(() => {
    loadFiles();
    loadFolderStats();
  }, [account]);

  const loadFiles = async () => {
    try {
      setLoading(true);
      // Call API to list chunks for this account
      const response = await fetch(`http://127.0.0.1:8000/drive/chunks/${account.account_id}?sort_by=${sortBy}&order=${sortOrder}`);
      
      if (response.ok) {
        const data = await response.json();
        setFiles(data.chunks || []);
      } else {
        throw new Error('Failed to load files');
      }
    } catch (error) {
      console.error('Error loading files:', error);
      showNotification('Failed to load Google Drive files', 'error');
      // Mock data for demonstration
      setFiles([
        {
          file_id: '1',
          name: 'brontobox_abc123_chunk_001_xyz.enc',
          size: 1048576,
          size_formatted: '1.0 MB',
          created_time: new Date().toISOString(),
          drive_account: account.account_id,
          file_type: 'Encrypted Chunk',
          metadata: { chunk_index: 0, brontobox_file_id: 'abc123' }
        },
        {
          file_id: '2',
          name: 'brontobox_def456_chunk_002_uvw.enc',
          size: 524288,
          size_formatted: '512 KB',
          created_time: new Date(Date.now() - 3600000).toISOString(),
          drive_account: account.account_id,
          file_type: 'Encrypted Chunk',
          metadata: { chunk_index: 1, brontobox_file_id: 'def456' }
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const loadFolderStats = async () => {
    try {
      // Call API to get folder statistics
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
          'Encrypted Chunk': files.length - 1,
          'Metadata': 1
        }
      });
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchTerm.trim()) {
      setSearchActive(false);
      loadFiles();
      return;
    }

    try {
      setIsSearching(true);
      setSearchActive(true);
      
      // Call search API
      const response = await fetch(`http://127.0.0.1:8000/drive/search/${account.account_id}?query=${encodeURIComponent(searchTerm)}`);
      
      if (response.ok) {
        const data = await response.json();
        setFiles(data.chunks || []);
        showNotification(`Found ${data.chunks?.length || 0} matching files`, 'info');
      } else {
        throw new Error('Search failed');
      }
    } catch (error) {
      console.error('Search error:', error);
      showNotification('Search failed', 'error');
      // Filter locally as fallback
      const filtered = files.filter(file => 
        file.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        JSON.stringify(file.metadata).toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFiles(filtered);
    } finally {
      setIsSearching(false);
    }
  };

  const clearSearch = () => {
    setSearchTerm('');
    setSearchActive(false);
    loadFiles();
  };

  const handleSort = (newSortBy) => {
    if (sortBy === newSortBy) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(newSortBy);
      setSortOrder('desc');
    }
    // Reload files with new sort
    setTimeout(loadFiles, 100);
  };

  const handleDownload = async (file) => {
    try {
      showNotification(`Downloading ${file.name}...`, 'info');
      
      // Download the raw chunk file
      const response = await fetch(`http://127.0.0.1:8000/drive/download/${account.account_id}/${file.file_id}`, {
        method: 'GET'
      });
      
      if (response.ok) {
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
        throw new Error('Download failed');
      }
    } catch (error) {
      console.error('Download error:', error);
      showNotification(`Download failed: ${error.message}`, 'error');
    }
  };

  const handleDelete = async (file) => {
    const confirmed = window.confirm(`Are you sure you want to delete "${file.name}"?\n\nThis will permanently remove this encrypted chunk from Google Drive.`);
    
    if (confirmed) {
      try {
        showNotification(`Deleting ${file.name}...`, 'info');
        
        const response = await fetch(`http://127.0.0.1:8000/drive/delete/${account.account_id}/${file.file_id}`, {
          method: 'DELETE'
        });
        
        if (response.ok) {
          setFiles(files.filter(f => f.file_id !== file.file_id));
          showNotification(`Deleted ${file.name}`, 'success');
          loadFolderStats(); // Refresh stats
        } else {
          throw new Error('Delete failed');
        }
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
            <h3 className="text-lg font-semibold text-gray-800 mb-2">Loading Google Drive Files</h3>
            <p className="text-gray-600">Scanning .brontobox_storage folder...</p>
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
                Google Drive Files
              </h2>
              <p className="text-sm text-gray-600">{account.email}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
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
                  📁 {folderStats.total_files} files
                </span>
                <span className="text-gray-600">
                  💾 {folderStats.total_size_mb} MB total
                </span>
                <span className="text-gray-600">
                  🔒 {folderStats.file_types['Encrypted Chunk'] || 0} chunks
                </span>
              </div>
              {files.length >= 100 && (
                <span className="text-green-600 font-medium">
                  🔍 Search enabled (100+ files)
                </span>
              )}
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
              {['name', 'date', 'size', 'type'].map((option) => (
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
                  : 'Upload some files to see them here'
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
                    <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Created</th>
                    <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Account</th>
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
              <span className="font-medium">.brontobox_storage</span> folder in Google Drive
            </div>
            <div>
              {files.length >= 100 ? (
                <span className="text-green-600">🔍 Search available</span>
              ) : (
                <span>{100 - files.length} more files to enable search</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileManager;
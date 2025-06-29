// public/electron.js - FIXED FOR PRODUCTION DEPLOYMENT
const { app, BrowserWindow, Menu, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const isDev = require('electron-is-dev');
const { spawn } = require('child_process');
const fs = require('fs');

// Keep a global reference of the window object
let mainWindow;
let pythonProcess;

function findPythonExecutable() {
  if (isDev) {
    // Development mode: Use relative path to Python script
    return {
      command: 'python',
      args: [path.join(__dirname, '..', '..', 'brontobox_api.py')],
      cwd: path.join(__dirname, '..', '..')
    };
  } else {
    // Production mode: Multiple possible locations for packaged executable
    const possiblePaths = [
      // Method 1: extraResources
      path.join(process.resourcesPath, 'python', 'brontobox_api.exe'),
      path.join(process.resourcesPath, 'python', 'brontobox_api'),
      // Method 2: app.asar.unpacked
      path.join(__dirname, '..', 'python', 'brontobox_api.exe'),
      path.join(__dirname, '..', 'python', 'brontobox_api'),
      // Method 3: relative to executable
      path.join(path.dirname(process.execPath), 'python', 'brontobox_api.exe'),
      path.join(path.dirname(process.execPath), 'python', 'brontobox_api'),
    ];
    
    for (const execPath of possiblePaths) {
      console.log(`🔍 Checking for Python executable at: ${execPath}`);
      if (fs.existsSync(execPath)) {
        console.log(`✅ Found Python executable: ${execPath}`);
        return {
          command: execPath,
          args: [],
          cwd: path.dirname(execPath)
        };
      }
    }
    
    // Fallback: try system Python with the script
    const scriptPath = path.join(process.resourcesPath, 'python', 'brontobox_api.py');
    if (fs.existsSync(scriptPath)) {
      console.log(`📄 Using system Python with script: ${scriptPath}`);
      return {
        command: 'python',
        args: [scriptPath],
        cwd: path.dirname(scriptPath)
      };
    }
    
    throw new Error('Python backend executable not found in any expected location');
  }
}

function startPythonBackend() {
  console.log('🚀 Starting Python backend...');
  
  try {
    const pythonConfig = findPythonExecutable();
    console.log('🐍 Python config:', pythonConfig);
    
    pythonProcess = spawn(pythonConfig.command, pythonConfig.args, {
      cwd: pythonConfig.cwd,
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env, PYTHONUNBUFFERED: '1' }
    });
    
    console.log(`🐍 Python process started with PID: ${pythonProcess.pid}`);
    
    // Log Python output
    if (pythonProcess.stdout) {
      pythonProcess.stdout.on('data', (data) => {
        const output = data.toString().trim();
        if (output) {
          console.log(`🐍 Python stdout: ${output}`);
        }
      });
    }
    
    if (pythonProcess.stderr) {
      pythonProcess.stderr.on('data', (data) => {
        const errorMsg = data.toString().trim();
        if (errorMsg && !errorMsg.includes('WARNING') && !errorMsg.includes('INFO')) {
          console.error(`🐍 Python stderr: ${errorMsg}`);
        }
      });
    }
    
    pythonProcess.on('close', (code) => {
      console.log(`🐍 Python process exited with code ${code}`);
      pythonProcess = null;
      
      if (code !== 0 && mainWindow && !isDev) {
        dialog.showErrorBox(
          'Backend Stopped', 
          `BrontoBox backend stopped unexpectedly (exit code ${code}). The application may not function correctly.`
        );
      }
    });
    
    pythonProcess.on('error', (error) => {
      console.error('🐍 Python process error:', error);
      
      // Show error dialog to user
      if (mainWindow) {
        const errorDetails = isDev 
          ? `Development Error: ${error.message}\n\nMake sure Python is installed and brontobox_api.py is in the correct location.`
          : `Production Error: ${error.message}\n\nThe BrontoBox backend could not be started. Please check if the application was installed correctly.`;
          
        dialog.showErrorBox('Backend Error', errorDetails);
      }
    });
    
    console.log('✅ Python backend started successfully');
    
  } catch (error) {
    console.error('❌ Failed to start Python backend:', error);
    
    if (mainWindow) {
      dialog.showErrorBox(
        'Startup Error', 
        `Failed to start BrontoBox backend:\n\n${error.message}\n\nPlease check the installation.`
      );
    }
  }
}

function stopPythonBackend() {
  if (pythonProcess && !pythonProcess.killed) {
    console.log('🛑 Stopping Python backend...');
    
    try {
      // Try graceful shutdown first
      pythonProcess.kill('SIGTERM');
      
      // Force kill after 5 seconds if still running
      setTimeout(() => {
        if (pythonProcess && !pythonProcess.killed) {
          console.log('🛑 Force stopping Python backend...');
          pythonProcess.kill('SIGKILL');
        }
      }, 5000);
    } catch (error) {
      console.error('Error stopping Python process:', error);
    }
  }
}

async function waitForBackend(maxAttempts = 15) {
  console.log('⏳ Waiting for Python backend to be ready...');
  
  for (let i = 0; i < maxAttempts; i++) {
    try {
      // Try to connect to the backend
      const { net } = require('electron');
      const request = net.request('http://127.0.0.1:8000/health');
      
      await new Promise((resolve, reject) => {
        request.on('response', (response) => {
          if (response.statusCode === 200) {
            console.log('✅ Backend is ready!');
            resolve();
          } else {
            reject(new Error(`Backend returned status ${response.statusCode}`));
          }
        });
        
        request.on('error', reject);
        request.end();
        
        // Timeout after 2 seconds
        setTimeout(() => reject(new Error('Timeout')), 2000);
      });
      
      return true; // Backend is ready
      
    } catch (error) {
      console.log(`⏳ Backend not ready yet (attempt ${i + 1}/${maxAttempts}), retrying...`);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  
  console.warn('⚠️ Backend did not become ready within timeout period');
  return false;
}

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'favicon256.ico'),
    titleBarStyle: 'default',
    show: false, // Don't show until ready
    backgroundColor: '#f8fafc'
  });

  // Start Python backend first
  startPythonBackend();

  // Load the app
  const startUrl = isDev 
    ? 'http://localhost:3000' 
    : `file://${path.join(__dirname, '../build/index.html')}`;
  
  if (isDev) {
    // Development: Wait for both React dev server and Python backend
    console.log('🔧 Development: Waiting for services to start...');
    setTimeout(async () => {
      await waitForBackend();
      mainWindow.loadURL(startUrl);
    }, 2000);
  } else {
    // Production: Wait for Python backend to start, then load built React app
    console.log('📦 Production: Starting backend and loading app...');
    setTimeout(async () => {
      const backendReady = await waitForBackend();
      if (backendReady || isDev) {
        mainWindow.loadURL(startUrl);
      } else {
        // Load app anyway but show warning
        mainWindow.loadURL(startUrl);
        setTimeout(() => {
          if (mainWindow) {
            dialog.showMessageBox(mainWindow, {
              type: 'warning',
              title: 'Backend Warning',
              message: 'BrontoBox backend is not responding',
              detail: 'The application interface will load, but some features may not work until the backend starts.',
              buttons: ['OK']
            });
          }
        }, 3000);
      }
    }, 2000);
  }

  // Show window when ready to prevent visual flash
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    // Open DevTools in development
    if (isDev) {
      mainWindow.webContents.openDevTools();
    }
    
    console.log('✅ BrontoBox window ready');
  });

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

// App event handlers
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  stopPythonBackend();
  
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on('before-quit', () => {
  stopPythonBackend();
});

// Security: Prevent new window creation
app.on('web-contents-created', (event, contents) => {
  contents.on('new-window', (event, navigationUrl) => {
    event.preventDefault();
    shell.openExternal(navigationUrl);
  });
});

// IPC handlers for file operations
ipcMain.handle('select-files', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile', 'multiSelections'],
    filters: [
      { name: 'All Files', extensions: ['*'] },
      { name: 'Documents', extensions: ['pdf', 'doc', 'docx', 'txt'] },
      { name: 'Images', extensions: ['jpg', 'jpeg', 'png', 'gif', 'bmp'] },
      { name: 'Videos', extensions: ['mp4', 'avi', 'mov', 'mkv'] },
      { name: 'Archives', extensions: ['zip', 'rar', '7z', 'tar'] }
    ]
  });
  
  return result.filePaths;
});

ipcMain.handle('select-download-location', async (event, fileName) => {
  const result = await dialog.showSaveDialog(mainWindow, {
    defaultPath: fileName,
    filters: [
      { name: 'All Files', extensions: ['*'] }
    ]
  });
  
  return result.filePath;
});

ipcMain.handle('show-message-box', async (event, options) => {
  const result = await dialog.showMessageBox(mainWindow, options);
  return result;
});

ipcMain.handle('check-backend-status', async () => {
  return {
    running: pythonProcess && !pythonProcess.killed,
    pid: pythonProcess?.pid || null,
    isDev: isDev
  };
});

// Menu setup (keeping your existing menu)
function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Add Files...',
          accelerator: 'CmdOrCtrl+O',
          click: () => {
            mainWindow.webContents.send('menu-add-files');
          }
        },
        { type: 'separator' },
        {
          label: 'New Vault',
          accelerator: 'CmdOrCtrl+N',
          click: () => {
            mainWindow.webContents.send('menu-new-vault');
          }
        },
        {
          label: 'Lock Vault',
          accelerator: 'CmdOrCtrl+L',
          click: () => {
            mainWindow.webContents.send('menu-lock-vault');
          }
        },
        { type: 'separator' },
        {
          label: 'Exit',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'Accounts',
      submenu: [
        {
          label: 'Add Google Account',
          click: () => {
            mainWindow.webContents.send('menu-add-account');
          }
        },
        {
          label: 'Manage Accounts',
          click: () => {
            mainWindow.webContents.send('menu-manage-accounts');
          }
        }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About BrontoBox',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About BrontoBox',
              message: 'BrontoBox v1.0.0',
              detail: '🦕 Secure Distributed Storage\n\nBrontoBox provides zero-knowledge encrypted storage using multiple Google Drive accounts for maximum security and capacity.',
              buttons: ['OK']
            });
          }
        },
        {
          label: 'Learn More',
          click: () => {
            shell.openExternal('https://github.com/brontobox/brontobox');
          }
        },
        { type: 'separator' },
        {
          label: 'Backend Status',
          click: () => {
            const status = pythonProcess && !pythonProcess.killed ? 'Running' : 'Stopped';
            const pid = pythonProcess?.pid || 'N/A';
            
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'Backend Status',
              message: `Python Backend: ${status}`,
              detail: `Process ID: ${pid}\nMode: ${isDev ? 'Development' : 'Production'}`,
              buttons: ['OK']
            });
          }
        }
      ]
    }
  ];

  if (process.platform === 'darwin') {
    template.unshift({
      label: app.getName(),
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        { role: 'services' },
        { type: 'separator' },
        { role: 'hide' },
        { role: 'hideothers' },
        { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit' }
      ]
    });
  }

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

app.whenReady().then(() => {
  createMenu();
});

// Handle app updates and notifications
ipcMain.handle('app-version', () => {
  return app.getVersion();
});

ipcMain.handle('show-item-in-folder', (event, fullPath) => {
  shell.showItemInFolder(fullPath);
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

console.log('🦕 BrontoBox Electron main process loaded');
console.log('🔧 Development mode:', isDev);
console.log('📁 App path:', app.getAppPath());
if (!isDev) {
  console.log('📁 Resources path:', process.resourcesPath);
}
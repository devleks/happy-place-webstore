/**
 * Electron Main Process
 * Handles window management, IPC communication, and system integration
 */

const { app, BrowserWindow, ipcMain, screen } = require('electron');
const path = require('path');
const isDev = require('./is-dev');
const { initDatabase, closeDatabase } = require('./database');
const { startBackgroundSync, stopBackgroundSync } = require('./sync');
const { initHardware, cleanupHardware } = require('./hardware');

let mainWindow;
let isQuitting = false;

/**
 * Create the main application window
 */
function createWindow() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;

  mainWindow = new BrowserWindow({
    width: Math.min(1280, width),
    height: Math.min(800, height),
    minWidth: 1024,
    minHeight: 768,
    fullscreen: false, // Set to true for kiosk mode
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      enableRemoteModule: false,
      sandbox: true
    },
    icon: path.join(__dirname, '../assets/icon.png')
  });

  // Load the app
  const startUrl = isDev
    ? 'http://localhost:3003'
    : `file://${path.join(__dirname, '../build/index.html')}`;

  mainWindow.loadURL(startUrl);

  // Open DevTools in development
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  // Handle window close
  mainWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault();
      mainWindow.hide();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Send window ready event
  mainWindow.webContents.on('did-finish-load', () => {
    mainWindow.webContents.send('app-ready');
  });
}

/**
 * Initialize the application
 */
async function initializeApp() {
  try {
    console.log('🚀 Initializing Happy Place POS...');

    // Initialize database
    await initDatabase();
    console.log('✅ Database initialized');

    // Initialize hardware
    await initHardware(mainWindow);
    console.log('✅ Hardware initialized');

    // Start background sync
    startBackgroundSync(mainWindow);
    console.log('✅ Background sync started');

    console.log('🎉 Happy Place POS ready!');
  } catch (error) {
    console.error('❌ Initialization failed:', error);
    app.quit();
  }
}

/**
 * Cleanup before quit
 */
async function cleanup() {
  console.log('🧹 Cleaning up...');
  
  try {
    stopBackgroundSync();
    await cleanupHardware();
    await closeDatabase();
    console.log('✅ Cleanup complete');
  } catch (error) {
    console.error('❌ Cleanup error:', error);
  }
}

// ============================================================================
// APP LIFECYCLE EVENTS
// ============================================================================

app.whenReady().then(async () => {
  await initializeApp();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    } else if (mainWindow) {
      mainWindow.show();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    isQuitting = true;
    app.quit();
  }
});

app.on('before-quit', async (event) => {
  if (!isQuitting) {
    event.preventDefault();
    isQuitting = true;
    await cleanup();
    app.quit();
  }
});

// ============================================================================
// IPC HANDLERS
// ============================================================================

// Get app version
ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});

// Get app path
ipcMain.handle('get-app-path', (event, name) => {
  return app.getPath(name);
});

// Toggle fullscreen (kiosk mode)
ipcMain.handle('toggle-fullscreen', () => {
  if (mainWindow) {
    const isFullScreen = mainWindow.isFullScreen();
    mainWindow.setFullScreen(!isFullScreen);
    return !isFullScreen;
  }
  return false;
});

// Minimize window
ipcMain.handle('minimize-window', () => {
  if (mainWindow) {
    mainWindow.minimize();
  }
});

// Maximize window
ipcMain.handle('maximize-window', () => {
  if (mainWindow) {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow.maximize();
    }
  }
});

// Close window
ipcMain.handle('close-window', () => {
  if (mainWindow) {
    mainWindow.close();
  }
});

// Restart app
ipcMain.handle('restart-app', () => {
  app.relaunch();
  app.exit();
});

// Check online status
ipcMain.handle('check-online', () => {
  return require('dns').promises.resolve('google.com')
    .then(() => true)
    .catch(() => false);
});

// ============================================================================
// ERROR HANDLING
// ============================================================================

process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
  if (mainWindow) {
    mainWindow.webContents.send('app-error', {
      message: error.message,
      stack: error.stack
    });
  }
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

// ============================================================================
// DEVELOPMENT HELPERS
// ============================================================================

if (isDev) {
  // Install React DevTools
  app.whenReady().then(() => {
    const { default: installExtension, REACT_DEVELOPER_TOOLS } = require('electron-devtools-installer');
    installExtension(REACT_DEVELOPER_TOOLS)
      .then((name) => console.log(`✅ Added Extension: ${name}`))
      .catch((err) => console.log('❌ Extension error:', err));
  });
}

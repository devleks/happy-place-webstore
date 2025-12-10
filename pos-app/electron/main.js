/**
 * Electron Main Process
 * Handles window management, IPC communication, and system integration
 * 
 * Production Features (Per ELECTRON_WINDSURF_RULES.md):
 * - Comprehensive logging with electron-log
 * - Crash reporting and error tracking
 * - Auto-updates with electron-updater
 * - Health monitoring
 */

const { app, BrowserWindow, ipcMain, screen } = require('electron');
const path = require('path');
const isDev = require('./is-dev');

// Production services
const { initLogger, logger, setupErrorHandlers, rotateLogs } = require('./logger');
const { initCrashReporter, setupCrashHandlers, startHealthMonitoring } = require('./crash-reporter');
const { initUpdater } = require('./updater');
const { initSecurity } = require('./security');
const { initMemoryManager, cleanupAllListeners, cleanupWindowListeners } = require('./memory-manager');

// Core services
const { initDatabase, closeDatabase } = require('./database');
const { startBackgroundSync, stopBackgroundSync } = require('./sync');
const { initHardware, cleanupHardware } = require('./hardware');

let mainWindow;
let isQuitting = false;

// ============================================================================
// EARLY INITIALIZATION
// ============================================================================

// Initialize logger as early as possible (before app.whenReady)
app.on('will-finish-launching', () => {
  initLogger();
  setupErrorHandlers();
  logger.info('App will finish launching...');
});

// ============================================================================
// WINDOW MANAGEMENT
// ============================================================================

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

  // Initialize security features for this window
  initSecurity(mainWindow);

  // Handle window close
  mainWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault();
      mainWindow.hide();
    }
  });

  mainWindow.on('closed', () => {
    // Clean up window-specific listeners
    if (mainWindow) {
      cleanupWindowListeners(mainWindow.id);
    }
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
    logger.separator('INITIALIZING HAPPY PLACE POS');

    // Initialize production services first
    logger.info('Initializing production services...');
    
    // Rotate old logs
    rotateLogs();
    
    // Setup crash reporter
    initCrashReporter();
    setupCrashHandlers();
    
    // Start health monitoring (every 5 minutes)
    startHealthMonitoring(5);
    
    // Initialize memory manager
    initMemoryManager();

    // Initialize core services
    logger.info('Initializing core services...');

    // Initialize database
    await initDatabase();
    logger.success('Database initialized');

    // Initialize hardware
    await initHardware(mainWindow);
    logger.success('Hardware initialized');

    // Start background sync
    startBackgroundSync(mainWindow);
    logger.success('Background sync started');

    // Initialize auto-updater (only in production)
    if (!isDev) {
      initUpdater(mainWindow);
      logger.success('Auto-updater initialized');
    } else {
      logger.info('Auto-updater disabled in development mode');
    }

    logger.separator();
    logger.success('🎉 Happy Place POS ready!');
    
    // Log startup info
    logger.startup({
      'Version': app.getVersion(),
      'Environment': isDev ? 'Development' : 'Production',
      'Platform': `${process.platform} ${process.arch}`,
      'Electron': process.versions.electron,
      'Node': process.versions.node,
      'Chrome': process.versions.chrome
    });

  } catch (error) {
    logger.fatal('Initialization failed', error);
    app.quit();
  }
}

/**
 * Cleanup before quit
 */
async function cleanup() {
  logger.separator('CLEANUP');
  
  try {
    // Clean up all event listeners
    cleanupAllListeners();
    logger.success('Event listeners cleaned up');
    
    stopBackgroundSync();
    logger.success('Background sync stopped');
    
    await cleanupHardware();
    logger.success('Hardware cleaned up');
    
    await closeDatabase();
    logger.success('Database closed');
    
    logger.separator();
    logger.shutdown('Normal shutdown');
  } catch (error) {
    logger.error('Cleanup error', error);
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

// Update management
ipcMain.handle('check-for-updates', () => {
  const { forceCheckForUpdates } = require('./updater');
  forceCheckForUpdates();
});

// Memory management
ipcMain.handle('get-memory-usage', () => {
  const { getMemoryUsage } = require('./memory-manager');
  return getMemoryUsage();
});

ipcMain.handle('check-memory-leaks', () => {
  const { checkMemoryLeaks } = require('./memory-manager');
  return checkMemoryLeaks();
});

// ============================================================================
// ERROR HANDLING
// ============================================================================

// Note: Error handlers are now in logger.js and crash-reporter.js
// They are initialized in initializeApp()

// Additional app-level error handler
app.on('render-process-gone', (event, webContents, details) => {
  logger.error('Renderer process gone', {
    reason: details.reason,
    exitCode: details.exitCode
  });
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

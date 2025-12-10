/**
 * Auto-Update Service
 * Handles automatic application updates
 * Per ELECTRON_WINDSURF_RULES.md Section 4.1
 */

const { autoUpdater } = require('electron-updater');
const { dialog, app } = require('electron');
const { logger } = require('./logger');

let mainWindow = null;
let updateCheckInterval = null;

// ============================================================================
// CONFIGURATION
// ============================================================================

/**
 * Configure auto-updater
 */
function configureUpdater() {
  // Don't auto-download updates (ask user first)
  autoUpdater.autoDownload = false;
  
  // Auto-install on app quit
  autoUpdater.autoInstallOnAppQuit = true;
  
  // Check for updates on startup
  autoUpdater.autoRunAppAfterInstall = true;

  // Configure update channel (stable, beta, alpha)
  autoUpdater.channel = process.env.UPDATE_CHANNEL || 'stable';

  // Allow downgrade (for testing)
  autoUpdater.allowDowngrade = process.env.NODE_ENV === 'development';

  // Configure update server (GitHub releases by default)
  // autoUpdater.setFeedURL({
  //   provider: 'github',
  //   owner: 'your-username',
  //   repo: 'happy-place-pos'
  // });

  logger.info('Auto-updater configured', {
    channel: autoUpdater.channel,
    autoDownload: autoUpdater.autoDownload,
    currentVersion: app.getVersion()
  });
}

// ============================================================================
// UPDATE EVENTS
// ============================================================================

/**
 * Setup update event listeners
 */
function setupUpdateListeners(window) {
  mainWindow = window;

  // Checking for update
  autoUpdater.on('checking-for-update', () => {
    logger.info('Checking for updates...');
    sendStatusToWindow('Checking for updates...');
  });

  // Update available
  autoUpdater.on('update-available', (info) => {
    logger.info('Update available', {
      version: info.version,
      releaseDate: info.releaseDate,
      size: info.files[0]?.size
    });

    sendStatusToWindow('Update available');
    promptDownload(info);
  });

  // Update not available
  autoUpdater.on('update-not-available', (info) => {
    logger.info('Update not available', {
      currentVersion: app.getVersion(),
      latestVersion: info.version
    });

    sendStatusToWindow('App is up to date');
  });

  // Download progress
  autoUpdater.on('download-progress', (progress) => {
    const percent = Math.round(progress.percent);
    logger.debug(`Download progress: ${percent}%`, {
      transferred: progress.transferred,
      total: progress.total,
      speed: progress.bytesPerSecond
    });

    sendStatusToWindow(`Downloading update: ${percent}%`, progress);
  });

  // Update downloaded
  autoUpdater.on('update-downloaded', (info) => {
    logger.success('Update downloaded', {
      version: info.version,
      releaseDate: info.releaseDate
    });

    sendStatusToWindow('Update ready to install');
    promptInstall(info);
  });

  // Error
  autoUpdater.on('error', (error) => {
    logger.error('Update error', error);
    sendStatusToWindow('Update error', { error: error.message });
    
    // Show error dialog
    if (mainWindow) {
      dialog.showMessageBox(mainWindow, {
        type: 'error',
        title: 'Update Error',
        message: 'Failed to check for updates',
        detail: error.message,
        buttons: ['OK']
      });
    }
  });

  logger.success('Update listeners configured');
}

// ============================================================================
// USER PROMPTS
// ============================================================================

/**
 * Prompt user to download update
 */
function promptDownload(info) {
  if (!mainWindow) return;

  const releaseNotes = info.releaseNotes || 'No release notes available';
  const size = info.files[0]?.size 
    ? `(${(info.files[0].size / 1024 / 1024).toFixed(2)} MB)` 
    : '';

  dialog.showMessageBox(mainWindow, {
    type: 'info',
    title: 'Update Available',
    message: `Version ${info.version} is available ${size}`,
    detail: `Current version: ${app.getVersion()}\n\nRelease notes:\n${releaseNotes}`,
    buttons: ['Download Now', 'Download Later', 'Skip This Version'],
    defaultId: 0,
    cancelId: 1
  }).then((result) => {
    if (result.response === 0) {
      // Download now
      logger.info('User chose to download update');
      autoUpdater.downloadUpdate();
      
      // Show download progress notification
      if (mainWindow) {
        mainWindow.webContents.send('update-downloading');
      }
    } else if (result.response === 1) {
      // Download later
      logger.info('User postponed update');
    } else {
      // Skip this version
      logger.info('User skipped update', { version: info.version });
      // TODO: Store skipped version
    }
  });
}

/**
 * Prompt user to install update
 */
function promptInstall(info) {
  if (!mainWindow) return;

  dialog.showMessageBox(mainWindow, {
    type: 'info',
    title: 'Update Ready',
    message: `Version ${info.version} has been downloaded`,
    detail: 'The update will be installed when you restart the application.\n\nWould you like to restart now?',
    buttons: ['Restart Now', 'Restart Later'],
    defaultId: 0,
    cancelId: 1
  }).then((result) => {
    if (result.response === 0) {
      // Restart now
      logger.info('User chose to restart and install update');
      logger.shutdown('Update installation');
      
      // Quit and install
      setImmediate(() => {
        autoUpdater.quitAndInstall(false, true);
      });
    } else {
      // Restart later
      logger.info('User postponed restart');
      
      // Notify that update will install on next restart
      if (mainWindow) {
        mainWindow.webContents.send('update-ready-on-restart');
      }
    }
  });
}

// ============================================================================
// UPDATE CHECKS
// ============================================================================

/**
 * Check for updates manually
 */
function checkForUpdates() {
  logger.info('Manual update check initiated');
  
  autoUpdater.checkForUpdates().catch((error) => {
    logger.error('Failed to check for updates', error);
  });
}

/**
 * Start periodic update checks
 */
function startPeriodicChecks(intervalHours = 1) {
  // Check immediately on startup (after 10 seconds)
  setTimeout(() => {
    checkForUpdates();
  }, 10000);

  // Then check periodically
  const interval = intervalHours * 60 * 60 * 1000;
  updateCheckInterval = setInterval(() => {
    checkForUpdates();
  }, interval);

  logger.info(`Periodic update checks started (every ${intervalHours} hour(s))`);
}

/**
 * Stop periodic update checks
 */
function stopPeriodicChecks() {
  if (updateCheckInterval) {
    clearInterval(updateCheckInterval);
    updateCheckInterval = null;
    logger.info('Periodic update checks stopped');
  }
}

// ============================================================================
// COMMUNICATION
// ============================================================================

/**
 * Send update status to renderer
 */
function sendStatusToWindow(message, data = {}) {
  if (mainWindow) {
    mainWindow.webContents.send('update-status', {
      message,
      timestamp: new Date().toISOString(),
      ...data
    });
  }
}

// ============================================================================
// INITIALIZATION
// ============================================================================

/**
 * Initialize auto-updater
 */
function initUpdater(window) {
  try {
    mainWindow = window;

    // Configure updater
    configureUpdater();

    // Setup event listeners
    setupUpdateListeners(window);

    // Start periodic checks (only in production)
    if (process.env.NODE_ENV !== 'development') {
      startPeriodicChecks(1); // Check every hour
    } else {
      logger.info('Auto-updates disabled in development mode');
    }

    logger.success('Auto-updater initialized');
    return true;
  } catch (error) {
    logger.error('Failed to initialize auto-updater', error);
    return false;
  }
}

// ============================================================================
// MANUAL UPDATE
// ============================================================================

/**
 * Force check for updates (for manual button)
 */
function forceCheckForUpdates() {
  logger.info('Force update check requested');
  
  if (process.env.NODE_ENV === 'development') {
    logger.warn('Updates disabled in development mode');
    
    if (mainWindow) {
      dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: 'Development Mode',
        message: 'Auto-updates are disabled in development mode',
        buttons: ['OK']
      });
    }
    return;
  }

  checkForUpdates();
}

// ============================================================================
// EXPORTS
// ============================================================================

module.exports = {
  initUpdater,
  checkForUpdates,
  forceCheckForUpdates,
  startPeriodicChecks,
  stopPeriodicChecks,
  // Export autoUpdater for direct access if needed
  autoUpdater
};

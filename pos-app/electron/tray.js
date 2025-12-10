/**
 * System Tray Service
 * Background app support with system tray icon
 * Per ELECTRON_WINDSURF_RULES.md Section 5.1
 */

const { app, Tray, Menu, nativeImage } = require('electron');
const path = require('path');
const { logger } = require('./logger');

let tray = null;
let mainWindow = null;

// ============================================================================
// TRAY ICON
// ============================================================================

/**
 * Create tray icon
 */
function createTrayIcon() {
  try {
    // Create icon (use template image on macOS for dark mode support)
    const iconPath = path.join(__dirname, '../assets/tray-icon.png');
    const icon = nativeImage.createFromPath(iconPath);
    
    // Resize for tray (16x16 on macOS, 16x16 on Windows)
    const trayIcon = icon.resize({ width: 16, height: 16 });
    
    // Set as template on macOS for automatic dark mode
    if (process.platform === 'darwin') {
      trayIcon.setTemplateImage(true);
    }

    return trayIcon;
  } catch (error) {
    logger.warn('Failed to load tray icon, using default', error);
    // Return empty image as fallback
    return nativeImage.createEmpty();
  }
}

// ============================================================================
// TRAY MENU
// ============================================================================

/**
 * Create tray context menu
 */
function createTrayMenu() {
  return Menu.buildFromTemplate([
    {
      label: 'Happy Place POS',
      enabled: false
    },
    { type: 'separator' },
    {
      label: 'Show Window',
      click: () => {
        logger.user('Show window from tray');
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
        }
      }
    },
    {
      label: 'Hide Window',
      click: () => {
        logger.user('Hide window from tray');
        if (mainWindow) {
          mainWindow.hide();
        }
      }
    },
    { type: 'separator' },
    {
      label: 'New Transaction',
      click: () => {
        logger.user('New transaction from tray');
        if (mainWindow) {
          mainWindow.show();
          mainWindow.webContents.send('new-transaction');
        }
      }
    },
    {
      label: 'Sync Now',
      click: () => {
        logger.user('Sync from tray');
        if (mainWindow) {
          mainWindow.webContents.send('sync-now');
        }
      }
    },
    { type: 'separator' },
    {
      label: 'Online Status',
      enabled: false,
      id: 'tray-online-status'
    },
    {
      label: 'Sync Status',
      enabled: false,
      id: 'tray-sync-status'
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        logger.user('Quit from tray');
        app.quit();
      }
    }
  ]);
}

// ============================================================================
// TRAY UPDATES
// ============================================================================

/**
 * Update online status in tray menu
 */
function updateTrayOnlineStatus(isOnline) {
  if (!tray) return;

  const menu = tray.getContextMenu();
  if (!menu) return;

  const item = menu.getMenuItemById('tray-online-status');
  if (item) {
    item.label = isOnline ? '🟢 Online' : '🔴 Offline';
    logger.debug('Tray online status updated', { isOnline });
  }
}

/**
 * Update sync status in tray menu
 */
function updateTraySyncStatus(status) {
  if (!tray) return;

  const menu = tray.getContextMenu();
  if (!menu) return;

  const item = menu.getMenuItemById('tray-sync-status');
  if (item) {
    const statusText = {
      syncing: '🔄 Syncing...',
      synced: '✅ Synced',
      error: '❌ Sync Error',
      offline: '⏸️ Offline'
    }[status] || '⏸️ Unknown';

    item.label = statusText;
    logger.debug('Tray sync status updated', { status });
  }
}

/**
 * Update tray tooltip
 */
function updateTrayTooltip(text) {
  if (!tray) return;

  tray.setToolTip(text || 'Happy Place POS');
  logger.debug('Tray tooltip updated', { text });
}

/**
 * Show tray notification (balloon)
 */
function showTrayNotification(title, body, icon = 'info') {
  if (!tray) return;

  // Only supported on Windows and macOS
  if (process.platform === 'win32' || process.platform === 'darwin') {
    tray.displayBalloon({
      title,
      content: body,
      icon: icon === 'error' ? 'error' : 'info'
    });
    logger.debug('Tray notification shown', { title, body });
  }
}

// ============================================================================
// INITIALIZATION
// ============================================================================

/**
 * Initialize system tray
 */
function initTray(window) {
  try {
    mainWindow = window;

    logger.info('Initializing system tray');

    // Create tray
    const icon = createTrayIcon();
    tray = new Tray(icon);

    // Set tooltip
    tray.setToolTip('Happy Place POS');

    // Set context menu
    const contextMenu = createTrayMenu();
    tray.setContextMenu(contextMenu);

    // Handle tray click (Windows/Linux)
    tray.on('click', () => {
      logger.user('Tray icon clicked');
      if (mainWindow) {
        if (mainWindow.isVisible()) {
          mainWindow.hide();
        } else {
          mainWindow.show();
          mainWindow.focus();
        }
      }
    });

    // Handle double-click (macOS)
    tray.on('double-click', () => {
      logger.user('Tray icon double-clicked');
      if (mainWindow) {
        mainWindow.show();
        mainWindow.focus();
      }
    });

    // Handle right-click (show menu)
    tray.on('right-click', () => {
      logger.user('Tray icon right-clicked');
      tray.popUpContextMenu();
    });

    logger.success('System tray initialized');
    return true;
  } catch (error) {
    logger.error('Failed to initialize system tray', error);
    return false;
  }
}

/**
 * Destroy system tray
 */
function destroyTray() {
  if (tray) {
    tray.destroy();
    tray = null;
    logger.info('System tray destroyed');
  }
}

// ============================================================================
// EXPORTS
// ============================================================================

module.exports = {
  initTray,
  destroyTray,
  updateTrayOnlineStatus,
  updateTraySyncStatus,
  updateTrayTooltip,
  showTrayNotification
};

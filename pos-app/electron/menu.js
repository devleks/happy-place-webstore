/**
 * Application Menu Service
 * Native application menu for desktop UX
 * Per ELECTRON_WINDSURF_RULES.md Section 5.1
 */

const { app, Menu, shell, dialog } = require('electron');
const { logger } = require('./logger');
const { forceCheckForUpdates } = require('./updater');
const { getMemoryUsage, checkMemoryLeaks } = require('./memory-manager');
const isDev = require('./is-dev');

let mainWindow = null;

// ============================================================================
// MENU TEMPLATE
// ============================================================================

/**
 * Create application menu template
 */
function createMenuTemplate() {
  const isMac = process.platform === 'darwin';

  const template = [
    // App Menu (macOS only)
    ...(isMac ? [{
      label: app.name,
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        {
          label: 'Preferences',
          accelerator: 'Cmd+,',
          click: () => {
            logger.user('Opened preferences');
            if (mainWindow) {
              mainWindow.webContents.send('open-preferences');
            }
          }
        },
        { type: 'separator' },
        { role: 'services' },
        { type: 'separator' },
        { role: 'hide' },
        { role: 'hideOthers' },
        { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit' }
      ]
    }] : []),

    // File Menu
    {
      label: 'File',
      submenu: [
        {
          label: 'New Transaction',
          accelerator: isMac ? 'Cmd+N' : 'Ctrl+N',
          click: () => {
            logger.user('New transaction');
            if (mainWindow) {
              mainWindow.webContents.send('new-transaction');
            }
          }
        },
        {
          label: 'Hold Transaction',
          accelerator: isMac ? 'Cmd+H' : 'Ctrl+H',
          click: () => {
            logger.user('Hold transaction');
            if (mainWindow) {
              mainWindow.webContents.send('hold-transaction');
            }
          }
        },
        {
          label: 'Recall Transaction',
          accelerator: isMac ? 'Cmd+R' : 'Ctrl+R',
          click: () => {
            logger.user('Recall transaction');
            if (mainWindow) {
              mainWindow.webContents.send('recall-transaction');
            }
          }
        },
        { type: 'separator' },
        {
          label: 'Print Receipt',
          accelerator: isMac ? 'Cmd+P' : 'Ctrl+P',
          click: () => {
            logger.user('Print receipt');
            if (mainWindow) {
              mainWindow.webContents.send('print-receipt');
            }
          }
        },
        { type: 'separator' },
        isMac ? { role: 'close' } : { role: 'quit' }
      ]
    },

    // Edit Menu
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        ...(isMac ? [
          { role: 'pasteAndMatchStyle' },
          { role: 'delete' },
          { role: 'selectAll' },
          { type: 'separator' },
          {
            label: 'Speech',
            submenu: [
              { role: 'startSpeaking' },
              { role: 'stopSpeaking' }
            ]
          }
        ] : [
          { role: 'delete' },
          { type: 'separator' },
          { role: 'selectAll' }
        ])
      ]
    },

    // View Menu
    {
      label: 'View',
      submenu: [
        {
          label: 'Dashboard',
          accelerator: isMac ? 'Cmd+1' : 'Ctrl+1',
          click: () => {
            logger.user('Navigate to dashboard');
            if (mainWindow) {
              mainWindow.webContents.send('navigate', '/');
            }
          }
        },
        {
          label: 'Products',
          accelerator: isMac ? 'Cmd+2' : 'Ctrl+2',
          click: () => {
            logger.user('Navigate to products');
            if (mainWindow) {
              mainWindow.webContents.send('navigate', '/products');
            }
          }
        },
        {
          label: 'Transactions',
          accelerator: isMac ? 'Cmd+3' : 'Ctrl+3',
          click: () => {
            logger.user('Navigate to transactions');
            if (mainWindow) {
              mainWindow.webContents.send('navigate', '/transactions');
            }
          }
        },
        { type: 'separator' },
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

    // Sync Menu
    {
      label: 'Sync',
      submenu: [
        {
          label: 'Sync Now',
          accelerator: isMac ? 'Cmd+Shift+S' : 'Ctrl+Shift+S',
          click: async () => {
            logger.user('Manual sync triggered');
            if (mainWindow) {
              mainWindow.webContents.send('sync-now');
            }
          }
        },
        {
          label: 'Sync Status',
          click: () => {
            logger.user('View sync status');
            if (mainWindow) {
              mainWindow.webContents.send('show-sync-status');
            }
          }
        },
        { type: 'separator' },
        {
          label: 'Online Status',
          enabled: false,
          id: 'online-status'
        }
      ]
    },

    // Window Menu
    {
      label: 'Window',
      submenu: [
        { role: 'minimize' },
        { role: 'zoom' },
        ...(isMac ? [
          { type: 'separator' },
          { role: 'front' },
          { type: 'separator' },
          { role: 'window' }
        ] : [
          { role: 'close' }
        ])
      ]
    },

    // Help Menu
    {
      role: 'help',
      submenu: [
        {
          label: 'Documentation',
          click: async () => {
            logger.user('Opened documentation');
            await shell.openExternal('https://github.com/happyplace/pos-docs');
          }
        },
        {
          label: 'Keyboard Shortcuts',
          accelerator: isMac ? 'Cmd+/' : 'Ctrl+/',
          click: () => {
            logger.user('View keyboard shortcuts');
            showKeyboardShortcuts();
          }
        },
        { type: 'separator' },
        {
          label: 'Check for Updates',
          click: () => {
            logger.user('Manual update check');
            forceCheckForUpdates();
          }
        },
        { type: 'separator' },
        {
          label: 'View Logs',
          click: () => {
            logger.user('View logs');
            const logPath = require('electron-log').transports.file.getFile().path;
            shell.showItemInFolder(logPath);
          }
        },
        {
          label: 'Memory Usage',
          click: () => {
            logger.user('View memory usage');
            showMemoryUsage();
          }
        },
        { type: 'separator' },
        {
          label: 'About',
          click: () => {
            logger.user('View about dialog');
            showAboutDialog();
          }
        }
      ]
    }
  ];

  // Add developer menu in development
  if (isDev) {
    template.push({
      label: 'Developer',
      submenu: [
        {
          label: 'Reload',
          accelerator: isMac ? 'Cmd+R' : 'Ctrl+R',
          click: () => {
            if (mainWindow) {
              mainWindow.reload();
            }
          }
        },
        {
          label: 'Toggle DevTools',
          accelerator: isMac ? 'Cmd+Alt+I' : 'Ctrl+Shift+I',
          click: () => {
            if (mainWindow) {
              mainWindow.webContents.toggleDevTools();
            }
          }
        },
        { type: 'separator' },
        {
          label: 'Clear Database',
          click: () => {
            logger.warn('Clear database requested (dev)');
            if (mainWindow) {
              mainWindow.webContents.send('clear-database');
            }
          }
        },
        {
          label: 'Clear Sync Queue',
          click: () => {
            logger.warn('Clear sync queue requested (dev)');
            if (mainWindow) {
              mainWindow.webContents.send('clear-sync-queue');
            }
          }
        },
        { type: 'separator' },
        {
          label: 'Test Crash Reporter',
          click: () => {
            logger.warn('Test crash triggered (dev)');
            throw new Error('Test crash from menu');
          }
        }
      ]
    });
  }

  return template;
}

// ============================================================================
// DIALOGS
// ============================================================================

/**
 * Show keyboard shortcuts dialog
 */
function showKeyboardShortcuts() {
  const isMac = process.platform === 'darwin';
  const mod = isMac ? 'Cmd' : 'Ctrl';

  const shortcuts = [
    '# File Operations',
    `${mod}+N - New Transaction`,
    `${mod}+H - Hold Transaction`,
    `${mod}+R - Recall Transaction`,
    `${mod}+P - Print Receipt`,
    '',
    '# Navigation',
    `${mod}+1 - Dashboard`,
    `${mod}+2 - Products`,
    `${mod}+3 - Transactions`,
    '',
    '# Sync',
    `${mod}+Shift+S - Sync Now`,
    '',
    '# View',
    `${mod}+0 - Reset Zoom`,
    `${mod}++ - Zoom In`,
    `${mod}+- - Zoom Out`,
    `${mod}+Shift+F - Toggle Fullscreen`,
    '',
    '# Help',
    `${mod}+/ - Keyboard Shortcuts`,
    '',
    '# Developer (Dev Mode)',
    `${mod}+Alt+I - Toggle DevTools`
  ].join('\n');

  dialog.showMessageBox(mainWindow, {
    type: 'info',
    title: 'Keyboard Shortcuts',
    message: 'Happy Place POS - Keyboard Shortcuts',
    detail: shortcuts,
    buttons: ['OK']
  });
}

/**
 * Show memory usage dialog
 */
function showMemoryUsage() {
  const usage = getMemoryUsage();
  const leakCheck = checkMemoryLeaks();

  const details = [
    '# Memory Usage',
    `Heap Used: ${usage.heapUsed} MB`,
    `Heap Total: ${usage.heapTotal} MB`,
    `External: ${usage.external} MB`,
    `RSS: ${usage.rss} MB`,
    '',
    '# Status',
    leakCheck.hasLeaks ? '⚠️ Potential memory leaks detected' : '✅ No memory leaks detected',
    '',
    leakCheck.warnings.length > 0 ? '# Warnings' : '',
    ...leakCheck.warnings.map(w => `- ${w.message}`)
  ].filter(Boolean).join('\n');

  dialog.showMessageBox(mainWindow, {
    type: leakCheck.hasLeaks ? 'warning' : 'info',
    title: 'Memory Usage',
    message: 'Application Memory Statistics',
    detail: details,
    buttons: ['OK']
  });
}

/**
 * Show about dialog
 */
function showAboutDialog() {
  const details = [
    `Version: ${app.getVersion()}`,
    `Electron: ${process.versions.electron}`,
    `Chrome: ${process.versions.chrome}`,
    `Node: ${process.versions.node}`,
    `Platform: ${process.platform} ${process.arch}`,
    '',
    'Happy Place Boutique',
    'Point of Sale System',
    '',
    'Copyright © 2025 Happy Place Boutique'
  ].join('\n');

  dialog.showMessageBox(mainWindow, {
    type: 'info',
    title: 'About Happy Place POS',
    message: 'Happy Place POS',
    detail: details,
    buttons: ['OK']
  });
}

// ============================================================================
// MENU UPDATES
// ============================================================================

/**
 * Update online status in menu
 */
function updateOnlineStatus(isOnline) {
  const menu = Menu.getApplicationMenu();
  if (!menu) return;

  const onlineItem = menu.getMenuItemById('online-status');
  if (onlineItem) {
    onlineItem.label = isOnline ? '🟢 Online' : '🔴 Offline';
    logger.debug('Menu online status updated', { isOnline });
  }
}

// ============================================================================
// INITIALIZATION
// ============================================================================

/**
 * Initialize application menu
 */
function initMenu(window) {
  try {
    mainWindow = window;

    logger.info('Initializing application menu');

    const template = createMenuTemplate();
    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);

    logger.success('Application menu initialized');
    return true;
  } catch (error) {
    logger.error('Failed to initialize menu', error);
    return false;
  }
}

// ============================================================================
// EXPORTS
// ============================================================================

module.exports = {
  initMenu,
  updateOnlineStatus,
  showKeyboardShortcuts,
  showMemoryUsage,
  showAboutDialog
};

/**
 * Keyboard Shortcuts Service
 * Global keyboard shortcuts for desktop UX
 * Per ELECTRON_WINDSURF_RULES.md Section 5.1
 */

const { globalShortcut } = require('electron');
const { logger } = require('./logger');

let mainWindow = null;
const registeredShortcuts = new Map();

// ============================================================================
// SHORTCUT DEFINITIONS
// ============================================================================

/**
 * Get platform-specific modifier key
 */
function getModifier() {
  return process.platform === 'darwin' ? 'Command' : 'Control';
}

/**
 * Define global shortcuts
 */
function getShortcutDefinitions() {
  const mod = getModifier();

  return [
    // Quick Actions
    {
      accelerator: `${mod}+Shift+N`,
      description: 'Quick New Transaction',
      action: () => {
        logger.user('Quick new transaction (global shortcut)');
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
          mainWindow.webContents.send('new-transaction');
        }
      }
    },
    {
      accelerator: `${mod}+Shift+H`,
      description: 'Quick Hold Transaction',
      action: () => {
        logger.user('Quick hold transaction (global shortcut)');
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
          mainWindow.webContents.send('hold-transaction');
        }
      }
    },
    {
      accelerator: `${mod}+Shift+R`,
      description: 'Quick Recall Transaction',
      action: () => {
        logger.user('Quick recall transaction (global shortcut)');
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
          mainWindow.webContents.send('recall-transaction');
        }
      }
    },

    // Window Management
    {
      accelerator: `${mod}+Shift+W`,
      description: 'Show/Hide Window',
      action: () => {
        logger.user('Toggle window visibility (global shortcut)');
        if (mainWindow) {
          if (mainWindow.isVisible()) {
            mainWindow.hide();
          } else {
            mainWindow.show();
            mainWindow.focus();
          }
        }
      }
    },

    // Search
    {
      accelerator: `${mod}+Shift+F`,
      description: 'Quick Search',
      action: () => {
        logger.user('Quick search (global shortcut)');
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
          mainWindow.webContents.send('focus-search');
        }
      }
    }
  ];
}

// ============================================================================
// SHORTCUT REGISTRATION
// ============================================================================

/**
 * Register a single shortcut
 */
function registerShortcut(accelerator, action, description) {
  try {
    const success = globalShortcut.register(accelerator, action);
    
    if (success) {
      registeredShortcuts.set(accelerator, { action, description });
      logger.debug('Shortcut registered', { accelerator, description });
      return true;
    } else {
      logger.warn('Failed to register shortcut', { accelerator, description });
      return false;
    }
  } catch (error) {
    logger.error('Error registering shortcut', error, { accelerator });
    return false;
  }
}

/**
 * Unregister a single shortcut
 */
function unregisterShortcut(accelerator) {
  try {
    globalShortcut.unregister(accelerator);
    registeredShortcuts.delete(accelerator);
    logger.debug('Shortcut unregistered', { accelerator });
    return true;
  } catch (error) {
    logger.error('Error unregistering shortcut', error, { accelerator });
    return false;
  }
}

/**
 * Check if shortcut is registered
 */
function isShortcutRegistered(accelerator) {
  return globalShortcut.isRegistered(accelerator);
}

// ============================================================================
// BULK OPERATIONS
// ============================================================================

/**
 * Register all shortcuts
 */
function registerAllShortcuts() {
  try {
    logger.info('Registering global shortcuts');

    const shortcuts = getShortcutDefinitions();
    let successCount = 0;
    let failCount = 0;

    for (const shortcut of shortcuts) {
      const success = registerShortcut(
        shortcut.accelerator,
        shortcut.action,
        shortcut.description
      );

      if (success) {
        successCount++;
      } else {
        failCount++;
      }
    }

    logger.success(`Registered ${successCount} shortcuts (${failCount} failed)`);
    return successCount;
  } catch (error) {
    logger.error('Failed to register shortcuts', error);
    return 0;
  }
}

/**
 * Unregister all shortcuts
 */
function unregisterAllShortcuts() {
  try {
    logger.info('Unregistering all shortcuts');
    
    globalShortcut.unregisterAll();
    registeredShortcuts.clear();
    
    logger.success('All shortcuts unregistered');
    return true;
  } catch (error) {
    logger.error('Failed to unregister shortcuts', error);
    return false;
  }
}

/**
 * Get list of registered shortcuts
 */
function getRegisteredShortcuts() {
  return Array.from(registeredShortcuts.entries()).map(([accelerator, data]) => ({
    accelerator,
    description: data.description
  }));
}

// ============================================================================
// LOCAL SHORTCUTS (IN-WINDOW)
// ============================================================================

/**
 * Setup local shortcuts (handled by renderer)
 */
function setupLocalShortcuts(window) {
  try {
    logger.info('Setting up local shortcuts');

    const mod = getModifier();

    // Send shortcut definitions to renderer
    const localShortcuts = [
      // Navigation
      { key: `${mod}+1`, action: 'navigate-dashboard', description: 'Go to Dashboard' },
      { key: `${mod}+2`, action: 'navigate-products', description: 'Go to Products' },
      { key: `${mod}+3`, action: 'navigate-transactions', description: 'Go to Transactions' },
      
      // Actions
      { key: `${mod}+N`, action: 'new-transaction', description: 'New Transaction' },
      { key: `${mod}+H`, action: 'hold-transaction', description: 'Hold Transaction' },
      { key: `${mod}+R`, action: 'recall-transaction', description: 'Recall Transaction' },
      { key: `${mod}+P`, action: 'print-receipt', description: 'Print Receipt' },
      
      // Search
      { key: `${mod}+F`, action: 'focus-search', description: 'Focus Search' },
      { key: `${mod}+K`, action: 'quick-search', description: 'Quick Search' },
      
      // Barcode
      { key: `${mod}+B`, action: 'focus-barcode', description: 'Focus Barcode Input' },
      
      // Sync
      { key: `${mod}+Shift+S`, action: 'sync-now', description: 'Sync Now' },
      
      // Help
      { key: `${mod}+/`, action: 'show-shortcuts', description: 'Show Shortcuts' },
      
      // Zoom
      { key: `${mod}+0`, action: 'reset-zoom', description: 'Reset Zoom' },
      { key: `${mod}++`, action: 'zoom-in', description: 'Zoom In' },
      { key: `${mod}+-`, action: 'zoom-out', description: 'Zoom Out' }
    ];

    window.webContents.send('setup-shortcuts', localShortcuts);
    
    logger.success('Local shortcuts configured');
    return true;
  } catch (error) {
    logger.error('Failed to setup local shortcuts', error);
    return false;
  }
}

// ============================================================================
// INITIALIZATION
// ============================================================================

/**
 * Initialize keyboard shortcuts
 */
function initShortcuts(window) {
  try {
    mainWindow = window;

    logger.info('Initializing keyboard shortcuts');

    // Register global shortcuts
    const count = registerAllShortcuts();

    // Setup local shortcuts
    setupLocalShortcuts(window);

    logger.success(`Keyboard shortcuts initialized (${count} global)`);
    return true;
  } catch (error) {
    logger.error('Failed to initialize shortcuts', error);
    return false;
  }
}

/**
 * Cleanup shortcuts
 */
function cleanupShortcuts() {
  unregisterAllShortcuts();
}

// ============================================================================
// EXPORTS
// ============================================================================

module.exports = {
  initShortcuts,
  cleanupShortcuts,
  registerShortcut,
  unregisterShortcut,
  registerAllShortcuts,
  unregisterAllShortcuts,
  isShortcutRegistered,
  getRegisteredShortcuts,
  setupLocalShortcuts
};

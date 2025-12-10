/**
 * Electron Preload Script
 * Exposes secure APIs to the renderer process via contextBridge
 */

const { contextBridge, ipcRenderer } = require('electron');

// ============================================================================
// EXPOSED APIs
// ============================================================================

contextBridge.exposeInMainWorld('electron', {
  // App info
  app: {
    getVersion: () => ipcRenderer.invoke('get-app-version'),
    getPlatform: () => ipcRenderer.invoke('get-platform'),
    getPath: (name) => ipcRenderer.invoke('get-path', name),
    
    // Update management
    checkForUpdates: () => ipcRenderer.invoke('check-for-updates'),
    onUpdateStatus: (callback) => {
      const subscription = (event, data) => callback(data);
      ipcRenderer.on('update-status', subscription);
      return () => ipcRenderer.removeListener('update-status', subscription);
    },
    onUpdateDownloading: (callback) => {
      const subscription = () => callback();
      ipcRenderer.on('update-downloading', subscription);
      return () => ipcRenderer.removeListener('update-downloading', subscription);
    },
    onUpdateReadyOnRestart: (callback) => {
      const subscription = () => callback();
      ipcRenderer.on('update-ready-on-restart', subscription);
      return () => ipcRenderer.removeListener('update-ready-on-restart', subscription);
    }
  },

  // Window controls
  toggleFullscreen: () => ipcRenderer.invoke('toggle-fullscreen'),
  minimizeWindow: () => ipcRenderer.invoke('minimize-window'),
  maximizeWindow: () => ipcRenderer.invoke('maximize-window'),
  closeWindow: () => ipcRenderer.invoke('close-window'),
  restartApp: () => ipcRenderer.invoke('restart-app'),

  // Network
  checkOnline: () => ipcRenderer.invoke('check-online'),
  
  // Memory management
  getMemoryUsage: () => ipcRenderer.invoke('get-memory-usage'),
  checkMemoryLeaks: () => ipcRenderer.invoke('check-memory-leaks'),

  // Authentication
  auth: {
    login: (email, password) => ipcRenderer.invoke('auth-login', email, password),
    validateSession: (sessionToken) => ipcRenderer.invoke('auth-validate-session', sessionToken),
    logout: (sessionToken) => ipcRenderer.invoke('auth-logout', sessionToken),
    getSessionStats: () => ipcRenderer.invoke('auth-get-session-stats'),
    setSyncToken: (token) => ipcRenderer.invoke('auth-set-sync-token', token),
    syncEmployees: () => ipcRenderer.invoke('auth-sync-employees')
  },

  // Database operations
  db: {
    getProducts: () => ipcRenderer.invoke('db-get-products'),
    searchProducts: (query) => ipcRenderer.invoke('db-search-products', query),
    getProductBySku: (sku) => ipcRenderer.invoke('db-get-product-by-sku', sku),
    updateProductStock: (productId, quantity) => ipcRenderer.invoke('db-update-product-stock', productId, quantity),
    
    createTransaction: (transaction) => ipcRenderer.invoke('db-create-transaction', transaction),
    getTransactions: (filters) => ipcRenderer.invoke('db-get-transactions', filters),
    getTransaction: (id) => ipcRenderer.invoke('db-get-transaction', id),
    
    holdTransaction: (transaction) => ipcRenderer.invoke('db-hold-transaction', transaction),
    getHeldTransactions: () => ipcRenderer.invoke('db-get-held-transactions'),
    recallTransaction: (id) => ipcRenderer.invoke('db-recall-transaction', id),
    deleteHeldTransaction: (id) => ipcRenderer.invoke('db-delete-held-transaction', id),
    
    getSyncQueue: () => ipcRenderer.invoke('db-get-sync-queue'),
    clearSyncQueue: (ids) => ipcRenderer.invoke('db-clear-sync-queue', ids)
  },

  // Sync operations
  sync: {
    syncNow: () => ipcRenderer.invoke('sync-now'),
    getSyncStatus: () => ipcRenderer.invoke('sync-get-status'),
    onSyncStatusChange: (callback) => {
      ipcRenderer.on('sync-status-changed', (event, status) => callback(status));
    }
  },

  // Hardware operations
  hardware: {
    scanBarcode: () => ipcRenderer.invoke('hardware-scan-barcode'),
    printReceipt: (receipt) => ipcRenderer.invoke('hardware-print-receipt', receipt),
    openCashDrawer: () => ipcRenderer.invoke('hardware-open-cash-drawer'),
    onBarcodeScanned: (callback) => {
      ipcRenderer.on('barcode-scanned', (event, barcode) => callback(barcode));
    },
    removeBarcodeListener: () => {
      ipcRenderer.removeAllListeners('barcode-scanned');
    }
  },

  // Event listeners
  on: (channel, callback) => {
    const validChannels = [
      'app-ready',
      'app-error',
      'sync-status-changed',
      'barcode-scanned',
      'online-status-changed'
    ];
    
    if (validChannels.includes(channel)) {
      ipcRenderer.on(channel, (event, ...args) => callback(...args));
    }
  },

  off: (channel, callback) => {
    ipcRenderer.removeListener(channel, callback);
  },

  // Send events
  send: (channel, data) => {
    const validChannels = ['log-message'];
    if (validChannels.includes(channel)) {
      ipcRenderer.send(channel, data);
    }
  }
});

// ============================================================================
// CONSOLE LOGGING
// ============================================================================

// Forward console logs to main process for debugging
const originalConsole = {
  log: console.log,
  error: console.error,
  warn: console.warn,
  info: console.info
};

console.log = (...args) => {
  originalConsole.log(...args);
  ipcRenderer.send('log-message', { level: 'log', message: args });
};

console.error = (...args) => {
  originalConsole.error(...args);
  ipcRenderer.send('log-message', { level: 'error', message: args });
};

console.warn = (...args) => {
  originalConsole.warn(...args);
  ipcRenderer.send('log-message', { level: 'warn', message: args });
};

console.info = (...args) => {
  originalConsole.info(...args);
  ipcRenderer.send('log-message', { level: 'info', message: args });
};

// ============================================================================
// INITIALIZATION
// ============================================================================

window.addEventListener('DOMContentLoaded', () => {
  console.log('🚀 Preload script loaded');
  console.log('📦 Electron APIs exposed to renderer');
});

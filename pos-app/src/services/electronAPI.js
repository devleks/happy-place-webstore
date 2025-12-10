/**
 * Electron API Service
 * Replaces REST API calls with Electron IPC
 */

// Check if running in Electron
const isElectron = () => {
  return window.electron !== undefined;
};

// Throw error if not in Electron
const ensureElectron = () => {
  if (!isElectron()) {
    throw new Error('This app must run in Electron');
  }
};

// ============================================================================
// PRODUCT OPERATIONS
// ============================================================================

export const productAPI = {
  /**
   * Get all products
   */
  async getAll() {
    ensureElectron();
    return await window.electron.db.getProducts();
  },

  /**
   * Search products
   */
  async search(query) {
    ensureElectron();
    return await window.electron.db.searchProducts(query);
  },

  /**
   * Get product by SKU
   */
  async getBySku(sku) {
    ensureElectron();
    return await window.electron.db.getProductBySku(sku);
  },

  /**
   * Update product stock
   */
  async updateStock(productId, quantity) {
    ensureElectron();
    return await window.electron.db.updateProductStock(productId, quantity);
  }
};

// ============================================================================
// TRANSACTION OPERATIONS
// ============================================================================

export const transactionAPI = {
  /**
   * Create new transaction
   */
  async create(transaction) {
    ensureElectron();
    return await window.electron.db.createTransaction(transaction);
  },

  /**
   * Get transactions with filters
   */
  async getAll(filters = {}) {
    ensureElectron();
    return await window.electron.db.getTransactions(filters);
  },

  /**
   * Get single transaction
   */
  async getById(id) {
    ensureElectron();
    return await window.electron.db.getTransaction(id);
  }
};

// ============================================================================
// HELD TRANSACTION OPERATIONS
// ============================================================================

export const heldTransactionAPI = {
  /**
   * Hold a transaction
   */
  async hold(transaction) {
    ensureElectron();
    return await window.electron.db.holdTransaction(transaction);
  },

  /**
   * Get all held transactions
   */
  async getAll() {
    ensureElectron();
    return await window.electron.db.getHeldTransactions();
  },

  /**
   * Recall a held transaction
   */
  async recall(id) {
    ensureElectron();
    return await window.electron.db.recallTransaction(id);
  },

  /**
   * Delete a held transaction
   */
  async delete(id) {
    ensureElectron();
    return await window.electron.db.deleteHeldTransaction(id);
  }
};

// ============================================================================
// SYNC OPERATIONS
// ============================================================================

export const syncAPI = {
  /**
   * Trigger manual sync
   */
  async syncNow() {
    ensureElectron();
    return await window.electron.sync.syncNow();
  },

  /**
   * Get sync status
   */
  async getStatus() {
    ensureElectron();
    return await window.electron.sync.getStatus();
  },

  /**
   * Listen for sync status changes
   */
  onStatusChange(callback) {
    ensureElectron();
    // This would be implemented with IPC listeners
    // For now, return a no-op cleanup function
    return () => {};
  }
};

// ============================================================================
// HARDWARE OPERATIONS
// ============================================================================

export const hardwareAPI = {
  /**
   * Scan barcode
   */
  async scanBarcode() {
    ensureElectron();
    return await window.electron.hardware.scanBarcode();
  },

  /**
   * Print receipt
   */
  async printReceipt(receiptData) {
    ensureElectron();
    return await window.electron.hardware.printReceipt(receiptData);
  },

  /**
   * Open cash drawer
   */
  async openCashDrawer() {
    ensureElectron();
    return await window.electron.hardware.openCashDrawer();
  },

  /**
   * Listen for barcode scans
   */
  onBarcodeScan(callback) {
    ensureElectron();
    return window.electron.hardware.onBarcodeScan(callback);
  }
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

export const utilityAPI = {
  /**
   * Check online status
   */
  async checkOnline() {
    ensureElectron();
    return await window.electron.checkOnline();
  },

  /**
   * Get app version
   */
  async getVersion() {
    ensureElectron();
    return await window.electron.app.getVersion();
  },

  /**
   * Get memory usage
   */
  async getMemoryUsage() {
    ensureElectron();
    return await window.electron.getMemoryUsage();
  },

  /**
   * Check for updates
   */
  async checkForUpdates() {
    ensureElectron();
    return await window.electron.app.checkForUpdates();
  }
};

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Generate transaction number
 */
export const generateTransactionNumber = () => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const seconds = String(now.getSeconds()).padStart(2, '0');
  const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
  
  return `TXN-${year}${month}${day}-${hours}${minutes}${seconds}-${random}`;
};

/**
 * Generate hold number
 */
export const generateHoldNumber = () => {
  const now = new Date();
  const timestamp = now.getTime();
  const random = Math.floor(Math.random() * 100).toString().padStart(2, '0');
  
  return `HOLD-${timestamp}-${random}`;
};

/**
 * Calculate transaction total
 */
export const calculateTotal = (items, tax = 0, discount = 0) => {
  const subtotal = items.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0);
  const total = subtotal + tax - discount;
  
  return {
    subtotal: Number(subtotal.toFixed(2)),
    tax: Number(tax.toFixed(2)),
    discount: Number(discount.toFixed(2)),
    total: Number(total.toFixed(2))
  };
};

// Export all APIs as default
export default {
  product: productAPI,
  transaction: transactionAPI,
  heldTransaction: heldTransactionAPI,
  sync: syncAPI,
  hardware: hardwareAPI,
  utility: utilityAPI,
  generateTransactionNumber,
  generateHoldNumber,
  calculateTotal,
  isElectron
};

/**
 * Background Sync Service
 * Syncs data between local SQLite and backend API
 */

const axios = require('axios');
const { ipcMain } = require('electron');
const {
  upsertProduct,
  getSyncQueue,
  clearSyncQueue,
  updateSyncQueueError
} = require('./database');

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';
const SYNC_INTERVAL = 30000; // 30 seconds

let syncInterval = null;
let mainWindow = null;
let syncStatus = {
  isOnline: false,
  lastSync: null,
  pendingItems: 0,
  isSyncing: false,
  lastError: null
};

/**
 * Start background sync
 */
function startBackgroundSync(window) {
  mainWindow = window;

  console.log('🔄 Starting background sync...');

  // Initial sync
  syncNow();

  // Periodic sync
  syncInterval = setInterval(() => {
    syncNow();
  }, SYNC_INTERVAL);

  // Setup IPC handlers
  setupIpcHandlers();
}

/**
 * Stop background sync
 */
function stopBackgroundSync() {
  if (syncInterval) {
    clearInterval(syncInterval);
    syncInterval = null;
    console.log('⏹️  Background sync stopped');
  }
}

/**
 * Perform sync now
 */
async function syncNow() {
  if (syncStatus.isSyncing) {
    console.log('⏳ Sync already in progress, skipping...');
    return;
  }

  try {
    syncStatus.isSyncing = true;
    updateSyncStatus();

    // Check if online
    const isOnline = await checkOnlineStatus();
    syncStatus.isOnline = isOnline;

    if (!isOnline) {
      console.log('📴 Offline - skipping sync');
      syncStatus.isSyncing = false;
      updateSyncStatus();
      return;
    }

    console.log('🔄 Syncing...');

    // Sync products from backend
    await syncProducts();

    // Sync transactions to backend
    await syncTransactions();

    syncStatus.lastSync = new Date().toISOString();
    syncStatus.lastError = null;
    console.log('✅ Sync completed successfully');

  } catch (error) {
    console.error('❌ Sync failed:', error);
    syncStatus.lastError = error.message;
  } finally {
    syncStatus.isSyncing = false;
    updateSyncStatus();
  }
}

/**
 * Check if online
 */
async function checkOnlineStatus() {
  try {
    await axios.get(`${API_URL}/health`, { timeout: 5000 });
    return true;
  } catch (error) {
    return false;
  }
}

/**
 * Sync products from backend to local database
 */
async function syncProducts() {
  try {
    console.log('📦 Syncing products...');

    const response = await axios.get(`${API_URL}/products`, {
      timeout: 10000
    });

    const products = response.data;

    if (!Array.isArray(products)) {
      throw new Error('Invalid products response');
    }

    // Upsert products in batch
    let syncedCount = 0;
    for (const product of products) {
      try {
        upsertProduct({
          id: product.id,
          sku: product.sku,
          name: product.name || product.product_name,
          description: product.description,
          category_id: product.category_id,
          category_name: product.category,
          price: parseFloat(product.price),
          stock_quantity: parseInt(product.stock_quantity) || 0,
          low_stock_threshold: parseInt(product.low_stock_threshold) || 5,
          image_url: product.image_url,
          size: product.size,
          color: product.color
        });
        syncedCount++;
      } catch (error) {
        console.error(`Failed to sync product ${product.id}:`, error);
      }
    }

    console.log(`✅ Synced ${syncedCount}/${products.length} products`);
    return syncedCount;

  } catch (error) {
    console.error('❌ Product sync failed:', error);
    throw error;
  }
}

/**
 * Sync transactions from local database to backend
 */
async function syncTransactions() {
  try {
    console.log('💳 Syncing transactions...');

    const queue = getSyncQueue();
    syncStatus.pendingItems = queue.length;

    if (queue.length === 0) {
      console.log('✅ No pending transactions to sync');
      return 0;
    }

    console.log(`📤 Syncing ${queue.length} pending transactions...`);

    const syncedIds = [];
    let syncedCount = 0;

    for (const item of queue) {
      try {
        const data = JSON.parse(item.data);

        // Send to backend
        const response = await axios.post(
          `${API_URL}/pos/transactions`,
          data,
          {
            timeout: 10000,
            headers: {
              'Content-Type': 'application/json'
            }
          }
        );

        if (response.status === 200 || response.status === 201) {
          syncedIds.push(item.id);
          syncedCount++;
          console.log(`✅ Synced transaction: ${data.transaction_number}`);
        }

      } catch (error) {
        console.error(`❌ Failed to sync item ${item.id}:`, error.message);
        
        // Update error in sync queue
        updateSyncQueueError(item.id, error.message);

        // Don't fail entire sync if one item fails
        continue;
      }
    }

    // Clear successfully synced items
    if (syncedIds.length > 0) {
      clearSyncQueue(syncedIds);
      console.log(`✅ Cleared ${syncedIds.length} synced items from queue`);
    }

    syncStatus.pendingItems = queue.length - syncedIds.length;
    return syncedCount;

  } catch (error) {
    console.error('❌ Transaction sync failed:', error);
    throw error;
  }
}

/**
 * Update sync status and notify renderer
 */
function updateSyncStatus() {
  if (mainWindow) {
    mainWindow.webContents.send('sync-status-changed', syncStatus);
  }
}

/**
 * Get current sync status
 */
function getSyncStatus() {
  return syncStatus;
}

/**
 * Setup IPC handlers
 */
function setupIpcHandlers() {
  ipcMain.handle('sync-now', async () => {
    await syncNow();
    return syncStatus;
  });

  ipcMain.handle('sync-get-status', () => {
    return syncStatus;
  });
}

// ============================================================================
// EXPORTS
// ============================================================================

module.exports = {
  startBackgroundSync,
  stopBackgroundSync,
  syncNow,
  getSyncStatus,
  checkOnlineStatus
};

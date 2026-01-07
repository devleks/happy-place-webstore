/**
 * Sync Operations for IndexedDB
 * Handles synchronization between local IndexedDB and backend API
 */

import { sync_queue, metadata } from './schema';
import { shifts, transactions } from './schema';
import { getUnsyncedShifts, markShiftAsSynced, setShiftBackendId } from './shifts';
import { getUnsyncedTransactions, markTransactionAsSynced } from './transactions';

async function getCurrentBackendShiftId(apiBaseUrl, authToken) {
  const res = await fetch(`${apiBaseUrl}/api/pos/shifts/current`, {
    headers: { 'Authorization': `Bearer ${authToken}` }
  });
  if (!res.ok) return null;
  const data = await res.json();
  return data?.shift?.shift_id ?? null;
}

async function isBackendShiftEnabled(apiBaseUrl, authToken) {
  try {
    const res = await fetch(`${apiBaseUrl}/api/pos/shifts/current`, {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });

    // If the backend is unreachable or errors, assume enabled and let normal logic handle retries.
    if (!res.ok) return true;

    const data = await res.json();
    const message = (data?.message || data?.error || '').toLowerCase();
    if (message.includes('not enabled') || message.includes('apply migration')) {
      return false;
    }
    return true;
  } catch (e) {
    return true;
  }
}

/**
 * Add item to sync queue
 * @param {Object} item - { entity_type, entity_id, operation, data }
 * @returns {Promise<number>} Queue item ID
 */
export async function addToSyncQueue(item) {
  try {
    const queueItem = {
      entity_type: item.entity_type, // 'shift', 'transaction', 'product'
      entity_id: item.entity_id,
      operation: item.operation, // 'create', 'update', 'delete'
      data: JSON.stringify(item.data),
      synced: false,
      retry_count: 0,
      last_error: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    const id = await sync_queue.add(queueItem);
    console.log(`✅ Added to sync queue: ${item.entity_type} ${item.entity_id}`);
    return id;
  } catch (error) {
    console.error('❌ Error adding to sync queue:', error);
    throw error;
  }
}

/**
 * Get pending sync items
 * @param {number} limit - Max items to return
 * @returns {Promise<Array>} Pending sync items
 */
export async function getPendingSyncItems(limit = 50) {
  try {
    const items = await sync_queue
      .toCollection()
      .filter((item) => (item.synced === false || item.synced === 0 || !item.synced) && item.retry_count < 5)
      .toArray();
    return items.slice(0, limit);
  } catch (error) {
    console.error('❌ Error getting pending sync items:', error);
    return [];
  }
}

/**
 * Mark sync item as completed
 * @param {number} queueId - Sync queue item ID
 */
export async function markSyncItemCompleted(queueId) {
  try {
    await sync_queue.update(queueId, {
      synced: true,
      updated_at: new Date().toISOString()
    });
    console.log(`✅ Sync item ${queueId} completed`);
  } catch (error) {
    console.error('❌ Error marking sync item completed:', error);
  }
}

/**
 * Mark sync item as failed
 * @param {number} queueId - Sync queue item ID
 * @param {string} error - Error message
 */
export async function markSyncItemFailed(queueId, error) {
  try {
    const item = await sync_queue.get(queueId);
    if (item) {
      await sync_queue.update(queueId, {
        retry_count: item.retry_count + 1,
        last_error: error,
        updated_at: new Date().toISOString()
      });
      console.log(`❌ Sync item ${queueId} failed (retry ${item.retry_count + 1}/5): ${error}`);
    }
  } catch (error) {
    console.error('❌ Error marking sync item failed:', error);
  }
}

/**
 * Clear completed sync items
 * @returns {Promise<number>} Number of items deleted
 */
export async function clearCompletedSyncItems() {
  try {
    const completed = await sync_queue
      .toCollection()
      .filter((item) => item.synced === true || item.synced === 1)
      .toArray();

    const ids = completed.map((i) => i.id);
    const count = ids.length;
    if (count > 0) {
      await sync_queue.bulkDelete(ids);
    }

    console.log(`✅ Cleared ${count} completed sync items`);
    return count;
  } catch (error) {
    console.error('❌ Error clearing completed sync items:', error);
    return 0;
  }
}

/**
 * Get sync queue stats
 * @returns {Promise<Object>} Sync queue statistics
 */
export async function getSyncQueueStats() {
  try {
    const all = await sync_queue.toArray();
    const total = all.length;
    const pending = all.filter((i) => (i.synced === false || i.synced === 0 || !i.synced)).length;
    const failed = all.filter((i) => (i.synced === false || i.synced === 0 || !i.synced) && i.retry_count >= 5).length;
    const completed = all.filter((i) => i.synced === true || i.synced === 1).length;

    return {
      total,
      pending,
      failed,
      completed
    };
  } catch (error) {
    console.error('❌ Error getting sync queue stats:', error);
    return { total: 0, pending: 0, failed: 0, completed: 0 };
  }
}

/**
 * Sync all unsynced data with backend
 * @param {string} apiBaseUrl - Backend API base URL
 * @param {string} authToken - JWT token for authentication
 * @returns {Promise<Object>} Sync results
 */
export async function syncWithBackend(apiBaseUrl, authToken) {
  try {
    const results = {
      shifts: { success: 0, failed: 0 },
      transactions: { success: 0, failed: 0 },
      errors: []
    };

    const backendShiftsEnabled = await isBackendShiftEnabled(apiBaseUrl, authToken);

    // Sync shifts (best-effort). If backend doesn't support shifts yet, we'll keep local-only.
    const unsyncedShifts = await getUnsyncedShifts();
    for (const shift of unsyncedShifts) {
      try {
        // If already mapped, nothing to do.
        if (shift.backend_shift_id) {
          await markShiftAsSynced(shift.id);
          results.shifts.success++;
          continue;
        }

        // If backend doesn't support shifts, don't block overall sync.
        if (!backendShiftsEnabled) {
          results.shifts.failed++;
          results.errors.push(`Shift ${shift.id}: backend shifts not enabled`);
          continue;
        }

        // Try to start a backend shift.
        const startRes = await fetch(`${apiBaseUrl}/api/pos/shifts/start`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          body: JSON.stringify({
            store_location_id: 1,
            opening_float: shift.starting_cash || 0
          })
        });

        if (!startRes.ok) {
          // If shift already exists, fetch current.
          const currentId = await getCurrentBackendShiftId(apiBaseUrl, authToken);
          if (currentId) {
            await setShiftBackendId(shift.id, currentId);
            await markShiftAsSynced(shift.id);
            results.shifts.success++;
            continue;
          }

          // Transient error: keep shift unsynced so we can retry later.
          results.shifts.failed++;
          results.errors.push(`Shift ${shift.id}: backend shift sync failed (${startRes.status})`);
          continue;
        }

        const startData = await startRes.json();
        const backendShiftId = startData?.shift?.shift_id;
        if (backendShiftId) {
          await setShiftBackendId(shift.id, backendShiftId);
        }
        await markShiftAsSynced(shift.id);
        results.shifts.success++;
      } catch (e) {
        // Keep shift unsynced so we can retry later
        results.shifts.failed++;
        results.errors.push(`Shift ${shift.id}: ${e.message}`);
      }
    }

    // Sync transactions
    const unsyncedTransactions = await getUnsyncedTransactions();
    for (const transaction of unsyncedTransactions) {
      try {
        // If a backend shift mapping exists, pass it through.
        let backendShiftId;
        if (transaction.shift_id) {
          const localShift = await shifts.get(transaction.shift_id);
          backendShiftId = localShift?.backend_shift_id;
        }

        // If backend shifts are enabled, don't attempt transaction sync without a mapped backend shift id.
        if (backendShiftsEnabled && transaction.shift_id && !backendShiftId) {
          results.transactions.failed++;
          results.errors.push(`Transaction ${transaction.id}: missing backend_shift_id mapping for shift ${transaction.shift_id}`);
          continue;
        }

        const response = await fetch(`${apiBaseUrl}/api/pos/transactions`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          body: JSON.stringify({
            store_location_id: 1,
            shift_id: backendShiftId,
            payment_method: transaction.payment_method,
            cash_tendered: transaction.payment_method === 'cash' ? (transaction.amount_paid || transaction.total || 0) : undefined,
            items: (transaction.items || []).map((item) => ({
              variant_id: item.variant_id,
              quantity: item.quantity
            }))
          })
        });

        if (response.ok) {
          try {
            const data = await response.json();
            const backendTransactionId = data?.transaction_id;
            if (backendTransactionId) {
              await transactions.update(transaction.id, {
                backend_transaction_id: backendTransactionId,
                updated_at: new Date().toISOString()
              });
            }
          } catch (e) {
            // ignore parse errors
          }
          await markTransactionAsSynced(transaction.id);
          results.transactions.success++;
        } else {
          results.transactions.failed++;
          results.errors.push(`Transaction ${transaction.id}: ${response.statusText}`);
        }
      } catch (error) {
        results.transactions.failed++;
        results.errors.push(`Transaction ${transaction.id}: ${error.message}`);
      }
    }

    // Update last sync timestamp
    await setMetadata('last_sync', new Date().toISOString());

    console.log('✅ Sync completed:', results);
    return results;
  } catch (error) {
    console.error('❌ Error syncing with backend:', error);
    throw error;
  }
}

/**
 * Check if online
 * @returns {boolean} Online status
 */
export function isOnline() {
  return navigator.onLine;
}

/**
 * Set metadata value
 * @param {string} key - Metadata key
 * @param {any} value - Metadata value
 */
export async function setMetadata(key, value) {
  try {
    await metadata.put({
      key,
      value: JSON.stringify(value),
      updated_at: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error setting metadata:', error);
  }
}

/**
 * Get metadata value
 * @param {string} key - Metadata key
 * @returns {Promise<any>} Metadata value or null
 */
export async function getMetadata(key) {
  try {
    const item = await metadata.get(key);
    return item ? JSON.parse(item.value) : null;
  } catch (error) {
    console.error('❌ Error getting metadata:', error);
    return null;
  }
}

/**
 * Get last sync timestamp
 * @returns {Promise<string|null>} Last sync ISO timestamp or null
 */
export async function getLastSyncTime() {
  return await getMetadata('last_sync');
}

/**
 * Setup automatic background sync
 * Registers service worker sync event
 */
export async function setupBackgroundSync() {
  try {
    if ('serviceWorker' in navigator && 'sync' in navigator.serviceWorker) {
      const registration = await navigator.serviceWorker.ready;
      await registration.sync.register('sync-pos-data');
      console.log('✅ Background sync registered');
      return true;
    } else {
      console.warn('⚠️ Background sync not supported');
      return false;
    }
  } catch (error) {
    console.error('❌ Error setting up background sync:', error);
    return false;
  }
}

/**
 * Force sync now (manual trigger)
 * @param {string} apiBaseUrl - Backend API base URL
 * @param {string} authToken - JWT token
 * @returns {Promise<Object>} Sync results
 */
export async function forceSyncNow(apiBaseUrl, authToken) {
  if (!isOnline()) {
    throw new Error('Cannot sync: Device is offline');
  }

  return await syncWithBackend(apiBaseUrl, authToken);
}

/**
 * Get sync status summary
 * @returns {Promise<Object>} Sync status
 */
export async function getSyncStatus() {
  try {
    const lastSync = await getLastSyncTime();
    const queueStats = await getSyncQueueStats();
    const unsyncedShiftCount = (await getUnsyncedShifts()).length;
    const unsyncedTransactionCount = (await getUnsyncedTransactions()).length;

    return {
      isOnline: isOnline(),
      lastSync,
      queueStats,
      unsyncedShiftCount,
      unsyncedTransactionCount,
      needsSync: unsyncedShiftCount > 0 || unsyncedTransactionCount > 0
    };
  } catch (error) {
    console.error('❌ Error getting sync status:', error);
    return null;
  }
}

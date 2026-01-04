/**
 * Held Transaction Operations for IndexedDB
 * Ported from electron/database.js held transaction functions
 * Used for "Park Sale" functionality in POS
 */

import { held_transactions, held_transaction_items } from './schema';

/**
 * Hold/Park a transaction
 * @param {Object} transactionData - Transaction data with items
 * @returns {Promise<Object>} Created held transaction
 */
export async function holdTransaction(transactionData) {
  try {
    const heldTransaction = {
      employee_id: transactionData.employee_id,
      employee_name: transactionData.employee_name,
      customer_name: transactionData.customer_name || null,
      customer_phone: transactionData.customer_phone || null,
      subtotal: transactionData.subtotal || 0,
      tax: transactionData.tax || 0,
      discount: transactionData.discount || 0,
      total: transactionData.total || 0,
      notes: transactionData.notes || null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    // Insert held transaction
    const heldId = await held_transactions.add(heldTransaction);

    // Insert held transaction items
    if (transactionData.items && transactionData.items.length > 0) {
      const itemsToInsert = transactionData.items.map(item => ({
        held_transaction_id: heldId,
        product_id: item.product_id,
        sku: item.sku,
        product_name: item.product_name,
        quantity: item.quantity,
        unit_price: item.unit_price,
        discount: item.discount || 0,
        total_price: item.total_price,
        created_at: new Date().toISOString()
      }));

      await held_transaction_items.bulkAdd(itemsToInsert);
    }

    // Fetch complete held transaction with items
    const createdHeldTransaction = await getHeldTransaction(heldId);

    console.log(`✅ Transaction held/parked: ${heldId} - Total: ${heldTransaction.total}`);
    return createdHeldTransaction;
  } catch (error) {
    console.error('❌ Error holding transaction:', error);
    throw error;
  }
}

/**
 * Get held transaction by ID with items
 * @param {number} id - Held transaction ID
 * @returns {Promise<Object|null>} Held transaction with items or null
 */
export async function getHeldTransaction(id) {
  try {
    const heldTransaction = await held_transactions.get(id);
    if (!heldTransaction) return null;

    const items = await held_transaction_items
      .where('held_transaction_id')
      .equals(id)
      .toArray();

    return {
      ...heldTransaction,
      items
    };
  } catch (error) {
    console.error('❌ Error getting held transaction:', error);
    return null;
  }
}

/**
 * Get all held transactions with optional filters
 * @param {Object} filters - { employee_id, customer_name, limit }
 * @returns {Promise<Array>} Array of held transactions with items
 */
export async function getHeldTransactions(filters = {}) {
  try {
    let query = held_transactions.toCollection();

    // Apply filters
    if (filters.employee_id) {
      query = held_transactions.where('employee_id').equals(filters.employee_id);
    }

    if (filters.customer_name) {
      const searchTerm = filters.customer_name.toLowerCase();
      query = query.filter(txn =>
        txn.customer_name && txn.customer_name.toLowerCase().includes(searchTerm)
      );
    }

    // Sort by created_at descending
    const results = await query.reverse().sortBy('created_at');

    // Apply limit
    const limit = filters.limit || 50;
    const limitedResults = results.slice(0, limit);

    // Fetch items for each held transaction
    const heldTransactionsWithItems = await Promise.all(
      limitedResults.map(async (txn) => {
        const items = await held_transaction_items
          .where('held_transaction_id')
          .equals(txn.id)
          .toArray();
        return { ...txn, items };
      })
    );

    return heldTransactionsWithItems;
  } catch (error) {
    console.error('❌ Error getting held transactions:', error);
    return [];
  }
}

/**
 * Get held transactions for current employee
 * @param {number} employeeId - Employee ID
 * @returns {Promise<Array>} Array of held transactions
 */
export async function getEmployeeHeldTransactions(employeeId) {
  return await getHeldTransactions({ employee_id: employeeId });
}

/**
 * Recall/Resume a held transaction
 * This retrieves the held transaction and deletes it from held table
 * @param {number} heldId - Held transaction ID
 * @returns {Promise<Object>} Held transaction data to resume
 */
export async function recallHeldTransaction(heldId) {
  try {
    const heldTransaction = await getHeldTransaction(heldId);

    if (!heldTransaction) {
      throw new Error(`Held transaction ${heldId} not found`);
    }

    // Delete held transaction items
    await held_transaction_items
      .where('held_transaction_id')
      .equals(heldId)
      .delete();

    // Delete held transaction
    await held_transactions.delete(heldId);

    console.log(`✅ Recalled held transaction: ${heldId}`);
    return heldTransaction;
  } catch (error) {
    console.error('❌ Error recalling held transaction:', error);
    throw error;
  }
}

/**
 * Delete a held transaction
 * @param {number} heldId - Held transaction ID
 */
export async function deleteHeldTransaction(heldId) {
  try {
    // Delete held transaction items
    await held_transaction_items
      .where('held_transaction_id')
      .equals(heldId)
      .delete();

    // Delete held transaction
    await held_transactions.delete(heldId);

    console.log(`✅ Deleted held transaction: ${heldId}`);
  } catch (error) {
    console.error('❌ Error deleting held transaction:', error);
    throw error;
  }
}

/**
 * Update held transaction notes
 * @param {number} heldId - Held transaction ID
 * @param {string} notes - Notes to add/update
 * @returns {Promise<Object>} Updated held transaction
 */
export async function updateHeldTransactionNotes(heldId, notes) {
  try {
    await held_transactions.update(heldId, {
      notes,
      updated_at: new Date().toISOString()
    });

    const updatedTransaction = await getHeldTransaction(heldId);
    console.log(`✅ Updated notes for held transaction: ${heldId}`);

    return updatedTransaction;
  } catch (error) {
    console.error('❌ Error updating held transaction notes:', error);
    throw error;
  }
}

/**
 * Get count of held transactions
 * @param {number} employeeId - Optional employee ID to filter
 * @returns {Promise<number>} Count of held transactions
 */
export async function getHeldTransactionCount(employeeId = null) {
  try {
    if (employeeId) {
      return await held_transactions
        .where('employee_id')
        .equals(employeeId)
        .count();
    }
    return await held_transactions.count();
  } catch (error) {
    console.error('❌ Error getting held transaction count:', error);
    return 0;
  }
}

/**
 * Clear old held transactions (cleanup utility)
 * @param {number} daysOld - Delete held transactions older than this many days
 * @returns {Promise<number>} Number of transactions deleted
 */
export async function clearOldHeldTransactions(daysOld = 7) {
  try {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - daysOld);
    const cutoffISO = cutoffDate.toISOString();

    const oldTransactions = await held_transactions
      .where('created_at')
      .below(cutoffISO)
      .toArray();

    let deletedCount = 0;

    for (const txn of oldTransactions) {
      await deleteHeldTransaction(txn.id);
      deletedCount++;
    }

    console.log(`✅ Cleared ${deletedCount} held transactions older than ${daysOld} days`);
    return deletedCount;
  } catch (error) {
    console.error('❌ Error clearing old held transactions:', error);
    return 0;
  }
}

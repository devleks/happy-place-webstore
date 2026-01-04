/**
 * Transaction Operations for IndexedDB
 * Ported from electron/database.js transaction functions
 */

import { transactions, transaction_items, products } from './schema';

/**
 * Create a new transaction
 * @param {Object} transactionData - Transaction data with items array
 * @returns {Promise<Object>} Created transaction with items
 */
export async function createTransaction(transactionData) {
  try {
    const transaction = {
      shift_id: transactionData.shift_id,
      employee_id: transactionData.employee_id,
      employee_name: transactionData.employee_name,
      customer_name: transactionData.customer_name || null,
      customer_phone: transactionData.customer_phone || null,
      subtotal: transactionData.subtotal || 0,
      tax: transactionData.tax || 0,
      discount: transactionData.discount || 0,
      total: transactionData.total || 0,
      payment_method: transactionData.payment_method, // 'cash', 'card', 'mpesa'
      payment_reference: transactionData.payment_reference || null,
      amount_paid: transactionData.amount_paid || 0,
      change_given: transactionData.change_given || 0,
      notes: transactionData.notes || null,
      synced: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    // Insert transaction
    const transactionId = await transactions.add(transaction);

    // Insert transaction items
    if (transactionData.items && transactionData.items.length > 0) {
      const itemsToInsert = transactionData.items.map(item => ({
        transaction_id: transactionId,
        product_id: item.product_id,
        sku: item.sku,
        product_name: item.product_name,
        quantity: item.quantity,
        unit_price: item.unit_price,
        discount: item.discount || 0,
        total_price: item.total_price,
        created_at: new Date().toISOString()
      }));

      await transaction_items.bulkAdd(itemsToInsert);

      // Update product stock
      for (const item of transactionData.items) {
        const product = await products.get(item.product_id);
        if (product) {
          await products.update(item.product_id, {
            quantity: product.quantity - item.quantity,
            updated_at: new Date().toISOString()
          });
        }
      }
    }

    // Fetch complete transaction with items
    const createdTransaction = await getTransaction(transactionId);

    console.log(`✅ Transaction ${transactionId} created - Total: ${transaction.total}`);
    return createdTransaction;
  } catch (error) {
    console.error('❌ Error creating transaction:', error);
    throw error;
  }
}

/**
 * Get transaction by ID with items
 * @param {number} id - Transaction ID
 * @returns {Promise<Object|null>} Transaction with items or null
 */
export async function getTransaction(id) {
  try {
    const transaction = await transactions.get(id);
    if (!transaction) return null;

    const items = await transaction_items
      .where('transaction_id')
      .equals(id)
      .toArray();

    return {
      ...transaction,
      items
    };
  } catch (error) {
    console.error('❌ Error getting transaction:', error);
    return null;
  }
}

/**
 * Get transactions with filters
 * @param {Object} filters - { shift_id, employee_id, payment_method, start_date, end_date, limit }
 * @returns {Promise<Array>} Array of transactions with items
 */
export async function getTransactions(filters = {}) {
  try {
    let query = transactions.toCollection();

    // Apply filters
    if (filters.shift_id) {
      query = transactions.where('shift_id').equals(filters.shift_id);
    }

    if (filters.employee_id) {
      query = query.filter(txn => txn.employee_id === filters.employee_id);
    }

    if (filters.payment_method) {
      query = query.filter(txn => txn.payment_method === filters.payment_method);
    }

    if (filters.start_date) {
      query = query.filter(txn => txn.created_at >= filters.start_date);
    }

    if (filters.end_date) {
      query = query.filter(txn => txn.created_at <= filters.end_date);
    }

    // Sort by created_at descending
    const results = await query.reverse().sortBy('created_at');

    // Apply limit
    const limit = filters.limit || 100;
    const limitedResults = results.slice(0, limit);

    // Fetch items for each transaction
    const transactionsWithItems = await Promise.all(
      limitedResults.map(async (txn) => {
        const items = await transaction_items
          .where('transaction_id')
          .equals(txn.id)
          .toArray();
        return { ...txn, items };
      })
    );

    return transactionsWithItems;
  } catch (error) {
    console.error('❌ Error getting transactions:', error);
    return [];
  }
}

/**
 * Get transactions for current shift
 * @param {number} shiftId - Shift ID
 * @returns {Promise<Array>} Array of transactions with items
 */
export async function getShiftTransactions(shiftId) {
  return await getTransactions({ shift_id: shiftId });
}

/**
 * Get daily sales summary
 * @param {string} date - Date string (YYYY-MM-DD)
 * @returns {Promise<Object>} Sales summary
 */
export async function getDailySalesSummary(date) {
  try {
    const startOfDay = `${date}T00:00:00`;
    const endOfDay = `${date}T23:59:59`;

    const dailyTransactions = await transactions
      .where('created_at')
      .between(startOfDay, endOfDay, true, true)
      .toArray();

    const summary = {
      date,
      total_sales: 0,
      transaction_count: dailyTransactions.length,
      cash_sales: 0,
      card_sales: 0,
      mpesa_sales: 0,
      total_items_sold: 0,
      average_transaction: 0
    };

    for (const txn of dailyTransactions) {
      summary.total_sales += parseFloat(txn.total || 0);

      if (txn.payment_method === 'cash') {
        summary.cash_sales += parseFloat(txn.total || 0);
      } else if (txn.payment_method === 'card') {
        summary.card_sales += parseFloat(txn.total || 0);
      } else if (txn.payment_method === 'mpesa') {
        summary.mpesa_sales += parseFloat(txn.total || 0);
      }

      // Count items
      const items = await transaction_items
        .where('transaction_id')
        .equals(txn.id)
        .toArray();
      summary.total_items_sold += items.reduce((sum, item) => sum + item.quantity, 0);
    }

    summary.average_transaction = summary.transaction_count > 0
      ? summary.total_sales / summary.transaction_count
      : 0;

    return summary;
  } catch (error) {
    console.error('❌ Error getting daily sales summary:', error);
    return null;
  }
}

/**
 * Get unsynced transactions
 * @returns {Promise<Array>} Unsynced transactions with items
 */
export async function getUnsyncedTransactions() {
  try {
    const unsynced = await transactions
      .where('synced')
      .equals(false)
      .toArray();

    // Fetch items for each transaction
    const transactionsWithItems = await Promise.all(
      unsynced.map(async (txn) => {
        const items = await transaction_items
          .where('transaction_id')
          .equals(txn.id)
          .toArray();
        return { ...txn, items };
      })
    );

    return transactionsWithItems;
  } catch (error) {
    console.error('❌ Error getting unsynced transactions:', error);
    return [];
  }
}

/**
 * Mark transaction as synced
 * @param {number} transactionId - Transaction ID
 */
export async function markTransactionAsSynced(transactionId) {
  try {
    await transactions.update(transactionId, {
      synced: true,
      updated_at: new Date().toISOString()
    });
    console.log(`✅ Transaction ${transactionId} marked as synced`);
  } catch (error) {
    console.error('❌ Error marking transaction as synced:', error);
  }
}

/**
 * Delete transaction (for testing/cleanup)
 * @param {number} transactionId - Transaction ID
 */
export async function deleteTransaction(transactionId) {
  try {
    // Delete transaction items first
    await transaction_items
      .where('transaction_id')
      .equals(transactionId)
      .delete();

    // Delete transaction
    await transactions.delete(transactionId);

    console.log(`✅ Transaction ${transactionId} deleted`);
  } catch (error) {
    console.error('❌ Error deleting transaction:', error);
    throw error;
  }
}

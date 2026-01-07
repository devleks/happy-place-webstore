/**
 * Shift Operations for IndexedDB
 * Ported from electron/database.js shift functions
 */

import { db, shifts, transactions } from './schema';

/**
 * Create a new shift
 * @param {Object} shiftData - { employee_id, employee_name, start_time, starting_cash, notes }
 * @returns {Promise<Object>} Created shift
 */
export async function createShift(shiftData) {
  try {
    const today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    const shiftNumber = `${today}-EMP${shiftData.employee_id}-${Date.now().toString().slice(-4)}`;

    const shift = {
      employee_id: shiftData.employee_id,
      employee_name: shiftData.employee_name,
      shift_number: shiftData.shift_number || shiftNumber,
      start_time: shiftData.start_time || new Date().toISOString(),
      starting_cash: shiftData.starting_cash ?? shiftData.opening_float ?? 0,
      notes: shiftData.notes || null,
      status: 'open',
      // Initialize to zero
      end_time: null,
      closing_cash: null,
      expected_cash: null,
      cash_difference: null,
      total_sales: 0,
      cash_sales: 0,
      card_sales: 0,
      mpesa_sales: 0,
      transaction_count: 0,
      discrepancy_reason: null,
      synced: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    const id = await shifts.add(shift);
    const createdShift = await shifts.get(id);

    console.log(`✅ Shift ${id} created for ${shift.employee_name}`);
    return createdShift;
  } catch (error) {
    console.error('❌ Error creating shift:', error);
    throw error;
  }
}

/**
 * Get currently open shift
 * @returns {Promise<Object|null>} Current shift or null
 */
export async function getCurrentShift(employeeId) {
  try {
    const ensureShiftNumber = async (shift) => {
      if (!shift) return null;
      if (shift.shift_number) return shift;
      const today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
      const shiftNumber = `${today}-EMP${shift.employee_id}-${Date.now().toString().slice(-4)}`;
      await shifts.update(shift.id, {
        shift_number: shiftNumber,
        updated_at: new Date().toISOString()
      });
      return { ...shift, shift_number: shiftNumber };
    };

    if (employeeId) {
      const list = await shifts
        .where('employee_id')
        .equals(employeeId)
        .toArray();
      const open = list
        .filter((s) => s.status === 'open')
        .sort((a, b) => (b.start_time || '').localeCompare(a.start_time || ''));
      return await ensureShiftNumber(open[0] || null);
    }

    const list = await shifts.toArray();
    const open = list
      .filter((s) => s.status === 'open')
      .sort((a, b) => (b.start_time || '').localeCompare(a.start_time || ''));
    return await ensureShiftNumber(open[0] || null);
  } catch (error) {
    console.error('❌ Error getting current shift:', error);
    return null;
  }
}

/**
 * Get shift by ID
 * @param {number} id - Shift ID
 * @returns {Promise<Object|null>} Shift or null
 */
export async function getShift(id) {
  try {
    return await shifts.get(id);
  } catch (error) {
    console.error('❌ Error getting shift:', error);
    return null;
  }
}

/**
 * Get shifts with filters
 * @param {Object} filters - { employee_id, status, start_date, end_date, limit }
 * @returns {Promise<Array>} Array of shifts
 */
export async function getShifts(filters = {}) {
  try {
    let query = shifts.toCollection();

    // Apply filters
    if (filters.employee_id) {
      query = shifts.where('employee_id').equals(filters.employee_id);
    }

    if (filters.status) {
      query = query.filter(shift => shift.status === filters.status);
    }

    if (filters.start_date) {
      query = query.filter(shift => shift.start_time >= filters.start_date);
    }

    if (filters.end_date) {
      query = query.filter(shift => shift.start_time <= filters.end_date);
    }

    // Sort by start_time descending
    const results = await query.reverse().sortBy('start_time');

    // Apply limit
    const limit = filters.limit || 100;
    return results.slice(0, limit);
  } catch (error) {
    console.error('❌ Error getting shifts:', error);
    return [];
  }
}

export async function updateShift(shiftId, updateData) {
  try {
    await shifts.update(shiftId, {
      ...updateData,
      updated_at: new Date().toISOString()
    });
    return await shifts.get(shiftId);
  } catch (error) {
    console.error('❌ Error updating shift:', error);
    return null;
  }
}

/**
 * Close a shift
 * @param {number} shiftId - Shift ID
 * @param {Object} closeData - Closing data (closing_cash, expected_cash, etc.)
 * @returns {Promise<Object>} Updated shift
 */
export async function closeShift(shiftId, closeData) {
  try {
    const shift = await shifts.get(shiftId);

    if (!shift) {
      throw new Error('Shift not found');
    }

    if (shift.status !== 'open') {
      throw new Error('Shift is already closed');
    }

    // Update shift with closing data
    await shifts.update(shiftId, {
      end_time: closeData.end_time || new Date().toISOString(),
      closing_cash: closeData.closing_cash,
      expected_cash: closeData.expected_cash || 0,
      cash_difference: closeData.cash_difference || 0,
      total_sales: closeData.total_sales || 0,
      cash_sales: closeData.cash_sales || 0,
      card_sales: closeData.card_sales || 0,
      mpesa_sales: closeData.mpesa_sales || 0,
      transaction_count: closeData.transaction_count || 0,
      notes: closeData.notes || shift.notes,
      discrepancy_reason: closeData.discrepancy_reason || null,
      status: 'closed',
      updated_at: new Date().toISOString()
    });

    const updatedShift = await shifts.get(shiftId);
    console.log(`✅ Shift ${shiftId} closed successfully`);

    return updatedShift;
  } catch (error) {
    console.error('❌ Error closing shift:', error);
    throw error;
  }
}

/**
 * Calculate shift totals from transactions
 * @param {number} shiftId - Shift ID
 * @returns {Promise<Object>} Shift totals
 */
export async function calculateShiftTotals(shiftId) {
  try {
    const shiftTransactions = await transactions
      .where('shift_id')
      .equals(shiftId)
      .toArray();

    const totals = {
      total_sales: 0,
      cash_sales: 0,
      card_sales: 0,
      mpesa_sales: 0,
      transaction_count: shiftTransactions.length
    };

    shiftTransactions.forEach(txn => {
      const amount = parseFloat(txn.total || 0);
      totals.total_sales += amount;

      if (txn.payment_method === 'cash') {
        totals.cash_sales += amount;
      } else if (txn.payment_method === 'card') {
        totals.card_sales += amount;
      } else if (txn.payment_method === 'mpesa') {
        totals.mpesa_sales += amount;
      }
    });

    return totals;
  } catch (error) {
    console.error('❌ Error calculating shift totals:', error);
    return {
      total_sales: 0,
      cash_sales: 0,
      card_sales: 0,
      mpesa_sales: 0,
      transaction_count: 0
    };
  }
}

/**
 * Get shifts pending sync
 * @returns {Promise<Array>} Unsynced shifts
 */
export async function getUnsyncedShifts() {
  try {
    if (!db.isOpen()) {
      await db.open();
    }
    return await shifts
      .toCollection()
      .filter((s) => s.synced === false || s.synced === 0 || !s.synced)
      .toArray();
  } catch (error) {
    console.error('❌ Error getting unsynced shifts:', error);
    return [];
  }
}

/**
 * Mark shift as synced
 * @param {number} shiftId - Shift ID
 */
export async function markShiftAsSynced(shiftId) {
  try {
    await shifts.update(shiftId, {
      synced: true,
      updated_at: new Date().toISOString()
    });
    console.log(`✅ Shift ${shiftId} marked as synced`);
  } catch (error) {
    console.error('❌ Error marking shift as synced:', error);
  }
}

export async function setShiftBackendId(shiftId, backendShiftId) {
  try {
    await shifts.update(shiftId, {
      backend_shift_id: backendShiftId,
      updated_at: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error setting backend_shift_id:', error);
  }
}

/**
 * PWA Database API Service
 * Replaces Electron IPC with direct IndexedDB calls
 * Compatible interface with previous Electron implementation
 */

import * as db from '../db';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:5001';

// ============================================================================
// AUTHENTICATION OPERATIONS
// ============================================================================

export const authAPI = {
  /**
   * Login with email and password
   */
  async login(email, password) {
    try {
      const employee = await db.validateEmployeeCredentials(email, password);

      if (!employee) {
        if (navigator.onLine) {
          let response;
          let data;

          try {
            response = await fetch(`${API_BASE_URL}/api/auth/employee/login`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                email,
                password
              })
            });

            if (!response.ok) {
              return {
                success: false,
                error: 'Invalid email or password'
              };
            }

            data = await response.json();
          } catch (fetchErr) {
            return {
              success: false,
              error: 'Cannot reach the POS server right now. If you have logged in before on this device, you can log in offline; otherwise connect to the server and try again.'
            };
          }

          if (data && data.access_token) {
            await db.setMetadata('sync_token', data.access_token);
          }

          // Cache employee locally to enable offline login later on this device
          try {
            const existing = await db.getEmployeeByEmail(email);
            if (existing) {
              await db.updateEmployee(existing.id, {
                full_name: data?.employee?.full_name || existing.full_name,
                role: data?.employee?.role || existing.role,
                password: password,
                active: true
              });
            } else {
              await db.addEmployee({
                email,
                password,
                full_name: data?.employee?.full_name || email,
                role: data?.employee?.role || 'cashier',
                active: true
              });
            }
          } catch (e) {
            // ignore; caching is best-effort
          }

          const sessionToken = btoa(JSON.stringify({
            id: data?.employee?.id,
            email: data?.employee?.email,
            role: data?.employee?.role,
            timestamp: Date.now()
          }));

          return {
            success: true,
            employee: {
              id: data?.employee?.id,
              email: data?.employee?.email,
              full_name: data?.employee?.full_name,
              role: data?.employee?.role
            },
            session: {
              token: sessionToken,
              employee_id: data?.employee?.id
            }
          };
        }

        return {
          success: false,
          error: 'Invalid email or password'
        };
      }

      // Create session token (simplified for offline use)
      const sessionToken = btoa(JSON.stringify({
        id: employee.id,
        email: employee.email,
        role: employee.role,
        timestamp: Date.now()
      }));

      return {
        success: true,
        employee: {
          id: employee.id,
          email: employee.email,
          full_name: employee.full_name,
          role: employee.role
        },
        session: {
          token: sessionToken,
          employee_id: employee.id
        }
      };
    } catch (error) {
      console.error('❌ Login error:', error);
      return {
        success: false,
        error: error?.message || 'Login failed'
      };
    }
  },

  /**
   * Validate current session
   */
  async validateSession(sessionToken) {
    try {
      const session = JSON.parse(atob(sessionToken));
      const employee = await db.getEmployee(session.id);

      if (!employee || !employee.active) {
        return { valid: false };
      }

      return {
        valid: true,
        session: {
          token: sessionToken,
          employee_id: employee.id
        }
      };
    } catch (error) {
      return { valid: false };
    }
  },

  /**
   * Logout
   */
  async logout(sessionToken) {
    // For IndexedDB, just clear localStorage
    localStorage.removeItem('session_token');
    localStorage.removeItem('employee_info');
    return { success: true };
  },

  /**
   * Get session statistics
   */
  async getSessionStats() {
    const employeeCount = await db.getActiveEmployeeCount();
    return {
      success: true,
      stats: {
        active_employees: employeeCount
      }
    };
  },

  /**
   * Set sync token (for backend sync)
   */
  async setSyncToken(token) {
    await db.setMetadata('sync_token', token);
    return { success: true };
  },

  /**
   * Manual employee sync from backend
   */
  async syncEmployees() {
    try {
      const syncToken = await db.getMetadata('sync_token');

      if (!syncToken) {
        return {
          success: false,
          error: 'No sync token set'
        };
      }

      const response = await fetch(`${API_BASE_URL}/api/admin/employees`, {
        headers: {
          'Authorization': `Bearer ${syncToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch employees: ${response.statusText}`);
      }

      const data = await response.json();
      const employees = data.employees || [];

      // Update local IndexedDB with fetched employees
      for (const emp of employees) {
        const existing = await db.getEmployeeByEmail(emp.email);

        if (existing) {
          await db.updateEmployee(existing.id, {
            full_name: emp.full_name,
            role: emp.role,
            active: emp.active
          });
        } else {
          await db.addEmployee({
            email: emp.email,
            password: emp.password || 'temp123', // Will be updated on first login
            full_name: emp.full_name,
            role: emp.role,
            pin: emp.pin || null,
            active: emp.active
          });
        }
      }

      return {
        success: true,
        count: employees.length
      };
    } catch (error) {
      console.error('❌ Employee sync error:', error);
      return {
        success: false,
        error: error.message
      };
    }
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
    const products = await db.getProducts({ active: true });
    return products;
  },

  /**
   * Search products
   */
  async search(query) {
    const products = await db.searchProducts(query);
    return products;
  },

  /**
   * Get product by SKU
   */
  async getBySku(sku) {
    const product = await db.getProductBySku(sku);
    return product;
  },

  /**
   * Update product stock
   */
  async updateStock(productId, quantityChange) {
    try {
      const product = await db.updateProductStock(productId, quantityChange);
      return { success: true, product };
    } catch (error) {
      return { success: false, error: error.message };
    }
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
    try {
      const created = await db.createTransaction(transaction);

      // Update shift totals immediately (offline-first)
      try {
        if (created?.shift_id) {
          const totals = await db.calculateShiftTotals(created.shift_id);
          await db.updateShift(created.shift_id, {
            total_sales: totals.total_sales,
            cash_sales: totals.cash_sales,
            card_sales: totals.card_sales,
            mpesa_sales: totals.mpesa_sales,
            transaction_count: totals.transaction_count
          });
        }
      } catch (e) {
        // ignore; totals will be recalculated on next shift fetch
      }

      // Best-effort immediate sync when online
      try {
        const syncToken = await db.getMetadata('sync_token');
        if (navigator.onLine && syncToken) {
          await db.syncWithBackend(API_BASE_URL, syncToken);
        }
      } catch (e) {
        // Ignore sync errors here; they will be retried later.
      }

      // Return latest transaction row (may now include backend_transaction_id)
      const updated = await db.getTransaction(created.id);
      return updated || created;
    } catch (error) {
      return null;
    }
  },

  /**
   * Get transactions with filters
   */
  async getAll(filters = {}) {
    const transactions = await db.getTransactions(filters);
    return transactions;
  },

  /**
   * Get single transaction
   */
  async getById(id) {
    const transaction = await db.getTransaction(id);
    return transaction;
  }
};

// ============================================================================
// SHIFT OPERATIONS
// ============================================================================

export const shiftAPI = {
  /**
   * Start a new shift
   */
  async start(shiftData) {
    try {
      const shift = await db.createShift(shiftData);

      // Best-effort backend shift start when online
      try {
        const syncToken = await db.getMetadata('sync_token');
        if (navigator.onLine && syncToken) {
          const res = await fetch(`${API_BASE_URL}/api/pos/shifts/start`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${syncToken}`
            },
            body: JSON.stringify({
              store_location_id: 1,
              opening_float: shift.starting_cash || 0
            })
          });

          if (res.ok) {
            const data = await res.json();
            const backendShiftId = data?.shift?.shift_id;
            const backendShiftNumber = data?.shift?.shift_number;
            if (backendShiftId) {
              await db.setShiftBackendId(shift.id, backendShiftId);
            }
            if (backendShiftNumber) {
              await db.updateShift(shift.id, { shift_number: backendShiftNumber });
            }
          }
        }
      } catch (e) {
        // ignore; shift remains local-only
      }

      return shift;
    } catch (error) {
      return null;
    }
  },

  /**
   * Close current shift
   */
  async close(shiftId, closeData) {
    try {
      const shift = await db.closeShift(shiftId, closeData);

      // Best-effort backend shift close when online
      try {
        const syncToken = await db.getMetadata('sync_token');
        const localShift = await db.getShift(shiftId);
        const backendShiftId = localShift?.backend_shift_id;
        if (navigator.onLine && syncToken && backendShiftId) {
          await fetch(`${API_BASE_URL}/api/pos/shifts/close`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${syncToken}`
            },
            body: JSON.stringify({
              shift_id: backendShiftId,
              closing_cash: closeData.closing_cash,
              notes: closeData.notes
            })
          });
        }
      } catch (e) {
        // ignore; shift close remains local-only
      }

      return shift;
    } catch (error) {
      return null;
    }
  },

  /**
   * Get current open shift
   */
  async getCurrent(employeeId) {
    const shift = await db.getCurrentShift(employeeId);
    if (!shift) return null;

    // Recalculate totals from local transactions so dashboard is always correct
    try {
      const totals = await db.calculateShiftTotals(shift.id);
      const updated = await db.updateShift(shift.id, {
        total_sales: totals.total_sales,
        cash_sales: totals.cash_sales,
        card_sales: totals.card_sales,
        mpesa_sales: totals.mpesa_sales,
        transaction_count: totals.transaction_count
      });
      return updated || shift;
    } catch (e) {
      return shift;
    }
  },

  /**
   * Get all shifts with filters
   */
  async getAll(filters = {}) {
    const shifts = await db.getShifts(filters);
    return shifts;
  },

  /**
   * Get shift by ID
   */
  async getById(id) {
    const shift = await db.getShift(id);
    return shift;
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
    try {
      const held = await db.holdTransaction(transaction);
      return { success: true, held };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  /**
   * Get all held transactions
   */
  async getAll() {
    const heldTransactions = await db.getHeldTransactions();
    return heldTransactions;
  },

  /**
   * Recall a held transaction
   */
  async recall(id) {
    try {
      const transaction = await db.recallHeldTransaction(id);
      return { success: true, transaction };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  /**
   * Delete a held transaction
   */
  async delete(id) {
    try {
      await db.deleteHeldTransaction(id);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
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
    try {
      const syncToken = await db.getMetadata('sync_token');

      if (!syncToken) {
        return {
          success: false,
          error: 'No sync token set'
        };
      }

      const results = await db.syncWithBackend(API_BASE_URL, syncToken);

      return {
        success: true,
        results
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  },

  /**
   * Get sync status
   */
  async getStatus() {
    const status = await db.getSyncStatus();
    return status;
  },

  /**
   * Listen for sync status changes
   */
  onStatusChange(callback) {
    // For PWA, we can use online/offline events
    const handleOnline = () => callback({ online: true });
    const handleOffline = () => callback({ online: false });

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }
};

// ============================================================================
// HARDWARE OPERATIONS
// ============================================================================

export const hardwareAPI = {
  /**
   * Scan barcode (Web API fallback)
   */
  async scanBarcode() {
    // For PWA, use Web Bluetooth or manual entry
    return { success: false, error: 'Barcode scanning requires hardware integration' };
  },

  /**
   * Print receipt (Web API fallback)
   */
  async printReceipt(receiptData) {
    // Use browser print API
    window.print();
    return { success: true };
  },

  /**
   * Open cash drawer (Web API fallback)
   */
  async openCashDrawer() {
    // Cash drawer would require hardware integration
    console.log('💰 Cash drawer open signal sent');
    return { success: true };
  },

  /**
   * Listen for barcode scans
   */
  onBarcodeScan(callback) {
    // For PWA, listen for keyboard input
    const handleKeyPress = (e) => {
      // Barcode scanners typically send Enter after scan
      if (e.key === 'Enter' && e.target.dataset.barcodeInput) {
        callback(e.target.value);
        e.target.value = '';
      }
    };

    document.addEventListener('keypress', handleKeyPress);

    return () => {
      document.removeEventListener('keypress', handleKeyPress);
    };
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
    return navigator.onLine;
  },

  /**
   * Get app version
   */
  async getVersion() {
    return process.env.REACT_APP_VERSION || '1.0.0';
  },

  /**
   * Get memory usage (Web API)
   */
  async getMemoryUsage() {
    if (performance.memory) {
      return {
        used: performance.memory.usedJSHeapSize,
        total: performance.memory.totalJSHeapSize,
        limit: performance.memory.jsHeapSizeLimit
      };
    }
    return null;
  },

  /**
   * Check for updates (Service Worker)
   */
  async checkForUpdates() {
    if ('serviceWorker' in navigator) {
      const registration = await navigator.serviceWorker.getRegistration();
      if (registration) {
        await registration.update();
        return { success: true, message: 'Checking for updates...' };
      }
    }
    return { success: false, error: 'Service Worker not registered' };
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

/**
 * Check if running in PWA mode
 */
export const isPWA = () => {
  return window.matchMedia('(display-mode: standalone)').matches ||
         window.navigator.standalone === true;
};

// Export all APIs as default
const api = {
  auth: authAPI,
  product: productAPI,
  transaction: transactionAPI,
  shift: shiftAPI,
  heldTransaction: heldTransactionAPI,
  sync: syncAPI,
  hardware: hardwareAPI,
  utility: utilityAPI,
  generateTransactionNumber,
  generateHoldNumber,
  calculateTotal,
  isPWA,
  isElectron: () => false // Always false for PWA
};

export default api;

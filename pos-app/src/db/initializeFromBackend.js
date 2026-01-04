/**
 * Initialize PWA data from Backend API
 * Syncs employees and products from the main Happy Place backend
 */

import * as db from './index';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:5001';

/**
 * Fetch employees from backend and store in IndexedDB
 * @param {string} authToken - JWT token from backend (admin/manager token)
 * @returns {Promise<Object>} Sync result
 */
export async function syncEmployeesFromBackend(authToken) {
  try {
    console.log('🔄 Syncing employees from backend...');

    const response = await fetch(`${API_BASE_URL}/api/admin/employees`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    const employees = data.employees || [];

    console.log(`📥 Received ${employees.length} employees from backend`);

    let syncedCount = 0;
    let updatedCount = 0;
    let errorCount = 0;

    // Sync each employee to IndexedDB
    for (const emp of employees) {
      try {
        const existing = await db.getEmployeeByEmail(emp.email);

        if (existing) {
          // Update existing employee
          await db.updateEmployee(existing.id, {
            full_name: emp.full_name,
            role: emp.role,
            active: emp.active,
            pin: emp.pin || existing.pin
          });
          updatedCount++;
        } else {
          // Add new employee
          await db.addEmployee({
            email: emp.email,
            password: 'synced123', // Placeholder - will authenticate via backend
            full_name: emp.full_name,
            role: emp.role,
            pin: emp.pin || null,
            active: emp.active
          });
          syncedCount++;
        }
      } catch (error) {
        console.error(`❌ Error syncing employee ${emp.email}:`, error);
        errorCount++;
      }
    }

    const result = {
      success: true,
      total: employees.length,
      synced: syncedCount,
      updated: updatedCount,
      errors: errorCount
    };

    // Store sync metadata
    await db.setMetadata('last_employee_sync', new Date().toISOString());
    await db.setMetadata('employee_sync_count', employees.length);

    console.log(`✅ Employee sync complete:`, result);
    return result;
  } catch (error) {
    console.error('❌ Employee sync failed:', error);
    return {
      success: false,
      error: error.message,
      total: 0,
      synced: 0,
      updated: 0,
      errors: 1
    };
  }
}

/**
 * Fetch products from backend and store in IndexedDB
 * @param {string} authToken - JWT token from backend
 * @returns {Promise<Object>} Sync result
 */
export async function syncProductsFromBackend(authToken) {
  try {
    console.log('🔄 Syncing products from backend...');

    const response = await fetch(`${API_BASE_URL}/api/admin/inventory`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    const products = data.products || [];

    console.log(`📥 Received ${products.length} products from backend`);

    let syncedCount = 0;
    let updatedCount = 0;
    let errorCount = 0;

    // Sync each product to IndexedDB
    for (const product of products) {
      try {
        const existing = await db.getProductBySku(product.sku);

        const productData = {
          sku: product.sku,
          barcode: product.barcode || null,
          name: product.name,
          description: product.description,
          category: product.category,
          price: parseFloat(product.price),
          cost: parseFloat(product.cost || 0),
          quantity: parseInt(product.quantity || 0),
          reorder_level: parseInt(product.reorder_level || 10),
          active: product.active !== false,
          image_url: product.image_url || null
        };

        if (existing) {
          // Update existing product
          await db.updateProduct(existing.id, productData);
          updatedCount++;
        } else {
          // Add new product
          await db.addProduct(productData);
          syncedCount++;
        }
      } catch (error) {
        console.error(`❌ Error syncing product ${product.sku}:`, error);
        errorCount++;
      }
    }

    const result = {
      success: true,
      total: products.length,
      synced: syncedCount,
      updated: updatedCount,
      errors: errorCount
    };

    // Store sync metadata
    await db.setMetadata('last_product_sync', new Date().toISOString());
    await db.setMetadata('product_sync_count', products.length);

    console.log(`✅ Product sync complete:`, result);
    return result;
  } catch (error) {
    console.error('❌ Product sync failed:', error);
    return {
      success: false,
      error: error.message,
      total: 0,
      synced: 0,
      updated: 0,
      errors: 1
    };
  }
}

/**
 * Get stored backend auth token
 * @returns {Promise<string|null>} Auth token or null
 */
export async function getBackendAuthToken() {
  return await db.getMetadata('backend_auth_token');
}

/**
 * Store backend auth token
 * @param {string} token - JWT token from backend
 */
export async function setBackendAuthToken(token) {
  await db.setMetadata('backend_auth_token', token);
  console.log('✅ Backend auth token stored');
}

/**
 * Initialize PWA with data from backend
 * Call this on app startup or manually trigger sync
 * @param {string} authToken - JWT token from backend (admin/manager required)
 * @returns {Promise<Object>} Sync results
 */
export async function initializeFromBackend(authToken) {
  console.log('🚀 Initializing PWA data from backend...');

  // Store auth token for future syncs
  await setBackendAuthToken(authToken);

  const results = {
    employees: { success: false },
    products: { success: false }
  };

  // Sync employees first (needed for login)
  results.employees = await syncEmployeesFromBackend(authToken);

  // Sync products (needed for POS transactions)
  results.products = await syncProductsFromBackend(authToken);

  const overallSuccess = results.employees.success && results.products.success;

  console.log(overallSuccess ? '✅ PWA initialization complete' : '⚠️ PWA initialization completed with errors');

  return {
    success: overallSuccess,
    results
  };
}

/**
 * Check if PWA needs initial sync from backend
 * @returns {Promise<boolean>} True if sync needed
 */
export async function needsInitialSync() {
  const employeeCount = await db.getActiveEmployeeCount();
  const lastSync = await db.getMetadata('last_employee_sync');

  // Need sync if no employees or last sync was over 24 hours ago
  if (employeeCount === 0) {
    return true;
  }

  if (!lastSync) {
    return true;
  }

  const lastSyncDate = new Date(lastSync);
  const hoursSinceSync = (Date.now() - lastSyncDate.getTime()) / (1000 * 60 * 60);

  return hoursSinceSync > 24;
}

/**
 * Auto-sync on app startup if needed
 * Uses stored auth token if available
 * @returns {Promise<Object|null>} Sync results or null if no token
 */
export async function autoSyncOnStartup() {
  try {
    const needsSync = await needsInitialSync();

    if (!needsSync) {
      console.log('✅ PWA data is up to date, skipping auto-sync');
      return null;
    }

    const token = await getBackendAuthToken();

    if (!token) {
      console.log('⚠️ No backend auth token found. Please run initial sync manually.');
      return null;
    }

    console.log('🔄 Auto-syncing PWA data from backend...');
    return await initializeFromBackend(token);
  } catch (error) {
    console.error('❌ Auto-sync failed:', error);
    return null;
  }
}

/**
 * IndexedDB Schema for Happy Place POS
 * Using Dexie.js - a wrapper around IndexedDB
 *
 * This replaces the SQLite database from Electron implementation
 */

import Dexie from 'dexie';

// Initialize database
export const db = new Dexie('HappyPlacePOS');

// Define schema
// Syntax: 'primaryKey, index1, index2, ...'
db.version(1).stores({
  // Products (cached from backend)
  products: '++id, sku, name, category, created_at',

  // Employees (cached from backend for offline login)
  employees: '++id, email, full_name, role, active',

  // Transactions (POS sales)
  transactions: '++id, shift_id, customer_name, payment_method, total, created_at, synced',

  // Transaction Items
  transaction_items: '++id, transaction_id, product_id, sku, quantity, unit_price',

  // Held Transactions (parked sales)
  held_transactions: '++id, employee_id, customer_name, created_at',

  // Held Transaction Items
  held_transaction_items: '++id, held_transaction_id, product_id, sku, quantity, unit_price',

  // Shifts (cashier shift management)
  shifts: '++id, employee_id, status, start_time, end_time, synced',

  // Sync Queue (pending sync to backend)
  sync_queue: '++id, entity_type, entity_id, operation, created_at, synced',

  // Metadata
  metadata: 'key, value, updated_at'
});

// Export collections for easy access
export const {
  products,
  employees,
  transactions,
  transaction_items,
  held_transactions,
  held_transaction_items,
  shifts,
  sync_queue,
  metadata
} = db;

// Database initialization
export async function initializeDatabase() {
  try {
    await db.open();
    console.log('✅ IndexedDB initialized successfully');

    // Check if we need to seed initial data
    const employeeCount = await employees.count();
    if (employeeCount === 0) {
      console.log('📦 Seeding initial employee data...');
      await seedInitialData();
    }

    return db;
  } catch (error) {
    console.error('❌ Failed to initialize IndexedDB:', error);
    throw error;
  }
}

/**
 * Seed initial employee data from backend
 * Fetches employees from the backend API
 */
export async function seedInitialData() {
  const count = await employees.count();
  
  if (count > 0) {
    console.log('✅ Employees already exist, skipping seed');
    return;
  }

  console.log('🌱 Fetching employees from backend...');

  try {
    const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:5001';
    
    // First, try to get admin token by logging in with admin credentials
    // This is needed to access the employee sync endpoint
    let authToken = null;
    
    try {
      const loginResponse = await fetch(`${API_BASE_URL}/api/auth/employee/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email: 'admin@happyplace.com',
          password: 'Admin123!'
        })
      });

      if (loginResponse.ok) {
        const loginData = await loginResponse.json();
        authToken = loginData.access_token;
        console.log('✅ Obtained admin token for employee sync');
      }
    } catch (loginError) {
      console.warn('⚠️ Could not obtain admin token:', loginError.message);
    }

    // Fetch employees from backend using the POS sync endpoint
    const response = await fetch(`${API_BASE_URL}/api/pos/employees/sync`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(authToken && { 'Authorization': `Bearer ${authToken}` })
      }
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch employees: ${response.status}`);
    }

    const data = await response.json();
    const backendEmployees = data.employees || [];

    console.log(`📥 Received ${backendEmployees.length} employees from backend`);

    // Add each employee to IndexedDB
    for (const emp of backendEmployees) {
      await employees.add({
        email: emp.email,
        password_hash: emp.password_hash || 'backend_managed', // Backend manages passwords
        full_name: emp.full_name,
        role: emp.role,
        pin: emp.pin || null,
        active: emp.active !== false,
        created_at: emp.created_at || new Date().toISOString(),
        updated_at: emp.updated_at || new Date().toISOString()
      });
    }

    console.log(`✅ Synced ${backendEmployees.length} employees from backend`);
  } catch (error) {
    console.error('❌ Failed to fetch employees from backend:', error);
    console.log('⚠️ Falling back to local test data...');
    
    // Fallback: Add minimal test data for offline development
    await employees.add({
      email: 'admin@happyplace.com',
      password_hash: 'admin123',
      full_name: 'Administrator',
      role: 'admin',
      pin: '0000',
      active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    });

    console.log('✅ Added fallback admin user for offline testing');
  }
}

// Clear all data (for testing/reset)
export async function clearDatabase() {
  await db.delete();
  await db.open();
  console.log('🗑️ Database cleared');
}

// Get database stats
export async function getDatabaseStats() {
  const stats = {
    products: await products.count(),
    employees: await employees.count(),
    transactions: await transactions.count(),
    shifts: await shifts.count(),
    held_transactions: await held_transactions.count(),
    sync_queue: await sync_queue.count()
  };

  return stats;
}

export default db;

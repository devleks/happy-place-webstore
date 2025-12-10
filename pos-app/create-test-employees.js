/**
 * Create Test Employees
 * Run this script to populate the database with test employees
 * Usage: node create-test-employees.js
 */

const Database = require('better-sqlite3');
const bcrypt = require('bcryptjs');
const path = require('path');
const os = require('os');

// Get database path (same as Electron app)
const userDataPath = path.join(os.homedir(), 'Library', 'Application Support', 'happy-place-pos');
const dbPath = path.join(userDataPath, 'pos.db');
console.log('Database path:', dbPath);

const db = new Database(dbPath);

// Create test employees
async function createTestEmployees() {
  console.log('Creating test employees...');

  const employees = [
    {
      backend_id: 1,
      email: 'admin@happyplace.co.ke',
      full_name: 'Admin User',
      role: 'admin',
      password: 'admin123'
    },
    {
      backend_id: 2,
      email: 'manager@happyplace.co.ke',
      full_name: 'Manager User',
      role: 'manager',
      password: 'manager123'
    },
    {
      backend_id: 3,
      email: 'cashier1@happyplace.co.ke',
      full_name: 'Cashier One',
      role: 'cashier',
      password: 'cashier123'
    }
  ];

  const stmt = db.prepare(`
    INSERT OR REPLACE INTO employees 
    (backend_id, email, full_name, role, password_hash, permissions, is_active, last_synced_at, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  for (const emp of employees) {
    // Hash password
    const passwordHash = await bcrypt.hash(emp.password, 10);
    const now = new Date().toISOString();

    stmt.run(
      emp.backend_id,
      emp.email,
      emp.full_name,
      emp.role,
      passwordHash,
      JSON.stringify({}),
      1, // is_active
      now,
      now,
      now
    );

    console.log(`✅ Created: ${emp.email} (password: ${emp.password})`);
  }

  console.log('\n✅ Test employees created successfully!');
  console.log('\nYou can now login with:');
  console.log('- admin@happyplace.co.ke / admin123');
  console.log('- manager@happyplace.co.ke / manager123');
  console.log('- cashier1@happyplace.co.ke / cashier123');

  db.close();
}

createTestEmployees().catch(console.error);

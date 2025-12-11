/**
 * Manual Employee Sync Script
 * Syncs employees from backend to POS SQLite database
 */

const Database = require('better-sqlite3');
const fetch = require('node-fetch');
const path = require('path');
const os = require('os');

// Database path
const DB_PATH = path.join(
  os.homedir(),
  'Library/Application Support/happy-place-pos/pos.db'
);

async function syncEmployees() {
  console.log('🔄 Starting employee sync...\n');

  // Open database
  const db = new Database(DB_PATH);

  try {
    // Get sync token
    const tokenRow = db.prepare('SELECT value FROM sync_metadata WHERE key = ?').get('sync_token');

    if (!tokenRow) {
      console.error('❌ No sync token found. Please configure sync token first.');
      process.exit(1);
    }

    const syncToken = tokenRow.value;
    console.log(`🔑 Sync token: ${syncToken.substring(0, 20)}...\n`);

    // Fetch employees from backend
    console.log('📡 Fetching employees from backend...');
    const response = await fetch('http://127.0.0.1:5001/api/employees/sync', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${syncToken}`,
        'Content-Type': 'application/json'
      }
    });

    console.log(`📊 Response status: ${response.status}\n`);

    if (!response.ok) {
      const error = await response.text();
      console.error(`❌ Sync failed: ${error}`);
      process.exit(1);
    }

    const data = await response.json();

    if (data.success && data.employees) {
      console.log(`📦 Received ${data.employees.length} employees\n`);

      // Prepare insert statement
      const stmt = db.prepare(`
        INSERT OR REPLACE INTO employees
        (backend_id, email, full_name, role, password_hash, permissions,
         is_active, last_synced_at, sync_version, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `);

      const syncTime = new Date().toISOString();
      let insertedCount = 0;

      // Insert each employee
      for (const emp of data.employees) {
        try {
          console.log(`👤 Syncing: ${emp.email} (${emp.role})`);

          stmt.run(
            emp.id,
            emp.email,
            emp.full_name,
            emp.role,
            emp.password_hash,
            JSON.stringify(emp.permissions || {}),
            emp.is_active ? 1 : 0,
            syncTime,
            emp.version || 1,
            syncTime
          );

          insertedCount++;
        } catch (empError) {
          console.error(`❌ Failed to insert ${emp.email}:`, empError.message);
        }
      }

      console.log(`\n✅ Successfully synced ${insertedCount}/${data.employees.length} employees`);

      // Save sync version
      db.prepare(`
        INSERT OR REPLACE INTO sync_metadata (key, value, updated_at)
        VALUES ('last_employee_sync', ?, ?)
      `).run(data.sync_version, new Date().toISOString());

      console.log(`📌 Saved sync version: ${data.sync_version}`);

      // Verify
      const count = db.prepare('SELECT COUNT(*) as count FROM employees').get();
      console.log(`\n📊 Total employees in database: ${count.count}`);

      // Show admin account
      const admin = db.prepare('SELECT email, role FROM employees WHERE role = ? LIMIT 1').get('admin');
      if (admin) {
        console.log(`\n🔐 Admin account available: ${admin.email}`);
        console.log(`   Password: admin123 (from backend)`);
      }

    } else {
      console.error('❌ No employee data received');
      process.exit(1);
    }

  } catch (error) {
    console.error('❌ Sync error:', error.message);
    process.exit(1);
  } finally {
    db.close();
  }
}

// Run sync
syncEmployees();

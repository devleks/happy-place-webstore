/**
 * Test Database Setup
 * Creates in-memory SQLite database for testing
 */

const Database = require('better-sqlite3');

/**
 * Create test database with schema
 */
function createTestDatabase() {
  const db = new Database(':memory:');

  // Create schema
  db.exec(`
    -- Employees table
    CREATE TABLE IF NOT EXISTS employees (
      id INTEGER PRIMARY KEY,
      backend_id INTEGER UNIQUE,
      email TEXT UNIQUE NOT NULL,
      full_name TEXT NOT NULL,
      role TEXT NOT NULL,
      password_hash TEXT NOT NULL,
      permissions TEXT,
      is_active INTEGER DEFAULT 1,
      last_synced_at TEXT,
      sync_version INTEGER DEFAULT 1,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_employees_email ON employees(email);
    CREATE INDEX IF NOT EXISTS idx_employees_backend_id ON employees(backend_id);

    -- Sessions table
    CREATE TABLE IF NOT EXISTS sessions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      employee_id INTEGER NOT NULL,
      session_token TEXT UNIQUE NOT NULL,
      started_at TEXT NOT NULL,
      last_activity_at TEXT NOT NULL,
      expires_at TEXT NOT NULL,
      is_active INTEGER DEFAULT 1,
      device_info TEXT,
      FOREIGN KEY (employee_id) REFERENCES employees(id)
    );

    CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token);
    CREATE INDEX IF NOT EXISTS idx_sessions_employee ON sessions(employee_id);

    -- Activity log
    CREATE TABLE IF NOT EXISTS activity_log (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      employee_id INTEGER,
      session_id INTEGER,
      action TEXT NOT NULL,
      details TEXT,
      timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
      synced INTEGER DEFAULT 0
    );

    CREATE INDEX IF NOT EXISTS idx_activity_employee ON activity_log(employee_id);
    CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON activity_log(timestamp);

    -- Sync metadata
    CREATE TABLE IF NOT EXISTS sync_metadata (
      key TEXT PRIMARY KEY,
      value TEXT NOT NULL,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    -- Products table
    CREATE TABLE IF NOT EXISTS products (
      id INTEGER PRIMARY KEY,
      sku TEXT UNIQUE NOT NULL,
      name TEXT NOT NULL,
      price REAL NOT NULL,
      stock_quantity INTEGER DEFAULT 0
    );

    -- Transactions table
    CREATE TABLE IF NOT EXISTS transactions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      transaction_number TEXT UNIQUE NOT NULL,
      employee_id INTEGER,
      subtotal REAL NOT NULL,
      total REAL NOT NULL,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
  `);

  return db;
}

/**
 * Seed test data
 */
async function seedTestData(db, bcrypt) {
  const passwordHash = await bcrypt.hash('password123', 10);

  // Insert test employees
  db.prepare(`
    INSERT INTO employees (id, backend_id, email, full_name, role, password_hash, is_active)
    VALUES 
      (1, 1, 'admin@test.com', 'Admin User', 'admin', ?, 1),
      (2, 2, 'manager@test.com', 'Manager User', 'manager', ?, 1),
      (3, 3, 'cashier@test.com', 'Cashier User', 'cashier', ?, 1)
  `).run(passwordHash, passwordHash, passwordHash);

  // Insert test products
  db.prepare(`
    INSERT INTO products (id, sku, name, price, stock_quantity)
    VALUES 
      (1, 'TEST-001', 'Test Product 1', 10.99, 100),
      (2, 'TEST-002', 'Test Product 2', 20.99, 50)
  `).run();

  return db;
}

module.exports = {
  createTestDatabase,
  seedTestData
};

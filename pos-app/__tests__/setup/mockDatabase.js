/**
 * Mock Database for Testing
 * Replaces better-sqlite3 with in-memory mock
 */

// In-memory data store
const dataStore = {
  employees: [],
  sessions: [],
  activity_log: [],
  sync_metadata: [],
  products: [],
  transactions: []
};

// Mock prepared statement
class MockStatement {
  constructor(sql, db) {
    this.sql = sql;
    this.db = db;
  }

  run(...params) {
    // Extract table name from SQL
    const match = this.sql.match(/INSERT INTO (\w+)/i);
    if (match) {
      const table = match[1];
      const id = dataStore[table] ? dataStore[table].length + 1 : 1;
      
      // Create mock record
      const record = { id, ...this._parseParams(params) };
      if (dataStore[table]) {
        dataStore[table].push(record);
      }
      
      return { lastInsertRowid: id, changes: 1 };
    }
    
    return { lastInsertRowid: 0, changes: 0 };
  }

  get(...params) {
    const match = this.sql.match(/SELECT .* FROM (\w+)/i);
    if (match) {
      const table = match[1];
      if (dataStore[table] && dataStore[table].length > 0) {
        return dataStore[table][0];
      }
    }
    return null;
  }

  all(...params) {
    const match = this.sql.match(/SELECT .* FROM (\w+)/i);
    if (match) {
      const table = match[1];
      return dataStore[table] || [];
    }
    return [];
  }

  _parseParams(params) {
    // Simple param parsing (can be enhanced)
    return {};
  }
}

// Mock database
class MockDatabase {
  constructor(path) {
    this.path = path;
    this.isOpen = true;
  }

  exec(sql) {
    // Mock table creation
    return this;
  }

  prepare(sql) {
    return new MockStatement(sql, this);
  }

  close() {
    this.isOpen = false;
  }

  // Helper method to reset data
  _reset() {
    Object.keys(dataStore).forEach(key => {
      dataStore[key] = [];
    });
  }

  // Helper method to seed data
  _seed(table, data) {
    if (dataStore[table]) {
      dataStore[table] = data;
    }
  }
}

/**
 * Create test database (in-memory mock)
 */
function createTestDatabase() {
  const db = new MockDatabase(':memory:');
  
  // Initialize tables
  db.exec(`
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

    CREATE TABLE IF NOT EXISTS sessions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      employee_id INTEGER NOT NULL,
      session_token TEXT UNIQUE NOT NULL,
      started_at TEXT NOT NULL,
      last_activity_at TEXT NOT NULL,
      expires_at TEXT NOT NULL,
      is_active INTEGER DEFAULT 1,
      device_info TEXT
    );

    CREATE TABLE IF NOT EXISTS activity_log (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      employee_id INTEGER,
      session_id INTEGER,
      action TEXT NOT NULL,
      details TEXT,
      timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
      synced INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS sync_metadata (
      key TEXT PRIMARY KEY,
      value TEXT NOT NULL,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS products (
      id INTEGER PRIMARY KEY,
      sku TEXT UNIQUE NOT NULL,
      name TEXT NOT NULL,
      price REAL NOT NULL,
      stock_quantity INTEGER DEFAULT 0
    );

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

  // Seed employees
  db._seed('employees', [
    {
      id: 1,
      backend_id: 1,
      email: 'admin@test.com',
      full_name: 'Admin User',
      role: 'admin',
      password_hash: passwordHash,
      is_active: 1
    },
    {
      id: 2,
      backend_id: 2,
      email: 'manager@test.com',
      full_name: 'Manager User',
      role: 'manager',
      password_hash: passwordHash,
      is_active: 1
    },
    {
      id: 3,
      backend_id: 3,
      email: 'cashier@test.com',
      full_name: 'Cashier User',
      role: 'cashier',
      password_hash: passwordHash,
      is_active: 1
    }
  ]);

  // Seed products
  db._seed('products', [
    { id: 1, sku: 'TEST-001', name: 'Test Product 1', price: 10.99, stock_quantity: 100 },
    { id: 2, sku: 'TEST-002', name: 'Test Product 2', price: 20.99, stock_quantity: 50 }
  ]);

  return db;
}

module.exports = {
  createTestDatabase,
  seedTestData,
  MockDatabase,
  dataStore  // Export for test assertions
};

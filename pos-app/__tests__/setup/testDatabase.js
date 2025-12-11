/**
 * Enhanced Mock Database for Testing
 * Replaces better-sqlite3 with in-memory mock that closely matches the API
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

// Auto-increment counters
const autoIncrementCounters = {
  sessions: 0,
  activity_log: 0,
  transactions: 0
};

/**
 * Parse SQL to extract table name, operation, and WHERE conditions
 */
function parseSQL(sql) {
  const normalized = sql.replace(/\s+/g, ' ').trim();

  // INSERT INTO table
  const insertMatch = normalized.match(/INSERT INTO (\w+)/i);
  if (insertMatch) {
    return { operation: 'INSERT', table: insertMatch[1] };
  }

  // SELECT FROM table WHERE
  const selectMatch = normalized.match(/SELECT .* FROM (\w+)(?: WHERE (.+))?/i);
  if (selectMatch) {
    return {
      operation: 'SELECT',
      table: selectMatch[1],
      where: selectMatch[2] || null
    };
  }

  // UPDATE table SET ... WHERE
  const updateMatch = normalized.match(/UPDATE (\w+) SET .+ WHERE (.+)/i);
  if (updateMatch) {
    return {
      operation: 'UPDATE',
      table: updateMatch[1],
      where: updateMatch[2]
    };
  }

  // DELETE FROM table WHERE
  const deleteMatch = normalized.match(/DELETE FROM (\w+)(?: WHERE (.+))?/i);
  if (deleteMatch) {
    return {
      operation: 'DELETE',
      table: deleteMatch[1],
      where: deleteMatch[2] || null
    };
  }

  return { operation: 'UNKNOWN', table: null };
}

/**
 * Extract column names and values from INSERT statement
 */
function parseInsert(sql) {
  const match = sql.match(/INSERT INTO \w+ \(([^)]+)\) VALUES \(([^)]+)\)/i);
  if (match) {
    const columns = match[1].split(',').map(c => c.trim());
    return { columns };
  }
  return { columns: [] };
}

/**
 * Evaluate WHERE clause against a record
 */
function matchesWhere(record, whereClause, params) {
  if (!whereClause) return true;

  // Simple WHERE column = ? pattern (generic)
  const simpleMatch = whereClause.match(/(\w+)\s*=\s*\?/);
  if (simpleMatch && params.length > 0) {
    const column = simpleMatch[1];
    return record[column] === params[0];
  }

  // WHERE is_active = 1 AND expires_at < ? (expired by time)
  if (whereClause.includes('is_active = 1') && whereClause.includes('expires_at < ?')) {
    const now = params[0];
    return record.is_active === 1 && record.expires_at < now;
  }

  // WHERE is_active = 1 AND last_activity_at < ? (expired by inactivity)
  if (whereClause.includes('is_active = 1') && whereClause.includes('last_activity_at < ?')) {
    const timeoutThreshold = params[0];
    return record.is_active === 1 && record.last_activity_at < timeoutThreshold;
  }

  // WHERE session_token = ? AND is_active = 1 (active session lookup)
  if (whereClause.includes('session_token') && whereClause.includes('is_active')) {
    return record.session_token === params[0] && record.is_active === 1;
  }

  return false;
}

/**
 * Mock prepared statement
 */
class MockStatement {
  constructor(sql, db) {
    this.sql = sql;
    this.db = db;
    this.parsed = parseSQL(sql);
  }

  /**
   * Execute INSERT/UPDATE/DELETE and return info
   */
  run(...params) {
    const { operation, table } = this.parsed;

    if (!dataStore[table]) {
      return { lastInsertRowid: 0, changes: 0 };
    }

    if (operation === 'INSERT') {
      const { columns } = parseInsert(this.sql);
      const record = {};

      // Auto-increment ID if needed
      if (autoIncrementCounters.hasOwnProperty(table)) {
        autoIncrementCounters[table]++;
        record.id = autoIncrementCounters[table];
      } else {
        // Use manual ID from params
        record.id = params[0] || dataStore[table].length + 1;
      }

      // Map columns to params
      columns.forEach((col, idx) => {
        if (col !== 'id' || !autoIncrementCounters.hasOwnProperty(table)) {
          record[col] = params[idx];
        }
      });

      dataStore[table].push(record);

      return {
        lastInsertRowid: record.id,
        changes: 1
      };
    }

    if (operation === 'UPDATE') {
      const { where } = this.parsed;
      let changesCount = 0;

      dataStore[table].forEach(record => {
        if (matchesWhere(record, where, params)) {
          // Update the record (simplified - just update timestamp fields)
          if (this.sql.includes('last_activity_at')) {
            record.last_activity_at = params[0];
          }
          if (this.sql.includes('is_active')) {
            record.is_active = 0;
          }
          changesCount++;
        }
      });

      return { lastInsertRowid: 0, changes: changesCount };
    }

    if (operation === 'DELETE') {
      const { where } = this.parsed;
      const initialLength = dataStore[table].length;

      dataStore[table] = dataStore[table].filter(record =>
        !matchesWhere(record, where, params)
      );

      return {
        lastInsertRowid: 0,
        changes: initialLength - dataStore[table].length
      };
    }

    return { lastInsertRowid: 0, changes: 0 };
  }

  /**
   * Execute SELECT and return first matching row
   */
  get(...params) {
    const { operation, table, where } = this.parsed;

    if (operation !== 'SELECT' || !dataStore[table]) {
      return null;
    }

    // Handle COUNT(*) queries
    if (this.sql.includes('COUNT(*)')) {
      const records = where
        ? dataStore[table].filter(record => matchesWhere(record, where, params))
        : dataStore[table];

      // Return aggregate results
      if (this.sql.includes('COUNT(*) as total_sessions')) {
        const activeRecords = records.filter(r => r.is_active === 1);
        const employeeIds = new Set(records.map(r => r.employee_id));

        return {
          total_sessions: records.length,
          active_sessions: activeRecords.length,
          unique_employees: employeeIds.size
        };
      }

      return { count: records.length };
    }

    if (!where) {
      return dataStore[table][0] || null;
    }

    const found = dataStore[table].find(record =>
      matchesWhere(record, where, params)
    );

    return found || null;
  }

  /**
   * Execute SELECT and return all matching rows
   */
  all(...params) {
    const { operation, table, where } = this.parsed;

    if (operation !== 'SELECT' || !dataStore[table]) {
      return [];
    }

    if (!where) {
      return dataStore[table];
    }

    return dataStore[table].filter(record =>
      matchesWhere(record, where, params)
    );
  }
}

/**
 * Mock database
 */
class MockDatabase {
  constructor(path) {
    this.path = path;
    this.isOpen = true;
  }

  exec(sql) {
    // Mock table creation - just return for chaining
    return this;
  }

  prepare(sql) {
    return new MockStatement(sql, this);
  }

  close() {
    this.isOpen = false;
  }

  // Helper method to reset all data
  _reset() {
    Object.keys(dataStore).forEach(key => {
      dataStore[key] = [];
    });
    Object.keys(autoIncrementCounters).forEach(key => {
      autoIncrementCounters[key] = 0;
    });
  }

  // Helper method to seed data directly
  _seed(table, data) {
    if (dataStore[table]) {
      dataStore[table] = data;

      // Update auto-increment counter
      if (autoIncrementCounters.hasOwnProperty(table) && data.length > 0) {
        const maxId = Math.max(...data.map(r => r.id || 0));
        autoIncrementCounters[table] = maxId;
      }
    }
  }

  // Helper to get data for assertions
  _getData(table) {
    return dataStore[table] || [];
  }
}

/**
 * Create test database (in-memory mock)
 */
function createTestDatabase() {
  const db = new MockDatabase(':memory:');

  // Initialize tables (schema is implicit in dataStore)
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

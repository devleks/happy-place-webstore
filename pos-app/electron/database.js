/**
 * SQLite Database Layer
 * Handles all local data storage for offline-first POS
 * 
 * Security: All IPC handlers validate input per Electron best practices
 */

const Database = require('better-sqlite3');
const { app, ipcMain } = require('electron');
const path = require('path');

let db = null;

// ============================================================================
// VALIDATION HELPERS
// ============================================================================

/**
 * Validate and sanitize input data
 */
const validators = {
  /**
   * Validate string input
   */
  validateString(value, fieldName, maxLength = 1000) {
    if (typeof value !== 'string') {
      throw new Error(`${fieldName} must be a string`);
    }
    if (value.length > maxLength) {
      throw new Error(`${fieldName} exceeds maximum length of ${maxLength}`);
    }
    return value.trim();
  },

  /**
   * Validate number input
   */
  validateNumber(value, fieldName, min = 0, max = Number.MAX_SAFE_INTEGER) {
    const num = Number(value);
    if (isNaN(num)) {
      throw new Error(`${fieldName} must be a valid number`);
    }
    if (num < min || num > max) {
      throw new Error(`${fieldName} must be between ${min} and ${max}`);
    }
    return num;
  },

  /**
   * Validate integer input
   */
  validateInteger(value, fieldName, min = 0, max = Number.MAX_SAFE_INTEGER) {
    const num = this.validateNumber(value, fieldName, min, max);
    if (!Number.isInteger(num)) {
      throw new Error(`${fieldName} must be an integer`);
    }
    return num;
  },

  /**
   * Validate array input
   */
  validateArray(value, fieldName, maxLength = 1000) {
    if (!Array.isArray(value)) {
      throw new Error(`${fieldName} must be an array`);
    }
    if (value.length > maxLength) {
      throw new Error(`${fieldName} exceeds maximum length of ${maxLength}`);
    }
    return value;
  },

  /**
   * Validate object input
   */
  validateObject(value, fieldName) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) {
      throw new Error(`${fieldName} must be a valid object`);
    }
    return value;
  },

  /**
   * Validate enum value
   */
  validateEnum(value, fieldName, allowedValues) {
    if (!allowedValues.includes(value)) {
      throw new Error(`${fieldName} must be one of: ${allowedValues.join(', ')}`);
    }
    return value;
  },

  /**
   * Sanitize file path (prevent directory traversal)
   */
  sanitizePath(filePath, fieldName = 'filePath') {
    if (typeof filePath !== 'string') {
      throw new Error(`${fieldName} must be a string`);
    }

    const normalized = path.normalize(filePath);
    const userDataPath = app.getPath('userData');

    // Ensure path is within userData directory
    if (!normalized.startsWith(userDataPath)) {
      throw new Error(`${fieldName} must be within user data directory`);
    }

    return normalized;
  }
};

/**
 * Initialize the database
 */
function initDatabase() {
  try {
    const dbPath = path.join(app.getPath('userData'), 'pos.db');
    console.log(`📁 Database path: ${dbPath}`);

    db = new Database(dbPath, { verbose: console.log });
    
    // Enable WAL mode for better concurrency
    db.pragma('journal_mode = WAL');
    db.pragma('foreign_keys = ON');

    createTables();
    setupIpcHandlers();

    console.log('✅ Database initialized successfully');
    return db;
  } catch (error) {
    console.error('❌ Database initialization failed:', error);
    throw error;
  }
}

/**
 * Create database tables
 */
function createTables() {
  db.exec(`
    -- Products table (cached from backend)
    CREATE TABLE IF NOT EXISTS products (
      id INTEGER PRIMARY KEY,
      sku TEXT UNIQUE NOT NULL,
      name TEXT NOT NULL,
      description TEXT,
      category_id INTEGER,
      category_name TEXT,
      price REAL NOT NULL,
      stock_quantity INTEGER DEFAULT 0,
      low_stock_threshold INTEGER DEFAULT 5,
      image_url TEXT,
      size TEXT,
      color TEXT,
      synced_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
    CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
    CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);

    -- Transactions table (POS sales)
    CREATE TABLE IF NOT EXISTS transactions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      transaction_number TEXT UNIQUE NOT NULL,
      employee_id INTEGER,
      employee_name TEXT,
      customer_id INTEGER,
      customer_name TEXT,
      subtotal REAL NOT NULL,
      tax REAL DEFAULT 0,
      discount REAL DEFAULT 0,
      total REAL NOT NULL,
      payment_method TEXT NOT NULL,
      payment_status TEXT DEFAULT 'completed',
      notes TEXT,
      status TEXT DEFAULT 'completed',
      synced INTEGER DEFAULT 0,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_transactions_number ON transactions(transaction_number);
    CREATE INDEX IF NOT EXISTS idx_transactions_synced ON transactions(synced);
    CREATE INDEX IF NOT EXISTS idx_transactions_created ON transactions(created_at);

    -- Transaction items table
    CREATE TABLE IF NOT EXISTS transaction_items (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      transaction_id INTEGER NOT NULL,
      product_id INTEGER NOT NULL,
      product_sku TEXT NOT NULL,
      product_name TEXT NOT NULL,
      quantity INTEGER NOT NULL,
      unit_price REAL NOT NULL,
      subtotal REAL NOT NULL,
      discount REAL DEFAULT 0,
      total REAL NOT NULL,
      FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_transaction_items_transaction ON transaction_items(transaction_id);

    -- Held transactions table (for hold/recall feature)
    CREATE TABLE IF NOT EXISTS held_transactions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      hold_number TEXT UNIQUE NOT NULL,
      employee_id INTEGER,
      employee_name TEXT,
      customer_name TEXT,
      items TEXT NOT NULL,
      subtotal REAL NOT NULL,
      notes TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_held_transactions_number ON held_transactions(hold_number);

    -- Sync queue table (for offline transactions)
    CREATE TABLE IF NOT EXISTS sync_queue (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      entity_type TEXT NOT NULL,
      entity_id INTEGER NOT NULL,
      action TEXT NOT NULL,
      data TEXT NOT NULL,
      retry_count INTEGER DEFAULT 0,
      last_error TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_sync_queue_entity ON sync_queue(entity_type, entity_id);

    -- App settings table
    CREATE TABLE IF NOT EXISTS settings (
      key TEXT PRIMARY KEY,
      value TEXT NOT NULL,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- Employees table (synced from backend)
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
    CREATE INDEX IF NOT EXISTS idx_employees_active ON employees(is_active);

    -- Sessions table (local session management)
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

    CREATE INDEX IF NOT EXISTS idx_sessions_employee ON sessions(employee_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token);
    CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(is_active);

    -- Activity log for security audit
    CREATE TABLE IF NOT EXISTS activity_log (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      employee_id INTEGER,
      session_id INTEGER,
      action TEXT NOT NULL,
      details TEXT,
      timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
      synced INTEGER DEFAULT 0,
      FOREIGN KEY (employee_id) REFERENCES employees(id),
      FOREIGN KEY (session_id) REFERENCES sessions(id)
    );

    CREATE INDEX IF NOT EXISTS idx_activity_employee ON activity_log(employee_id);
    CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON activity_log(timestamp);
    CREATE INDEX IF NOT EXISTS idx_activity_synced ON activity_log(synced);

    -- Sync metadata table
    CREATE TABLE IF NOT EXISTS sync_metadata (
      key TEXT PRIMARY KEY,
      value TEXT NOT NULL,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
  `);

  console.log('✅ Database tables created');
}

// ============================================================================
// PRODUCT OPERATIONS
// ============================================================================

function getProducts() {
  try {
    return db.prepare(`
      SELECT * FROM products 
      WHERE stock_quantity > 0 
      ORDER BY name ASC
    `).all();
  } catch (error) {
    console.error('Error getting products:', error);
    return [];
  }
}

function searchProducts(query) {
  try {
    // ✅ Validate input
    const validatedQuery = validators.validateString(query, 'search query', 100);
    
    if (validatedQuery.length < 1) {
      throw new Error('Search query must be at least 1 character');
    }

    const searchTerm = `%${validatedQuery}%`;
    return db.prepare(`
      SELECT * FROM products 
      WHERE (name LIKE ? OR sku LIKE ? OR description LIKE ?)
        AND stock_quantity > 0
      ORDER BY name ASC
      LIMIT 50
    `).all(searchTerm, searchTerm, searchTerm);
  } catch (error) {
    console.error('Error searching products:', error);
    throw error; // Re-throw to inform caller
  }
}

function getProductBySku(sku) {
  try {
    // ✅ Validate input
    const validatedSku = validators.validateString(sku, 'SKU', 50);

    return db.prepare(`
      SELECT * FROM products WHERE sku = ?
    `).get(validatedSku);
  } catch (error) {
    console.error('Error getting product by SKU:', error);
    throw error;
  }
}

function upsertProduct(product) {
  try {
    const stmt = db.prepare(`
      INSERT INTO products (
        id, sku, name, description, category_id, category_name,
        price, stock_quantity, low_stock_threshold, image_url,
        size, color, synced_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
      ON CONFLICT(id) DO UPDATE SET
        name = excluded.name,
        description = excluded.description,
        price = excluded.price,
        stock_quantity = excluded.stock_quantity,
        low_stock_threshold = excluded.low_stock_threshold,
        image_url = excluded.image_url,
        size = excluded.size,
        color = excluded.color,
        synced_at = CURRENT_TIMESTAMP
    `);

    return stmt.run(
      product.id,
      product.sku,
      product.name,
      product.description || null,
      product.category_id || null,
      product.category_name || null,
      product.price,
      product.stock_quantity || 0,
      product.low_stock_threshold || 5,
      product.image_url || null,
      product.size || null,
      product.color || null
    );
  } catch (error) {
    console.error('Error upserting product:', error);
    throw error;
  }
}

function updateProductStock(productId, quantity) {
  try {
    return db.prepare(`
      UPDATE products 
      SET stock_quantity = stock_quantity - ?
      WHERE id = ?
    `).run(quantity, productId);
  } catch (error) {
    console.error('Error updating product stock:', error);
    throw error;
  }
}

// ============================================================================
// TRANSACTION OPERATIONS
// ============================================================================

function createTransaction(transaction) {
  try {
    // ✅ COMPREHENSIVE INPUT VALIDATION
    validators.validateObject(transaction, 'transaction');

    // Validate transaction fields
    const validatedTxn = {
      transaction_number: validators.validateString(transaction.transaction_number, 'transaction_number', 50),
      employee_id: transaction.employee_id ? validators.validateInteger(transaction.employee_id, 'employee_id', 1) : null,
      employee_name: transaction.employee_name ? validators.validateString(transaction.employee_name, 'employee_name', 100) : null,
      customer_id: transaction.customer_id ? validators.validateInteger(transaction.customer_id, 'customer_id', 1) : null,
      customer_name: transaction.customer_name ? validators.validateString(transaction.customer_name, 'customer_name', 100) : null,
      subtotal: validators.validateNumber(transaction.subtotal, 'subtotal', 0, 1000000),
      tax: validators.validateNumber(transaction.tax || 0, 'tax', 0, 100000),
      discount: validators.validateNumber(transaction.discount || 0, 'discount', 0, 100000),
      total: validators.validateNumber(transaction.total, 'total', 0, 1000000),
      payment_method: validators.validateEnum(
        transaction.payment_method,
        'payment_method',
        ['cash', 'card', 'mpesa', 'cod']
      ),
      payment_status: validators.validateEnum(
        transaction.payment_status || 'completed',
        'payment_status',
        ['pending', 'completed', 'failed', 'refunded']
      ),
      notes: transaction.notes ? validators.validateString(transaction.notes, 'notes', 500) : null,
      status: validators.validateEnum(
        transaction.status || 'completed',
        'status',
        ['pending', 'processing', 'completed', 'cancelled']
      )
    };

    // Validate items array
    const items = validators.validateArray(transaction.items, 'items', 100);
    
    if (items.length === 0) {
      throw new Error('Transaction must have at least one item');
    }

    // Validate each item
    const validatedItems = items.map((item, index) => {
      validators.validateObject(item, `item[${index}]`);
      
      return {
        product_id: validators.validateInteger(item.product_id, `item[${index}].product_id`, 1),
        product_sku: validators.validateString(item.product_sku, `item[${index}].product_sku`, 50),
        product_name: validators.validateString(item.product_name, `item[${index}].product_name`, 200),
        quantity: validators.validateInteger(item.quantity, `item[${index}].quantity`, 1, 1000),
        unit_price: validators.validateNumber(item.unit_price, `item[${index}].unit_price`, 0, 1000000),
        subtotal: validators.validateNumber(item.subtotal, `item[${index}].subtotal`, 0, 1000000),
        discount: validators.validateNumber(item.discount || 0, `item[${index}].discount`, 0, 100000),
        total: validators.validateNumber(item.total, `item[${index}].total`, 0, 1000000)
      };
    });

    // Validate total calculation
    const calculatedSubtotal = validatedItems.reduce((sum, item) => sum + item.subtotal, 0);
    const calculatedTotal = calculatedSubtotal + validatedTxn.tax - validatedTxn.discount;
    
    if (Math.abs(calculatedTotal - validatedTxn.total) > 0.01) {
      throw new Error('Transaction total does not match calculated total');
    }

    // ✅ ALL VALIDATION PASSED - Proceed with database operations
    const insertTransaction = db.prepare(`
      INSERT INTO transactions (
        transaction_number, employee_id, employee_name, customer_id, customer_name,
        subtotal, tax, discount, total, payment_method, payment_status, notes, status
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    const insertItem = db.prepare(`
      INSERT INTO transaction_items (
        transaction_id, product_id, product_sku, product_name,
        quantity, unit_price, subtotal, discount, total
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    const addToSyncQueue = db.prepare(`
      INSERT INTO sync_queue (entity_type, entity_id, action, data)
      VALUES (?, ?, ?, ?)
    `);

    // Run in transaction
    const result = db.transaction(() => {
      // Insert transaction
      const txnResult = insertTransaction.run(
        validatedTxn.transaction_number,
        validatedTxn.employee_id,
        validatedTxn.employee_name,
        validatedTxn.customer_id,
        validatedTxn.customer_name,
        validatedTxn.subtotal,
        validatedTxn.tax,
        validatedTxn.discount,
        validatedTxn.total,
        validatedTxn.payment_method,
        validatedTxn.payment_status,
        validatedTxn.notes,
        validatedTxn.status
      );

      const transactionId = txnResult.lastInsertRowid;

      // Insert items
      for (const item of validatedItems) {
        insertItem.run(
          transactionId,
          item.product_id,
          item.product_sku,
          item.product_name,
          item.quantity,
          item.unit_price,
          item.subtotal,
          item.discount,
          item.total
        );

        // Update stock
        updateProductStock(item.product_id, item.quantity);
      }

      // Add to sync queue (use original transaction for backend compatibility)
      addToSyncQueue.run(
        'transaction',
        transactionId,
        'create',
        JSON.stringify(transaction)
      );

      return transactionId;
    })();

    console.log(`✅ Transaction created: ${validatedTxn.transaction_number}`);
    return result;
  } catch (error) {
    console.error('❌ Error creating transaction:', error);
    throw error;
  }
}

function getTransactions(filters = {}) {
  try {
    let query = 'SELECT * FROM transactions WHERE 1=1';
    const params = [];

    if (filters.startDate) {
      query += ' AND created_at >= ?';
      params.push(filters.startDate);
    }

    if (filters.endDate) {
      query += ' AND created_at <= ?';
      params.push(filters.endDate);
    }

    if (filters.paymentMethod) {
      query += ' AND payment_method = ?';
      params.push(filters.paymentMethod);
    }

    query += ' ORDER BY created_at DESC LIMIT ?';
    params.push(filters.limit || 100);

    return db.prepare(query).all(...params);
  } catch (error) {
    console.error('Error getting transactions:', error);
    return [];
  }
}

function getTransaction(id) {
  try {
    const transaction = db.prepare(`
      SELECT * FROM transactions WHERE id = ?
    `).get(id);

    if (transaction) {
      transaction.items = db.prepare(`
        SELECT * FROM transaction_items WHERE transaction_id = ?
      `).all(id);
    }

    return transaction;
  } catch (error) {
    console.error('Error getting transaction:', error);
    return null;
  }
}

// ============================================================================
// HELD TRANSACTIONS (HOLD/RECALL)
// ============================================================================

function holdTransaction(transaction) {
  try {
    // ✅ Validate input
    validators.validateObject(transaction, 'transaction');

    const validatedHold = {
      hold_number: validators.validateString(transaction.hold_number, 'hold_number', 50),
      employee_id: transaction.employee_id ? validators.validateInteger(transaction.employee_id, 'employee_id', 1) : null,
      employee_name: transaction.employee_name ? validators.validateString(transaction.employee_name, 'employee_name', 100) : null,
      customer_name: transaction.customer_name ? validators.validateString(transaction.customer_name, 'customer_name', 100) : null,
      items: validators.validateArray(transaction.items, 'items', 100),
      subtotal: validators.validateNumber(transaction.subtotal, 'subtotal', 0, 1000000),
      notes: transaction.notes ? validators.validateString(transaction.notes, 'notes', 500) : null
    };

    if (validatedHold.items.length === 0) {
      throw new Error('Cannot hold transaction with no items');
    }

    const stmt = db.prepare(`
      INSERT INTO held_transactions (
        hold_number, employee_id, employee_name, customer_name,
        items, subtotal, notes
      ) VALUES (?, ?, ?, ?, ?, ?, ?)
    `);

    return stmt.run(
      validatedHold.hold_number,
      validatedHold.employee_id,
      validatedHold.employee_name,
      validatedHold.customer_name,
      JSON.stringify(validatedHold.items),
      validatedHold.subtotal,
      validatedHold.notes
    );
  } catch (error) {
    console.error('❌ Error holding transaction:', error);
    throw error;
  }
}

function getHeldTransactions() {
  try {
    const transactions = db.prepare(`
      SELECT * FROM held_transactions ORDER BY created_at DESC
    `).all();

    // Parse items JSON
    return transactions.map(txn => ({
      ...txn,
      items: JSON.parse(txn.items)
    }));
  } catch (error) {
    console.error('Error getting held transactions:', error);
    return [];
  }
}

function recallTransaction(id) {
  try {
    const transaction = db.prepare(`
      SELECT * FROM held_transactions WHERE id = ?
    `).get(id);

    if (transaction) {
      transaction.items = JSON.parse(transaction.items);
    }

    return transaction;
  } catch (error) {
    console.error('Error recalling transaction:', error);
    return null;
  }
}

function deleteHeldTransaction(id) {
  try {
    return db.prepare(`
      DELETE FROM held_transactions WHERE id = ?
    `).run(id);
  } catch (error) {
    console.error('Error deleting held transaction:', error);
    throw error;
  }
}

// ============================================================================
// SYNC QUEUE OPERATIONS
// ============================================================================

function getSyncQueue() {
  try {
    return db.prepare(`
      SELECT * FROM sync_queue ORDER BY created_at ASC
    `).all();
  } catch (error) {
    console.error('Error getting sync queue:', error);
    return [];
  }
}

function clearSyncQueue(ids) {
  try {
    const placeholders = ids.map(() => '?').join(',');
    return db.prepare(`
      DELETE FROM sync_queue WHERE id IN (${placeholders})
    `).run(...ids);
  } catch (error) {
    console.error('Error clearing sync queue:', error);
    throw error;
  }
}

function updateSyncQueueError(id, error) {
  try {
    return db.prepare(`
      UPDATE sync_queue 
      SET retry_count = retry_count + 1,
          last_error = ?
      WHERE id = ?
    `).run(error, id);
  } catch (error) {
    console.error('Error updating sync queue error:', error);
  }
}

// ============================================================================
// IPC HANDLERS (WITH COMPREHENSIVE ERROR HANDLING)
// ============================================================================

/**
 * Wrap IPC handler with error handling and logging
 */
function wrapIpcHandler(handlerName, handler) {
  return async (event, ...args) => {
    try {
      console.log(`📥 IPC: ${handlerName}`, args.length > 0 ? `(${args.length} args)` : '');
      const result = await handler(...args);
      console.log(`✅ IPC: ${handlerName} completed`);
      return result;
    } catch (error) {
      console.error(`❌ IPC: ${handlerName} failed:`, error.message);
      // Return error object instead of throwing (better for renderer)
      return {
        success: false,
        error: error.message,
        code: error.code || 'UNKNOWN_ERROR'
      };
    }
  };
}

function setupIpcHandlers() {
  // Products
  ipcMain.handle('db-get-products', wrapIpcHandler('db-get-products', 
    () => getProducts()
  ));
  
  ipcMain.handle('db-search-products', wrapIpcHandler('db-search-products',
    (query) => searchProducts(query)
  ));
  
  ipcMain.handle('db-get-product-by-sku', wrapIpcHandler('db-get-product-by-sku',
    (sku) => getProductBySku(sku)
  ));
  
  ipcMain.handle('db-update-product-stock', wrapIpcHandler('db-update-product-stock',
    (productId, quantity) => {
      // ✅ Validate inputs
      const validatedId = validators.validateInteger(productId, 'productId', 1);
      const validatedQty = validators.validateInteger(quantity, 'quantity', 1, 1000);
      return updateProductStock(validatedId, validatedQty);
    }
  ));

  // Transactions
  ipcMain.handle('db-create-transaction', wrapIpcHandler('db-create-transaction',
    (transaction) => createTransaction(transaction)
  ));
  
  ipcMain.handle('db-get-transactions', wrapIpcHandler('db-get-transactions',
    (filters) => {
      // ✅ Validate filters
      if (filters && typeof filters !== 'object') {
        throw new Error('Filters must be an object');
      }
      return getTransactions(filters || {});
    }
  ));
  
  ipcMain.handle('db-get-transaction', wrapIpcHandler('db-get-transaction',
    (id) => {
      const validatedId = validators.validateInteger(id, 'id', 1);
      return getTransaction(validatedId);
    }
  ));

  // Held transactions
  ipcMain.handle('db-hold-transaction', wrapIpcHandler('db-hold-transaction',
    (transaction) => holdTransaction(transaction)
  ));
  
  ipcMain.handle('db-get-held-transactions', wrapIpcHandler('db-get-held-transactions',
    () => getHeldTransactions()
  ));
  
  ipcMain.handle('db-recall-transaction', wrapIpcHandler('db-recall-transaction',
    (id) => {
      const validatedId = validators.validateInteger(id, 'id', 1);
      return recallTransaction(validatedId);
    }
  ));
  
  ipcMain.handle('db-delete-held-transaction', wrapIpcHandler('db-delete-held-transaction',
    (id) => {
      const validatedId = validators.validateInteger(id, 'id', 1);
      return deleteHeldTransaction(validatedId);
    }
  ));

  // Sync queue
  ipcMain.handle('db-get-sync-queue', wrapIpcHandler('db-get-sync-queue',
    () => getSyncQueue()
  ));
  
  ipcMain.handle('db-clear-sync-queue', wrapIpcHandler('db-clear-sync-queue',
    (ids) => {
      const validatedIds = validators.validateArray(ids, 'ids', 1000);
      // Validate each ID
      validatedIds.forEach((id, index) => {
        validators.validateInteger(id, `ids[${index}]`, 1);
      });
      return clearSyncQueue(validatedIds);
    }
  ));

  console.log('✅ IPC handlers registered with validation');
}

// ============================================================================
// CLEANUP
// ============================================================================

function closeDatabase() {
  if (db) {
    db.close();
    console.log('✅ Database closed');
  }
}

// ============================================================================
// EXPORTS
// ============================================================================

module.exports = {
  initDatabase,
  closeDatabase,
  getProducts,
  searchProducts,
  getProductBySku,
  upsertProduct,
  updateProductStock,
  createTransaction,
  getTransactions,
  getTransaction,
  holdTransaction,
  getHeldTransactions,
  recallTransaction,
  deleteHeldTransaction,
  getSyncQueue,
  clearSyncQueue,
  updateSyncQueueError
};

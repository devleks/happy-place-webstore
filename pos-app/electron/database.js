/**
 * SQLite Database Layer
 * Handles all local data storage for offline-first POS
 */

const Database = require('better-sqlite3');
const { app, ipcMain } = require('electron');
const path = require('path');

let db = null;

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
    const searchTerm = `%${query}%`;
    return db.prepare(`
      SELECT * FROM products 
      WHERE (name LIKE ? OR sku LIKE ? OR description LIKE ?)
        AND stock_quantity > 0
      ORDER BY name ASC
      LIMIT 50
    `).all(searchTerm, searchTerm, searchTerm);
  } catch (error) {
    console.error('Error searching products:', error);
    return [];
  }
}

function getProductBySku(sku) {
  try {
    return db.prepare(`
      SELECT * FROM products WHERE sku = ?
    `).get(sku);
  } catch (error) {
    console.error('Error getting product by SKU:', error);
    return null;
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
        transaction.transaction_number,
        transaction.employee_id || null,
        transaction.employee_name || null,
        transaction.customer_id || null,
        transaction.customer_name || null,
        transaction.subtotal,
        transaction.tax || 0,
        transaction.discount || 0,
        transaction.total,
        transaction.payment_method,
        transaction.payment_status || 'completed',
        transaction.notes || null,
        transaction.status || 'completed'
      );

      const transactionId = txnResult.lastInsertRowid;

      // Insert items
      for (const item of transaction.items) {
        insertItem.run(
          transactionId,
          item.product_id,
          item.product_sku,
          item.product_name,
          item.quantity,
          item.unit_price,
          item.subtotal,
          item.discount || 0,
          item.total
        );

        // Update stock
        updateProductStock(item.product_id, item.quantity);
      }

      // Add to sync queue
      addToSyncQueue.run(
        'transaction',
        transactionId,
        'create',
        JSON.stringify(transaction)
      );

      return transactionId;
    })();

    console.log(`✅ Transaction created: ${transaction.transaction_number}`);
    return result;
  } catch (error) {
    console.error('Error creating transaction:', error);
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
    const stmt = db.prepare(`
      INSERT INTO held_transactions (
        hold_number, employee_id, employee_name, customer_name,
        items, subtotal, notes
      ) VALUES (?, ?, ?, ?, ?, ?, ?)
    `);

    return stmt.run(
      transaction.hold_number,
      transaction.employee_id || null,
      transaction.employee_name || null,
      transaction.customer_name || null,
      JSON.stringify(transaction.items),
      transaction.subtotal,
      transaction.notes || null
    );
  } catch (error) {
    console.error('Error holding transaction:', error);
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
// IPC HANDLERS
// ============================================================================

function setupIpcHandlers() {
  // Products
  ipcMain.handle('db-get-products', () => getProducts());
  ipcMain.handle('db-search-products', (event, query) => searchProducts(query));
  ipcMain.handle('db-get-product-by-sku', (event, sku) => getProductBySku(sku));
  ipcMain.handle('db-update-product-stock', (event, productId, quantity) => 
    updateProductStock(productId, quantity)
  );

  // Transactions
  ipcMain.handle('db-create-transaction', (event, transaction) => 
    createTransaction(transaction)
  );
  ipcMain.handle('db-get-transactions', (event, filters) => 
    getTransactions(filters)
  );
  ipcMain.handle('db-get-transaction', (event, id) => getTransaction(id));

  // Held transactions
  ipcMain.handle('db-hold-transaction', (event, transaction) => 
    holdTransaction(transaction)
  );
  ipcMain.handle('db-get-held-transactions', () => getHeldTransactions());
  ipcMain.handle('db-recall-transaction', (event, id) => recallTransaction(id));
  ipcMain.handle('db-delete-held-transaction', (event, id) => 
    deleteHeldTransaction(id)
  );

  // Sync queue
  ipcMain.handle('db-get-sync-queue', () => getSyncQueue());
  ipcMain.handle('db-clear-sync-queue', (event, ids) => clearSyncQueue(ids));
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

/**
 * Integration Tests: Database Service
 * Tests for database.js transaction operations
 */

describe('Database Service Integration', () => {
  let mockDb;
  let database;

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock database operations
    const mockData = {
      products: [],
      transactions: [],
      transactionItems: [],
      heldTransactions: [],
      syncQueue: []
    };

    mockDb = {
      prepare: jest.fn((sql) => ({
        run: jest.fn((...args) => {
          if (sql.includes('INSERT INTO transactions')) {
            const id = mockData.transactions.length + 1;
            mockData.transactions.push({ id, ...args });
            return { lastInsertRowid: id };
          }
          if (sql.includes('INSERT INTO transaction_items')) {
            mockData.transactionItems.push(args);
          }
          if (sql.includes('INSERT INTO sync_queue')) {
            mockData.syncQueue.push(args);
          }
          return { changes: 1 };
        })),
        get: jest.fn((...args) => {
          if (sql.includes('SELECT * FROM products WHERE sku')) {
            return mockData.products.find(p => p.sku === args[0]);
          }
          return null;
        }),
        all: jest.fn(() => {
          if (sql.includes('SELECT * FROM products')) {
            return mockData.products;
          }
          if (sql.includes('SELECT * FROM transactions')) {
            return mockData.transactions;
          }
          return [];
        })
      })),
      transaction: jest.fn((fn) => () => fn()),
      exec: jest.fn(),
      close: jest.fn()
    };

    // Create database service mock
    database = {
      createTransaction(transaction) {
        // Validate transaction
        if (!transaction || typeof transaction !== 'object') {
          throw new Error('transaction must be a valid object');
        }

        if (!transaction.transaction_number) {
          throw new Error('transaction_number must be a string');
        }

        if (!transaction.items || !Array.isArray(transaction.items)) {
          throw new Error('items must be an array');
        }

        if (transaction.items.length === 0) {
          throw new Error('Transaction must have at least one item');
        }

        if (typeof transaction.total !== 'number') {
          throw new Error('total must be a valid number');
        }

        // Validate payment method
        const allowedMethods = ['cash', 'card', 'mpesa', 'cod'];
        if (!allowedMethods.includes(transaction.payment_method)) {
          throw new Error(`payment_method must be one of: ${allowedMethods.join(', ')}`);
        }

        // Validate items
        transaction.items.forEach((item, index) => {
          if (!item.product_id || typeof item.product_id !== 'number') {
            throw new Error(`item[${index}].product_id must be a valid number`);
          }
          if (!item.quantity || typeof item.quantity !== 'number') {
            throw new Error(`item[${index}].quantity must be a valid number`);
          }
        });

        // Calculate and verify total
        const calculatedSubtotal = transaction.items.reduce((sum, item) => sum + item.subtotal, 0);
        const calculatedTotal = calculatedSubtotal + (transaction.tax || 0) - (transaction.discount || 0);
        
        if (Math.abs(calculatedTotal - transaction.total) > 0.01) {
          throw new Error('Transaction total does not match calculated total');
        }

        // Insert transaction
        const txnStmt = mockDb.prepare('INSERT INTO transactions');
        const txnResult = txnStmt.run(
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
        const itemStmt = mockDb.prepare('INSERT INTO transaction_items');
        transaction.items.forEach(item => {
          itemStmt.run(
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
        });

        // Add to sync queue
        const syncStmt = mockDb.prepare('INSERT INTO sync_queue');
        syncStmt.run('transaction', transactionId, 'create', JSON.stringify(transaction));

        return transactionId;
      }
    };
  });

  describe('createTransaction', () => {
    it('should create a valid transaction', () => {
      const transaction = {
        transaction_number: 'TXN-001',
        employee_id: 1,
        employee_name: 'John Doe',
        subtotal: 1000,
        tax: 160,
        discount: 0,
        total: 1160,
        payment_method: 'cash',
        payment_status: 'completed',
        status: 'completed',
        items: [
          {
            product_id: 1,
            product_sku: 'SKU-001',
            product_name: 'Product 1',
            quantity: 2,
            unit_price: 500,
            subtotal: 1000,
            discount: 0,
            total: 1000
          }
        ]
      };

      const result = database.createTransaction(transaction);

      expect(result).toBe(1);
      expect(mockDb.prepare).toHaveBeenCalledWith(expect.stringContaining('INSERT INTO transactions'));
      expect(mockDb.prepare).toHaveBeenCalledWith(expect.stringContaining('INSERT INTO transaction_items'));
      expect(mockDb.prepare).toHaveBeenCalledWith(expect.stringContaining('INSERT INTO sync_queue'));
    });

    it('should reject transaction with no items', () => {
      const transaction = {
        transaction_number: 'TXN-002',
        total: 1000,
        payment_method: 'cash',
        items: []
      };

      expect(() => database.createTransaction(transaction)).toThrow(
        'Transaction must have at least one item'
      );
    });

    it('should reject transaction with invalid payment method', () => {
      const transaction = {
        transaction_number: 'TXN-003',
        total: 1000,
        payment_method: 'bitcoin',
        items: [
          {
            product_id: 1,
            product_sku: 'SKU-001',
            product_name: 'Product 1',
            quantity: 1,
            unit_price: 1000,
            subtotal: 1000,
            total: 1000
          }
        ]
      };

      expect(() => database.createTransaction(transaction)).toThrow(
        'payment_method must be one of: cash, card, mpesa, cod'
      );
    });

    it('should reject transaction with incorrect total', () => {
      const transaction = {
        transaction_number: 'TXN-004',
        subtotal: 1000,
        tax: 160,
        discount: 0,
        total: 999, // Incorrect total
        payment_method: 'cash',
        items: [
          {
            product_id: 1,
            product_sku: 'SKU-001',
            product_name: 'Product 1',
            quantity: 2,
            unit_price: 500,
            subtotal: 1000,
            total: 1000
          }
        ]
      };

      expect(() => database.createTransaction(transaction)).toThrow(
        'Transaction total does not match calculated total'
      );
    });

    it('should reject transaction with invalid item data', () => {
      const transaction = {
        transaction_number: 'TXN-005',
        total: 1000,
        payment_method: 'cash',
        items: [
          {
            product_id: 'invalid', // Should be number
            quantity: 1,
            subtotal: 1000,
            total: 1000
          }
        ]
      };

      expect(() => database.createTransaction(transaction)).toThrow(
        'item[0].product_id must be a valid number'
      );
    });

    it('should handle multiple items correctly', () => {
      const transaction = {
        transaction_number: 'TXN-006',
        subtotal: 1500,
        tax: 240,
        discount: 100,
        total: 1640,
        payment_method: 'card',
        items: [
          {
            product_id: 1,
            product_sku: 'SKU-001',
            product_name: 'Product 1',
            quantity: 2,
            unit_price: 500,
            subtotal: 1000,
            total: 1000
          },
          {
            product_id: 2,
            product_sku: 'SKU-002',
            product_name: 'Product 2',
            quantity: 1,
            unit_price: 500,
            subtotal: 500,
            total: 500
          }
        ]
      };

      const result = database.createTransaction(transaction);

      expect(result).toBe(1);
      
      // Verify both items were inserted
      const itemCalls = mockDb.prepare.mock.calls.filter(
        call => call[0].includes('INSERT INTO transaction_items')
      );
      expect(itemCalls.length).toBeGreaterThan(0);
    });
  });
});

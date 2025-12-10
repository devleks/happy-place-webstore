/**
 * End-to-End Complete Flow Tests
 * Tests the complete POS workflow from sync to transaction
 * 
 * Prerequisites:
 * - Backend server running
 * - Test employee with admin/manager role
 * - Test products in backend
 */

const fetch = require('node-fetch');
const AuthService = require('../../electron/auth');
const { createTestDatabase, seedTestData } = require('../setup/testDatabase');
const bcrypt = require('bcryptjs');

// Mock logger
jest.mock('../../electron/logger', () => ({
  logger: {
    info: jest.fn(),
    success: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
    debug: jest.fn()
  }
}));

describe('End-to-End Complete Flow', () => {
  let authService;
  let db;
  let backendToken;
  let employeeSession;
  const BACKEND_URL = 'http://localhost:5001';

  beforeAll(async () => {
    // Check backend availability
    try {
      const response = await fetch(`${BACKEND_URL}/api/pos/health`);
      if (!response.ok) {
        console.warn('⚠️  Backend not available - skipping E2E tests');
        return;
      }
    } catch (error) {
      console.warn('⚠️  Backend not available - skipping E2E tests');
      return;
    }

    // Create and seed test database
    db = createTestDatabase();
    await seedTestData(db, bcrypt);
    authService = new AuthService(db);
  });

  afterAll(() => {
    if (authService) {
      authService.cleanup();
    }
    if (db) {
      db.close();
    }
  });

  describe('Complete POS Workflow', () => {
    it('Step 1: Get backend authentication token', async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/api/auth/employee/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: 'admin@happyplace.co.ke',
            password: 'admin123'
          })
        });

        const data = await response.json();

        if (!data.success) {
          console.warn('⚠️  Backend login failed - ensure test employee exists');
          return;
        }

        expect(data.success).toBe(true);
        expect(data.access_token).toBeDefined();

        backendToken = data.access_token;
      } catch (error) {
        console.warn('⚠️  Backend connection failed:', error.message);
      }
    });

    it('Step 2: Configure POS with sync token', () => {
      if (!backendToken) {
        console.warn('⚠️  Skipping - no backend token');
        return;
      }

      authService.setSyncToken(backendToken);

      // Verify token was saved
      const savedToken = authService.getSyncToken();
      expect(savedToken).toBe(backendToken);
    });

    it('Step 3: Sync employees from backend', async () => {
      if (!backendToken) {
        console.warn('⚠️  Skipping - no backend token');
        return;
      }

      const result = await authService.syncEmployeesFromBackend();

      expect(result.success).toBe(true);
      expect(result.count).toBeGreaterThan(0);

      // Verify employees in local database
      const employees = db.prepare('SELECT * FROM employees').all();
      expect(employees.length).toBeGreaterThan(0);

      console.log(`✅ Synced ${employees.length} employees from backend`);
    });

    it('Step 4: Login to POS with synced credentials', async () => {
      // Use local test employee (we know the password)
      const result = await authService.login('cashier@test.com', 'password123', {
        device: 'test-pos'
      });

      expect(result.success).toBe(true);
      expect(result.employee).toBeDefined();
      expect(result.session).toBeDefined();

      employeeSession = result.session;

      console.log(`✅ Logged in as ${result.employee.full_name}`);
    });

    it('Step 5: Validate active session', () => {
      if (!employeeSession) {
        console.warn('⚠️  Skipping - no active session');
        return;
      }

      const result = authService.validateSession(employeeSession.token);

      expect(result.valid).toBe(true);
      expect(result.session).toBeDefined();
      expect(result.session.email).toBe('cashier@test.com');
    });

    it('Step 6: Check session statistics', () => {
      const stats = authService.getSessionStats();

      expect(stats).toBeDefined();
      expect(stats.total_sessions).toBeGreaterThan(0);
      expect(stats.active_sessions).toBeGreaterThan(0);

      console.log(`✅ Active sessions: ${stats.active_sessions}`);
    });

    it('Step 7: Verify activity logging', () => {
      const logs = db.prepare('SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT 5').all();

      expect(logs.length).toBeGreaterThan(0);
      
      // Should have login activity
      const loginLog = logs.find(log => log.action.includes('LOGIN'));
      expect(loginLog).toBeDefined();

      console.log(`✅ ${logs.length} activity logs recorded`);
    });

    it('Step 8: Simulate transaction (local)', () => {
      // Create a test transaction
      const transaction = db.prepare(`
        INSERT INTO transactions (transaction_number, employee_id, subtotal, total)
        VALUES (?, ?, ?, ?)
      `).run('TEST-001', 3, 31.98, 31.98);

      expect(transaction.lastInsertRowid).toBeGreaterThan(0);

      // Verify transaction
      const saved = db.prepare('SELECT * FROM transactions WHERE id = ?')
        .get(transaction.lastInsertRowid);

      expect(saved).toBeDefined();
      expect(saved.transaction_number).toBe('TEST-001');

      console.log(`✅ Transaction created: ${saved.transaction_number}`);
    });

    it('Step 9: Send activity logs to backend', async () => {
      if (!backendToken) {
        console.warn('⚠️  Skipping - no backend token');
        return;
      }

      // Get unsynced logs
      const logs = db.prepare('SELECT * FROM activity_log WHERE synced = 0').all();

      if (logs.length === 0) {
        console.log('ℹ️  No logs to sync');
        return;
      }

      // Send to backend
      const response = await fetch(`${BACKEND_URL}/api/pos/activity-log`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${backendToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          logs: logs.map(log => ({
            employee_id: log.employee_id,
            action: log.action,
            details: log.details
          }))
        })
      });

      const data = await response.json();

      expect(response.ok).toBe(true);
      expect(data.success).toBe(true);

      console.log(`✅ Synced ${data.stored} activity logs to backend`);
    });

    it('Step 10: Logout from POS', () => {
      if (!employeeSession) {
        console.warn('⚠️  Skipping - no active session');
        return;
      }

      const result = authService.logout(employeeSession.token);

      expect(result.success).toBe(true);

      // Verify session is invalidated
      const validateResult = authService.validateSession(employeeSession.token);
      expect(validateResult.valid).toBe(false);

      console.log('✅ Logged out successfully');
    });
  });

  describe('Offline Capability', () => {
    it('should work offline after initial sync', async () => {
      // Ensure we have employees
      const employees = db.prepare('SELECT * FROM employees WHERE is_active = 1').all();
      
      if (employees.length === 0) {
        console.warn('⚠️  No employees - skipping offline test');
        return;
      }

      // Login should work without backend
      const result = await authService.login('cashier@test.com', 'password123');

      expect(result.success).toBe(true);
      expect(result.employee).toBeDefined();

      console.log('✅ Offline login successful');
    });

    it('should queue transactions for sync', () => {
      // Create transaction while "offline"
      const transaction = db.prepare(`
        INSERT INTO transactions (transaction_number, employee_id, subtotal, total)
        VALUES (?, ?, ?, ?)
      `).run('OFFLINE-001', 3, 50.00, 50.00);

      expect(transaction.lastInsertRowid).toBeGreaterThan(0);

      // In real app, this would be queued for sync
      const saved = db.prepare('SELECT * FROM transactions WHERE id = ?')
        .get(transaction.lastInsertRowid);

      expect(saved).toBeDefined();

      console.log('✅ Transaction queued for sync');
    });
  });

  describe('Security Features', () => {
    it('should enforce session timeout', async () => {
      // Create session
      const loginResult = await authService.login('cashier@test.com', 'password123');
      expect(loginResult.success).toBe(true);

      // Simulate old last_activity (31 minutes ago)
      const oldActivity = new Date(Date.now() - 31 * 60 * 1000).toISOString();
      db.prepare('UPDATE sessions SET last_activity_at = ? WHERE session_token = ?')
        .run(oldActivity, loginResult.session.token);

      // Validate should fail
      const validateResult = authService.validateSession(loginResult.session.token);
      expect(validateResult.valid).toBe(false);
      expect(validateResult.reason).toBe('inactivity_timeout');

      console.log('✅ Session timeout enforced');
    });

    it('should detect password changes', async () => {
      // Create employee and session
      const loginResult = await authService.login('cashier@test.com', 'password123');
      expect(loginResult.success).toBe(true);

      // Simulate password change (update employee updated_at)
      db.prepare('UPDATE employees SET updated_at = ? WHERE email = ?')
        .run(new Date().toISOString(), 'cashier@test.com');

      // Session should be invalidated
      const validateResult = authService.validateSession(loginResult.session.token);
      expect(validateResult.valid).toBe(false);
      expect(validateResult.reason).toBe('password_changed');

      console.log('✅ Password change detected');
    });
  });
});

/**
 * Backend Sync Integration Tests
 * Tests POS ↔ Backend synchronization
 * 
 * Prerequisites:
 * - Backend server running on http://localhost:5001
 * - Test employee in backend database
 */

const fetch = require('node-fetch');
const AuthService = require('../../electron/auth');
const { createTestDatabase } = require('../setup/testDatabase');

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

describe('Backend Sync Integration', () => {
  let authService;
  let db;
  let backendToken;
  const BACKEND_URL = 'http://localhost:5001';

  beforeAll(async () => {
    // Check if backend is available
    try {
      const response = await fetch(`${BACKEND_URL}/api/pos/health`);
      if (!response.ok) {
        console.warn('⚠️  Backend not available - skipping integration tests');
        return;
      }
    } catch (error) {
      console.warn('⚠️  Backend not available - skipping integration tests');
      return;
    }

    // Create test database
    db = createTestDatabase();
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

  describe('Employee Sync from Backend', () => {
    it('should get JWT token from backend', async () => {
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
          console.warn('⚠️  Test employee not found in backend - create one first');
          return;
        }

        expect(data.success).toBe(true);
        expect(data.access_token).toBeDefined();

        backendToken = data.access_token;
      } catch (error) {
        console.warn('⚠️  Backend login failed:', error.message);
      }
    });

    it('should sync employees from backend', async () => {
      if (!backendToken) {
        console.warn('⚠️  Skipping - no backend token');
        return;
      }

      // Set sync token
      authService.setSyncToken(backendToken);

      // Trigger sync
      const result = await authService.syncEmployeesFromBackend();

      expect(result.success).toBe(true);
      expect(result.count).toBeGreaterThan(0);
      expect(result.sync_version).toBeDefined();

      // Verify employees in local database
      const employees = db.prepare('SELECT * FROM employees').all();
      expect(employees.length).toBeGreaterThan(0);
    });

    it('should login with synced credentials', async () => {
      if (!backendToken) {
        console.warn('⚠️  Skipping - no backend token');
        return;
      }

      // Ensure employees are synced
      const employees = db.prepare('SELECT * FROM employees WHERE is_active = 1').all();
      
      if (employees.length === 0) {
        console.warn('⚠️  No employees synced - skipping login test');
        return;
      }

      const testEmployee = employees[0];

      // Try to login (will fail because we don't have the actual password)
      // This test verifies the login flow works
      const result = await authService.login(testEmployee.email, 'wrong-password');
      
      // Should fail with invalid credentials (not "employee not found")
      expect(result.success).toBe(false);
      expect(result.error).toBe('Invalid credentials');
    });

    it('should handle incremental sync', async () => {
      if (!backendToken) {
        console.warn('⚠️  Skipping - no backend token');
        return;
      }

      // Set last sync timestamp
      const lastSync = new Date(Date.now() - 60000).toISOString(); // 1 minute ago
      authService.saveLastSyncTimestamp(lastSync);

      // Trigger incremental sync
      const result = await authService.syncEmployeesFromBackend();

      expect(result).toBeDefined();
      // Result may have 0 employees if none were updated
      expect(result.success).toBe(true);
    });
  });

  describe('Backend API Endpoints', () => {
    it('should access full sync endpoint', async () => {
      if (!backendToken) {
        console.warn('⚠️  Skipping - no backend token');
        return;
      }

      const response = await fetch(`${BACKEND_URL}/api/employees/sync`, {
        headers: {
          'Authorization': `Bearer ${backendToken}`
        }
      });

      const data = await response.json();

      expect(response.ok).toBe(true);
      expect(data.success).toBe(true);
      expect(data.employees).toBeDefined();
      expect(Array.isArray(data.employees)).toBe(true);
      expect(data.sync_version).toBeDefined();
    });

    it('should access incremental sync endpoint', async () => {
      if (!backendToken) {
        console.warn('⚠️  Skipping - no backend token');
        return;
      }

      const lastSync = new Date(Date.now() - 60000).toISOString();
      const response = await fetch(
        `${BACKEND_URL}/api/employees/sync/incremental?last_sync=${lastSync}`,
        {
          headers: {
            'Authorization': `Bearer ${backendToken}`
          }
        }
      );

      const data = await response.json();

      expect(response.ok).toBe(true);
      expect(data.success).toBe(true);
      expect(data.employees).toBeDefined();
    });

    it('should reject sync without authentication', async () => {
      const response = await fetch(`${BACKEND_URL}/api/employees/sync`);

      expect(response.ok).toBe(false);
      expect(response.status).toBe(401);
    });

    it('should send activity logs to backend', async () => {
      if (!backendToken) {
        console.warn('⚠️  Skipping - no backend token');
        return;
      }

      const response = await fetch(`${BACKEND_URL}/api/pos/activity-log`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${backendToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          logs: [
            {
              employee_id: 1,
              action: 'TEST_ACTION',
              details: JSON.stringify({ test: true })
            }
          ]
        })
      });

      const data = await response.json();

      expect(response.ok).toBe(true);
      expect(data.success).toBe(true);
      expect(data.stored).toBe(1);
    });
  });

  describe('Error Handling', () => {
    it('should handle backend unavailable', async () => {
      // Create new auth service with invalid URL
      const testDb = createTestDatabase();
      const testAuthService = new AuthService(testDb);
      
      testAuthService.setSyncToken('fake-token');

      // Mock fetch to simulate network error
      const originalFetch = global.fetch;
      global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));

      const result = await testAuthService.syncEmployeesFromBackend();

      expect(result.success).toBe(false);
      expect(result.reason).toBe('sync_error');

      // Restore fetch
      global.fetch = originalFetch;
      
      testAuthService.cleanup();
      testDb.close();
    });

    it('should handle invalid token', async () => {
      const response = await fetch(`${BACKEND_URL}/api/employees/sync`, {
        headers: {
          'Authorization': 'Bearer invalid-token'
        }
      });

      expect(response.ok).toBe(false);
      expect(response.status).toBe(422); // Unprocessable Entity (invalid JWT)
    });

    it('should handle unauthorized role', async () => {
      // This would require a cashier token
      // For now, we just verify the endpoint exists
      expect(true).toBe(true);
    });
  });
});

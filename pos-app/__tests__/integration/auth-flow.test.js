/**
 * Authentication Flow Integration Tests
 * Tests the complete authentication flow from login to logout
 */

const AuthService = require('../../electron/auth');
const Database = require('better-sqlite3');
const bcrypt = require('bcryptjs');
const path = require('path');
const fs = require('fs');

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

describe('Authentication Flow Integration', () => {
  let authService;
  let db;
  let testDbPath;

  beforeAll(() => {
    // Create test database
    testDbPath = path.join(__dirname, 'test-integration.db');
    db = new Database(testDbPath);

    // Create tables
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
        device_info TEXT,
        FOREIGN KEY (employee_id) REFERENCES employees(id)
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
    `);

    authService = new AuthService(db);
  });

  afterAll(() => {
    if (authService) {
      authService.cleanup();
    }
    if (db) {
      db.close();
    }
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
    }
  });

  describe('Complete Authentication Flow', () => {
    it('should complete full login-validate-logout cycle', async () => {
      // 1. Create employee
      const passwordHash = await bcrypt.hash('password123', 10);
      db.prepare(`
        INSERT INTO employees (id, backend_id, email, full_name, role, password_hash, is_active)
        VALUES (1, 1, 'cashier@example.com', 'Cashier User', 'cashier', ?, 1)
      `).run(passwordHash);

      // 2. Login
      const loginResult = await authService.login('cashier@example.com', 'password123', {
        platform: 'darwin',
        arch: 'x64'
      });

      expect(loginResult.success).toBe(true);
      expect(loginResult.employee).toBeDefined();
      expect(loginResult.session).toBeDefined();

      const sessionToken = loginResult.session.token;

      // 3. Validate session immediately
      const validateResult1 = authService.validateSession(sessionToken);
      expect(validateResult1.valid).toBe(true);
      expect(validateResult1.session.email).toBe('cashier@example.com');

      // 4. Simulate activity (wait a bit)
      await new Promise(resolve => setTimeout(resolve, 100));

      // 5. Validate session again
      const validateResult2 = authService.validateSession(sessionToken);
      expect(validateResult2.valid).toBe(true);

      // 6. Check activity log
      const activityLogs = db.prepare('SELECT * FROM activity_log ORDER BY timestamp DESC').all();
      expect(activityLogs.length).toBeGreaterThan(0);
      expect(activityLogs[0].action).toContain('LOGIN');

      // 7. Logout
      const logoutResult = authService.logout(sessionToken);
      expect(logoutResult.success).toBe(true);

      // 8. Validate session after logout (should fail)
      const validateResult3 = authService.validateSession(sessionToken);
      expect(validateResult3.valid).toBe(false);

      // 9. Check session is inactive
      const session = db.prepare('SELECT is_active FROM sessions WHERE session_token = ?')
        .get(sessionToken);
      expect(session.is_active).toBe(0);
    });

    it('should handle multiple concurrent sessions', async () => {
      // Create employee
      const passwordHash = await bcrypt.hash('password123', 10);
      db.prepare(`
        INSERT OR REPLACE INTO employees (id, backend_id, email, full_name, role, password_hash, is_active)
        VALUES (2, 2, 'manager@example.com', 'Manager User', 'manager', ?, 1)
      `).run(passwordHash);

      // Login from multiple devices
      const login1 = await authService.login('manager@example.com', 'password123', {
        device: 'POS-1'
      });
      const login2 = await authService.login('manager@example.com', 'password123', {
        device: 'POS-2'
      });

      expect(login1.success).toBe(true);
      expect(login2.success).toBe(true);
      expect(login1.session.token).not.toBe(login2.session.token);

      // Both sessions should be valid
      const validate1 = authService.validateSession(login1.session.token);
      const validate2 = authService.validateSession(login2.session.token);

      expect(validate1.valid).toBe(true);
      expect(validate2.valid).toBe(true);

      // Logout from one device
      authService.logout(login1.session.token);

      // First session invalid, second still valid
      const validate1After = authService.validateSession(login1.session.token);
      const validate2After = authService.validateSession(login2.session.token);

      expect(validate1After.valid).toBe(false);
      expect(validate2After.valid).toBe(true);
    });

    it('should handle employee deactivation', async () => {
      // Create and login employee
      const passwordHash = await bcrypt.hash('password123', 10);
      db.prepare(`
        INSERT OR REPLACE INTO employees (id, backend_id, email, full_name, role, password_hash, is_active)
        VALUES (3, 3, 'temp@example.com', 'Temp User', 'cashier', ?, 1)
      `).run(passwordHash);

      const loginResult = await authService.login('temp@example.com', 'password123');
      expect(loginResult.success).toBe(true);

      const sessionToken = loginResult.session.token;

      // Deactivate employee
      db.prepare('UPDATE employees SET is_active = 0 WHERE id = 3').run();

      // Session should now be invalid
      const validateResult = authService.validateSession(sessionToken);
      expect(validateResult.valid).toBe(false);
      expect(validateResult.reason).toBe('employee_deactivated');
    });

    it('should detect password changes', async () => {
      // Create and login employee
      const passwordHash = await bcrypt.hash('oldpassword', 10);
      db.prepare(`
        INSERT OR REPLACE INTO employees (id, backend_id, email, full_name, role, password_hash, is_active, updated_at)
        VALUES (4, 4, 'user@example.com', 'Regular User', 'cashier', ?, 1, ?)
      `).run(passwordHash, new Date(Date.now() - 60000).toISOString()); // 1 minute ago

      const loginResult = await authService.login('user@example.com', 'oldpassword');
      expect(loginResult.success).toBe(true);

      const sessionToken = loginResult.session.token;

      // Simulate password change
      const newPasswordHash = await bcrypt.hash('newpassword', 10);
      db.prepare('UPDATE employees SET password_hash = ?, updated_at = ? WHERE id = 4')
        .run(newPasswordHash, new Date().toISOString());

      // Session should be invalidated
      const validateResult = authService.validateSession(sessionToken);
      expect(validateResult.valid).toBe(false);
      expect(validateResult.reason).toBe('password_changed');

      // Old password should not work
      const loginOld = await authService.login('user@example.com', 'oldpassword');
      expect(loginOld.success).toBe(false);

      // New password should work
      const loginNew = await authService.login('user@example.com', 'newpassword');
      expect(loginNew.success).toBe(true);
    });
  });

  describe('Session Management', () => {
    it('should cleanup expired sessions automatically', async () => {
      // Create employee
      const passwordHash = await bcrypt.hash('password123', 10);
      db.prepare(`
        INSERT OR REPLACE INTO employees (id, backend_id, email, full_name, role, password_hash, is_active)
        VALUES (5, 5, 'cleanup@example.com', 'Cleanup User', 'cashier', ?, 1)
      `).run(passwordHash);

      // Create expired session manually
      const expiredDate = new Date(Date.now() - 9 * 60 * 60 * 1000);
      db.prepare(`
        INSERT INTO sessions (employee_id, session_token, started_at, last_activity_at, expires_at, is_active)
        VALUES (5, 'expired-session', ?, ?, ?, 1)
      `).run(expiredDate.toISOString(), expiredDate.toISOString(), expiredDate.toISOString());

      // Create active session
      const loginResult = await authService.login('cleanup@example.com', 'password123');
      expect(loginResult.success).toBe(true);

      // Run cleanup
      authService.cleanupExpiredSessions();

      // Check sessions
      const expiredSession = db.prepare('SELECT is_active FROM sessions WHERE session_token = ?')
        .get('expired-session');
      const activeSession = db.prepare('SELECT is_active FROM sessions WHERE session_token = ?')
        .get(loginResult.session.token);

      expect(expiredSession.is_active).toBe(0);
      expect(activeSession.is_active).toBe(1);
    });

    it('should track session statistics', async () => {
      // Create multiple employees and sessions
      for (let i = 6; i <= 8; i++) {
        const passwordHash = await bcrypt.hash('password123', 10);
        db.prepare(`
          INSERT OR REPLACE INTO employees (id, backend_id, email, full_name, role, password_hash, is_active)
          VALUES (?, ?, ?, ?, 'cashier', ?, 1)
        `).run(i, i, `user${i}@example.com`, `User ${i}`, passwordHash);

        await authService.login(`user${i}@example.com`, 'password123');
      }

      const stats = authService.getSessionStats();

      expect(stats.total_sessions).toBeGreaterThan(0);
      expect(stats.active_sessions).toBeGreaterThan(0);
      expect(stats.unique_employees).toBeGreaterThan(0);
    });
  });
});

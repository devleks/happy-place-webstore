/**
 * Auth Service Unit Tests
 * Tests authentication, session management, and employee sync
 */

const AuthService = require('../../electron/auth');
const bcrypt = require('bcryptjs');
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

// Mock fetch
global.fetch = jest.fn();

describe('AuthService', () => {
  let authService;
  let db;

  beforeEach(() => {
    // Create in-memory test database
    db = createTestDatabase();
    authService = new AuthService(db);
  });

  afterEach(() => {
    // Cleanup
    if (authService) {
      authService.cleanup();
    }
    if (db) {
      db.close();
    }
    jest.clearAllMocks();
  });


  describe('login', () => {
    it('should successfully login with valid credentials', async () => {
      // Create test employee
      const passwordHash = await bcrypt.hash('password123', 10);
      db.prepare(`
        INSERT INTO employees (id, backend_id, email, full_name, role, password_hash, is_active)
        VALUES (1, 1, 'test@example.com', 'Test User', 'cashier', ?, 1)
      `).run(passwordHash);

      // Attempt login
      const result = await authService.login('test@example.com', 'password123');

      expect(result.success).toBe(true);
      expect(result.employee).toBeDefined();
      expect(result.employee.email).toBe('test@example.com');
      expect(result.session).toBeDefined();
      expect(result.session.token).toBeDefined();
    });

    it('should fail login with invalid email', async () => {
      const result = await authService.login('nonexistent@example.com', 'password123');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Invalid credentials');
    });

    it('should fail login with invalid password', async () => {
      const passwordHash = await bcrypt.hash('password123', 10);
      db.prepare(`
        INSERT INTO employees (id, backend_id, email, full_name, role, password_hash, is_active)
        VALUES (1, 1, 'test@example.com', 'Test User', 'cashier', ?, 1)
      `).run(passwordHash);

      const result = await authService.login('test@example.com', 'wrongpassword');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Invalid credentials');
    });

    it('should fail login for inactive employee', async () => {
      const passwordHash = await bcrypt.hash('password123', 10);
      db.prepare(`
        INSERT INTO employees (id, backend_id, email, full_name, role, password_hash, is_active)
        VALUES (1, 1, 'test@example.com', 'Test User', 'cashier', ?, 0)
      `).run(passwordHash);

      const result = await authService.login('test@example.com', 'password123');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Invalid credentials');
    });
  });

  describe('validateSession', () => {
    it('should validate active session', async () => {
      // Create employee and session
      const passwordHash = await bcrypt.hash('password123', 10);
      db.prepare(`
        INSERT INTO employees (id, backend_id, email, full_name, role, password_hash, is_active)
        VALUES (1, 1, 'test@example.com', 'Test User', 'cashier', ?, 1)
      `).run(passwordHash);

      const session = authService.createSession(1, {});
      
      // Validate session
      const result = authService.validateSession(session.session_token);

      expect(result.valid).toBe(true);
      expect(result.session).toBeDefined();
      expect(result.session.email).toBe('test@example.com');
    });

    it('should invalidate expired session', async () => {
      // Create employee
      const passwordHash = await bcrypt.hash('password123', 10);
      db.prepare(`
        INSERT INTO employees (id, backend_id, email, full_name, role, password_hash, is_active)
        VALUES (1, 1, 'test@example.com', 'Test User', 'cashier', ?, 1)
      `).run(passwordHash);

      // Create expired session
      const now = new Date();
      const expiredDate = new Date(now.getTime() - 9 * 60 * 60 * 1000); // 9 hours ago
      
      db.prepare(`
        INSERT INTO sessions (employee_id, session_token, started_at, last_activity_at, expires_at, is_active)
        VALUES (1, 'expired-token', ?, ?, ?, 1)
      `).run(expiredDate.toISOString(), expiredDate.toISOString(), expiredDate.toISOString());

      const result = authService.validateSession('expired-token');

      expect(result.valid).toBe(false);
      expect(result.reason).toBe('session_expired');
    });

    it('should invalidate session after inactivity timeout', async () => {
      // Create employee
      const passwordHash = await bcrypt.hash('password123', 10);
      db.prepare(`
        INSERT INTO employees (id, backend_id, email, full_name, role, password_hash, is_active)
        VALUES (1, 1, 'test@example.com', 'Test User', 'cashier', ?, 1)
      `).run(passwordHash);

      // Create session with old last_activity
      const now = new Date();
      const inactiveDate = new Date(now.getTime() - 31 * 60 * 1000); // 31 minutes ago
      const expiresDate = new Date(now.getTime() + 7 * 60 * 60 * 1000); // 7 hours from now
      
      db.prepare(`
        INSERT INTO sessions (employee_id, session_token, started_at, last_activity_at, expires_at, is_active)
        VALUES (1, 'inactive-token', ?, ?, ?, 1)
      `).run(now.toISOString(), inactiveDate.toISOString(), expiresDate.toISOString());

      const result = authService.validateSession('inactive-token');

      expect(result.valid).toBe(false);
      expect(result.reason).toBe('inactivity_timeout');
    });

    it('should detect password change and invalidate session', async () => {
      // Create employee
      const passwordHash = await bcrypt.hash('password123', 10);
      db.prepare(`
        INSERT INTO employees (id, backend_id, email, full_name, role, password_hash, is_active, updated_at)
        VALUES (1, 1, 'test@example.com', 'Test User', 'cashier', ?, 1, ?)
      `).run(passwordHash, new Date().toISOString());

      // Create session with old started_at
      const oldDate = new Date(Date.now() - 60 * 60 * 1000); // 1 hour ago
      const expiresDate = new Date(Date.now() + 7 * 60 * 60 * 1000);
      
      db.prepare(`
        INSERT INTO sessions (employee_id, session_token, started_at, last_activity_at, expires_at, is_active)
        VALUES (1, 'old-session', ?, ?, ?, 1)
      `).run(oldDate.toISOString(), new Date().toISOString(), expiresDate.toISOString());

      const result = authService.validateSession('old-session');

      expect(result.valid).toBe(false);
      expect(result.reason).toBe('password_changed');
    });
  });

  describe('logout', () => {
    it('should successfully logout', async () => {
      // Create employee and session
      const passwordHash = await bcrypt.hash('password123', 10);
      db.prepare(`
        INSERT INTO employees (id, backend_id, email, full_name, role, password_hash, is_active)
        VALUES (1, 1, 'test@example.com', 'Test User', 'cashier', ?, 1)
      `).run(passwordHash);

      const session = authService.createSession(1, {});
      
      // Logout
      const result = authService.logout(session.session_token);

      expect(result.success).toBe(true);

      // Verify session is invalidated
      const sessionCheck = db.prepare('SELECT is_active FROM sessions WHERE session_token = ?')
        .get(session.session_token);
      expect(sessionCheck.is_active).toBe(0);
    });
  });

  describe('syncEmployeesFromBackend', () => {
    it('should sync employees successfully', async () => {
      // Set sync token
      authService.setSyncToken('test-token');

      // Mock fetch response
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          sync_version: '2025-12-11T00:00:00Z',
          employees: [
            {
              id: 1,
              email: 'admin@example.com',
              full_name: 'Admin User',
              role: 'admin',
              password_hash: await bcrypt.hash('admin123', 10),
              permissions: {},
              is_active: true,
              updated_at: '2025-12-11T00:00:00Z'
            }
          ]
        })
      });

      const result = await authService.syncEmployeesFromBackend();

      expect(result.success).toBe(true);
      expect(result.count).toBe(1);

      // Verify employee was inserted
      const employee = db.prepare('SELECT * FROM employees WHERE email = ?')
        .get('admin@example.com');
      expect(employee).toBeDefined();
      expect(employee.full_name).toBe('Admin User');
    });

    it('should fail sync without token', async () => {
      const result = await authService.syncEmployeesFromBackend();

      expect(result.success).toBe(false);
      expect(result.reason).toBe('no_token');
    });

    it('should handle sync errors gracefully', async () => {
      authService.setSyncToken('test-token');

      global.fetch.mockRejectedValueOnce(new Error('Network error'));

      const result = await authService.syncEmployeesFromBackend();

      expect(result.success).toBe(false);
      expect(result.reason).toBe('sync_error');
    });
  });

  describe('cleanupExpiredSessions', () => {
    it('should cleanup expired sessions', async () => {
      // Create employee
      const passwordHash = await bcrypt.hash('password123', 10);
      db.prepare(`
        INSERT INTO employees (id, backend_id, email, full_name, role, password_hash, is_active)
        VALUES (1, 1, 'test@example.com', 'Test User', 'cashier', ?, 1)
      `).run(passwordHash);

      // Create expired session
      const expiredDate = new Date(Date.now() - 9 * 60 * 60 * 1000);
      db.prepare(`
        INSERT INTO sessions (employee_id, session_token, started_at, last_activity_at, expires_at, is_active)
        VALUES (1, 'expired', ?, ?, ?, 1)
      `).run(expiredDate.toISOString(), expiredDate.toISOString(), expiredDate.toISOString());

      // Create active session
      const now = new Date();
      const futureDate = new Date(now.getTime() + 7 * 60 * 60 * 1000);
      db.prepare(`
        INSERT INTO sessions (employee_id, session_token, started_at, last_activity_at, expires_at, is_active)
        VALUES (1, 'active', ?, ?, ?, 1)
      `).run(now.toISOString(), now.toISOString(), futureDate.toISOString());

      // Cleanup
      authService.cleanupExpiredSessions();

      // Check sessions
      const expiredSession = db.prepare('SELECT is_active FROM sessions WHERE session_token = ?')
        .get('expired');
      const activeSession = db.prepare('SELECT is_active FROM sessions WHERE session_token = ?')
        .get('active');

      expect(expiredSession.is_active).toBe(0);
      expect(activeSession.is_active).toBe(1);
    });
  });

  describe('getSessionStats', () => {
    it('should return session statistics', async () => {
      // Create employee
      const passwordHash = await bcrypt.hash('password123', 10);
      db.prepare(`
        INSERT INTO employees (id, backend_id, email, full_name, role, password_hash, is_active)
        VALUES (1, 1, 'test@example.com', 'Test User', 'cashier', ?, 1)
      `).run(passwordHash);

      // Create sessions
      const now = new Date();
      const futureDate = new Date(now.getTime() + 7 * 60 * 60 * 1000);
      
      db.prepare(`
        INSERT INTO sessions (employee_id, session_token, started_at, last_activity_at, expires_at, is_active)
        VALUES (1, 'session1', ?, ?, ?, 1)
      `).run(now.toISOString(), now.toISOString(), futureDate.toISOString());

      db.prepare(`
        INSERT INTO sessions (employee_id, session_token, started_at, last_activity_at, expires_at, is_active)
        VALUES (1, 'session2', ?, ?, ?, 0)
      `).run(now.toISOString(), now.toISOString(), futureDate.toISOString());

      const stats = authService.getSessionStats();

      expect(stats.total_sessions).toBe(2);
      expect(stats.active_sessions).toBe(1);
      expect(stats.unique_employees).toBe(1);
    });
  });
});

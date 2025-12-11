/**
 * Authentication Service
 * Secure hybrid auth with automatic sync and session management
 * Per ELECTRON_WINDSURF_RULES.md Section 1 (Security)
 */

const bcrypt = require('bcryptjs');
const crypto = require('crypto');
const { logger } = require('./logger');
const fetch = require('node-fetch');

// Session configuration
const SESSION_CONFIG = {
  TIMEOUT_MINUTES: 30,        // Auto-logout after 30 min inactivity
  MAX_DURATION_HOURS: 8,      // Force re-login after 8 hours
  REFRESH_INTERVAL_MS: 60000, // Check sessions every minute
  SYNC_INTERVAL_MS: 300000    // Sync employees every 5 minutes
};

class AuthService {
  constructor(db) {
    this.db = db;
    this.sessionCheckInterval = null;
    this.syncInterval = null;
  }

  /**
   * Initialize auth service with automatic timers
   */
  initialize() {
    logger.info('Initializing auth service');
    
    // Start session monitoring
    this.startSessionMonitoring();
    
    // Start auto-sync
    this.startAutoSync();
    
    // Clean up old sessions on startup
    this.cleanupExpiredSessions();
    
    logger.success('Auth service initialized');
  }

  /**
   * Validate employee credentials and create session
   */
  async login(email, password, deviceInfo = {}) {
    try {
      // 1. Validate credentials
      const employee = this.db.prepare(`
        SELECT * FROM employees 
        WHERE email = ? AND is_active = 1
      `).get(email);

      if (!employee) {
        logger.warn('Login failed: employee not found', { email });
        this.logActivity(null, null, 'LOGIN_FAILED', { email, reason: 'not_found' });
        return { success: false, error: 'Invalid credentials' };
      }

      // 2. Verify password
      const isValid = await bcrypt.compare(password, employee.password_hash);
      
      if (!isValid) {
        logger.warn('Login failed: invalid password', { email });
        this.logActivity(employee.id, null, 'LOGIN_FAILED', { reason: 'invalid_password' });
        return { success: false, error: 'Invalid credentials' };
      }

      // 3. Create session
      const session = this.createSession(employee.id, deviceInfo);
      
      if (!session) {
        return { success: false, error: 'Failed to create session' };
      }

      // 4. Log successful login
      this.logActivity(employee.id, session.id, 'LOGIN_SUCCESS', { email });
      
      logger.success('Employee authenticated', { 
        email, 
        role: employee.role,
        session_id: session.id
      });

      // 5. Return employee data without password
      const { password_hash, ...employeeData } = employee;
      
      return {
        success: true,
        employee: employeeData,
        session: {
          token: session.session_token,
          expires_at: session.expires_at
        }
      };
    } catch (error) {
      logger.error('Login error', error);
      return { success: false, error: 'Login failed' };
    }
  }

  /**
   * Create new session
   */
  createSession(employeeId, deviceInfo) {
    try {
      const now = new Date();
      const expiresAt = new Date(now.getTime() + SESSION_CONFIG.MAX_DURATION_HOURS * 60 * 60 * 1000);
      const sessionToken = crypto.randomBytes(32).toString('hex');

      const result = this.db.prepare(`
        INSERT INTO sessions (
          employee_id, session_token, started_at, 
          last_activity_at, expires_at, device_info
        ) VALUES (?, ?, ?, ?, ?, ?)
      `).run(
        employeeId,
        sessionToken,
        now.toISOString(),
        now.toISOString(),
        expiresAt.toISOString(),
        JSON.stringify(deviceInfo)
      );

      return {
        id: result.lastInsertRowid,
        session_token: sessionToken,
        expires_at: expiresAt.toISOString()
      };
    } catch (error) {
      logger.error('Session creation error', error);
      return null;
    }
  }

  /**
   * Validate session and update activity
   */
  validateSession(sessionToken) {
    try {
      const now = new Date();
      
      // Get session
      const session = this.db.prepare(`
        SELECT s.*, e.email, e.full_name, e.role, e.is_active as employee_active, e.updated_at as employee_updated_at
        FROM sessions s
        JOIN employees e ON s.employee_id = e.id
        WHERE s.session_token = ? AND s.is_active = 1
      `).get(sessionToken);

      if (!session) {
        logger.warn('Session validation failed: not found');
        return { valid: false, reason: 'session_not_found' };
      }

      // Check if employee is still active
      if (!session.employee_active) {
        this.invalidateSession(session.id);
        logger.warn('Session invalidated: employee deactivated');
        return { valid: false, reason: 'employee_deactivated' };
      }

      // Check if password was changed after session creation
      const sessionStarted = new Date(session.started_at);
      const employeeUpdated = new Date(session.employee_updated_at);
      
      if (employeeUpdated > sessionStarted) {
        this.invalidateSession(session.id);
        this.logActivity(session.employee_id, session.id, 'SESSION_INVALIDATED_PASSWORD_CHANGE', {});
        return { 
          valid: false, 
          reason: 'password_changed',
          message: 'Your password was changed. Please login again.'
        };
      }

      // Check expiration
      const expiresAt = new Date(session.expires_at);
      if (now > expiresAt) {
        this.invalidateSession(session.id);
        logger.warn('Session expired', { session_id: session.id });
        return { valid: false, reason: 'session_expired' };
      }

      // Check inactivity timeout
      const lastActivity = new Date(session.last_activity_at);
      const inactiveMinutes = (now - lastActivity) / (1000 * 60);
      
      if (inactiveMinutes > SESSION_CONFIG.TIMEOUT_MINUTES) {
        this.invalidateSession(session.id);
        logger.warn('Session timed out due to inactivity', { 
          session_id: session.id,
          inactive_minutes: inactiveMinutes
        });
        return { valid: false, reason: 'inactivity_timeout' };
      }

      // Update last activity
      this.updateSessionActivity(session.id);

      return {
        valid: true,
        session: {
          id: session.id,
          employee_id: session.employee_id,
          email: session.email,
          full_name: session.full_name,
          role: session.role
        }
      };
    } catch (error) {
      logger.error('Session validation error', error);
      return { valid: false, reason: 'validation_error' };
    }
  }

  /**
   * Update session activity timestamp
   */
  updateSessionActivity(sessionId) {
    try {
      this.db.prepare(`
        UPDATE sessions 
        SET last_activity_at = ? 
        WHERE id = ?
      `).run(new Date().toISOString(), sessionId);
    } catch (error) {
      logger.error('Failed to update session activity', error);
    }
  }

  /**
   * Invalidate session (logout)
   */
  invalidateSession(sessionId) {
    try {
      this.db.prepare(`
        UPDATE sessions 
        SET is_active = 0 
        WHERE id = ?
      `).run(sessionId);
      
      this.logActivity(null, sessionId, 'SESSION_INVALIDATED', {});
      logger.info('Session invalidated', { session_id: sessionId });
    } catch (error) {
      logger.error('Session invalidation error', error);
    }
  }

  /**
   * Logout - invalidate session and log activity
   */
  logout(sessionToken) {
    try {
      const session = this.db.prepare(`
        SELECT id, employee_id FROM sessions 
        WHERE session_token = ?
      `).get(sessionToken);

      if (session) {
        this.invalidateSession(session.id);
        this.logActivity(session.employee_id, session.id, 'LOGOUT', {});
        logger.info('Employee logged out', { session_id: session.id });
        return { success: true };
      }

      return { success: false, error: 'Session not found' };
    } catch (error) {
      logger.error('Logout error', error);
      return { success: false, error: 'Logout failed' };
    }
  }

  /**
   * Start automatic session monitoring
   */
  startSessionMonitoring() {
    if (this.sessionCheckInterval) {
      clearInterval(this.sessionCheckInterval);
    }

    this.sessionCheckInterval = setInterval(() => {
      this.cleanupExpiredSessions();
    }, SESSION_CONFIG.REFRESH_INTERVAL_MS);

    logger.info('Session monitoring started');
  }

  /**
   * Clean up expired sessions
   */
  cleanupExpiredSessions() {
    try {
      const now = new Date().toISOString();
      
      // Expire sessions past max duration
      const expiredByTime = this.db.prepare(`
        UPDATE sessions 
        SET is_active = 0 
        WHERE is_active = 1 AND expires_at < ?
      `).run(now);

      // Expire sessions with inactivity timeout
      const timeoutThreshold = new Date(
        Date.now() - SESSION_CONFIG.TIMEOUT_MINUTES * 60 * 1000
      ).toISOString();

      const expiredByInactivity = this.db.prepare(`
        UPDATE sessions 
        SET is_active = 0 
        WHERE is_active = 1 AND last_activity_at < ?
      `).run(timeoutThreshold);

      const totalExpired = expiredByTime.changes + expiredByInactivity.changes;

      if (totalExpired > 0) {
        logger.info(`Cleaned up ${totalExpired} expired sessions`);
      }
    } catch (error) {
      logger.error('Session cleanup error', error);
    }
  }

  /**
   * Start automatic employee sync
   */
  startAutoSync() {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
    }

    // Initial sync
    this.syncEmployeesFromBackend();

    // Periodic sync
    this.syncInterval = setInterval(() => {
      this.syncEmployeesFromBackend();
    }, SESSION_CONFIG.SYNC_INTERVAL_MS);

    logger.info('Auto-sync started');
  }

  /**
   * Sync employees from backend (ONE-WAY SYNC)
   */
  async syncEmployeesFromBackend() {
    try {
      logger.info('Starting employee sync from backend');

      // Get last sync timestamp for incremental sync
      const lastSync = this.getLastSyncTimestamp();
      
      // Build sync URL (use 127.0.0.1 instead of localhost to avoid IPv6 issues)
      const syncUrl = lastSync 
        ? `http://127.0.0.1:5001/api/employees/sync/incremental?last_sync=${lastSync}`
        : 'http://127.0.0.1:5001/api/employees/sync';

      // Get sync token
      const syncToken = this.getSyncToken();
      
      if (!syncToken) {
        logger.debug('No sync token available - skipping sync');
        return { success: false, reason: 'no_token' };
      }

      // Fetch employees from backend
      const response = await fetch(syncUrl, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${syncToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Sync failed: ${response.status}`);
      }

      const data = await response.json();

      if (data.success && data.employees) {
        // Update local database
        await this.updateEmployees(data.employees);
        
        // Save sync version
        this.saveLastSyncTimestamp(data.sync_version);
        
        logger.success(`Synced ${data.employees.length} employees from backend`);
        
        return { 
          success: true, 
          count: data.employees.length,
          sync_version: data.sync_version
        };
      }

      return { success: false, reason: 'no_data' };
    } catch (error) {
      logger.error('Employee sync error', error);
      return { success: false, reason: 'sync_error', error: error.message };
    }
  }

  /**
   * Update employees in local database
   */
  async updateEmployees(employees) {
    try {
      const stmt = this.db.prepare(`
        INSERT OR REPLACE INTO employees 
        (backend_id, email, full_name, role, password_hash, permissions, 
         is_active, last_synced_at, sync_version, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `);

      const syncTime = new Date().toISOString();

      for (const emp of employees) {
        stmt.run(
          emp.id,
          emp.email,
          emp.full_name,
          emp.role,
          emp.password_hash,
          JSON.stringify(emp.permissions || {}),
          emp.is_active ? 1 : 0,
          syncTime,
          emp.version || 1,
          syncTime
        );
      }

      // Invalidate sessions for deactivated employees
      this.invalidateDeactivatedEmployeeSessions();
    } catch (error) {
      logger.error('Employee update error', error);
      throw error;
    }
  }

  /**
   * Invalidate sessions for deactivated employees
   */
  invalidateDeactivatedEmployeeSessions() {
    try {
      const result = this.db.prepare(`
        UPDATE sessions 
        SET is_active = 0 
        WHERE is_active = 1 
        AND employee_id IN (
          SELECT id FROM employees WHERE is_active = 0
        )
      `).run();

      if (result.changes > 0) {
        logger.warn(`Invalidated ${result.changes} sessions for deactivated employees`);
      }
    } catch (error) {
      logger.error('Failed to invalidate deactivated employee sessions', error);
    }
  }

  /**
   * Get last sync timestamp
   */
  getLastSyncTimestamp() {
    try {
      const result = this.db.prepare(`
        SELECT value FROM sync_metadata 
        WHERE key = 'last_employee_sync'
      `).get();
      
      return result ? result.value : null;
    } catch (error) {
      return null;
    }
  }

  /**
   * Save last sync timestamp
   */
  saveLastSyncTimestamp(timestamp) {
    try {
      this.db.prepare(`
        INSERT OR REPLACE INTO sync_metadata (key, value, updated_at)
        VALUES ('last_employee_sync', ?, ?)
      `).run(timestamp, new Date().toISOString());
    } catch (error) {
      logger.error('Failed to save sync timestamp', error);
    }
  }

  /**
   * Get sync token
   */
  getSyncToken() {
    try {
      const result = this.db.prepare(`
        SELECT value FROM sync_metadata 
        WHERE key = 'sync_token'
      `).get();
      
      return result ? result.value : null;
    } catch (error) {
      return null;
    }
  }

  /**
   * Set sync token (called during initial POS setup)
   */
  setSyncToken(token) {
    try {
      this.db.prepare(`
        INSERT OR REPLACE INTO sync_metadata (key, value, updated_at)
        VALUES ('sync_token', ?, ?)
      `).run(token, new Date().toISOString());
      
      logger.info('Sync token configured');
    } catch (error) {
      logger.error('Failed to save sync token', error);
    }
  }

  /**
   * Log activity for security audit
   */
  logActivity(employeeId, sessionId, action, details) {
    try {
      this.db.prepare(`
        INSERT INTO activity_log (employee_id, session_id, action, details)
        VALUES (?, ?, ?, ?)
      `).run(
        employeeId,
        sessionId,
        action,
        JSON.stringify(details)
      );
    } catch (error) {
      logger.error('Activity logging error', error);
    }
  }

  /**
   * Get session statistics
   */
  getSessionStats() {
    try {
      const stats = this.db.prepare(`
        SELECT 
          COUNT(*) as total_sessions,
          SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_sessions,
          COUNT(DISTINCT employee_id) as unique_employees
        FROM sessions
        WHERE started_at > datetime('now', '-24 hours')
      `).get();

      return stats;
    } catch (error) {
      logger.error('Failed to get session stats', error);
      return null;
    }
  }

  /**
   * Cleanup on shutdown
   */
  cleanup() {
    if (this.sessionCheckInterval) {
      clearInterval(this.sessionCheckInterval);
    }
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
    }
    logger.info('Auth service cleaned up');
  }
}

module.exports = AuthService;

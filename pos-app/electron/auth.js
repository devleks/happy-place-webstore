/**
 * Authentication Service
 * Secure hybrid auth with automatic sync and session management
 * Per ELECTRON_WINDSURF_RULES.md Section 1 (Security)
 */

const bcrypt = require('bcryptjs');
const crypto = require('crypto');
const { logger } = require('./logger');
const fetch = require('node-fetch');

/**
 * Verify password against Werkzeug scrypt hash (Flask backend format)
 * Format: scrypt:N:r:p$salt$hash
 * Example: scrypt:32768:8:1$base64salt$hexhash
 * IMPORTANT: Werkzeug uses the base64 salt string as UTF-8 bytes (not decoded!)
 * Hash is hex-encoded
 */
function verifyScryptPassword(password, passwordHash) {
  try {
    // Check if it's a scrypt hash
    if (!passwordHash.startsWith('scrypt:')) {
      return false;
    }

    // Parse the hash: scrypt:N:r:p$salt$hash
    const parts = passwordHash.split('$');
    if (parts.length !== 3) return false;

    const [params, saltStr, expectedHash] = parts;
    const paramParts = params.split(':');
    if (paramParts.length !== 4) return false;

    const [, N, r, p] = paramParts;

    // Werkzeug uses the base64 string itself as UTF-8 bytes (NOT decoded base64!)
    // See werkzeug/security.py: salt = salt.encode("utf-8")
    const salt = Buffer.from(saltStr, 'utf-8');

    // Derive key using scrypt (maxmem formula from Werkzeug: 132 * N * r * p)
    const derivedKey = crypto.scryptSync(
      password,
      salt,
      64, // Flask scrypt outputs 64 bytes by default
      {
        N: parseInt(N),
        r: parseInt(r),
        p: parseInt(p),
        maxmem: 132 * parseInt(N) * parseInt(r) * parseInt(p)
      }
    );

    // Werkzeug uses hex encoding for the hash
    const derivedHash = derivedKey.toString('hex');

    // Compare hashes (constant-time comparison would be better in production)
    const match = derivedHash === expectedHash;

    if (!match) {
      logger.warn(`Scrypt password verification failed for hash starting with: ${passwordHash.substring(0, 30)}...`);
    }

    return match;
  } catch (error) {
    logger.error('Scrypt password verification error', error);
    return false;
  }
}

/**
 * Verify password against Werkzeug hash (pbkdf2:sha256 format from Flask backend)
 * Format: pbkdf2:sha256:iterations$salt$hash
 * Werkzeug uses base64-encoded salt and hash
 */
function verifyWerkzeugPassword(password, passwordHash) {
  try {
    // Check if it's a Werkzeug hash
    if (!passwordHash.startsWith('pbkdf2:sha256:')) {
      return false;
    }

    // Parse the hash: pbkdf2:sha256:iterations$salt$hash
    const parts = passwordHash.split(':');
    if (parts.length !== 3) return false;

    const [, , data] = parts;
    const hashParts = data.split('$');
    if (hashParts.length !== 3) return false;

    const [iterations, saltB64, expectedHash] = hashParts;

    // Werkzeug stores salt and hash as base64 strings
    // Decode salt from base64
    const salt = Buffer.from(saltB64, 'base64');

    // Derive key using same parameters as Werkzeug
    const derivedKey = crypto.pbkdf2Sync(
      password,
      salt,
      parseInt(iterations),
      32, // 32 bytes = 256 bits for sha256
      'sha256'
    );

    // Werkzeug uses base64 encoding without padding for the hash
    const derivedHash = derivedKey.toString('base64').replace(/=+$/, '');

    // Compare hashes (constant-time comparison would be better in production)
    const match = derivedHash === expectedHash;

    if (!match) {
      logger.warn(`Password verification failed for hash starting with: ${passwordHash.substring(0, 30)}...`);
    }

    return match;
  } catch (error) {
    logger.error('Werkzeug password verification error', error);
    return false;
  }
}

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

      // 2. Verify password (support scrypt, pbkdf2, and bcrypt formats)
      let isValid = false;

      // Try scrypt format first (current Flask backend default)
      if (employee.password_hash.startsWith('scrypt:')) {
        isValid = verifyScryptPassword(password, employee.password_hash);
      }
      // Try Werkzeug pbkdf2 format
      else if (employee.password_hash.startsWith('pbkdf2:sha256:')) {
        isValid = verifyWerkzeugPassword(password, employee.password_hash);
      }
      // Fall back to bcrypt
      else {
        isValid = await bcrypt.compare(password, employee.password_hash);
      }
      
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
      logger.info('🔄 Starting employee sync from backend');

      // Get last sync timestamp for incremental sync
      const lastSync = this.getLastSyncTimestamp();
      logger.info(`📅 Last sync timestamp: ${lastSync || 'NONE (full sync)'}`);
      
      // Build sync URL (use 127.0.0.1 instead of localhost to avoid IPv6 issues)
      const syncUrl = lastSync 
        ? `http://127.0.0.1:5001/api/employees/sync/incremental?last_sync=${lastSync}`
        : 'http://127.0.0.1:5001/api/employees/sync';

      logger.info(`🌐 Sync URL: ${syncUrl}`);

      // Get sync token
      const syncToken = this.getSyncToken();
      
      if (!syncToken) {
        logger.debug('❌ No sync token available - skipping sync');
        return { success: false, reason: 'no_token' };
      }

      logger.info(`🔑 Sync token available: ${syncToken.substring(0, 20)}...`);

      // Fetch employees from backend
      logger.info('📡 Fetching employees from backend...');
      const response = await fetch(syncUrl, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${syncToken}`,
          'Content-Type': 'application/json'
        }
      });

      logger.info(`📊 Response status: ${response.status}`);

      if (!response.ok) {
        throw new Error(`Sync failed: ${response.status}`);
      }

      const data = await response.json();
      logger.info(`📦 Received data: success=${data.success}, employees=${data.employees?.length || 0}`);

      if (data.success && data.employees) {
        logger.info(`💾 Updating ${data.employees.length} employees in local database...`);
        
        // Update local database
        await this.updateEmployees(data.employees);
        
        logger.info('✅ Database update complete');
        
        // Save sync version
        this.saveLastSyncTimestamp(data.sync_version);
        logger.info(`📌 Saved sync version: ${data.sync_version}`);
        
        logger.success(`✅ Synced ${data.employees.length} employees from backend`);
        
        return { 
          success: true, 
          count: data.employees.length,
          sync_version: data.sync_version
        };
      }

      logger.warn('⚠️ No employee data in response');
      return { success: false, reason: 'no_data' };
    } catch (error) {
      logger.error('❌ Employee sync error', error);
      return { success: false, reason: 'sync_error', error: error.message };
    }
  }

  /**
   * Update employees in local database
   */
  async updateEmployees(employees) {
    try {
      logger.info(`📝 updateEmployees called with ${employees.length} employees`);
      
      const stmt = this.db.prepare(`
        INSERT OR REPLACE INTO employees 
        (backend_id, email, full_name, role, password_hash, permissions, 
         is_active, last_synced_at, sync_version, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `);

      const syncTime = new Date().toISOString();
      let insertedCount = 0;

      for (const emp of employees) {
        try {
          logger.info(`👤 Inserting employee: ${emp.email} (${emp.role})`);
          
          const result = stmt.run(
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
          
          insertedCount++;
          logger.info(`✅ Inserted employee ${emp.email}, changes: ${result.changes}`);
        } catch (empError) {
          logger.error(`❌ Failed to insert employee ${emp.email}:`, empError);
          throw empError;
        }
      }

      logger.info(`✅ Successfully inserted ${insertedCount}/${employees.length} employees`);

      // Verify insertion
      const count = this.db.prepare('SELECT COUNT(*) as count FROM employees').get();
      logger.info(`📊 Total employees in database: ${count.count}`);

      // Invalidate sessions for deactivated employees
      this.invalidateDeactivatedEmployeeSessions();
    } catch (error) {
      logger.error('❌ Employee update error', error);
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

/**
 * Logging Service
 * Comprehensive logging with electron-log
 * Per ELECTRON_WINDSURF_RULES.md Section 4.3
 */

const log = require('electron-log');
const path = require('path');
const { app } = require('electron');

// ============================================================================
// CONFIGURATION
// ============================================================================

/**
 * Configure logging transports and formats
 */
function initLogger() {
  try {
    // Set log file location
    const logPath = path.join(app.getPath('userData'), 'logs');
    log.transports.file.resolvePathFn = () => path.join(logPath, 'main.log');

    // Configure file transport
    log.transports.file.level = 'info';
    log.transports.file.maxSize = 5 * 1024 * 1024; // 5MB
    log.transports.file.format = '[{y}-{m}-{d} {h}:{i}:{s}.{ms}] [{level}] {text}';
    
    // Configure console transport
    log.transports.console.level = process.env.NODE_ENV === 'development' ? 'debug' : 'info';
    log.transports.console.format = '[{h}:{i}:{s}] [{level}] {text}';

    // Add custom colors
    log.transports.console.useStyles = true;

    // Log initialization
    log.info('='.repeat(80));
    log.info('📝 Logger initialized');
    log.info(`📁 Log file: ${log.transports.file.getFile().path}`);
    log.info(`🔧 Environment: ${process.env.NODE_ENV || 'production'}`);
    log.info(`📦 App version: ${app.getVersion()}`);
    log.info(`💻 Platform: ${process.platform} ${process.arch}`);
    log.info(`🖥️  Electron: ${process.versions.electron}`);
    log.info(`⚛️  Chrome: ${process.versions.chrome}`);
    log.info(`📍 Node: ${process.versions.node}`);
    log.info('='.repeat(80));

    return log;
  } catch (error) {
    console.error('Failed to initialize logger:', error);
    return log; // Return default log even if config fails
  }
}

// ============================================================================
// LOGGING HELPERS
// ============================================================================

/**
 * Log levels with emojis for better visibility
 */
const logger = {
  /**
   * Debug level - detailed information for debugging
   */
  debug(message, ...args) {
    log.debug(`🔍 ${message}`, ...args);
  },

  /**
   * Info level - general informational messages
   */
  info(message, ...args) {
    log.info(`ℹ️  ${message}`, ...args);
  },

  /**
   * Success level - successful operations
   */
  success(message, ...args) {
    log.info(`✅ ${message}`, ...args);
  },

  /**
   * Warning level - warning messages
   */
  warn(message, ...args) {
    log.warn(`⚠️  ${message}`, ...args);
  },

  /**
   * Error level - error messages
   */
  error(message, error, ...args) {
    if (error instanceof Error) {
      log.error(`❌ ${message}`, {
        message: error.message,
        stack: error.stack,
        ...args
      });
    } else {
      log.error(`❌ ${message}`, error, ...args);
    }
  },

  /**
   * Fatal level - critical errors
   */
  fatal(message, error, ...args) {
    if (error instanceof Error) {
      log.error(`💀 FATAL: ${message}`, {
        message: error.message,
        stack: error.stack,
        ...args
      });
    } else {
      log.error(`💀 FATAL: ${message}`, error, ...args);
    }
  },

  /**
   * Log performance metrics
   */
  perf(operation, duration, ...args) {
    log.info(`⚡ Performance: ${operation} took ${duration}ms`, ...args);
  },

  /**
   * Log security events
   */
  security(event, details) {
    log.warn(`🔒 Security: ${event}`, details);
  },

  /**
   * Log database operations
   */
  db(operation, details) {
    log.debug(`💾 Database: ${operation}`, details);
  },

  /**
   * Log IPC operations
   */
  ipc(channel, direction, details) {
    const arrow = direction === 'send' ? '📤' : '📥';
    log.debug(`${arrow} IPC: ${channel}`, details);
  },

  /**
   * Log sync operations
   */
  sync(operation, details) {
    log.info(`🔄 Sync: ${operation}`, details);
  },

  /**
   * Log hardware operations
   */
  hardware(operation, details) {
    log.info(`🔌 Hardware: ${operation}`, details);
  },

  /**
   * Log user actions
   */
  user(action, details) {
    log.info(`👤 User: ${action}`, details);
  },

  /**
   * Log system events
   */
  system(event, details) {
    log.info(`🖥️  System: ${event}`, details);
  },

  /**
   * Create a section separator
   */
  separator(title) {
    log.info('─'.repeat(80));
    if (title) {
      log.info(`  ${title}`);
      log.info('─'.repeat(80));
    }
  },

  /**
   * Log startup information
   */
  startup(info) {
    this.separator('APPLICATION STARTUP');
    Object.entries(info).forEach(([key, value]) => {
      log.info(`  ${key}: ${value}`);
    });
    this.separator();
  },

  /**
   * Log shutdown information
   */
  shutdown(reason) {
    this.separator('APPLICATION SHUTDOWN');
    log.info(`  Reason: ${reason || 'User initiated'}`);
    log.info(`  Uptime: ${process.uptime().toFixed(2)}s`);
    this.separator();
  }
};

// ============================================================================
// ERROR TRACKING
// ============================================================================

/**
 * Track and log unhandled errors
 */
function setupErrorHandlers() {
  // Uncaught exceptions
  process.on('uncaughtException', (error) => {
    logger.fatal('Uncaught Exception', error);
    
    // Give logger time to write before exiting
    setTimeout(() => {
      process.exit(1);
    }, 1000);
  });

  // Unhandled promise rejections
  process.on('unhandledRejection', (reason, promise) => {
    logger.error('Unhandled Promise Rejection', {
      reason: reason,
      promise: promise
    });
  });

  // Warning events
  process.on('warning', (warning) => {
    logger.warn('Process Warning', {
      name: warning.name,
      message: warning.message,
      stack: warning.stack
    });
  });

  logger.success('Error handlers configured');
}

// ============================================================================
// PERFORMANCE MONITORING
// ============================================================================

/**
 * Create a performance timer
 */
function createTimer(operation) {
  const start = Date.now();
  
  return {
    end: () => {
      const duration = Date.now() - start;
      logger.perf(operation, duration);
      return duration;
    }
  };
}

/**
 * Measure async operation performance
 */
async function measureAsync(operation, fn) {
  const timer = createTimer(operation);
  try {
    const result = await fn();
    timer.end();
    return result;
  } catch (error) {
    timer.end();
    throw error;
  }
}

// ============================================================================
// LOG ROTATION
// ============================================================================

/**
 * Rotate old log files
 */
function rotateLogs() {
  try {
    const fs = require('fs');
    const logDir = path.join(app.getPath('userData'), 'logs');
    
    if (!fs.existsSync(logDir)) {
      return;
    }

    const files = fs.readdirSync(logDir);
    const logFiles = files.filter(f => f.endsWith('.log'));

    // Keep only last 10 log files
    if (logFiles.length > 10) {
      logFiles
        .map(f => ({
          name: f,
          path: path.join(logDir, f),
          time: fs.statSync(path.join(logDir, f)).mtime.getTime()
        }))
        .sort((a, b) => b.time - a.time)
        .slice(10)
        .forEach(file => {
          fs.unlinkSync(file.path);
          logger.info(`Deleted old log file: ${file.name}`);
        });
    }
  } catch (error) {
    logger.error('Failed to rotate logs', error);
  }
}

// ============================================================================
// EXPORTS
// ============================================================================

module.exports = {
  initLogger,
  logger,
  setupErrorHandlers,
  createTimer,
  measureAsync,
  rotateLogs,
  // Export raw log for direct access if needed
  log
};

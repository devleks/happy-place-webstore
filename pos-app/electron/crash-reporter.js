/**
 * Crash Reporter Service
 * Handles crash reporting and error tracking
 * Per ELECTRON_WINDSURF_RULES.md Section 4.3
 */

const { crashReporter, app } = require('electron');
const { logger } = require('./logger');
const path = require('path');
const fs = require('fs');

// ============================================================================
// CONFIGURATION
// ============================================================================

/**
 * Initialize crash reporter
 */
function initCrashReporter() {
  try {
    const crashesPath = path.join(app.getPath('userData'), 'crashes');

    // Ensure crashes directory exists
    if (!fs.existsSync(crashesPath)) {
      fs.mkdirSync(crashesPath, { recursive: true });
    }

    // Start crash reporter
    crashReporter.start({
      productName: 'Happy Place POS',
      companyName: 'Happy Place Boutique',
      submitURL: '', // TODO: Set up crash reporting server
      uploadToServer: false, // Set to true when server is ready
      compress: true,
      extra: {
        version: app.getVersion(),
        platform: process.platform,
        arch: process.arch,
        electronVersion: process.versions.electron,
        nodeVersion: process.versions.node,
        chromeVersion: process.versions.chrome
      }
    });

    logger.success('Crash reporter initialized');
    logger.info(`Crash reports: ${crashesPath}`);

    // Check for previous crashes
    checkPreviousCrashes(crashesPath);

    return true;
  } catch (error) {
    logger.error('Failed to initialize crash reporter', error);
    return false;
  }
}

// ============================================================================
// CRASH DETECTION
// ============================================================================

/**
 * Check for previous crashes
 */
function checkPreviousCrashes(crashesPath) {
  try {
    if (!fs.existsSync(crashesPath)) {
      return;
    }

    const files = fs.readdirSync(crashesPath);
    const crashFiles = files.filter(f => f.endsWith('.dmp'));

    if (crashFiles.length > 0) {
      logger.warn(`Found ${crashFiles.length} previous crash report(s)`);
      
      // Log crash file details
      crashFiles.forEach(file => {
        const filePath = path.join(crashesPath, file);
        const stats = fs.statSync(filePath);
        logger.warn(`Crash report: ${file} (${stats.size} bytes, ${stats.mtime.toISOString()})`);
      });

      // Optionally clean up old crash reports (keep last 5)
      if (crashFiles.length > 5) {
        cleanupOldCrashes(crashesPath, crashFiles);
      }
    } else {
      logger.info('No previous crashes detected');
    }
  } catch (error) {
    logger.error('Failed to check previous crashes', error);
  }
}

/**
 * Clean up old crash reports
 */
function cleanupOldCrashes(crashesPath, crashFiles) {
  try {
    const crashesWithTime = crashFiles.map(file => ({
      name: file,
      path: path.join(crashesPath, file),
      time: fs.statSync(path.join(crashesPath, file)).mtime.getTime()
    }));

    // Sort by time (newest first) and keep only last 5
    crashesWithTime
      .sort((a, b) => b.time - a.time)
      .slice(5)
      .forEach(crash => {
        fs.unlinkSync(crash.path);
        logger.info(`Deleted old crash report: ${crash.name}`);
      });
  } catch (error) {
    logger.error('Failed to cleanup old crashes', error);
  }
}

// ============================================================================
// ERROR CONTEXT
// ============================================================================

/**
 * Capture error context for debugging
 */
function captureErrorContext(error) {
  const context = {
    timestamp: new Date().toISOString(),
    error: {
      name: error.name,
      message: error.message,
      stack: error.stack
    },
    app: {
      version: app.getVersion(),
      name: app.getName(),
      path: app.getAppPath()
    },
    system: {
      platform: process.platform,
      arch: process.arch,
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      cpu: process.cpuUsage()
    },
    versions: {
      electron: process.versions.electron,
      node: process.versions.node,
      chrome: process.versions.chrome,
      v8: process.versions.v8
    }
  };

  return context;
}

/**
 * Save error context to file
 */
function saveErrorContext(error, filename) {
  try {
    const context = captureErrorContext(error);
    const errorPath = path.join(app.getPath('userData'), 'crashes', filename);
    
    fs.writeFileSync(errorPath, JSON.stringify(context, null, 2), 'utf8');
    logger.info(`Error context saved: ${errorPath}`);
    
    return errorPath;
  } catch (err) {
    logger.error('Failed to save error context', err);
    return null;
  }
}

// ============================================================================
// CRASH HANDLING
// ============================================================================

/**
 * Handle application crash
 */
function handleCrash(error, isFatal = false) {
  try {
    // Log the crash
    if (isFatal) {
      logger.fatal('Application crashed', error);
    } else {
      logger.error('Application error', error);
    }

    // Capture and save error context
    const timestamp = Date.now();
    const filename = `error-${timestamp}.json`;
    saveErrorContext(error, filename);

    // If fatal, prepare for shutdown
    if (isFatal) {
      logger.shutdown('Fatal crash');
      
      // Give logger time to write
      setTimeout(() => {
        process.exit(1);
      }, 1000);
    }
  } catch (err) {
    console.error('Failed to handle crash:', err);
    if (isFatal) {
      process.exit(1);
    }
  }
}

/**
 * Setup crash handlers
 */
function setupCrashHandlers() {
  // Uncaught exceptions (fatal)
  process.on('uncaughtException', (error) => {
    handleCrash(error, true);
  });

  // Unhandled promise rejections (non-fatal but logged)
  process.on('unhandledRejection', (reason, promise) => {
    const error = reason instanceof Error ? reason : new Error(String(reason));
    handleCrash(error, false);
  });

  logger.success('Crash handlers configured');
}

// ============================================================================
// HEALTH CHECK
// ============================================================================

/**
 * Perform health check
 */
function healthCheck() {
  const health = {
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    cpu: process.cpuUsage(),
    status: 'healthy'
  };

  // Check memory usage
  const memoryUsageMB = health.memory.heapUsed / 1024 / 1024;
  if (memoryUsageMB > 500) {
    logger.warn(`High memory usage: ${memoryUsageMB.toFixed(2)}MB`);
    health.status = 'warning';
  }

  return health;
}

/**
 * Start periodic health checks
 */
function startHealthMonitoring(intervalMinutes = 5) {
  const interval = intervalMinutes * 60 * 1000;

  setInterval(() => {
    const health = healthCheck();
    logger.debug('Health check', health);
  }, interval);

  logger.info(`Health monitoring started (every ${intervalMinutes} minutes)`);
}

// ============================================================================
// EXPORTS
// ============================================================================

module.exports = {
  initCrashReporter,
  setupCrashHandlers,
  handleCrash,
  captureErrorContext,
  saveErrorContext,
  healthCheck,
  startHealthMonitoring
};

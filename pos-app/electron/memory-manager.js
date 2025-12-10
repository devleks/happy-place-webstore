/**
 * Memory Management Service
 * Handles event listener cleanup and memory leak prevention
 * Per ELECTRON_WINDSURF_RULES.md Section 2.3
 */

const { logger } = require('./logger');

// ============================================================================
// LISTENER TRACKING
// ============================================================================

/**
 * Global listener registry
 */
const listenerRegistry = {
  ipc: new Map(), // IPC listeners
  window: new Map(), // Window event listeners
  app: new Map() // App event listeners
};

/**
 * Register a listener for tracking
 */
function registerListener(type, event, callback, source = 'unknown') {
  try {
    if (!listenerRegistry[type]) {
      logger.warn('Unknown listener type', { type });
      return;
    }

    const key = `${event}-${source}`;
    
    if (!listenerRegistry[type].has(key)) {
      listenerRegistry[type].set(key, []);
    }

    listenerRegistry[type].get(key).push({
      event,
      callback,
      source,
      registeredAt: new Date()
    });

    logger.debug('Listener registered', { type, event, source });
  } catch (error) {
    logger.error('Failed to register listener', error);
  }
}

/**
 * Unregister a listener
 */
function unregisterListener(type, event, callback, source = 'unknown') {
  try {
    if (!listenerRegistry[type]) {
      return;
    }

    const key = `${event}-${source}`;
    const listeners = listenerRegistry[type].get(key);

    if (listeners) {
      const index = listeners.findIndex(l => l.callback === callback);
      if (index !== -1) {
        listeners.splice(index, 1);
        logger.debug('Listener unregistered', { type, event, source });
      }

      // Clean up empty arrays
      if (listeners.length === 0) {
        listenerRegistry[type].delete(key);
      }
    }
  } catch (error) {
    logger.error('Failed to unregister listener', error);
  }
}

/**
 * Get listener statistics
 */
function getListenerStats() {
  const stats = {};

  for (const [type, registry] of Object.entries(listenerRegistry)) {
    let totalListeners = 0;
    const events = {};

    for (const [key, listeners] of registry.entries()) {
      totalListeners += listeners.length;
      const [event] = key.split('-');
      events[event] = (events[event] || 0) + listeners.length;
    }

    stats[type] = {
      total: totalListeners,
      events
    };
  }

  return stats;
}

/**
 * Log listener statistics
 */
function logListenerStats() {
  const stats = getListenerStats();
  logger.debug('Listener statistics', stats);
  return stats;
}

// ============================================================================
// MEMORY MONITORING
// ============================================================================

/**
 * Get current memory usage
 */
function getMemoryUsage() {
  const usage = process.memoryUsage();
  
  return {
    heapUsed: Math.round(usage.heapUsed / 1024 / 1024), // MB
    heapTotal: Math.round(usage.heapTotal / 1024 / 1024), // MB
    external: Math.round(usage.external / 1024 / 1024), // MB
    rss: Math.round(usage.rss / 1024 / 1024), // MB
    arrayBuffers: Math.round(usage.arrayBuffers / 1024 / 1024) // MB
  };
}

/**
 * Check for memory leaks
 */
function checkMemoryLeaks() {
  const usage = getMemoryUsage();
  const stats = getListenerStats();

  // Warning thresholds
  const HEAP_WARNING_MB = 500;
  const LISTENER_WARNING_COUNT = 100;

  const warnings = [];

  // Check heap usage
  if (usage.heapUsed > HEAP_WARNING_MB) {
    warnings.push({
      type: 'high_memory',
      message: `High heap usage: ${usage.heapUsed}MB`,
      value: usage.heapUsed
    });
  }

  // Check listener counts
  for (const [type, stat] of Object.entries(stats)) {
    if (stat.total > LISTENER_WARNING_COUNT) {
      warnings.push({
        type: 'high_listener_count',
        message: `High ${type} listener count: ${stat.total}`,
        value: stat.total
      });
    }
  }

  if (warnings.length > 0) {
    logger.warn('Potential memory leaks detected', { warnings, usage, stats });
  }

  return {
    hasLeaks: warnings.length > 0,
    warnings,
    usage,
    stats
  };
}

/**
 * Force garbage collection (if available)
 */
function forceGarbageCollection() {
  if (global.gc) {
    logger.debug('Running garbage collection');
    global.gc();
    logger.debug('Garbage collection complete');
    return true;
  } else {
    logger.warn('Garbage collection not available (run with --expose-gc)');
    return false;
  }
}

// ============================================================================
// CLEANUP UTILITIES
// ============================================================================

/**
 * Clean up all registered listeners of a specific type
 */
function cleanupListeners(type) {
  try {
    if (!listenerRegistry[type]) {
      logger.warn('Unknown listener type for cleanup', { type });
      return 0;
    }

    let count = 0;
    for (const [key, listeners] of listenerRegistry[type].entries()) {
      count += listeners.length;
    }

    listenerRegistry[type].clear();
    logger.info(`Cleaned up ${count} ${type} listeners`);
    
    return count;
  } catch (error) {
    logger.error('Failed to cleanup listeners', error);
    return 0;
  }
}

/**
 * Clean up all listeners
 */
function cleanupAllListeners() {
  try {
    logger.info('Cleaning up all listeners');
    
    let totalCleaned = 0;
    for (const type of Object.keys(listenerRegistry)) {
      totalCleaned += cleanupListeners(type);
    }

    logger.success(`Cleaned up ${totalCleaned} total listeners`);
    return totalCleaned;
  } catch (error) {
    logger.error('Failed to cleanup all listeners', error);
    return 0;
  }
}

/**
 * Clean up window-specific listeners
 */
function cleanupWindowListeners(windowId) {
  try {
    logger.info('Cleaning up window listeners', { windowId });
    
    let count = 0;
    for (const [key, listeners] of listenerRegistry.window.entries()) {
      const filtered = listeners.filter(l => l.source !== windowId);
      count += listeners.length - filtered.length;
      
      if (filtered.length > 0) {
        listenerRegistry.window.set(key, filtered);
      } else {
        listenerRegistry.window.delete(key);
      }
    }

    logger.success(`Cleaned up ${count} window listeners for window ${windowId}`);
    return count;
  } catch (error) {
    logger.error('Failed to cleanup window listeners', error);
    return 0;
  }
}

// ============================================================================
// PERIODIC MONITORING
// ============================================================================

let monitoringInterval = null;

/**
 * Start periodic memory monitoring
 */
function startMemoryMonitoring(intervalMinutes = 5) {
  if (monitoringInterval) {
    logger.warn('Memory monitoring already started');
    return;
  }

  const interval = intervalMinutes * 60 * 1000;

  monitoringInterval = setInterval(() => {
    logger.debug('Memory monitoring check');
    
    // Log memory usage
    const usage = getMemoryUsage();
    logger.debug('Memory usage', usage);
    
    // Log listener stats
    logListenerStats();
    
    // Check for leaks
    const leakCheck = checkMemoryLeaks();
    
    if (leakCheck.hasLeaks) {
      logger.warn('Memory leak check failed', leakCheck);
    }
  }, interval);

  logger.info(`Memory monitoring started (every ${intervalMinutes} minutes)`);
}

/**
 * Stop periodic memory monitoring
 */
function stopMemoryMonitoring() {
  if (monitoringInterval) {
    clearInterval(monitoringInterval);
    monitoringInterval = null;
    logger.info('Memory monitoring stopped');
  }
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Create a tracked event listener
 */
function createTrackedListener(emitter, event, callback, source = 'unknown', type = 'app') {
  // Register the listener
  registerListener(type, event, callback, source);
  
  // Add the listener
  emitter.on(event, callback);
  
  // Return cleanup function
  return () => {
    emitter.removeListener(event, callback);
    unregisterListener(type, event, callback, source);
  };
}

/**
 * Create a one-time tracked listener
 */
function createTrackedOnceListener(emitter, event, callback, source = 'unknown', type = 'app') {
  const wrappedCallback = (...args) => {
    unregisterListener(type, event, wrappedCallback, source);
    callback(...args);
  };
  
  registerListener(type, event, wrappedCallback, source);
  emitter.once(event, wrappedCallback);
  
  return () => {
    emitter.removeListener(event, wrappedCallback);
    unregisterListener(type, event, wrappedCallback, source);
  };
}

// ============================================================================
// INITIALIZATION
// ============================================================================

/**
 * Initialize memory manager
 */
function initMemoryManager() {
  try {
    logger.info('Initializing memory manager');
    
    // Start monitoring
    startMemoryMonitoring(5); // Every 5 minutes
    
    // Log initial stats
    const usage = getMemoryUsage();
    logger.info('Initial memory usage', usage);
    
    logger.success('Memory manager initialized');
    return true;
  } catch (error) {
    logger.error('Failed to initialize memory manager', error);
    return false;
  }
}

// ============================================================================
// EXPORTS
// ============================================================================

module.exports = {
  // Initialization
  initMemoryManager,
  
  // Listener tracking
  registerListener,
  unregisterListener,
  getListenerStats,
  logListenerStats,
  
  // Memory monitoring
  getMemoryUsage,
  checkMemoryLeaks,
  forceGarbageCollection,
  
  // Cleanup
  cleanupListeners,
  cleanupAllListeners,
  cleanupWindowListeners,
  
  // Monitoring
  startMemoryMonitoring,
  stopMemoryMonitoring,
  
  // Helpers
  createTrackedListener,
  createTrackedOnceListener
};

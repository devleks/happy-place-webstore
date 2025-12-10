/**
 * Rate Limiter Service
 * IPC rate limiting to prevent abuse
 * Per ELECTRON_WINDSURF_RULES.md Section 2.2
 */

const { logger } = require('./logger');

// ============================================================================
// RATE LIMITER
// ============================================================================

class RateLimiter {
  constructor(maxRequests, windowMs) {
    this.maxRequests = maxRequests;
    this.windowMs = windowMs;
    this.requests = new Map(); // channel -> array of timestamps
  }

  /**
   * Check if request is allowed
   */
  isAllowed(channel, identifier = 'default') {
    const key = `${channel}:${identifier}`;
    const now = Date.now();

    // Get existing requests for this key
    if (!this.requests.has(key)) {
      this.requests.set(key, []);
    }

    const timestamps = this.requests.get(key);

    // Remove old timestamps outside the window
    const validTimestamps = timestamps.filter(
      timestamp => now - timestamp < this.windowMs
    );

    // Check if limit exceeded
    if (validTimestamps.length >= this.maxRequests) {
      logger.warn('Rate limit exceeded', {
        channel,
        identifier,
        count: validTimestamps.length,
        limit: this.maxRequests
      });
      return false;
    }

    // Add current timestamp
    validTimestamps.push(now);
    this.requests.set(key, validTimestamps);

    return true;
  }

  /**
   * Reset rate limit for a channel
   */
  reset(channel, identifier = 'default') {
    const key = `${channel}:${identifier}`;
    this.requests.delete(key);
    logger.debug('Rate limit reset', { channel, identifier });
  }

  /**
   * Reset all rate limits
   */
  resetAll() {
    this.requests.clear();
    logger.debug('All rate limits reset');
  }

  /**
   * Get current request count
   */
  getCount(channel, identifier = 'default') {
    const key = `${channel}:${identifier}`;
    const now = Date.now();

    if (!this.requests.has(key)) {
      return 0;
    }

    const timestamps = this.requests.get(key);
    const validTimestamps = timestamps.filter(
      timestamp => now - timestamp < this.windowMs
    );

    return validTimestamps.length;
  }

  /**
   * Get remaining requests
   */
  getRemaining(channel, identifier = 'default') {
    const count = this.getCount(channel, identifier);
    return Math.max(0, this.maxRequests - count);
  }
}

// ============================================================================
// RATE LIMIT CONFIGURATIONS
// ============================================================================

/**
 * Rate limit configurations for different operations
 */
const rateLimitConfigs = {
  // Search operations - 10 requests per second
  search: {
    maxRequests: 10,
    windowMs: 1000
  },

  // Database reads - 50 requests per second
  read: {
    maxRequests: 50,
    windowMs: 1000
  },

  // Database writes - 20 requests per second
  write: {
    maxRequests: 20,
    windowMs: 1000
  },

  // Sync operations - 5 requests per minute
  sync: {
    maxRequests: 5,
    windowMs: 60000
  },

  // Hardware operations - 10 requests per second
  hardware: {
    maxRequests: 10,
    windowMs: 1000
  },

  // Update checks - 1 request per minute
  update: {
    maxRequests: 1,
    windowMs: 60000
  },

  // Memory checks - 5 requests per minute
  memory: {
    maxRequests: 5,
    windowMs: 60000
  },

  // Default - 30 requests per second
  default: {
    maxRequests: 30,
    windowMs: 1000
  }
};

// ============================================================================
// RATE LIMITER INSTANCES
// ============================================================================

const rateLimiters = {};

/**
 * Get or create rate limiter for a type
 */
function getRateLimiter(type) {
  if (!rateLimiters[type]) {
    const config = rateLimitConfigs[type] || rateLimitConfigs.default;
    rateLimiters[type] = new RateLimiter(config.maxRequests, config.windowMs);
  }
  return rateLimiters[type];
}

// ============================================================================
// IPC RATE LIMITING
// ============================================================================

/**
 * Map IPC channels to rate limit types
 */
const channelTypeMap = {
  // Search
  'db-search-products': 'search',
  
  // Database reads
  'db-get-products': 'read',
  'db-get-product-by-sku': 'read',
  'db-get-transactions': 'read',
  'db-get-transaction': 'read',
  'db-get-held-transactions': 'read',
  'db-get-sync-queue': 'read',
  
  // Database writes
  'db-create-transaction': 'write',
  'db-update-product-stock': 'write',
  'db-hold-transaction': 'write',
  'db-recall-transaction': 'write',
  'db-delete-held-transaction': 'write',
  'db-clear-sync-queue': 'write',
  
  // Sync
  'sync-now': 'sync',
  'sync-products': 'sync',
  'sync-transactions': 'sync',
  'get-sync-status': 'sync',
  
  // Hardware
  'scan-barcode': 'hardware',
  'print-receipt': 'hardware',
  'open-cash-drawer': 'hardware',
  
  // Update
  'check-for-updates': 'update',
  
  // Memory
  'get-memory-usage': 'memory',
  'check-memory-leaks': 'memory'
};

/**
 * Get rate limit type for IPC channel
 */
function getRateLimitType(channel) {
  return channelTypeMap[channel] || 'default';
}

/**
 * Check if IPC request is allowed
 */
function isIpcAllowed(channel, identifier) {
  const type = getRateLimitType(channel);
  const limiter = getRateLimiter(type);
  return limiter.isAllowed(channel, identifier);
}

/**
 * Get IPC rate limit info
 */
function getIpcRateLimitInfo(channel, identifier) {
  const type = getRateLimitType(channel);
  const limiter = getRateLimiter(type);
  const config = rateLimitConfigs[type] || rateLimitConfigs.default;

  return {
    type,
    maxRequests: config.maxRequests,
    windowMs: config.windowMs,
    current: limiter.getCount(channel, identifier),
    remaining: limiter.getRemaining(channel, identifier)
  };
}

/**
 * Reset IPC rate limit
 */
function resetIpcRateLimit(channel, identifier) {
  const type = getRateLimitType(channel);
  const limiter = getRateLimiter(type);
  limiter.reset(channel, identifier);
}

// ============================================================================
// MIDDLEWARE
// ============================================================================

/**
 * Create rate limit middleware for IPC handler
 */
function createRateLimitMiddleware(channel) {
  return (event, ...args) => {
    // Use webContents.id as identifier
    const identifier = event.sender.id.toString();

    if (!isIpcAllowed(channel, identifier)) {
      const info = getIpcRateLimitInfo(channel, identifier);
      
      logger.warn('IPC rate limit exceeded', {
        channel,
        identifier,
        ...info
      });

      // Return error response
      return {
        success: false,
        error: 'Rate limit exceeded',
        code: 'RATE_LIMIT_EXCEEDED',
        retryAfter: info.windowMs
      };
    }

    // Request allowed, continue
    return null; // null means continue to actual handler
  };
}

/**
 * Wrap IPC handler with rate limiting
 */
function withRateLimit(channel, handler) {
  const middleware = createRateLimitMiddleware(channel);

  return async (event, ...args) => {
    // Check rate limit
    const rateLimitResult = middleware(event, ...args);
    
    if (rateLimitResult !== null) {
      // Rate limit exceeded
      return rateLimitResult;
    }

    // Execute actual handler
    try {
      return await handler(event, ...args);
    } catch (error) {
      logger.error(`IPC handler error: ${channel}`, error);
      return {
        success: false,
        error: error.message,
        code: 'HANDLER_ERROR'
      };
    }
  };
}

// ============================================================================
// STATISTICS
// ============================================================================

/**
 * Get rate limit statistics
 */
function getRateLimitStats() {
  const stats = {};

  for (const [type, limiter] of Object.entries(rateLimiters)) {
    const config = rateLimitConfigs[type] || rateLimitConfigs.default;
    
    stats[type] = {
      maxRequests: config.maxRequests,
      windowMs: config.windowMs,
      activeChannels: limiter.requests.size
    };
  }

  return stats;
}

/**
 * Log rate limit statistics
 */
function logRateLimitStats() {
  const stats = getRateLimitStats();
  logger.debug('Rate limit statistics', stats);
  return stats;
}

// ============================================================================
// CLEANUP
// ============================================================================

/**
 * Cleanup rate limiters
 */
function cleanupRateLimiters() {
  for (const limiter of Object.values(rateLimiters)) {
    limiter.resetAll();
  }
  logger.info('Rate limiters cleaned up');
}

// ============================================================================
// EXPORTS
// ============================================================================

module.exports = {
  RateLimiter,
  getRateLimiter,
  isIpcAllowed,
  getIpcRateLimitInfo,
  resetIpcRateLimit,
  createRateLimitMiddleware,
  withRateLimit,
  getRateLimitStats,
  logRateLimitStats,
  cleanupRateLimiters
};

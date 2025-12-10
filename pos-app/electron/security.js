/**
 * Security Service
 * Handles CSP headers, navigation guards, and security policies
 * Per ELECTRON_WINDSURF_RULES.md Section 1.3
 */

const { session, shell } = require('electron');
const { logger } = require('./logger');
const isDev = require('./is-dev');

// ============================================================================
// CONFIGURATION
// ============================================================================

/**
 * Content Security Policy configuration
 */
const CSP_POLICY = {
  // Default source - only allow self
  'default-src': ["'self'"],
  
  // Scripts - allow self and inline (for React)
  'script-src': [
    "'self'",
    isDev ? "'unsafe-eval'" : "", // Allow eval in development for hot reload
    isDev ? "'unsafe-inline'" : "" // Allow inline in development
  ].filter(Boolean),
  
  // Styles - allow self and inline (for styled-components)
  'style-src': [
    "'self'",
    "'unsafe-inline'" // Required for many CSS-in-JS solutions
  ],
  
  // Images - allow self, data URIs, and HTTPS
  'img-src': [
    "'self'",
    'data:',
    'https:'
  ],
  
  // Fonts - allow self and data URIs
  'font-src': [
    "'self'",
    'data:'
  ],
  
  // Connect - allow self and backend API
  'connect-src': [
    "'self'",
    'http://localhost:5001', // Backend API (development)
    'https://api.happyplace.com' // Backend API (production)
  ],
  
  // Media - allow self
  'media-src': ["'self'"],
  
  // Objects - disallow
  'object-src': ["'none'"],
  
  // Base URI - restrict to self
  'base-uri': ["'self'"],
  
  // Form action - restrict to self
  'form-action': ["'self'"],
  
  // Frame ancestors - disallow embedding
  'frame-ancestors': ["'none'"],
  
  // Upgrade insecure requests (production only)
  ...(isDev ? {} : { 'upgrade-insecure-requests': [] })
};

/**
 * Allowed navigation origins
 */
const ALLOWED_ORIGINS = [
  'http://localhost:3003', // Development server
  'http://localhost:5001', // Backend API
  'file://' // Local files (production build)
];

/**
 * Allowed external domains (will open in default browser)
 */
const ALLOWED_EXTERNAL_DOMAINS = [
  'github.com',
  'happyplace.com',
  'google.com'
];

// ============================================================================
// CSP HEADERS
// ============================================================================

/**
 * Build CSP header string from policy object
 */
function buildCSPHeader(policy) {
  return Object.entries(policy)
    .map(([directive, values]) => {
      if (values.length === 0) {
        return directive; // Directives like 'upgrade-insecure-requests'
      }
      return `${directive} ${values.join(' ')}`;
    })
    .join('; ');
}

/**
 * Setup Content Security Policy headers
 */
function setupCSP() {
  try {
    const cspHeader = buildCSPHeader(CSP_POLICY);
    
    logger.security('Setting up CSP headers');
    logger.debug('CSP Policy:', cspHeader);

    session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
      callback({
        responseHeaders: {
          ...details.responseHeaders,
          'Content-Security-Policy': [cspHeader],
          // Additional security headers
          'X-Content-Type-Options': ['nosniff'],
          'X-Frame-Options': ['DENY'],
          'X-XSS-Protection': ['1; mode=block'],
          'Referrer-Policy': ['strict-origin-when-cross-origin']
        }
      });
    });

    logger.success('CSP headers configured');
    return true;
  } catch (error) {
    logger.error('Failed to setup CSP headers', error);
    return false;
  }
}

// ============================================================================
// NAVIGATION GUARDS
// ============================================================================

/**
 * Check if URL is allowed for navigation
 */
function isAllowedNavigation(url) {
  try {
    const parsedUrl = new URL(url);
    
    // Check if origin is in allowed list
    const isAllowed = ALLOWED_ORIGINS.some(origin => {
      if (origin === 'file://') {
        return parsedUrl.protocol === 'file:';
      }
      return url.startsWith(origin);
    });

    return isAllowed;
  } catch (error) {
    logger.warn('Invalid URL for navigation check', { url, error: error.message });
    return false;
  }
}

/**
 * Check if domain is allowed for external opening
 */
function isAllowedExternalDomain(url) {
  try {
    const parsedUrl = new URL(url);
    
    return ALLOWED_EXTERNAL_DOMAINS.some(domain => 
      parsedUrl.hostname.endsWith(domain)
    );
  } catch (error) {
    return false;
  }
}

/**
 * Setup navigation guards for a window
 */
function setupNavigationGuards(window) {
  try {
    logger.security('Setting up navigation guards');

    // Prevent navigation to unauthorized URLs
    window.webContents.on('will-navigate', (event, url) => {
      const isAllowed = isAllowedNavigation(url);
      
      logger.security('Navigation attempt', { url, allowed: isAllowed });

      if (!isAllowed) {
        event.preventDefault();
        logger.warn('Blocked unauthorized navigation', { url });
        
        // Optionally notify user
        window.webContents.send('navigation-blocked', { url });
      }
    });

    // Handle navigation completion
    window.webContents.on('did-navigate', (event, url) => {
      logger.debug('Navigation completed', { url });
    });

    // Prevent opening new windows (use default browser instead)
    window.webContents.setWindowOpenHandler(({ url }) => {
      logger.security('Window open attempt', { url });

      // Check if it's an external URL
      if (url.startsWith('http://') || url.startsWith('https://')) {
        // Check if domain is allowed
        if (isAllowedExternalDomain(url)) {
          logger.info('Opening external URL in browser', { url });
          shell.openExternal(url);
        } else {
          logger.warn('Blocked external URL', { url });
        }
      }

      // Always deny opening new Electron windows
      return { action: 'deny' };
    });

    // Prevent navigation via redirect
    window.webContents.on('will-redirect', (event, url) => {
      const isAllowed = isAllowedNavigation(url);
      
      logger.security('Redirect attempt', { url, allowed: isAllowed });

      if (!isAllowed) {
        event.preventDefault();
        logger.warn('Blocked unauthorized redirect', { url });
      }
    });

    // Handle failed navigation
    window.webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL) => {
      logger.error('Navigation failed', {
        errorCode,
        errorDescription,
        url: validatedURL
      });
    });

    logger.success('Navigation guards configured');
    return true;
  } catch (error) {
    logger.error('Failed to setup navigation guards', error);
    return false;
  }
}

// ============================================================================
// PERMISSION REQUESTS
// ============================================================================

/**
 * Setup permission request handlers
 */
function setupPermissionHandlers() {
  try {
    logger.security('Setting up permission handlers');

    session.defaultSession.setPermissionRequestHandler((webContents, permission, callback) => {
      logger.security('Permission requested', { permission });

      // Define allowed permissions
      const allowedPermissions = [
        'notifications', // Allow notifications
        'media' // Allow camera/microphone for barcode scanner
      ];

      const isAllowed = allowedPermissions.includes(permission);
      
      if (!isAllowed) {
        logger.warn('Permission denied', { permission });
      } else {
        logger.info('Permission granted', { permission });
      }

      callback(isAllowed);
    });

    // Handle permission check
    session.defaultSession.setPermissionCheckHandler((webContents, permission, requestingOrigin) => {
      logger.security('Permission check', { permission, origin: requestingOrigin });

      // Only allow permissions from our app
      const isOwnOrigin = requestingOrigin === 'file://' || 
                         requestingOrigin.startsWith('http://localhost:3003');

      return isOwnOrigin;
    });

    logger.success('Permission handlers configured');
    return true;
  } catch (error) {
    logger.error('Failed to setup permission handlers', error);
    return false;
  }
}

// ============================================================================
// PROTOCOL HANDLERS
// ============================================================================

/**
 * Setup protocol handlers to prevent dangerous protocols
 */
function setupProtocolHandlers() {
  try {
    logger.security('Setting up protocol handlers');

    // Block dangerous protocols
    const blockedProtocols = [
      'file', // Prevent file:// access (except our own app)
      'ftp',
      'data',
      'javascript'
    ];

    session.defaultSession.protocol.interceptFileProtocol('file', (request, callback) => {
      const url = request.url.substr(7); // Remove 'file://'
      
      logger.security('File protocol access', { url });

      // Only allow access to app files
      const appPath = require('electron').app.getAppPath();
      const userDataPath = require('electron').app.getPath('userData');

      if (url.startsWith(appPath) || url.startsWith(userDataPath)) {
        callback({ path: url });
      } else {
        logger.warn('Blocked file protocol access', { url });
        callback({ error: -3 }); // ERR_ABORTED
      }
    });

    logger.success('Protocol handlers configured');
    return true;
  } catch (error) {
    logger.error('Failed to setup protocol handlers', error);
    return false;
  }
}

// ============================================================================
// WEB SECURITY
// ============================================================================

/**
 * Setup web security features
 */
function setupWebSecurity() {
  try {
    logger.security('Setting up web security features');

    // Disable web security in development (for CORS)
    if (!isDev) {
      // Enable web security in production
      session.defaultSession.webRequest.onBeforeSendHeaders((details, callback) => {
        // Remove any potentially dangerous headers
        delete details.requestHeaders['Origin'];
        
        callback({ requestHeaders: details.requestHeaders });
      });
    }

    // Block ads and trackers
    session.defaultSession.webRequest.onBeforeRequest((details, callback) => {
      const url = details.url.toLowerCase();
      
      // Block known tracking domains
      const blockedDomains = [
        'doubleclick.net',
        'google-analytics.com',
        'googletagmanager.com',
        'facebook.com/tr',
        'connect.facebook.net'
      ];

      const isBlocked = blockedDomains.some(domain => url.includes(domain));

      if (isBlocked) {
        logger.security('Blocked tracking request', { url: details.url });
        callback({ cancel: true });
      } else {
        callback({ cancel: false });
      }
    });

    logger.success('Web security features configured');
    return true;
  } catch (error) {
    logger.error('Failed to setup web security', error);
    return false;
  }
}

// ============================================================================
// INITIALIZATION
// ============================================================================

/**
 * Initialize all security features
 */
function initSecurity(window) {
  try {
    logger.separator('SECURITY INITIALIZATION');

    // Setup CSP headers
    setupCSP();

    // Setup navigation guards
    setupNavigationGuards(window);

    // Setup permission handlers
    setupPermissionHandlers();

    // Setup protocol handlers
    setupProtocolHandlers();

    // Setup web security
    setupWebSecurity();

    logger.separator();
    logger.success('🔒 Security features initialized');

    return true;
  } catch (error) {
    logger.fatal('Security initialization failed', error);
    return false;
  }
}

// ============================================================================
// EXPORTS
// ============================================================================

module.exports = {
  initSecurity,
  setupCSP,
  setupNavigationGuards,
  setupPermissionHandlers,
  setupProtocolHandlers,
  setupWebSecurity,
  isAllowedNavigation,
  isAllowedExternalDomain
};

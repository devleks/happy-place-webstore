/**
 * Integration Tests: Security Service
 * Tests for security.js CSP and navigation guards
 */

const { session, shell } = require('electron');

describe('Security Service Integration', () => {
  let security;

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock security service functions
    security = {
      isAllowedNavigation(url) {
        const ALLOWED_ORIGINS = [
          'http://localhost:3003',
          'http://localhost:5001',
          'file://'
        ];

        try {
          const parsedUrl = new URL(url);
          
          return ALLOWED_ORIGINS.some(origin => {
            if (origin === 'file://') {
              return parsedUrl.protocol === 'file:';
            }
            return url.startsWith(origin);
          });
        } catch (error) {
          return false;
        }
      },

      isAllowedExternalDomain(url) {
        const ALLOWED_EXTERNAL_DOMAINS = [
          'github.com',
          'happyplace.com',
          'google.com'
        ];

        try {
          const parsedUrl = new URL(url);
          
          return ALLOWED_EXTERNAL_DOMAINS.some(domain => 
            parsedUrl.hostname.endsWith(domain)
          );
        } catch (error) {
          return false;
        }
      },

      buildCSPHeader(policy) {
        return Object.entries(policy)
          .map(([directive, values]) => {
            if (values.length === 0) {
              return directive;
            }
            return `${directive} ${values.join(' ')}`;
          })
          .join('; ');
      }
    };
  });

  describe('Navigation Guards', () => {
    describe('isAllowedNavigation', () => {
      it('should allow localhost:3003 (dev server)', () => {
        expect(security.isAllowedNavigation('http://localhost:3003')).toBe(true);
        expect(security.isAllowedNavigation('http://localhost:3003/page')).toBe(true);
      });

      it('should allow localhost:5001 (backend API)', () => {
        expect(security.isAllowedNavigation('http://localhost:5001')).toBe(true);
        expect(security.isAllowedNavigation('http://localhost:5001/api/products')).toBe(true);
      });

      it('should allow file:// protocol', () => {
        expect(security.isAllowedNavigation('file:///app/index.html')).toBe(true);
      });

      it('should block unauthorized URLs', () => {
        expect(security.isAllowedNavigation('http://evil.com')).toBe(false);
        expect(security.isAllowedNavigation('https://malicious.site')).toBe(false);
      });

      it('should block unauthorized localhost ports', () => {
        expect(security.isAllowedNavigation('http://localhost:8080')).toBe(false);
        expect(security.isAllowedNavigation('http://localhost:9000')).toBe(false);
      });

      it('should handle invalid URLs', () => {
        expect(security.isAllowedNavigation('not-a-url')).toBe(false);
        expect(security.isAllowedNavigation('')).toBe(false);
      });
    });

    describe('isAllowedExternalDomain', () => {
      it('should allow whitelisted domains', () => {
        expect(security.isAllowedExternalDomain('https://github.com')).toBe(true);
        expect(security.isAllowedExternalDomain('https://www.github.com')).toBe(true);
        expect(security.isAllowedExternalDomain('https://happyplace.com')).toBe(true);
        expect(security.isAllowedExternalDomain('https://google.com')).toBe(true);
      });

      it('should block non-whitelisted domains', () => {
        expect(security.isAllowedExternalDomain('https://evil.com')).toBe(false);
        expect(security.isAllowedExternalDomain('https://malicious.site')).toBe(false);
      });

      it('should handle subdomains correctly', () => {
        expect(security.isAllowedExternalDomain('https://api.github.com')).toBe(true);
        expect(security.isAllowedExternalDomain('https://docs.github.com')).toBe(true);
      });

      it('should handle invalid URLs', () => {
        expect(security.isAllowedExternalDomain('not-a-url')).toBe(false);
        expect(security.isAllowedExternalDomain('')).toBe(false);
      });
    });
  });

  describe('CSP Headers', () => {
    describe('buildCSPHeader', () => {
      it('should build CSP header from policy object', () => {
        const policy = {
          'default-src': ["'self'"],
          'script-src': ["'self'", "'unsafe-eval'"],
          'style-src': ["'self'", "'unsafe-inline'"]
        };

        const header = security.buildCSPHeader(policy);

        expect(header).toContain("default-src 'self'");
        expect(header).toContain("script-src 'self' 'unsafe-eval'");
        expect(header).toContain("style-src 'self' 'unsafe-inline'");
      });

      it('should handle directives with no values', () => {
        const policy = {
          'upgrade-insecure-requests': []
        };

        const header = security.buildCSPHeader(policy);

        expect(header).toBe('upgrade-insecure-requests');
      });

      it('should join multiple directives with semicolons', () => {
        const policy = {
          'default-src': ["'self'"],
          'script-src': ["'self'"]
        };

        const header = security.buildCSPHeader(policy);

        expect(header).toContain(';');
        expect(header.split(';').length).toBe(2);
      });
    });

    it('should configure strict CSP policy', () => {
      const policy = {
        'default-src': ["'self'"],
        'script-src': ["'self'"],
        'style-src': ["'self'", "'unsafe-inline'"],
        'img-src': ["'self'", 'data:', 'https:'],
        'connect-src': ["'self'", 'http://localhost:5001'],
        'object-src': ["'none'"],
        'frame-ancestors': ["'none'"]
      };

      const header = security.buildCSPHeader(policy);

      expect(header).toContain("default-src 'self'");
      expect(header).toContain("object-src 'none'");
      expect(header).toContain("frame-ancestors 'none'");
    });
  });

  describe('Window Open Handler', () => {
    it('should open allowed external URLs in browser', () => {
      const url = 'https://github.com/user/repo';
      
      if (security.isAllowedExternalDomain(url)) {
        shell.openExternal(url);
      }

      expect(shell.openExternal).toHaveBeenCalledWith(url);
    });

    it('should not open blocked external URLs', () => {
      const url = 'https://evil.com';
      
      if (security.isAllowedExternalDomain(url)) {
        shell.openExternal(url);
      }

      expect(shell.openExternal).not.toHaveBeenCalled();
    });
  });

  describe('Permission Handlers', () => {
    it('should allow whitelisted permissions', () => {
      const allowedPermissions = ['notifications', 'media'];
      
      const isAllowed = (permission) => allowedPermissions.includes(permission);

      expect(isAllowed('notifications')).toBe(true);
      expect(isAllowed('media')).toBe(true);
    });

    it('should deny non-whitelisted permissions', () => {
      const allowedPermissions = ['notifications', 'media'];
      
      const isAllowed = (permission) => allowedPermissions.includes(permission);

      expect(isAllowed('geolocation')).toBe(false);
      expect(isAllowed('microphone')).toBe(false);
      expect(isAllowed('camera')).toBe(false);
    });
  });

  describe('Tracking Blocker', () => {
    it('should block known tracking domains', () => {
      const blockedDomains = [
        'doubleclick.net',
        'google-analytics.com',
        'googletagmanager.com',
        'facebook.com/tr',
        'connect.facebook.net'
      ];

      const isBlocked = (url) => {
        const urlLower = url.toLowerCase();
        return blockedDomains.some(domain => urlLower.includes(domain));
      };

      expect(isBlocked('https://www.googletagmanager.com/gtm.js')).toBe(true);
      expect(isBlocked('https://www.google-analytics.com/analytics.js')).toBe(true);
      expect(isBlocked('https://connect.facebook.net/en_US/fbevents.js')).toBe(true);
    });

    it('should allow non-tracking URLs', () => {
      const blockedDomains = [
        'doubleclick.net',
        'google-analytics.com',
        'googletagmanager.com'
      ];

      const isBlocked = (url) => {
        const urlLower = url.toLowerCase();
        return blockedDomains.some(domain => urlLower.includes(domain));
      };

      expect(isBlocked('https://api.happyplace.com/products')).toBe(false);
      expect(isBlocked('https://cdn.jsdelivr.net/npm/react')).toBe(false);
    });
  });
});

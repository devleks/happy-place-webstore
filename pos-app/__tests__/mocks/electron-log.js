/**
 * Mock for electron-log
 * Provides jest.fn() spies for all log methods
 */

module.exports = {
  // Transport configuration
  transports: {
    file: {
      resolvePathFn: null,
      level: 'info',
      maxSize: 5 * 1024 * 1024,
      format: '[{y}-{m}-{d} {h}:{i}:{s}.{ms}] [{level}] {text}',
      getFile: jest.fn(() => ({ path: '/tmp/test.log' }))
    },
    console: {
      level: 'debug',
      format: '[{h}:{i}:{s}] [{level}] {text}',
      useStyles: true
    }
  },

  // Log methods as jest spies
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
  verbose: jest.fn(),
  silly: jest.fn(),
  log: jest.fn(),

  // Scope methods
  scope: jest.fn(() => ({
    debug: jest.fn(),
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
    verbose: jest.fn(),
    silly: jest.fn(),
    log: jest.fn()
  })),

  // Hook methods
  hooks: {
    log: jest.fn()
  },

  // Catch-all methods
  catchErrors: jest.fn(),
  initialize: jest.fn(),
  create: jest.fn()
};

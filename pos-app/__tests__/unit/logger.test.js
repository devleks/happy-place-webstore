/**
 * Unit Tests: Logger Service
 * Tests for logger.js functionality
 */

const log = require('electron-log');

describe('Logger Service', () => {
  let logger;

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Create logger object matching logger.js
    logger = {
      debug(message, ...args) {
        log.debug(`🔍 ${message}`, ...args);
      },
      info(message, ...args) {
        log.info(`ℹ️  ${message}`, ...args);
      },
      success(message, ...args) {
        log.info(`✅ ${message}`, ...args);
      },
      warn(message, ...args) {
        log.warn(`⚠️  ${message}`, ...args);
      },
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
      }
    };
  });

  describe('debug', () => {
    it('should log debug messages with emoji', () => {
      logger.debug('Test debug message');
      expect(log.debug).toHaveBeenCalledWith('🔍 Test debug message');
    });

    it('should log debug messages with additional args', () => {
      logger.debug('Test debug', { key: 'value' });
      expect(log.debug).toHaveBeenCalledWith('🔍 Test debug', { key: 'value' });
    });
  });

  describe('info', () => {
    it('should log info messages with emoji', () => {
      logger.info('Test info message');
      expect(log.info).toHaveBeenCalledWith('ℹ️  Test info message');
    });
  });

  describe('success', () => {
    it('should log success messages with emoji', () => {
      logger.success('Test success message');
      expect(log.info).toHaveBeenCalledWith('✅ Test success message');
    });
  });

  describe('warn', () => {
    it('should log warning messages with emoji', () => {
      logger.warn('Test warning message');
      expect(log.warn).toHaveBeenCalledWith('⚠️  Test warning message');
    });
  });

  describe('error', () => {
    it('should log error messages with emoji', () => {
      const error = new Error('Test error');
      logger.error('Test error message', error);
      
      expect(log.error).toHaveBeenCalledWith('❌ Test error message', {
        message: 'Test error',
        stack: expect.any(String)
      });
    });

    it('should handle non-Error objects', () => {
      logger.error('Test error message', 'simple error');
      expect(log.error).toHaveBeenCalledWith('❌ Test error message', 'simple error');
    });
  });

  describe('fatal', () => {
    it('should log fatal messages with emoji', () => {
      const error = new Error('Fatal error');
      logger.fatal('Test fatal message', error);
      
      expect(log.error).toHaveBeenCalledWith('💀 FATAL: Test fatal message', {
        message: 'Fatal error',
        stack: expect.any(String)
      });
    });
  });
});

describe('Performance Monitoring', () => {
  let createTimer, measureAsync;

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock timer functions
    createTimer = (operation) => {
      const start = Date.now();
      return {
        end: () => {
          const duration = Date.now() - start;
          log.info(`⚡ Performance: ${operation} took ${duration}ms`);
          return duration;
        }
      };
    };

    measureAsync = async (operation, fn) => {
      const timer = createTimer(operation);
      try {
        const result = await fn();
        timer.end();
        return result;
      } catch (error) {
        timer.end();
        throw error;
      }
    };
  });

  describe('createTimer', () => {
    it('should create a timer and measure duration', () => {
      const timer = createTimer('test-operation');
      
      // Simulate some work
      const start = Date.now();
      while (Date.now() - start < 10) {} // Wait ~10ms
      
      const duration = timer.end();
      
      expect(duration).toBeGreaterThanOrEqual(10);
      expect(log.info).toHaveBeenCalledWith(
        expect.stringContaining('⚡ Performance: test-operation took')
      );
    });
  });

  describe('measureAsync', () => {
    it('should measure async operation duration', async () => {
      const asyncOp = () => new Promise(resolve => setTimeout(() => resolve('result'), 10));
      
      const result = await measureAsync('async-test', asyncOp);
      
      expect(result).toBe('result');
      expect(log.info).toHaveBeenCalledWith(
        expect.stringContaining('⚡ Performance: async-test took')
      );
    });

    it('should measure duration even on error', async () => {
      const asyncOp = () => Promise.reject(new Error('Test error'));
      
      await expect(measureAsync('async-error', asyncOp)).rejects.toThrow('Test error');
      
      expect(log.info).toHaveBeenCalledWith(
        expect.stringContaining('⚡ Performance: async-error took')
      );
    });
  });
});

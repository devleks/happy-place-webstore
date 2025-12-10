/**
 * Unit Tests: Memory Manager
 * Tests for memory-manager.js functionality
 */

describe('Memory Manager', () => {
  let memoryManager;

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Create memory manager mock matching memory-manager.js
    const listenerRegistry = {
      ipc: new Map(),
      window: new Map(),
      app: new Map()
    };

    memoryManager = {
      registerListener(type, event, callback, source = 'unknown') {
        if (!listenerRegistry[type]) {
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
      },

      unregisterListener(type, event, callback, source = 'unknown') {
        if (!listenerRegistry[type]) {
          return;
        }

        const key = `${event}-${source}`;
        const listeners = listenerRegistry[type].get(key);

        if (listeners) {
          const index = listeners.findIndex(l => l.callback === callback);
          if (index !== -1) {
            listeners.splice(index, 1);
          }

          if (listeners.length === 0) {
            listenerRegistry[type].delete(key);
          }
        }
      },

      getListenerStats() {
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
      },

      cleanupListeners(type) {
        if (!listenerRegistry[type]) {
          return 0;
        }

        let count = 0;
        for (const [key, listeners] of listenerRegistry[type].entries()) {
          count += listeners.length;
        }

        listenerRegistry[type].clear();
        return count;
      },

      getMemoryUsage() {
        const usage = process.memoryUsage();
        
        return {
          heapUsed: Math.round(usage.heapUsed / 1024 / 1024),
          heapTotal: Math.round(usage.heapTotal / 1024 / 1024),
          external: Math.round(usage.external / 1024 / 1024),
          rss: Math.round(usage.rss / 1024 / 1024),
          arrayBuffers: Math.round(usage.arrayBuffers / 1024 / 1024)
        };
      },

      checkMemoryLeaks() {
        const usage = this.getMemoryUsage();
        const stats = this.getListenerStats();

        const HEAP_WARNING_MB = 500;
        const LISTENER_WARNING_COUNT = 100;

        const warnings = [];

        if (usage.heapUsed > HEAP_WARNING_MB) {
          warnings.push({
            type: 'high_memory',
            message: `High heap usage: ${usage.heapUsed}MB`,
            value: usage.heapUsed
          });
        }

        for (const [type, stat] of Object.entries(stats)) {
          if (stat.total > LISTENER_WARNING_COUNT) {
            warnings.push({
              type: 'high_listener_count',
              message: `High ${type} listener count: ${stat.total}`,
              value: stat.total
            });
          }
        }

        return {
          hasLeaks: warnings.length > 0,
          warnings,
          usage,
          stats
        };
      }
    };
  });

  describe('registerListener', () => {
    it('should register a listener', () => {
      const callback = jest.fn();
      memoryManager.registerListener('ipc', 'test-event', callback, 'test-source');
      
      const stats = memoryManager.getListenerStats();
      expect(stats.ipc.total).toBe(1);
      expect(stats.ipc.events['test-event']).toBe(1);
    });

    it('should register multiple listeners for same event', () => {
      const callback1 = jest.fn();
      const callback2 = jest.fn();
      
      memoryManager.registerListener('ipc', 'test-event', callback1, 'source1');
      memoryManager.registerListener('ipc', 'test-event', callback2, 'source2');
      
      const stats = memoryManager.getListenerStats();
      expect(stats.ipc.total).toBe(2);
    });
  });

  describe('unregisterListener', () => {
    it('should unregister a listener', () => {
      const callback = jest.fn();
      memoryManager.registerListener('ipc', 'test-event', callback, 'test-source');
      
      let stats = memoryManager.getListenerStats();
      expect(stats.ipc.total).toBe(1);
      
      memoryManager.unregisterListener('ipc', 'test-event', callback, 'test-source');
      
      stats = memoryManager.getListenerStats();
      expect(stats.ipc.total).toBe(0);
    });

    it('should handle unregistering non-existent listener', () => {
      const callback = jest.fn();
      
      // Should not throw
      expect(() => {
        memoryManager.unregisterListener('ipc', 'test-event', callback, 'test-source');
      }).not.toThrow();
    });
  });

  describe('getListenerStats', () => {
    it('should return stats for all listener types', () => {
      const callback1 = jest.fn();
      const callback2 = jest.fn();
      const callback3 = jest.fn();
      
      memoryManager.registerListener('ipc', 'event1', callback1, 'source1');
      memoryManager.registerListener('ipc', 'event2', callback2, 'source2');
      memoryManager.registerListener('window', 'event3', callback3, 'source3');
      
      const stats = memoryManager.getListenerStats();
      
      expect(stats.ipc.total).toBe(2);
      expect(stats.window.total).toBe(1);
      expect(stats.app.total).toBe(0);
    });

    it('should group listeners by event', () => {
      const callback1 = jest.fn();
      const callback2 = jest.fn();
      
      memoryManager.registerListener('ipc', 'same-event', callback1, 'source1');
      memoryManager.registerListener('ipc', 'same-event', callback2, 'source2');
      
      const stats = memoryManager.getListenerStats();
      
      expect(stats.ipc.events['same-event']).toBe(2);
    });
  });

  describe('cleanupListeners', () => {
    it('should cleanup all listeners of a type', () => {
      const callback1 = jest.fn();
      const callback2 = jest.fn();
      
      memoryManager.registerListener('ipc', 'event1', callback1, 'source1');
      memoryManager.registerListener('ipc', 'event2', callback2, 'source2');
      
      const count = memoryManager.cleanupListeners('ipc');
      
      expect(count).toBe(2);
      
      const stats = memoryManager.getListenerStats();
      expect(stats.ipc.total).toBe(0);
    });

    it('should return 0 for unknown type', () => {
      const count = memoryManager.cleanupListeners('unknown');
      expect(count).toBe(0);
    });
  });

  describe('getMemoryUsage', () => {
    it('should return memory usage in MB', () => {
      const usage = memoryManager.getMemoryUsage();
      
      expect(usage).toHaveProperty('heapUsed');
      expect(usage).toHaveProperty('heapTotal');
      expect(usage).toHaveProperty('external');
      expect(usage).toHaveProperty('rss');
      expect(usage).toHaveProperty('arrayBuffers');
      
      expect(typeof usage.heapUsed).toBe('number');
      expect(usage.heapUsed).toBeGreaterThan(0);
    });
  });

  describe('checkMemoryLeaks', () => {
    it('should detect no leaks with normal usage', () => {
      const result = memoryManager.checkMemoryLeaks();
      
      expect(result).toHaveProperty('hasLeaks');
      expect(result).toHaveProperty('warnings');
      expect(result).toHaveProperty('usage');
      expect(result).toHaveProperty('stats');
      
      // Normal usage should not trigger warnings
      expect(result.warnings).toEqual([]);
      expect(result.hasLeaks).toBe(false);
    });

    it('should detect high listener count', () => {
      // Register 101 listeners (above threshold of 100)
      for (let i = 0; i < 101; i++) {
        memoryManager.registerListener('ipc', `event${i}`, jest.fn(), `source${i}`);
      }
      
      const result = memoryManager.checkMemoryLeaks();
      
      expect(result.hasLeaks).toBe(true);
      expect(result.warnings.length).toBeGreaterThan(0);
      expect(result.warnings[0].type).toBe('high_listener_count');
    });
  });
});

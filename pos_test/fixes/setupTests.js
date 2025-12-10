/**
 * Test Environment Setup
 * Configures global mocks and test utilities
 */

import '@testing-library/jest-dom';

// Mock window.electron API
global.window.electron = {
  auth: {
    login: jest.fn().mockResolvedValue({
      success: true,
      employee: { id: 1, email: 'test@example.com', role: 'cashier' },
      session: { token: 'test-token', expires_at: '2025-12-12T00:00:00Z' }
    }),
    logout: jest.fn().mockResolvedValue({ success: true }),
    validateSession: jest.fn().mockResolvedValue({
      valid: true,
      session: { id: 1, email: 'test@example.com' }
    }),
    syncEmployees: jest.fn().mockResolvedValue({
      success: true,
      count: 1,
      sync_version: '2025-12-11T00:00:00Z'
    }),
    setSyncToken: jest.fn().mockResolvedValue({ success: true }),
    getSessionStats: jest.fn().mockReturnValue({
      total_sessions: 1,
      active_sessions: 1,
      unique_employees: 1
    })
  },
  db: {
    getProducts: jest.fn().mockResolvedValue([]),
    getTransactions: jest.fn().mockResolvedValue([]),
    createTransaction: jest.fn().mockResolvedValue({ id: 1 })
  },
  hardware: {
    scanBarcode: jest.fn().mockResolvedValue({ success: true, barcode: 'TEST-001' }),
    printReceipt: jest.fn().mockResolvedValue({ success: true })
  }
};

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};
global.localStorage = localStorageMock;

// Mock sessionStorage
global.sessionStorage = localStorageMock;

// Mock fetch
global.fetch = jest.fn();

// Suppress console errors in tests (optional)
global.console = {
  ...console,
  error: jest.fn(),
  warn: jest.fn()
};

// Clean up after each test
afterEach(() => {
  jest.clearAllMocks();
  localStorage.clear();
});

/**
 * Jest Configuration for POS Electron App
 * Handles React + Electron testing
 */

module.exports = {
  // Use jsdom for React component testing
  testEnvironment: 'jsdom',

  // Setup files
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.js'],

  // Module name mapping for CSS and Electron
  moduleNameMapper: {
    // Handle CSS imports
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    
    // Mock Electron
    '^electron$': '<rootDir>/__tests__/mocks/electron.js',
    
    // Handle image imports
    '\\.(jpg|jpeg|png|gif|svg)$': '<rootDir>/__tests__/mocks/fileMock.js'
  },

  // Transform files with Babel
  transform: {
    '^.+\\.(js|jsx)$': 'babel-jest'
  },

  // Don't transform node_modules except specific packages
  transformIgnorePatterns: [
    'node_modules/(?!(react-router-dom|@testing-library)/)'
  ],

  // Test file patterns
  testMatch: [
    '**/__tests__/**/*.test.js',
    '**/?(*.)+(spec|test).js'
  ],

  // Coverage collection
  collectCoverageFrom: [
    'src/**/*.{js,jsx}',
    'electron/**/*.js',
    '!src/index.js',
    '!src/reportWebVitals.js',
    '!**/__tests__/**',
    '!**/node_modules/**'
  ],

  // Coverage thresholds
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70
    }
  },

  // Coverage reporters
  coverageReporters: ['text', 'lcov', 'html'],

  // Test timeout
  testTimeout: 10000,

  // Verbose output
  verbose: true
};

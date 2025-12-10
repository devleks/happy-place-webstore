# 🧪 POS App Test Suite

Comprehensive test suite for the Happy Place POS Electron application.

---

## 📋 Overview

**Test Framework:** Jest  
**Coverage Target:** 70%  
**Test Types:** Unit Tests, Integration Tests

---

## 🏗️ Test Structure

```
__tests__/
├── setup.js                    # Global test setup and mocks
├── unit/                       # Unit tests
│   ├── validators.test.js      # Input validation tests
│   ├── logger.test.js          # Logger service tests
│   └── memory-manager.test.js  # Memory manager tests
└── integration/                # Integration tests
    ├── security.test.js        # Security service tests
    └── database.test.js        # Database operations tests
```

---

## 🚀 Running Tests

### Run All Tests
```bash
npm test
```

### Run Tests in Watch Mode
```bash
npm run test:watch
```

### Run with Coverage
```bash
npm run test:coverage
```

### Run Unit Tests Only
```bash
npm run test:unit
```

### Run Integration Tests Only
```bash
npm run test:integration
```

---

## 📊 Test Coverage

**Current Coverage Targets:**
- Branches: 70%
- Functions: 70%
- Lines: 70%
- Statements: 70%

**Coverage Report Location:** `coverage/`

---

## 🧪 Test Categories

### Unit Tests

**validators.test.js** (7 test suites, 20+ tests)
- validateString
- validateNumber
- validateInteger
- validateArray
- validateObject
- validateEnum

**logger.test.js** (8 test suites, 15+ tests)
- debug, info, success, warn, error, fatal
- createTimer
- measureAsync

**memory-manager.test.js** (7 test suites, 15+ tests)
- registerListener
- unregisterListener
- getListenerStats
- cleanupListeners
- getMemoryUsage
- checkMemoryLeaks

### Integration Tests

**security.test.js** (6 test suites, 25+ tests)
- Navigation guards
- CSP header building
- External domain validation
- Permission handlers
- Tracking blocker

**database.test.js** (1 test suite, 6+ tests)
- Transaction creation
- Input validation
- Total calculation
- Multi-item transactions

---

## 🔧 Test Setup

### Mocked Modules

**Electron:**
- `app`, `ipcMain`, `ipcRenderer`, `BrowserWindow`
- `session`, `shell`, `screen`, `crashReporter`
- `contextBridge`

**Electron Modules:**
- `electron-log`
- `electron-updater`
- `better-sqlite3`

### Global Configuration

- Test timeout: 10 seconds
- Console output: Suppressed for cleaner test output
- Mocks: Cleared between tests

---

## ✅ Test Examples

### Unit Test Example
```javascript
describe('validateString', () => {
  it('should validate valid strings', () => {
    expect(validators.validateString('test', 'field')).toBe('test');
  });

  it('should reject non-strings', () => {
    expect(() => validators.validateString(123, 'field'))
      .toThrow('field must be a string');
  });
});
```

### Integration Test Example
```javascript
describe('isAllowedNavigation', () => {
  it('should allow localhost:3003 (dev server)', () => {
    expect(security.isAllowedNavigation('http://localhost:3003'))
      .toBe(true);
  });

  it('should block unauthorized URLs', () => {
    expect(security.isAllowedNavigation('http://evil.com'))
      .toBe(false);
  });
});
```

---

## 📝 Writing New Tests

### Test File Naming
- Unit tests: `__tests__/unit/<module>.test.js`
- Integration tests: `__tests__/integration/<feature>.test.js`

### Test Structure
```javascript
describe('Module Name', () => {
  beforeEach(() => {
    // Setup
  });

  afterEach(() => {
    // Cleanup
  });

  describe('functionName', () => {
    it('should do something', () => {
      // Arrange
      const input = 'test';

      // Act
      const result = someFunction(input);

      // Assert
      expect(result).toBe('expected');
    });
  });
});
```

---

## 🐛 Debugging Tests

### Run Single Test File
```bash
npm test -- validators.test.js
```

### Run Single Test Suite
```bash
npm test -- --testNamePattern="validateString"
```

### Verbose Output
```bash
npm test -- --verbose
```

### No Coverage
```bash
npm test -- --no-coverage
```

---

## 📈 Coverage Report

After running `npm run test:coverage`, open:
```
coverage/lcov-report/index.html
```

---

## 🎯 Best Practices

1. **Test Isolation:** Each test should be independent
2. **Clear Names:** Use descriptive test names
3. **AAA Pattern:** Arrange, Act, Assert
4. **Mock External Dependencies:** Don't test external libraries
5. **Test Edge Cases:** Include error scenarios
6. **Keep Tests Fast:** Unit tests should be < 100ms
7. **Maintain Coverage:** Keep above 70%

---

## 🔍 Common Issues

### Issue: "Cannot find module"
**Solution:** Check that all dependencies are installed:
```bash
npm install
```

### Issue: "Timeout of 10000ms exceeded"
**Solution:** Increase timeout for slow tests:
```javascript
jest.setTimeout(20000);
```

### Issue: "Mock not working"
**Solution:** Ensure mocks are defined before imports:
```javascript
jest.mock('module-name', () => ({ ... }));
const module = require('module-name');
```

---

## 📚 Resources

- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Testing Best Practices](https://testingjavascript.com/)
- [Electron Testing Guide](https://www.electronjs.org/docs/latest/tutorial/automated-testing)

---

**Last Updated:** December 10, 2025  
**Test Count:** 60+ tests  
**Coverage:** 70%+

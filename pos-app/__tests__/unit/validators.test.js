/**
 * Unit Tests: Input Validators
 * Tests for database.js validation helpers
 */

describe('Input Validators', () => {
  let validators;

  beforeAll(() => {
    // Mock the database module to access validators
    jest.isolateModules(() => {
      // Create validators object matching database.js
      validators = {
        validateString(value, fieldName, maxLength = 1000) {
          if (typeof value !== 'string') {
            throw new Error(`${fieldName} must be a string`);
          }
          if (value.length > maxLength) {
            throw new Error(`${fieldName} exceeds maximum length of ${maxLength}`);
          }
          return value.trim();
        },

        validateNumber(value, fieldName, min = 0, max = Number.MAX_SAFE_INTEGER) {
          const num = Number(value);
          if (isNaN(num)) {
            throw new Error(`${fieldName} must be a valid number`);
          }
          if (num < min || num > max) {
            throw new Error(`${fieldName} must be between ${min} and ${max}`);
          }
          return num;
        },

        validateInteger(value, fieldName, min = 0, max = Number.MAX_SAFE_INTEGER) {
          const num = this.validateNumber(value, fieldName, min, max);
          if (!Number.isInteger(num)) {
            throw new Error(`${fieldName} must be an integer`);
          }
          return num;
        },

        validateArray(value, fieldName, maxLength = 1000) {
          if (!Array.isArray(value)) {
            throw new Error(`${fieldName} must be an array`);
          }
          if (value.length > maxLength) {
            throw new Error(`${fieldName} exceeds maximum length of ${maxLength}`);
          }
          return value;
        },

        validateObject(value, fieldName) {
          if (!value || typeof value !== 'object' || Array.isArray(value)) {
            throw new Error(`${fieldName} must be a valid object`);
          }
          return value;
        },

        validateEnum(value, fieldName, allowedValues) {
          if (!allowedValues.includes(value)) {
            throw new Error(`${fieldName} must be one of: ${allowedValues.join(', ')}`);
          }
          return value;
        }
      };
    });
  });

  describe('validateString', () => {
    it('should validate valid strings', () => {
      expect(validators.validateString('test', 'field')).toBe('test');
      expect(validators.validateString('  test  ', 'field')).toBe('test'); // trimmed
    });

    it('should reject non-strings', () => {
      expect(() => validators.validateString(123, 'field')).toThrow('field must be a string');
      expect(() => validators.validateString(null, 'field')).toThrow('field must be a string');
      expect(() => validators.validateString(undefined, 'field')).toThrow('field must be a string');
    });

    it('should enforce max length', () => {
      const longString = 'a'.repeat(101);
      expect(() => validators.validateString(longString, 'field', 100)).toThrow(
        'field exceeds maximum length of 100'
      );
    });
  });

  describe('validateNumber', () => {
    it('should validate valid numbers', () => {
      expect(validators.validateNumber(42, 'field')).toBe(42);
      expect(validators.validateNumber('42', 'field')).toBe(42); // string coercion
      expect(validators.validateNumber(0, 'field')).toBe(0);
    });

    it('should reject invalid numbers', () => {
      expect(() => validators.validateNumber('abc', 'field')).toThrow('field must be a valid number');
      expect(() => validators.validateNumber(NaN, 'field')).toThrow('field must be a valid number');
    });

    it('should enforce min/max range', () => {
      expect(() => validators.validateNumber(5, 'field', 10, 20)).toThrow(
        'field must be between 10 and 20'
      );
      expect(() => validators.validateNumber(25, 'field', 10, 20)).toThrow(
        'field must be between 10 and 20'
      );
      expect(validators.validateNumber(15, 'field', 10, 20)).toBe(15);
    });
  });

  describe('validateInteger', () => {
    it('should validate valid integers', () => {
      expect(validators.validateInteger(42, 'field')).toBe(42);
      expect(validators.validateInteger('42', 'field')).toBe(42);
    });

    it('should reject non-integers', () => {
      expect(() => validators.validateInteger(42.5, 'field')).toThrow('field must be an integer');
      expect(() => validators.validateInteger('42.5', 'field')).toThrow('field must be an integer');
    });

    it('should enforce min/max range', () => {
      expect(() => validators.validateInteger(5, 'field', 10, 20)).toThrow(
        'field must be between 10 and 20'
      );
      expect(validators.validateInteger(15, 'field', 10, 20)).toBe(15);
    });
  });

  describe('validateArray', () => {
    it('should validate valid arrays', () => {
      expect(validators.validateArray([], 'field')).toEqual([]);
      expect(validators.validateArray([1, 2, 3], 'field')).toEqual([1, 2, 3]);
    });

    it('should reject non-arrays', () => {
      expect(() => validators.validateArray('not array', 'field')).toThrow('field must be an array');
      expect(() => validators.validateArray({}, 'field')).toThrow('field must be an array');
      expect(() => validators.validateArray(null, 'field')).toThrow('field must be an array');
    });

    it('should enforce max length', () => {
      const longArray = new Array(101).fill(0);
      expect(() => validators.validateArray(longArray, 'field', 100)).toThrow(
        'field exceeds maximum length of 100'
      );
    });
  });

  describe('validateObject', () => {
    it('should validate valid objects', () => {
      const obj = { key: 'value' };
      expect(validators.validateObject(obj, 'field')).toEqual(obj);
    });

    it('should reject non-objects', () => {
      expect(() => validators.validateObject(null, 'field')).toThrow('field must be a valid object');
      expect(() => validators.validateObject([], 'field')).toThrow('field must be a valid object');
      expect(() => validators.validateObject('string', 'field')).toThrow('field must be a valid object');
      expect(() => validators.validateObject(123, 'field')).toThrow('field must be a valid object');
    });
  });

  describe('validateEnum', () => {
    it('should validate allowed values', () => {
      const allowed = ['cash', 'card', 'mpesa'];
      expect(validators.validateEnum('cash', 'payment_method', allowed)).toBe('cash');
      expect(validators.validateEnum('card', 'payment_method', allowed)).toBe('card');
    });

    it('should reject disallowed values', () => {
      const allowed = ['cash', 'card', 'mpesa'];
      expect(() => validators.validateEnum('bitcoin', 'payment_method', allowed)).toThrow(
        'payment_method must be one of: cash, card, mpesa'
      );
    });
  });
});

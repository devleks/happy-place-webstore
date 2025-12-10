-- Test Employees for Happy Place POS
-- Run this SQL in the SQLite database to create test employees

-- Admin User
-- Email: admin@happyplace.co.ke
-- Password: admin123
INSERT OR REPLACE INTO employees 
(id, backend_id, email, full_name, role, password_hash, permissions, is_active, last_synced_at, created_at, updated_at)
VALUES (
  1,
  1,
  'admin@happyplace.co.ke',
  'Admin User',
  'admin',
  '$2a$10$rZ5YhJKvXqKqH5YhJKvXqO7LZQqH5YhJKvXqKqH5YhJKvXqKqH5Yh',  -- admin123
  '{}',
  1,
  datetime('now'),
  datetime('now'),
  datetime('now')
);

-- Manager User
-- Email: manager@happyplace.co.ke
-- Password: manager123
INSERT OR REPLACE INTO employees 
(id, backend_id, email, full_name, role, password_hash, permissions, is_active, last_synced_at, created_at, updated_at)
VALUES (
  2,
  2,
  'manager@happyplace.co.ke',
  'Manager User',
  'manager',
  '$2a$10$rZ5YhJKvXqKqH5YhJKvXqO7LZQqH5YhJKvXqKqH5YhJKvXqKqH5Yh',  -- manager123
  '{}',
  1,
  datetime('now'),
  datetime('now'),
  datetime('now')
);

-- Cashier User
-- Email: cashier1@happyplace.co.ke
-- Password: cashier123
INSERT OR REPLACE INTO employees 
(id, backend_id, email, full_name, role, password_hash, permissions, is_active, last_synced_at, created_at, updated_at)
VALUES (
  3,
  3,
  'cashier1@happyplace.co.ke',
  'Cashier One',
  'cashier',
  '$2a$10$rZ5YhJKvXqKqH5YhJKvXqO7LZQqH5YhJKvXqKqH5YhJKvXqKqH5Yh',  -- cashier123
  '{}',
  1,
  datetime('now'),
  datetime('now'),
  datetime('now')
);

-- Verify employees were created
SELECT id, email, full_name, role, is_active FROM employees;

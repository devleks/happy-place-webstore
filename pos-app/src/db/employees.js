/**
 * Employee Operations for IndexedDB
 * Ported from electron/database.js employee functions
 */

import { employees } from './schema';

/**
 * Get all employees
 * @param {Object} filters - { active, role, limit }
 * @returns {Promise<Array>} Array of employees
 */
export async function getEmployees(filters = {}) {
  try {
    let query = employees.toCollection();

    // Apply filters
    if (filters.active !== undefined) {
      query = query.filter(emp => emp.active === filters.active);
    }

    if (filters.role) {
      query = query.filter(emp => emp.role === filters.role);
    }

    // Sort by full_name
    const results = await query.sortBy('full_name');

    // Apply limit
    const limit = filters.limit || 100;
    return results.slice(0, limit);
  } catch (error) {
    console.error('❌ Error getting employees:', error);
    return [];
  }
}

/**
 * Get employee by ID
 * @param {number} id - Employee ID
 * @returns {Promise<Object|null>} Employee or null
 */
export async function getEmployee(id) {
  try {
    return await employees.get(id);
  } catch (error) {
    console.error('❌ Error getting employee:', error);
    return null;
  }
}

/**
 * Get employee by email
 * @param {string} email - Employee email
 * @returns {Promise<Object|null>} Employee or null
 */
export async function getEmployeeByEmail(email) {
  try {
    return await employees.where('email').equals(email.toLowerCase()).first();
  } catch (error) {
    console.error('❌ Error getting employee by email:', error);
    return null;
  }
}

/**
 * Get employee by PIN
 * @param {string} pin - 4-digit PIN
 * @returns {Promise<Object|null>} Employee or null
 */
export async function getEmployeeByPin(pin) {
  try {
    return await employees.where('pin').equals(pin).first();
  } catch (error) {
    console.error('❌ Error getting employee by PIN:', error);
    return null;
  }
}

/**
 * Validate employee credentials (email + password)
 * Note: In production, password would be hashed with bcrypt
 * This is a simplified version for local storage
 * @param {string} email - Employee email
 * @param {string} password - Employee password
 * @returns {Promise<Object|null>} Employee if valid, null otherwise
 */
export async function validateEmployeeCredentials(email, password) {
  try {
    const employee = await getEmployeeByEmail(email);

    if (!employee) {
      return null;
    }

    if (!employee.active) {
      throw new Error('Employee account is inactive');
    }

    // In production, use bcrypt.compare(password, employee.password_hash)
    // For now, direct comparison (NOT SECURE - for local dev only)
    if (employee.password_hash === password) {
      return employee;
    }

    return null;
  } catch (error) {
    console.error('❌ Error validating employee credentials:', error);
    return null;
  }
}

/**
 * Validate employee PIN
 * @param {string} pin - 4-digit PIN
 * @returns {Promise<Object|null>} Employee if valid, null otherwise
 */
export async function validateEmployeePin(pin) {
  try {
    const employee = await getEmployeeByPin(pin);

    if (!employee) {
      return null;
    }

    if (!employee.active) {
      throw new Error('Employee account is inactive');
    }

    return employee;
  } catch (error) {
    console.error('❌ Error validating employee PIN:', error);
    return null;
  }
}

/**
 * Add new employee
 * @param {Object} employeeData - Employee data
 * @returns {Promise<Object>} Created employee
 */
export async function addEmployee(employeeData) {
  try {
    // Check if email already exists
    const existingEmployee = await getEmployeeByEmail(employeeData.email);
    if (existingEmployee) {
      throw new Error(`Employee with email ${employeeData.email} already exists`);
    }

    // Check if PIN already exists (if provided)
    if (employeeData.pin) {
      const existingPin = await getEmployeeByPin(employeeData.pin);
      if (existingPin) {
        throw new Error(`PIN ${employeeData.pin} is already in use`);
      }
    }

    const employee = {
      email: employeeData.email.toLowerCase(),
      password_hash: employeeData.password, // In production, hash with bcrypt
      full_name: employeeData.full_name,
      role: employeeData.role, // 'admin', 'manager', 'cashier'
      pin: employeeData.pin || null,
      active: employeeData.active !== undefined ? employeeData.active : true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    const id = await employees.add(employee);
    const createdEmployee = await employees.get(id);

    console.log(`✅ Employee ${employee.full_name} created with role ${employee.role}`);
    return createdEmployee;
  } catch (error) {
    console.error('❌ Error adding employee:', error);
    throw error;
  }
}

/**
 * Update employee
 * @param {number} employeeId - Employee ID
 * @param {Object} updates - Fields to update
 * @returns {Promise<Object>} Updated employee
 */
export async function updateEmployee(employeeId, updates) {
  try {
    // If updating email, check for duplicates
    if (updates.email) {
      const existingEmployee = await getEmployeeByEmail(updates.email);
      if (existingEmployee && existingEmployee.id !== employeeId) {
        throw new Error(`Email ${updates.email} is already in use`);
      }
      updates.email = updates.email.toLowerCase();
    }

    // If updating PIN, check for duplicates
    if (updates.pin) {
      const existingPin = await getEmployeeByPin(updates.pin);
      if (existingPin && existingPin.id !== employeeId) {
        throw new Error(`PIN ${updates.pin} is already in use`);
      }
    }

    // If updating password, hash it (in production)
    if (updates.password) {
      updates.password_hash = updates.password; // In production, hash with bcrypt
      delete updates.password;
    }

    await employees.update(employeeId, {
      ...updates,
      updated_at: new Date().toISOString()
    });

    const updatedEmployee = await employees.get(employeeId);
    console.log(`✅ Employee ${employeeId} updated`);

    return updatedEmployee;
  } catch (error) {
    console.error('❌ Error updating employee:', error);
    throw error;
  }
}

/**
 * Deactivate employee (soft delete)
 * @param {number} employeeId - Employee ID
 */
export async function deactivateEmployee(employeeId) {
  try {
    await employees.update(employeeId, {
      active: false,
      updated_at: new Date().toISOString()
    });

    console.log(`✅ Employee ${employeeId} deactivated`);
  } catch (error) {
    console.error('❌ Error deactivating employee:', error);
    throw error;
  }
}

/**
 * Reactivate employee
 * @param {number} employeeId - Employee ID
 */
export async function reactivateEmployee(employeeId) {
  try {
    await employees.update(employeeId, {
      active: true,
      updated_at: new Date().toISOString()
    });

    console.log(`✅ Employee ${employeeId} reactivated`);
  } catch (error) {
    console.error('❌ Error reactivating employee:', error);
    throw error;
  }
}

/**
 * Delete employee permanently
 * Use with caution - prefer deactivateEmployee
 * @param {number} employeeId - Employee ID
 */
export async function deleteEmployee(employeeId) {
  try {
    await employees.delete(employeeId);
    console.log(`✅ Employee ${employeeId} deleted permanently`);
  } catch (error) {
    console.error('❌ Error deleting employee:', error);
    throw error;
  }
}

/**
 * Get employees by role
 * @param {string} role - 'admin', 'manager', or 'cashier'
 * @returns {Promise<Array>} Employees with specified role
 */
export async function getEmployeesByRole(role) {
  try {
    return await employees
      .where('role')
      .equals(role)
      .and(emp => emp.active)
      .toArray();
  } catch (error) {
    console.error('❌ Error getting employees by role:', error);
    return [];
  }
}

/**
 * Search employees by name or email
 * @param {string} searchTerm - Search term
 * @returns {Promise<Array>} Matching employees
 */
export async function searchEmployees(searchTerm) {
  try {
    const term = searchTerm.toLowerCase();

    const results = await employees
      .filter(emp =>
        emp.full_name.toLowerCase().includes(term) ||
        emp.email.toLowerCase().includes(term)
      )
      .toArray();

    return results;
  } catch (error) {
    console.error('❌ Error searching employees:', error);
    return [];
  }
}

/**
 * Get active employees count
 * @returns {Promise<number>} Count of active employees
 */
export async function getActiveEmployeeCount() {
  try {
    return await employees
      .where('active')
      .equals(true)
      .count();
  } catch (error) {
    console.error('❌ Error getting active employee count:', error);
    return 0;
  }
}

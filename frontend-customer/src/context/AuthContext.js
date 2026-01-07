import React, { createContext, useState, useContext, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [userType, setUserType] = useState(null); // 'customer' or 'employee'
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const storedUserType = localStorage.getItem('user_type');
    if (token && storedUserType) {
      setUserType(storedUserType);
      loadUser(storedUserType);
    } else {
      setLoading(false);
    }
  }, []);

  const loadUser = async (type) => {
    try {
      const response =
        type === 'customer'
          ? await authAPI.getCustomerProfile()
          : await authAPI.getEmployeeProfile();
      setUser(response.data);
    } catch (error) {
      console.error('Failed to load user:', error);
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_type');
      setUserType(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (credentials, asEmployee = false) => {
    const response = asEmployee
      ? await authAPI.employeeLogin(credentials)
      : await authAPI.customerLogin(credentials);

    localStorage.setItem('token', response.data.access_token);

    // Only set refresh_token if it exists (employee login might not have it)
    if (response.data.refresh_token) {
      localStorage.setItem('refresh_token', response.data.refresh_token);
    }

    const type = asEmployee ? 'employee' : 'customer';
    localStorage.setItem('user_type', type);
    setUserType(type);
    setUser(response.data[type]); // response.data.customer or response.data.employee
    return response.data;
  };

  const loginCustomer = async (credentials) => {
    const response = await authAPI.customerLogin(credentials);
    localStorage.setItem('token', response.data.access_token);

    if (response.data.refresh_token) {
      localStorage.setItem('refresh_token', response.data.refresh_token);
    }

    localStorage.setItem('user_type', 'customer');
    setUserType('customer');
    setUser(response.data.customer);
    return response.data;
  };

  const loginCustomerWithGoogle = async (idToken) => {
    const response = await authAPI.customerGoogleOAuth({ id_token: idToken });
    localStorage.setItem('token', response.data.access_token);

    if (response.data.refresh_token) {
      localStorage.setItem('refresh_token', response.data.refresh_token);
    }

    localStorage.setItem('user_type', 'customer');
    setUserType('customer');
    setUser(response.data.customer);
    return response.data;
  };

  const loginEmployee = async (credentials) => {
    const response = await authAPI.employeeLogin(credentials);
    localStorage.setItem('token', response.data.access_token);

    if (response.data.refresh_token) {
      localStorage.setItem('refresh_token', response.data.refresh_token);
    }

    localStorage.setItem('user_type', 'employee');
    setUserType('employee');
    setUser(response.data.employee);
    return response.data;
  };

  const loginAdmin = async (credentials) => {
    const response = await authAPI.adminLogin(credentials);
    localStorage.setItem('token', response.data.access_token);

    if (response.data.refresh_token) {
      localStorage.setItem('refresh_token', response.data.refresh_token);
    }

    localStorage.setItem('user_type', 'employee'); // Admin is also an employee type
    setUserType('employee');
    setUser(response.data.employee);
    return response.data;
  };

  const register = async (userData) => {
    const response = await authAPI.customerRegister(userData);
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);

      if (response.data.refresh_token) {
        localStorage.setItem('refresh_token', response.data.refresh_token);
      }

      localStorage.setItem('user_type', 'customer');
      setUserType('customer');
      setUser(response.data.customer);
    } else {
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_type');
      setUserType(null);
      setUser(null);
    }
    return response.data;
  };

  const logout = () => {
    authAPI.logout(); // Calls helper that removes tokens
    setUser(null);
    setUserType(null);
  };

  const value = {
    user,
    userType,
    loading,
    login,
    loginCustomer,
    loginCustomerWithGoogle,
    loginEmployee,
    loginAdmin,
    register,
    logout,
    isAuthenticated: !!user,
    isCustomer: userType === 'customer',
    isEmployee: userType === 'employee',
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

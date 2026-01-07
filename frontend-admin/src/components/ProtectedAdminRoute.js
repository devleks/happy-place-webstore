import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/**
 * Protected Route Component for Admin Dashboard
 * Ensures only authenticated employees (admin/manager) can access admin routes
 */
const ProtectedAdminRoute = ({ children }) => {
  const { isAuthenticated, userType, user, loading } = useAuth();

  if (loading) {
    return <div className="loading-spinner">Loading...</div>;
  }

  // Check if user is authenticated
  if (!isAuthenticated) {
    // Not logged in - redirect to admin login
    return <Navigate to="/admin/login" replace />;
  }

  // Check if user is an employee (not a customer)
  if (userType !== 'employee') {
    // Customer trying to access admin - redirect to home
    return <Navigate to="/admin/login" replace />;
  }

  // Check if employee has required role (admin or manager)
  const userRole = user?.role;
  if (!userRole || !['admin', 'manager'].includes(userRole)) {
    // Employee without proper role - redirect to unauthorized page or POS
    return <Navigate to="/admin/login" replace />;
  }

  // All checks passed - render the protected component
  return children;
};

export default ProtectedAdminRoute;

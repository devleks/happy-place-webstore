import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import { AuthProvider } from './context/AuthContext';
import AdminLayout from './components/admin/AdminLayout';
import ProtectedAdminRoute from './components/ProtectedAdminRoute';

// Admin Pages
import AdminLogin from './pages/admin/AdminLogin';
import AdminDashboard from './pages/admin/AdminDashboard';
import AdminInventory from './pages/admin/AdminInventory';
import AddProduct from './pages/admin/AddProduct';
import AdminOrders from './pages/admin/AdminOrders';
import AdminCustomers from './pages/admin/AdminCustomers';
import AdminEmployees from './pages/admin/AdminEmployees';
import AdminPromotions from './pages/admin/AdminPromotions';
import AdminReports from './pages/admin/AdminReports';
import AdminSettings from './pages/admin/AdminSettings';

import './styles/App.css';
import 'react-toastify/dist/ReactToastify.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/" element={<Navigate to="/admin" replace />} />

            {/* Admin Login */}
            <Route path="/admin/login" element={<AdminLogin />} />

            {/* Admin Portal Routes */}
            <Route
              path="/admin"
              element={
                <ProtectedAdminRoute>
                  <AdminLayout />
                </ProtectedAdminRoute>
              }
            >
              <Route index element={<Navigate to="dashboard" replace />} />
              <Route path="dashboard" element={<AdminDashboard />} />
              <Route path="inventory" element={<AdminInventory />} />
              <Route path="inventory/add" element={<AddProduct />} />
              <Route path="orders" element={<AdminOrders />} />
              <Route path="customers" element={<AdminCustomers />} />
              <Route path="employees" element={<AdminEmployees />} />
              <Route path="promotions" element={<AdminPromotions />} />
              <Route path="reports" element={<AdminReports />} />
              <Route path="settings" element={<AdminSettings />} />
            </Route>

            {/* Redirect all other routes to admin login */}
            <Route path="*" element={<Navigate to="/admin/login" replace />} />
          </Routes>
          <ToastContainer position="top-right" autoClose={3000} />
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;

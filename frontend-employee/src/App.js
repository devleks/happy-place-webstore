import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import { AuthProvider } from './context/AuthContext';

// Employee Login
import EmployeeLogin from './pages/EmployeeLogin';

// Employee Dashboard (will create next)
import EmployeeDashboard from './pages/employee/EmployeeDashboard';
import PackerDashboard from './pages/employee/PackerDashboard';
import ShipperDashboard from './pages/employee/ShipperDashboard';

import './styles/App.css';
import 'react-toastify/dist/ReactToastify.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Routes>
            {/* Employee Login */}
            <Route path="/login" element={<EmployeeLogin />} />
            
            {/* Employee Dashboards */}
            <Route path="/dashboard" element={<EmployeeDashboard />} />
            <Route path="/packing" element={<PackerDashboard />} />
            <Route path="/shipping" element={<ShipperDashboard />} />

            {/* Redirect */}
            <Route index element={<Navigate to="/login" replace />} />
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
          <ToastContainer position="top-right" autoClose={3000} />
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;

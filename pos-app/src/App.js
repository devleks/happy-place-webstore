/**
 * Main App Component
 * POS Application Root
 */

import React, { useState, useEffect } from 'react';
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';

// POS Pages
import POSSetup from './pages/POS/POSSetup';
import POSLogin from './pages/POS/POSLogin';
import POSDashboard from './pages/POS/POSDashboard';
import POSNewSale from './pages/POS/POSNewSale';
import POSCloseShift from './pages/POS/POSCloseShift';
import POSReceipt from './pages/POS/POSReceipt';

function App() {
  const [isOnline, setIsOnline] = useState(true);
  const [syncStatus, setSyncStatus] = useState('synced');
  const [employee, setEmployee] = useState(() => {
    // Check for existing session on mount
    const savedEmployee = localStorage.getItem('employee_info');
    return savedEmployee ? JSON.parse(savedEmployee) : null;
  });

  // Check online status
  useEffect(() => {
    const checkOnline = () => {
      setIsOnline(navigator.onLine);
    };

    // Check immediately
    checkOnline();

    // Listen for online/offline events
    window.addEventListener('online', checkOnline);
    window.addEventListener('offline', checkOnline);

    return () => {
      window.removeEventListener('online', checkOnline);
      window.removeEventListener('offline', checkOnline);
    };
  }, []);

  // Listen for sync status updates
  useEffect(() => {
    // Listen for sync status from main process
    const handleSyncStatus = (status) => {
      setSyncStatus(status);
    };

    // Note: This would be set up via IPC in a real implementation
    // window.electron.sync.onStatusChange(handleSyncStatus);

    return () => {
      // Cleanup listener
    };
  }, []);

  // Listen for app-ready event
  useEffect(() => {
    console.log('✅ PWA POS App mounted and ready');
    console.log('📱 Running as Progressive Web App');
  }, []);

  return (
    <div className="app">
      {/* Status Bar */}
      <div className="status-bar">
        <div className="status-item">
          <span className={`status-indicator ${isOnline ? 'online' : 'offline'}`}>
            {isOnline ? '🟢' : '🔴'}
          </span>
          <span>{isOnline ? 'Online' : 'Offline'}</span>
        </div>
        <div className="status-item">
          <span className={`status-indicator ${syncStatus === 'synced' ? 'synced' : 'syncing'}`}>
            {syncStatus === 'synced' ? '✅' : '🔄'}
          </span>
          <span>{syncStatus === 'synced' ? 'Synced' : 'Syncing...'}</span>
        </div>
        {employee && (
          <div className="status-item">
            <span>👤 {employee.full_name || employee.name}</span>
          </div>
        )}
      </div>

      {/* Main Router */}
      <Router>
        <Routes>
          <Route path="/setup" element={<POSSetup />} />
          <Route path="/login" element={<POSLogin onLogin={setEmployee} />} />
          <Route 
            path="/dashboard" 
            element={
              employee ? <POSDashboard employee={employee} /> : <Navigate to="/login" />
            } 
          />
          <Route 
            path="/pos/sale" 
            element={
              employee ? <POSNewSale employee={employee} /> : <Navigate to="/login" />
            } 
          />
          <Route 
            path="/new-sale" 
            element={
              employee ? <POSNewSale employee={employee} /> : <Navigate to="/login" />
            } 
          />
          <Route 
            path="/pos/close-shift" 
            element={
              employee ? <POSCloseShift employee={employee} /> : <Navigate to="/login" />
            } 
          />
          <Route 
            path="/close-shift" 
            element={
              employee ? <POSCloseShift employee={employee} /> : <Navigate to="/login" />
            } 
          />
          <Route 
            path="/receipt/:transactionId" 
            element={<POSReceipt />} 
          />
          <Route path="/" element={<Navigate to={employee ? "/dashboard" : "/login"} />} />
        </Routes>
      </Router>
    </div>
  );
}

export default App;

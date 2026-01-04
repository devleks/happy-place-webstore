import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { shiftAPI, transactionAPI } from '../../services/electronAPI';
import '../../styles/POSDashboard.css';

const POSDashboard = () => {
  const [employee, setEmployee] = useState(null);
  const [currentShift, setCurrentShift] = useState(null);
  const [loading, setLoading] = useState(true);
  const [shiftModal, setShiftModal] = useState(false);
  const [openingFloat, setOpeningFloat] = useState('5000.00');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    // Check if employee is logged in
    const sessionToken = localStorage.getItem('session_token');
    const employeeInfo = localStorage.getItem('employee_info');

    if (!sessionToken || !employeeInfo) {
      navigate('/login');
      return;
    }

    const emp = JSON.parse(employeeInfo);
    setEmployee(emp);
    checkCurrentShift(emp.id);
  }, [navigate]);

  const checkCurrentShift = async (employeeId) => {
    try {
      // Use PWA API - works offline with IndexedDB
      const shift = await shiftAPI.getCurrent();

      if (shift) {
        setCurrentShift(shift);
      }
    } catch (err) {
      console.error('Error checking shift:', err);
    } finally {
      setLoading(false);
    }
  };

  const startShift = async () => {
    setError('');

    try {
      // Use PWA API - creates shift in IndexedDB and syncs to backend when online
      const shift = await shiftAPI.start({
        employee_id: employee.id,
        employee_name: employee.full_name,
        opening_float: parseFloat(openingFloat)
      });

      if (shift) {
        setCurrentShift(shift);
        setShiftModal(false);
      } else {
        setError('Failed to start shift');
      }
    } catch (err) {
      setError('Error starting shift. Please try again.');
      console.error('Start shift error:', err);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('session_token');
    localStorage.removeItem('employee_info');
    navigate('/login');
  };

  const formatCurrency = (amount) => {
    return `KSh ${parseFloat(amount).toLocaleString('en-KE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const formatTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-KE', { hour: '2-digit', minute: '2-digit' });
  };

  if (loading) {
    return (
      <div className="pos-loading-screen">
        <div className="pos-loading-spinner"></div>
        <p>Loading POS System...</p>
      </div>
    );
  }

  return (
    <div className="pos-dashboard">
      {/* Header */}
      <header className="pos-header">
        <div className="pos-header-left">
          <div className="pos-logo-small">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="#9b59b6" strokeWidth="2"/>
              <path d="M8 12h8M12 8v8" stroke="#9b59b6" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </div>
          <div className="pos-header-info">
            <h1>Happy Place POS</h1>
            <p>Nairobi Store</p>
          </div>
        </div>

        <div className="pos-header-right">
          {currentShift && (
            <div className="pos-shift-indicator">
              <div className="shift-status active">
                <span className="status-dot"></span>
                Shift Active
              </div>
              <div className="shift-details">
                <span>Shift #{currentShift.shift_number}</span>
                <span>Started: {formatTime(currentShift.start_time)}</span>
              </div>
            </div>
          )}

          <div className="pos-employee-info">
            <div className="employee-avatar">
              {employee?.full_name?.charAt(0) || 'E'}
            </div>
            <div className="employee-details">
              <span className="employee-name">{employee?.full_name}</span>
              <span className="employee-role">{employee?.role}</span>
            </div>
          </div>

          <button className="pos-logout-btn" onClick={handleLogout}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Logout
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="pos-main-content">
        {!currentShift ? (
          // No Active Shift - Show Start Shift Screen
          <div className="pos-no-shift">
            <div className="no-shift-card">
              <div className="no-shift-icon">
                <svg width="80" height="80" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="#9b59b6" strokeWidth="2"/>
                  <path d="M12 6v6l4 2" stroke="#9b59b6" strokeWidth="2" strokeLinecap="round"/>
                </svg>
              </div>
              <h2>No Active Shift</h2>
              <p>Start your shift to begin processing transactions</p>
              <button className="start-shift-btn" onClick={() => setShiftModal(true)}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
                  <path d="M10 8l6 4-6 4V8z" fill="currentColor"/>
                </svg>
                Start Shift
              </button>
            </div>
          </div>
        ) : (
          // Active Shift - Show POS Functions
          <div className="pos-functions-grid">
            <div className="pos-function-card primary" onClick={() => navigate('/pos/sale')}>
              <div className="function-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
                  <path d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <h3>New Sale</h3>
              <p>Process customer transaction</p>
            </div>

            <div className="pos-function-card">
              <div className="function-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
                  <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <h3>Transactions</h3>
              <p>View today's sales</p>
              <div className="function-badge">{currentShift.transaction_count || 0}</div>
            </div>

            <div className="pos-function-card">
              <div className="function-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
                  <path d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <h3>Cash Management</h3>
              <p>Cash in/out operations</p>
            </div>

            <div className="pos-function-card danger" onClick={() => navigate('/pos/close-shift')}>
              <div className="function-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
                  <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <h3>Close Shift</h3>
              <p>End shift & reconcile cash</p>
            </div>
          </div>
        )}

        {/* Shift Stats */}
        {currentShift && (
          <div className="pos-shift-stats">
            <h3>Today's Summary</h3>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Total Sales</div>
                <div className="stat-value">{formatCurrency(currentShift.total_sales || 0)}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Transactions</div>
                <div className="stat-value">{currentShift.transaction_count || 0}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Cash Sales</div>
                <div className="stat-value">{formatCurrency(currentShift.cash_sales || 0)}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">M-Pesa Sales</div>
                <div className="stat-value">{formatCurrency(currentShift.mpesa_sales || 0)}</div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Start Shift Modal */}
      {shiftModal && (
        <div className="pos-modal-overlay" onClick={() => setShiftModal(false)}>
          <div className="pos-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Start New Shift</h2>
              <button className="modal-close" onClick={() => setShiftModal(false)}>×</button>
            </div>

            <div className="modal-body">
              {error && <div className="modal-error">{error}</div>}

              <div className="form-group">
                <label>Opening Float (KSh)</label>
                <input
                  type="number"
                  value={openingFloat}
                  onChange={(e) => setOpeningFloat(e.target.value)}
                  step="0.01"
                  min="0"
                  placeholder="5000.00"
                />
                <small>Amount of cash in register at shift start</small>
              </div>

              <div className="shift-info">
                <div className="info-row">
                  <span>Employee:</span>
                  <strong>{employee?.full_name}</strong>
                </div>
                <div className="info-row">
                  <span>Role:</span>
                  <strong>{employee?.role}</strong>
                </div>
                <div className="info-row">
                  <span>Store:</span>
                  <strong>Nairobi - Kimathi Street</strong>
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShiftModal(false)}>
                Cancel
              </button>
              <button className="btn-primary" onClick={startShift}>
                Start Shift
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default POSDashboard;

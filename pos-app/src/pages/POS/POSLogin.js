import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/electronAPI';
import '../../styles/POSLogin.css';

const POSLogin = ({ onLogin }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const navigate = useNavigate();

  useEffect(() => {
    // Online status monitoring
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    // Auto-sync employees from backend on component mount
    autoSyncEmployees();
    
    // Check for existing valid session
    checkExistingSession();
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const autoSyncEmployees = async () => {
    try {
      console.log('🔄 Auto-sync: Starting employee sync from backend...');
      
      // Set sync token (this should be configured or obtained from backend login)
      const syncToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc2NTQxMTY0OCwianRpIjoiZWVhMWRiYzgtMDk4Ni00MjAzLWI2OGItZThjOTBkOWZhNTcwIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3NjU0MTE2NDgsImNzcmYiOiI2MjZhMTE4NC02ODZkLTRhYmItYWJkNi05N2VlNTk5OGM2ZDkiLCJleHAiOjE3NjU0NDA0NDgsInVzZXJfdHlwZSI6ImVtcGxveWVlIiwicm9sZSI6ImFkbWluIn0.TY2ZE5Z3bWtZt5ZqbbQAGjhhclzRwDDfUYpUhaaua6Q';
      
      await api.auth.setSyncToken(syncToken);
      console.log('✅ Auto-sync: Sync token set');
      
      // Sync employees from backend
      const result = await api.auth.syncEmployees();
      
      if (result.success) {
        console.log(`✅ Auto-sync: Successfully synced ${result.count} employees from backend`);
      } else {
        console.warn('⚠️ Auto-sync: Failed to sync employees:', result.error);
      }
    } catch (error) {
      console.error('❌ Auto-sync: Error during employee sync:', error);
      // Don't block login if sync fails - offline mode should still work
    }
  };

  const checkExistingSession = async () => {
    const sessionToken = localStorage.getItem('session_token');
    if (sessionToken) {
      const result = await api.auth.validateSession(sessionToken);
      if (result.valid) {
        // Session still valid, redirect to dashboard
        if (onLogin) {
          onLogin(result.session);
        }
        navigate('/dashboard');
      } else {
        // Session invalid, clear storage
        localStorage.removeItem('session_token');
        localStorage.removeItem('employee_info');
      }
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    // Clear error when user starts typing
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const result = await api.auth.login(formData.email, formData.password);

      if (result.success) {
        // Store session token and employee info
        localStorage.setItem('session_token', result.session.token);
        localStorage.setItem('employee_info', JSON.stringify(result.employee));
        
        // Call parent onLogin
        if (onLogin) {
          onLogin(result.employee);
        }
        
        navigate('/dashboard');
      } else {
        setError(result.error || 'Login failed');
      }
    } catch (err) {
      console.error('Login error:', err);
      setError('Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Quick login buttons for testing
  const quickLogin = (email, password) => {
    setFormData({ email, password });
  };

  return (
    <div className="pos-login-container">
      {/* Online Status Indicator */}
      <div className="online-status-banner" style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        padding: '8px',
        textAlign: 'center',
        backgroundColor: isOnline ? '#27ae60' : '#e74c3c',
        color: 'white',
        fontSize: '14px',
        zIndex: 1000
      }}>
        {isOnline ? '🟢 Online - Auto-sync enabled' : '🔴 Offline - Using cached credentials'}
      </div>

      <div className="pos-login-box" style={{ marginTop: '40px' }}>
        <div className="pos-login-header">
          <div className="pos-logo">
            <svg width="60" height="60" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="#9b59b6" strokeWidth="2"/>
              <path d="M8 12h8M12 8v8" stroke="#9b59b6" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </div>
          <h1>Happy Place POS</h1>
          <p>Employee Login</p>
        </div>

        <form onSubmit={handleSubmit} className="pos-login-form">
          {error && (
            <div className="pos-error-message">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="#e74c3c" strokeWidth="2"/>
                <path d="M12 8v4M12 16h.01" stroke="#e74c3c" strokeWidth="2" strokeLinecap="round"/>
              </svg>
              {error}
            </div>
          )}

          <div className="pos-form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="employee@happyplace.co.ke"
              required
              disabled={loading}
              autoComplete="email"
            />
          </div>

          <div className="pos-form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Enter your password"
              required
              disabled={loading}
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            className="pos-login-button"
            disabled={loading}
          >
            {loading ? (
              <span className="pos-loading-spinner"></span>
            ) : (
              'Login to POS'
            )}
          </button>
        </form>

        {/* Quick login buttons for testing */}
        <div className="pos-quick-login">
          <p className="pos-quick-login-title">Quick Login (Testing):</p>
          <div className="pos-quick-login-buttons">
            <button
              className="pos-quick-btn admin"
              onClick={() => quickLogin('admin@happyplace.co.ke', 'admin123')}
              disabled={loading}
            >
              Admin
            </button>
            <button
              className="pos-quick-btn manager"
              onClick={() => quickLogin('manager@happyplace.co.ke', 'manager123')}
              disabled={loading}
            >
              Manager
            </button>
            <button
              className="pos-quick-btn cashier"
              onClick={() => quickLogin('cashier1@happyplace.co.ke', 'cashier123')}
              disabled={loading}
            >
              Cashier
            </button>
          </div>
        </div>

        <div className="pos-login-footer">
          <a href="/" className="pos-back-link">← Back to Store</a>
        </div>
      </div>
    </div>
  );
};

export default POSLogin;

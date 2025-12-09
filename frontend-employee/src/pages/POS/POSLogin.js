import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../../styles/POSLogin.css';

const POSLogin = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

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
      const response = await fetch('http://127.0.0.1:5001/api/auth/employee/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        // Store employee token and info
        localStorage.setItem('employee_token', data.access_token);
        localStorage.setItem('employee_info', JSON.stringify({
          id: data.employee.id,
          email: data.employee.email,
          full_name: data.employee.full_name,
          role: data.employee.role
        }));

        // Redirect to POS dashboard
        navigate('/pos/dashboard');
      } else {
        setError(data.error || 'Login failed. Please check your credentials.');
      }
    } catch (err) {
      setError('Connection error. Please ensure the backend server is running.');
      console.error('Login error:', err);
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
      <div className="pos-login-box">
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

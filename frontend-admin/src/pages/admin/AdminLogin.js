import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import '../../styles/AdminLogin.css';

const AdminLogin = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    totp_code: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [requires2FA, setRequires2FA] = useState(false);

  const { loginAdmin, isAuthenticated, userType } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // If already authenticated as admin/manager, redirect to dashboard
    if (isAuthenticated && userType === 'employee') {
      navigate('/admin/dashboard');
    }
  }, [isAuthenticated, userType, navigate]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const loginData = {
        email: formData.email,
        password: formData.password,
      };

      if (requires2FA && formData.totp_code) {
        loginData.totp_code = formData.totp_code;
      }

      await loginAdmin(loginData); // Use dedicated admin login endpoint

      // Successful login - redirect to admin dashboard
      navigate('/dashboard');
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'Failed to login. Please check your credentials.';

      // Check if 2FA is required
      if (err.response?.data?.requires_2fa) {
        setRequires2FA(true);
        setError('Please enter your 2FA code');
      } else {
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-login-container">
      <div className="admin-login-box">
        <div className="admin-login-header">
          <div className="admin-logo">
            <span className="logo-icon">🏪</span>
            <h1>Happy Place</h1>
          </div>
          <h2>Admin Dashboard</h2>
          <p className="admin-subtitle">Management Portal</p>
        </div>

        <form onSubmit={handleSubmit} className="admin-login-form">
          {error && (
            <div className="alert alert-error">
              <span className="alert-icon">⚠️</span>
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="admin@happyplace.co.ke"
              required
              autoComplete="email"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Enter your password"
              required
              autoComplete="current-password"
              disabled={loading}
            />
          </div>

          {requires2FA && (
            <div className="form-group">
              <label htmlFor="totp_code">2FA Code</label>
              <input
                type="text"
                id="totp_code"
                name="totp_code"
                value={formData.totp_code}
                onChange={handleChange}
                placeholder="Enter 6-digit code"
                maxLength="6"
                required
                autoComplete="one-time-code"
                disabled={loading}
              />
              <small className="form-hint">Enter the 6-digit code from your authenticator app</small>
            </div>
          )}

          <button
            type="submit"
            className="btn-admin-login"
            disabled={loading}
          >
            {loading ? (
              <span>
                <span className="spinner"></span>
                Authenticating...
              </span>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        <div className="admin-login-footer">
          <p className="security-notice">
            <span className="lock-icon">🔒</span>
            Secure Admin Access - Authorized Personnel Only
          </p>
          <div className="login-links">
            <a href="/">← Back to Store</a>
            <a href="/pos/login">POS Login</a>
          </div>
        </div>
      </div>

      <div className="admin-login-background">
        <div className="bg-gradient"></div>
      </div>
    </div>
  );
};

export default AdminLogin;

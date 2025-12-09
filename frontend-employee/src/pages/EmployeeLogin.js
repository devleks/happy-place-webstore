import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import '../styles/Auth.css';

const EmployeeLogin = () => {
  const [step, setStep] = useState(1); // 1: email/password, 2: 2FA code
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    totp_code: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [tempAuthData, setTempAuthData] = useState(null);

  const { loginEmployee } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleInitialLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await loginEmployee({
        email: formData.email,
        password: formData.password,
      });

      // Check if 2FA is required
      if (response.requires_2fa) {
        setTempAuthData(response);
        setStep(2);
      } else {
        // No 2FA required, redirect based on role
        redirectBasedOnRole(response.employee);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to login. Please check your credentials and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleTwoFactorSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await loginEmployee({
        email: formData.email,
        password: formData.password,
        totp_code: formData.totp_code,
      });

      // Successful 2FA verification
      redirectBasedOnRole(response.employee);
    } catch (err) {
      setError(err.response?.data?.error || 'Invalid 2FA code. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const redirectBasedOnRole = (employee) => {
    // Redirect based on employee role
    const role = employee.role.toLowerCase();
    
    if (role === 'packer') {
      navigate('/packing');
    } else if (role === 'shipper') {
      navigate('/shipping');
    } else {
      // For other roles, go to dashboard which will redirect appropriately
      navigate('/dashboard');
    }
  };

  // Step 1: Email and Password
  if (step === 1) {
    return (
      <div className="auth-page">
        <div className="auth-container">
          <h1 className="auth-title">Employee Login</h1>
          <p className="auth-subtitle">Sign in to access the admin dashboard</p>

          {error && <div className="error-message">{error}</div>}

          <form onSubmit={handleInitialLogin} className="auth-form">
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                className="form-input"
                placeholder="your.email@happyplace.com"
                autoComplete="email"
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
                required
                className="form-input"
                placeholder="Enter your password"
                autoComplete="current-password"
              />
            </div>

            <button type="submit" disabled={loading} className="btn-primary-large">
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </form>

          <div className="auth-footer" style={{ marginTop: '30px' }}>
            <p style={{ color: '#999', fontSize: '0.875rem' }}>
              Employee accounts are created by administrators.
            </p>
            <p style={{ marginTop: '10px' }}>
              <Link to="/customer/login" style={{ color: '#9B7EBD', fontSize: '0.875rem' }}>
                Customer Login
              </Link>
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Step 2: Two-Factor Authentication
  return (
    <div className="auth-page">
      <div className="auth-container">
        <h1 className="auth-title">Two-Factor Authentication</h1>
        <p className="auth-subtitle">
          Enter the 6-digit code from your authenticator app
        </p>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleTwoFactorSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="totp_code">Authentication Code</label>
            <input
              type="text"
              id="totp_code"
              name="totp_code"
              value={formData.totp_code}
              onChange={handleChange}
              required
              className="form-input"
              placeholder="000000"
              maxLength="6"
              pattern="[0-9]{6}"
              autoComplete="one-time-code"
              style={{
                fontSize: '1.5rem',
                textAlign: 'center',
                letterSpacing: '0.5rem',
                fontFamily: 'monospace',
              }}
              autoFocus
            />
            <small style={{ color: '#999', fontSize: '0.75rem', marginTop: '8px', display: 'block' }}>
              Enter the 6-digit code from Google Authenticator or your backup codes
            </small>
          </div>

          <button type="submit" disabled={loading} className="btn-primary-large">
            {loading ? 'Verifying...' : 'Verify & Login'}
          </button>

          <button
            type="button"
            onClick={() => {
              setStep(1);
              setFormData({ ...formData, totp_code: '' });
              setError('');
            }}
            className="btn-secondary"
            style={{ marginTop: '15px' }}
          >
            Back to Login
          </button>
        </form>

        <div className="auth-footer" style={{ marginTop: '30px' }}>
          <p style={{ color: '#999', fontSize: '0.875rem' }}>
            Having trouble? Contact your system administrator.
          </p>
        </div>
      </div>
    </div>
  );
};

export default EmployeeLogin;

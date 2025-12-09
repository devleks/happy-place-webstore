import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { GoogleLogin } from '@react-oauth/google';
import { useAuth } from '../context/AuthContext';
import '../styles/Auth.css';

const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID || '';
const isGoogleOAuthEnabled = GOOGLE_CLIENT_ID && GOOGLE_CLIENT_ID !== '';

const CustomerLogin = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { loginCustomer, loginCustomerWithGoogle } = useAuth();
  const navigate = useNavigate();

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
      await loginCustomer(formData);
      navigate('/dashboard'); // Redirect to customer dashboard
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to login. Please check your credentials and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSuccess = async (credentialResponse) => {
    setError('');
    setLoading(true);

    try {
      await loginCustomerWithGoogle(credentialResponse.credential);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to login with Google. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleError = () => {
    setError('Google login failed. Please try again.');
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        <h1 className="auth-title">Customer Login</h1>
        <p className="auth-subtitle">Welcome back! Sign in to your account</p>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
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
              placeholder="your.email@example.com"
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
            />
          </div>

          <div className="form-footer" style={{ marginBottom: '20px' }}>
            <Link to="/forgot-password" style={{ fontSize: '0.875rem', color: '#9B7EBD' }}>
              Forgot password?
            </Link>
          </div>

          <button type="submit" disabled={loading} className="btn-primary-large">
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        {isGoogleOAuthEnabled && (
          <>
            <div className="divider" style={{ margin: '30px 0', textAlign: 'center', position: 'relative' }}>
              <span
                style={{
                  background: 'white',
                  padding: '0 15px',
                  color: '#999',
                  fontSize: '0.875rem',
                  position: 'relative',
                  zIndex: 1,
                }}
              >
                OR
              </span>
              <div
                style={{
                  position: 'absolute',
                  top: '50%',
                  left: 0,
                  right: 0,
                  height: '1px',
                  background: '#e5e5e5',
                  zIndex: 0,
                }}
              />
            </div>

            <div className="google-login-wrapper" style={{ display: 'flex', justifyContent: 'center' }}>
              <GoogleLogin
                onSuccess={handleGoogleSuccess}
                onError={handleGoogleError}
                useOneTap
                text="signin_with"
                shape="rectangular"
                theme="outline"
                size="large"
                width="100%"
              />
            </div>
          </>
        )}

        <div className="auth-footer" style={{ marginTop: '30px' }}>
          <p>
            Don't have an account? <Link to="/register">Sign up here</Link>
          </p>
          <p style={{ marginTop: '10px' }}>
            <Link to="/employee/login" style={{ color: '#999', fontSize: '0.875rem' }}>
              Employee Login
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default CustomerLogin;

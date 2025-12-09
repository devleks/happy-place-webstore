import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import '../styles/Auth.css';

const Register = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
    phone: '',
    gdpr_consent: false,
    marketing_consent: false,
    accept_terms: false,
    accept_privacy: false,
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    if (!formData.accept_terms) {
      setError('You must accept the Terms of Service to continue');
      return;
    }

    if (!formData.accept_privacy) {
      setError('You must accept the Privacy Policy to continue');
      return;
    }

    if (!formData.gdpr_consent) {
      setError('You must consent to data processing (GDPR) to continue');
      return;
    }

    setLoading(true);

    try {
      const { confirmPassword, ...userData } = formData;
      await register(userData);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to register. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        <h1 className="auth-title">Sign Up</h1>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="first_name">First Name</label>
              <input
                type="text"
                id="first_name"
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                required
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="last_name">Last Name</label>
              <input
                type="text"
                id="last_name"
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                required
                className="form-input"
              />
            </div>
          </div>

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
            />
          </div>

          <div className="form-group">
            <label htmlFor="phone">Phone Number (Optional)</label>
            <input
              type="tel"
              id="phone"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              placeholder="+254712345678"
              className="form-input"
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
              minLength="8"
            />
            <small style={{ color: '#666', fontSize: '0.875rem' }}>
              Must be at least 8 characters
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
              className="form-input"
            />
          </div>

          {/* Policy Acceptance Section */}
          <div className="policy-section" style={{ marginTop: '1.5rem', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: '500', marginBottom: '1rem', color: '#333' }}>
              Terms & Policies
            </h3>

            <div className="policy-checkboxes">
              <label className="policy-checkbox-label">
                <input
                  type="checkbox"
                  name="accept_terms"
                  checked={formData.accept_terms}
                  onChange={handleChange}
                  required
                />
                <span className="policy-text">
                  I have read and agree to the{' '}
                  <Link to="/terms-of-service" target="_blank" rel="noopener noreferrer" className="policy-link">
                    Terms of Service
                  </Link>{' '}
                  *
                </span>
              </label>

              <label className="policy-checkbox-label">
                <input
                  type="checkbox"
                  name="accept_privacy"
                  checked={formData.accept_privacy}
                  onChange={handleChange}
                  required
                />
                <span className="policy-text">
                  I have read and agree to the{' '}
                  <Link to="/privacy-policy" target="_blank" rel="noopener noreferrer" className="policy-link">
                    Privacy Policy
                  </Link>{' '}
                  *
                </span>
              </label>

              <label className="policy-checkbox-label">
                <input
                  type="checkbox"
                  name="gdpr_consent"
                  checked={formData.gdpr_consent}
                  onChange={handleChange}
                  required
                />
                <span className="policy-text">
                  I consent to the processing of my personal data in accordance with the Privacy Policy (GDPR compliance) *
                </span>
              </label>

              <label className="policy-checkbox-label" style={{ borderColor: '#e5e5e5' }}>
                <input
                  type="checkbox"
                  name="marketing_consent"
                  checked={formData.marketing_consent}
                  onChange={handleChange}
                />
                <span className="policy-text">
                  I would like to receive marketing emails about new products and promotions (optional)
                </span>
              </label>
            </div>
          </div>

          <button type="submit" disabled={loading} className="btn-primary-large">
            {loading ? 'Creating account...' : 'Sign Up'}
          </button>
        </form>

        <p className="auth-footer">
          Already have an account? <Link to="/login">Login here</Link>
        </p>
      </div>
    </div>
  );
};

export default Register;

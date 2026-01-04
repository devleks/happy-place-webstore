import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import * as db from '../../db';
import '../../styles/POSSetup.css';

const POSSetup = () => {
  const [authToken, setAuthToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [syncStatus, setSyncStatus] = useState(null);
  const [needsSetup, setNeedsSetup] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    checkSetupStatus();
  }, []);

  const checkSetupStatus = async () => {
    const needs = await db.needsInitialSync();
    setNeedsSetup(needs);

    if (!needs) {
      // Already set up, redirect to login
      navigate('/');
    }
  };

  const handleSync = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSyncStatus(null);

    try {
      const result = await db.initializeFromBackend(authToken);

      if (result.success) {
        setSyncStatus({
          success: true,
          employees: result.results.employees,
          products: result.results.products
        });

        // Redirect to login after 2 seconds
        setTimeout(() => {
          navigate('/');
        }, 2000);
      } else {
        setError('Sync failed. Check your auth token and backend connection.');
        setSyncStatus(result);
      }
    } catch (err) {
      setError(`Sync error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = () => {
    navigate('/');
  };

  if (!needsSetup && syncStatus === null) {
    return (
      <div className="pos-setup-container">
        <div className="pos-setup-card">
          <h2>✅ POS Already Set Up</h2>
          <p>Redirecting to login...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="pos-setup-container">
      <div className="pos-setup-card">
        <div className="setup-header">
          <h1>🚀 Happy Place POS Setup</h1>
          <p className="setup-subtitle">Sync employees and products from backend</p>
        </div>

        {!syncStatus && (
          <form onSubmit={handleSync} className="setup-form">
            <div className="form-group">
              <label htmlFor="authToken">Backend Auth Token</label>
              <textarea
                id="authToken"
                value={authToken}
                onChange={(e) => setAuthToken(e.target.value)}
                placeholder="Paste JWT token from backend admin login..."
                rows="4"
                required
                disabled={loading}
              />
              <small className="form-help">
                Get this token by logging into the admin panel at{' '}
                <code>http://127.0.0.1:5001</code>
              </small>
            </div>

            {error && (
              <div className="setup-error">
                <strong>❌ Error:</strong> {error}
              </div>
            )}

            <div className="setup-actions">
              <button
                type="submit"
                className="btn-sync"
                disabled={loading || !authToken}
              >
                {loading ? '⏳ Syncing...' : '🔄 Sync from Backend'}
              </button>

              <button
                type="button"
                className="btn-skip"
                onClick={handleSkip}
                disabled={loading}
              >
                Skip (Use Test Data)
              </button>
            </div>
          </form>
        )}

        {syncStatus && (
          <div className="sync-results">
            <h2>
              {syncStatus.success ? '✅ Sync Complete!' : '⚠️ Sync Issues'}
            </h2>

            <div className="sync-stats">
              <div className="sync-stat">
                <h3>👥 Employees</h3>
                <p>
                  Total: {syncStatus.employees.total}<br />
                  New: {syncStatus.employees.synced}<br />
                  Updated: {syncStatus.employees.updated}<br />
                  {syncStatus.employees.errors > 0 && (
                    <span className="error-count">
                      Errors: {syncStatus.employees.errors}
                    </span>
                  )}
                </p>
              </div>

              <div className="sync-stat">
                <h3>📦 Products</h3>
                <p>
                  Total: {syncStatus.products.total}<br />
                  New: {syncStatus.products.synced}<br />
                  Updated: {syncStatus.products.updated}<br />
                  {syncStatus.products.errors > 0 && (
                    <span className="error-count">
                      Errors: {syncStatus.products.errors}
                    </span>
                  )}
                </p>
              </div>
            </div>

            {syncStatus.success && (
              <p className="redirect-message">
                Redirecting to login page...
              </p>
            )}
          </div>
        )}

        <div className="setup-instructions">
          <h3>📖 How to get the auth token:</h3>
          <ol>
            <li>
              Open the backend admin panel:{' '}
              <a href="http://127.0.0.1:5001" target="_blank" rel="noopener noreferrer">
                http://127.0.0.1:5001
              </a>
            </li>
            <li>Login with admin credentials</li>
            <li>Open browser DevTools (F12) → Console tab</li>
            <li>
              Type: <code>localStorage.getItem('access_token')</code>
            </li>
            <li>Copy the token (without quotes) and paste above</li>
          </ol>
        </div>
      </div>
    </div>
  );
};

export default POSSetup;

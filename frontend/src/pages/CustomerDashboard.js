import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import '../styles/Dashboard.css';

const CustomerDashboard = () => {
  const { user, userType, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Redirect if not authenticated or not a customer
    if (!isAuthenticated || userType !== 'customer') {
      navigate('/customer/login');
      return;
    }
    setLoading(false);
  }, [isAuthenticated, userType, navigate]);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="loading">Loading...</div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>Welcome back, {user?.first_name || 'Customer'}!</h1>
        <button onClick={handleLogout} className="btn-secondary">
          Logout
        </button>
      </div>

      <div className="dashboard-grid">
        {/* Quick Actions */}
        <div className="dashboard-card">
          <h2>Quick Actions</h2>
          <div className="quick-actions">
            <Link to="/products" className="action-button">
              <div className="action-icon">🛍️</div>
              <div className="action-text">
                <h3>Shop Now</h3>
                <p>Browse our latest collection</p>
              </div>
            </Link>
            <Link to="/orders" className="action-button">
              <div className="action-icon">📦</div>
              <div className="action-text">
                <h3>My Orders</h3>
                <p>Track your orders</p>
              </div>
            </Link>
            <Link to="/wishlist" className="action-button">
              <div className="action-icon">❤️</div>
              <div className="action-text">
                <h3>Wishlist</h3>
                <p>View saved items</p>
              </div>
            </Link>
            <Link to="/cart" className="action-button">
              <div className="action-icon">🛒</div>
              <div className="action-text">
                <h3>Shopping Cart</h3>
                <p>Complete your purchase</p>
              </div>
            </Link>
          </div>
        </div>

        {/* Account Information */}
        <div className="dashboard-card">
          <h2>Account Information</h2>
          <div className="account-info">
            <div className="info-row">
              <span className="info-label">Email:</span>
              <span className="info-value">{user?.email || 'Not set'}</span>
            </div>
            <div className="info-row">
              <span className="info-label">Name:</span>
              <span className="info-value">
                {user?.first_name} {user?.last_name}
              </span>
            </div>
            <div className="info-row">
              <span className="info-label">Phone:</span>
              <span className="info-value">{user?.phone || 'Not set'}</span>
            </div>
            <div className="info-row">
              <span className="info-label">Member Since:</span>
              <span className="info-value">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
              </span>
            </div>
          </div>
          <Link to="/account/settings" className="btn-link" style={{ marginTop: '20px', display: 'inline-block' }}>
            Edit Profile →
          </Link>
        </div>

        {/* Recent Orders Preview */}
        <div className="dashboard-card full-width">
          <h2>Recent Orders</h2>
          <div className="orders-preview">
            <p className="empty-message">You haven't placed any orders yet.</p>
            <Link to="/products" className="btn-primary">
              Start Shopping
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CustomerDashboard;

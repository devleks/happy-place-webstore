import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import '../../styles/EmployeeDashboard.css';

const ShipperDashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('pending');

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    fetchShippingQueue();
  }, [user, navigate, statusFilter]);

  const fetchShippingQueue = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get(`/fulfillment/shipping/queue?status=${statusFilter}`);
      setOrders(response.data.orders || []);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load shipping queue');
      console.error('Error fetching shipping queue:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStartShipping = async (orderId) => {
    try {
      await api.post(`/fulfillment/shipping/${orderId}/start`);
      fetchShippingQueue();
      alert('Shipping started!');
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to start shipping');
    }
  };

  const handleCompleteShipping = async (assignmentId) => {
    const notes = prompt('Add shipping notes (e.g., "Handed to DHL courier"):');
    try {
      await api.post(`/fulfillment/shipping/${assignmentId}/complete`, {
        notes: notes || ''
      });
      fetchShippingQueue();
      alert('Shipping completed!');
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to complete shipping');
    }
  };

  if (loading) {
    return (
      <div className="employee-dashboard">
        <div className="loading-spinner">Loading shipping queue...</div>
      </div>
    );
  }

  return (
    <div className="employee-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>🚚 Shipping Station</h1>
          <p>Welcome, {user?.full_name}</p>
        </div>
        <div className="header-right">
          <button onClick={logout} className="btn-logout">
            Logout
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="filter-tabs">
        <button
          className={`filter-tab ${statusFilter === 'pending' ? 'active' : ''}`}
          onClick={() => setStatusFilter('pending')}
        >
          Pending ({orders.filter(o => o.status === 'pending').length})
        </button>
        <button
          className={`filter-tab ${statusFilter === 'in_progress' ? 'active' : ''}`}
          onClick={() => setStatusFilter('in_progress')}
        >
          In Progress ({orders.filter(o => o.status === 'in_progress').length})
        </button>
        <button
          className={`filter-tab ${statusFilter === 'completed' ? 'active' : ''}`}
          onClick={() => setStatusFilter('completed')}
        >
          Completed ({orders.filter(o => o.status === 'completed').length})
        </button>
        <button
          className={`filter-tab ${statusFilter === 'all' ? 'active' : ''}`}
          onClick={() => setStatusFilter('all')}
        >
          All Orders
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="error-message">
          <p>{error}</p>
          <button onClick={fetchShippingQueue} className="btn-retry">
            Retry
          </button>
        </div>
      )}

      {/* Orders Queue */}
      <div className="orders-queue">
        {orders.length === 0 ? (
          <div className="empty-state">
            <h3>No orders to ship</h3>
            <p>Check back later or change the filter</p>
          </div>
        ) : (
          <div className="orders-grid">
            {orders.map((order) => (
              <div key={order.assignment_id} className="order-card">
                <div className="order-header">
                  <h3>Order #{order.order_number}</h3>
                  <span className={`status-badge status-${order.status}`}>
                    {order.status.replace('_', ' ').toUpperCase()}
                  </span>
                </div>

                <div className="order-details">
                  <p><strong>Customer:</strong> {order.customer_name}</p>
                  {order.shipping_address && (
                    <p><strong>Address:</strong> {
                      typeof order.shipping_address === 'object' 
                        ? `${order.shipping_address.street || ''}, ${order.shipping_address.city || ''}, ${order.shipping_address.state || ''} ${order.shipping_address.zip || ''}`
                        : order.shipping_address
                    }</p>
                  )}
                  {order.tracking_number && (
                    <p><strong>Tracking:</strong> {order.tracking_number}</p>
                  )}
                  {order.carrier && (
                    <p><strong>Carrier:</strong> {order.carrier}</p>
                  )}
                  {order.assigned_at && (
                    <p><strong>Assigned:</strong> {new Date(order.assigned_at).toLocaleString()}</p>
                  )}
                  {order.started_at && (
                    <p><strong>Started:</strong> {new Date(order.started_at).toLocaleString()}</p>
                  )}
                </div>

                <div className="order-actions">
                  {order.status === 'pending' && (
                    <button
                      onClick={() => handleStartShipping(order.order_id)}
                      className="btn-primary"
                    >
                      Start Shipping
                    </button>
                  )}
                  {order.status === 'in_progress' && (
                    <button
                      onClick={() => handleCompleteShipping(order.assignment_id)}
                      className="btn-success"
                    >
                      Complete Shipping
                    </button>
                  )}
                  {order.status === 'completed' && (
                    <span className="completed-badge">✅ Shipped</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Refresh Button */}
      <div className="dashboard-footer">
        <button onClick={fetchShippingQueue} className="btn-refresh">
          🔄 Refresh Queue
        </button>
      </div>
    </div>
  );
};

export default ShipperDashboard;

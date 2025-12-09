import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import '../../styles/EmployeeDashboard.css';

const PackerDashboard = () => {
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
    fetchPackingQueue();
  }, [user, navigate, statusFilter]);

  const fetchPackingQueue = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get(`/fulfillment/packing/queue?status=${statusFilter}`);
      setOrders(response.data.orders || []);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load packing queue');
      console.error('Error fetching packing queue:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStartPacking = async (assignmentId) => {
    try {
      await api.post(`/fulfillment/packing/${assignmentId}/start`);
      fetchPackingQueue();
      alert('Packing started!');
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to start packing');
    }
  };

  const handleCompletePacking = async (assignmentId) => {
    const notes = prompt('Add any notes about the packing (optional):');
    try {
      await api.post(`/fulfillment/packing/${assignmentId}/complete`, {
        notes: notes || ''
      });
      fetchPackingQueue();
      alert('Packing completed! Order ready for shipping.');
    } catch (err) {
      alert(err.response?.data?.error || 'Failed to complete packing');
    }
  };

  if (loading) {
    return (
      <div className="employee-dashboard">
        <div className="loading-spinner">Loading packing queue...</div>
      </div>
    );
  }

  return (
    <div className="employee-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-left">
          <h1>📦 Packing Station</h1>
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
          <button onClick={fetchPackingQueue} className="btn-retry">
            Retry
          </button>
        </div>
      )}

      {/* Orders Queue */}
      <div className="orders-queue">
        {orders.length === 0 ? (
          <div className="empty-state">
            <h3>No orders to pack</h3>
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
                  <p><strong>Items:</strong> {order.items_count}</p>
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
                      onClick={() => handleStartPacking(order.assignment_id)}
                      className="btn-primary"
                    >
                      Start Packing
                    </button>
                  )}
                  {order.status === 'in_progress' && (
                    <button
                      onClick={() => handleCompletePacking(order.assignment_id)}
                      className="btn-success"
                    >
                      Complete Packing
                    </button>
                  )}
                  {order.status === 'completed' && (
                    <span className="completed-badge">✅ Packed</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Refresh Button */}
      <div className="dashboard-footer">
        <button onClick={fetchPackingQueue} className="btn-refresh">
          🔄 Refresh Queue
        </button>
      </div>
    </div>
  );
};

export default PackerDashboard;

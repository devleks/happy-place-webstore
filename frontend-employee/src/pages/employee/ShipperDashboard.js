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
  const [showShippingModal, setShowShippingModal] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [shippingDetails, setShippingDetails] = useState({
    carrier: '',
    tracking_number: '',
    notes: ''
  });

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

  const openShippingModal = (order) => {
    setSelectedOrder(order);
    setShippingDetails({
      carrier: '',
      tracking_number: '',
      notes: ''
    });
    setShowShippingModal(true);
  };

  const handleCompleteShipping = async () => {
    if (!shippingDetails.carrier || !shippingDetails.tracking_number) {
      alert('Please enter both carrier and tracking number');
      return;
    }

    try {
      await api.post(`/fulfillment/shipping/${selectedOrder.assignment_id}/complete`, shippingDetails);
      setShowShippingModal(false);
      fetchShippingQueue();
      alert('Shipping completed successfully!');
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
          className={`filter-tab ${statusFilter === 'shipped' ? 'active' : ''}`}
          onClick={() => setStatusFilter('shipped')}
        >
          Completed ({orders.filter(o => o.status === 'shipped').length})
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
            {orders
              .filter(order => statusFilter === 'all' || order.status === statusFilter)
              .map((order) => (
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
                      onClick={() => openShippingModal(order)}
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

      {/* Shipping Completion Modal */}
      {showShippingModal && (
        <div className="modal-overlay" onClick={() => setShowShippingModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Complete Shipping</h2>
            <p><strong>Order:</strong> {selectedOrder?.order_number}</p>
            <p><strong>Customer:</strong> {selectedOrder?.customer_name}</p>
            
            <div className="form-group">
              <label>Shipping Carrier/Agent *</label>
              <select
                value={shippingDetails.carrier}
                onChange={(e) => setShippingDetails({...shippingDetails, carrier: e.target.value})}
                required
              >
                <option value="">Select Carrier...</option>
                <option value="DHL">DHL</option>
                <option value="FedEx">FedEx</option>
                <option value="UPS">UPS</option>
                <option value="Aramex">Aramex</option>
                <option value="Posta Kenya">Posta Kenya</option>
                <option value="G4S Courier">G4S Courier</option>
                <option value="Sendy">Sendy</option>
                <option value="Other">Other</option>
              </select>
            </div>

            <div className="form-group">
              <label>Tracking Number *</label>
              <input
                type="text"
                value={shippingDetails.tracking_number}
                onChange={(e) => setShippingDetails({...shippingDetails, tracking_number: e.target.value})}
                placeholder="Enter tracking number"
                required
              />
            </div>

            <div className="form-group">
              <label>Notes (Optional)</label>
              <textarea
                value={shippingDetails.notes}
                onChange={(e) => setShippingDetails({...shippingDetails, notes: e.target.value})}
                placeholder="Add any shipping notes..."
                rows="3"
              />
            </div>

            <div className="modal-actions">
              <button onClick={() => setShowShippingModal(false)} className="btn-secondary">
                Cancel
              </button>
              <button onClick={handleCompleteShipping} className="btn-primary">
                Complete Shipping
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ShipperDashboard;

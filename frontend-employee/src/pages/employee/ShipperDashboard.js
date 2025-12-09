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
  const [statusFilter, setStatusFilter] = useState('packed');
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

  const openShippingForm = (order) => {
    setSelectedOrder(order);
    setShippingDetails({
      carrier: '',
      tracking_number: '',
      notes: ''
    });
  };

  const handleCompleteShipping = async () => {
    if (!shippingDetails.carrier || !shippingDetails.tracking_number) {
      alert('Please enter both carrier and tracking number');
      return;
    }

    try {
      await api.post(`/fulfillment/shipping/${selectedOrder.assignment_id}/complete`, shippingDetails);
      setSelectedOrder(null);
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
      <div className="filter-tabs" style={{ marginBottom: '20px' }}>
        <button
          className={`filter-tab ${statusFilter === 'packed' ? 'active' : ''}`}
          onClick={() => setStatusFilter('packed')}
        >
          Pending ({orders.filter(o => o.order_status === 'packed').length})
        </button>
        <button
          className={`filter-tab ${statusFilter === 'shipping' ? 'active' : ''}`}
          onClick={() => setStatusFilter('shipping')}
        >
          In Progress ({orders.filter(o => o.order_status === 'shipping').length})
        </button>
        <button
          className={`filter-tab ${statusFilter === 'shipped' ? 'active' : ''}`}
          onClick={() => setStatusFilter('shipped')}
        >
          Completed ({orders.filter(o => o.order_status === 'shipped').length})
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

      {/* Two Column Layout */}
      <div style={{ display: 'flex', gap: '20px', height: 'calc(100vh - 250px)' }}>
        {/* Left Column - Orders Queue */}
        <div style={{ flex: selectedOrder ? '0 0 60%' : '1', overflowY: 'auto' }}>
        {orders.length === 0 ? (
          <div className="empty-state">
            <h3>No orders to ship</h3>
            <p>Check back later or change the filter</p>
          </div>
        ) : (
          <div className="orders-grid">
            {orders
              .filter(order => statusFilter === 'all' || order.order_status === statusFilter)
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
                      onClick={() => openShippingForm(order)}
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

        {/* Right Column - Shipping Completion Form */}
        {selectedOrder && (
          <div style={{ 
            flex: '0 0 38%', 
            backgroundColor: '#f8f9fa', 
            padding: '20px', 
            borderRadius: '8px',
            overflowY: 'auto',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h2 style={{ margin: 0 }}>Complete Shipping</h2>
              <button 
                onClick={() => setSelectedOrder(null)} 
                style={{ 
                  background: 'none', 
                  border: 'none', 
                  fontSize: '24px', 
                  cursor: 'pointer',
                  color: '#666'
                }}
              >
                ×
              </button>
            </div>
            
            <div style={{ marginBottom: '15px', padding: '15px', backgroundColor: 'white', borderRadius: '6px' }}>
              <p style={{ margin: '5px 0' }}><strong>Order:</strong> {selectedOrder.order_number}</p>
              <p style={{ margin: '5px 0' }}><strong>Customer:</strong> {selectedOrder.customer_name}</p>
            </div>
            
            <div className="form-group" style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Shipping Carrier/Agent *
              </label>
              <select
                value={shippingDetails.carrier}
                onChange={(e) => setShippingDetails({...shippingDetails, carrier: e.target.value})}
                required
                style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid #ddd' }}
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

            <div className="form-group" style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Tracking Number *
              </label>
              <input
                type="text"
                value={shippingDetails.tracking_number}
                onChange={(e) => setShippingDetails({...shippingDetails, tracking_number: e.target.value})}
                placeholder="Enter tracking number"
                required
                style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid #ddd' }}
              />
            </div>

            <div className="form-group" style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Notes (Optional)
              </label>
              <textarea
                value={shippingDetails.notes}
                onChange={(e) => setShippingDetails({...shippingDetails, notes: e.target.value})}
                placeholder="Add any shipping notes..."
                rows="3"
                style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid #ddd', resize: 'vertical' }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button 
                onClick={() => setSelectedOrder(null)} 
                className="btn-secondary"
                style={{ padding: '10px 20px', borderRadius: '4px', border: '1px solid #ddd', background: 'white', cursor: 'pointer' }}
              >
                Cancel
              </button>
              <button 
                onClick={handleCompleteShipping} 
                className="btn-primary"
                style={{ padding: '10px 20px', borderRadius: '4px', border: 'none', background: '#28a745', color: 'white', cursor: 'pointer' }}
              >
                Complete Shipping
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Refresh Button */}
      <div className="dashboard-footer" style={{ marginTop: '20px' }}>
        <button onClick={fetchShippingQueue} className="btn-refresh">
          🔄 Refresh Queue
        </button>
      </div>
    </div>
  );
};

export default ShipperDashboard;

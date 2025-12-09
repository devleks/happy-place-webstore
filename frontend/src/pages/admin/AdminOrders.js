import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { adminAPI } from '../../services/adminAPI';
import DataTable from '../../components/admin/DataTable';
import StatusBadge from '../../components/admin/StatusBadge';
import '../../styles/AdminDashboard.css';

const AdminOrders = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [orders, setOrders] = useState([]);
  const [filteredOrders, setFilteredOrders] = useState([]);
  const [statusFilter, setStatusFilter] = useState('all');
  const [paymentFilter, setPaymentFilter] = useState('all');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [showModal, setShowModal] = useState(false);
  const [currentOrder, setCurrentOrder] = useState(null);
  const [newStatus, setNewStatus] = useState('');

  useEffect(() => {
    if (!user || (user.role !== 'admin' && user.role !== 'manager')) {
      navigate('/login');
      return;
    }

    fetchOrders();
  }, [user, navigate]);

  useEffect(() => {
    filterOrders();
  }, [statusFilter, paymentFilter, dateRange, orders]);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      const data = await adminAPI.getOrders();
      // API returns {orders: [...], total, page, per_page, total_pages}
      setOrders(data.orders || data || []);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load orders');
      console.error('Orders error:', err);
    } finally {
      setLoading(false);
    }
  };

  const filterOrders = () => {
    let filtered = [...orders];

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter((order) => order.status === statusFilter);
    }

    // Payment filter
    if (paymentFilter !== 'all') {
      filtered = filtered.filter((order) => order.payment_status === paymentFilter);
    }

    // Date range filter
    if (dateRange.start) {
      filtered = filtered.filter(
        (order) => new Date(order.created_at) >= new Date(dateRange.start)
      );
    }
    if (dateRange.end) {
      filtered = filtered.filter(
        (order) => new Date(order.created_at) <= new Date(dateRange.end)
      );
    }

    setFilteredOrders(filtered);
  };

  const openOrderDetails = (order) => {
    setCurrentOrder(order);
    setNewStatus(order.status);
    setShowModal(true);
  };

  const handleUpdateStatus = async () => {
    if (!currentOrder || !newStatus) return;

    try {
      await adminAPI.updateOrderStatus(currentOrder.id, newStatus);
      setShowModal(false);
      fetchOrders();
      alert('Order status updated successfully');
    } catch (err) {
      alert(err.message || 'Failed to update order status');
    }
  };

  const handleCancelOrder = async (orderId) => {
    if (!window.confirm('Are you sure you want to cancel this order?')) return;

    try {
      await adminAPI.cancelOrder(orderId);
      fetchOrders();
      alert('Order cancelled successfully');
    } catch (err) {
      alert(err.message || 'Failed to cancel order');
    }
  };

  const handleRefundOrder = async (orderId) => {
    if (!window.confirm('Are you sure you want to refund this order?')) return;

    try {
      await adminAPI.refundOrder(orderId);
      fetchOrders();
      alert('Order refunded successfully');
    } catch (err) {
      alert(err.message || 'Failed to refund order');
    }
  };

  const columns = [
    { key: 'order_number', label: 'Order #' },
    {
      key: 'customer_name',
      label: 'Customer',
      render: (order) => order.customer_name || `User ${order.user_id}`,
    },
    {
      key: 'created_at',
      label: 'Date',
      render: (order) => new Date(order.created_at).toLocaleDateString(),
    },
    {
      key: 'total_amount',
      label: 'Total',
      render: (order) => `$${order.total_amount.toFixed(2)}`,
    },
    {
      key: 'status',
      label: 'Status',
      render: (order) => <StatusBadge status={order.status} />,
    },
    {
      key: 'payment_status',
      label: 'Payment',
      render: (order) => <StatusBadge status={order.payment_status} />,
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (order) => (
        <div className="action-buttons">
          <button
            className="btn-icon"
            onClick={() => openOrderDetails(order)}
            title="View Details"
          >
            👁️
          </button>
          {order.status !== 'cancelled' && (
            <button
              className="btn-icon"
              onClick={() => handleCancelOrder(order.id)}
              title="Cancel Order"
            >
              ❌
            </button>
          )}
        </div>
      ),
    },
  ];

  if (loading) {
    return <div className="loading-spinner">Loading orders...</div>;
  }

  return (
    <div className="admin-orders">
      <div className="page-header">
        <h1>Order Management</h1>
      </div>

      {error && (
        <div className="error-message">
          {error}
          <button onClick={() => setError(null)} className="close-btn">×</button>
        </div>
      )}

      {/* Filters */}
      <div className="filters-section">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="filter-select"
        >
          <option value="all">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="processing">Processing</option>
          <option value="shipped">Shipped</option>
          <option value="delivered">Delivered</option>
          <option value="cancelled">Cancelled</option>
        </select>

        <select
          value={paymentFilter}
          onChange={(e) => setPaymentFilter(e.target.value)}
          className="filter-select"
        >
          <option value="all">All Payment Statuses</option>
          <option value="pending">Pending</option>
          <option value="paid">Paid</option>
          <option value="failed">Failed</option>
          <option value="refunded">Refunded</option>
        </select>

        <input
          type="date"
          value={dateRange.start}
          onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
          className="filter-input"
          placeholder="Start Date"
        />

        <input
          type="date"
          value={dateRange.end}
          onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
          className="filter-input"
          placeholder="End Date"
        />

        <button
          onClick={() => {
            setStatusFilter('all');
            setPaymentFilter('all');
            setDateRange({ start: '', end: '' });
          }}
          className="btn-secondary"
        >
          Clear Filters
        </button>
      </div>

      {/* Data Table */}
      <DataTable
        columns={columns}
        data={filteredOrders}
        keyField="id"
        emptyMessage="No orders found"
      />

      {/* Order Details Modal */}
      {showModal && currentOrder && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Order Details - {currentOrder.order_number}</h2>
              <button onClick={() => setShowModal(false)} className="close-btn">
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="order-details">
                <div className="detail-section">
                  <h3>Customer Information</h3>
                  <p><strong>Name:</strong> {currentOrder.customer_name}</p>
                  <p><strong>Email:</strong> {currentOrder.customer_email}</p>
                  <p><strong>Phone:</strong> {currentOrder.customer_phone}</p>
                </div>

                <div className="detail-section">
                  <h3>Shipping Address</h3>
                  <p>{currentOrder.shipping_address?.street}</p>
                  <p>
                    {currentOrder.shipping_address?.city},{' '}
                    {currentOrder.shipping_address?.state}{' '}
                    {currentOrder.shipping_address?.zip_code}
                  </p>
                  <p>{currentOrder.shipping_address?.country}</p>
                </div>

                <div className="detail-section">
                  <h3>Order Items</h3>
                  {currentOrder.items?.map((item) => (
                    <div key={item.id} className="order-item">
                      <span>{item.product_name}</span>
                      <span>Qty: {item.quantity}</span>
                      <span>${item.price.toFixed(2)}</span>
                    </div>
                  ))}
                </div>

                <div className="detail-section">
                  <h3>Order Summary</h3>
                  <p><strong>Subtotal:</strong> ${currentOrder.subtotal?.toFixed(2)}</p>
                  <p><strong>Tax:</strong> ${currentOrder.tax?.toFixed(2)}</p>
                  <p><strong>Shipping:</strong> ${currentOrder.shipping_cost?.toFixed(2)}</p>
                  <p><strong>Total:</strong> ${currentOrder.total_amount.toFixed(2)}</p>
                </div>

                <div className="detail-section">
                  <h3>Update Status</h3>
                  <select
                    value={newStatus}
                    onChange={(e) => setNewStatus(e.target.value)}
                    className="form-input"
                  >
                    <option value="pending">Pending</option>
                    <option value="processing">Processing</option>
                    <option value="shipped">Shipped</option>
                    <option value="delivered">Delivered</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowModal(false)} className="btn-secondary">
                Close
              </button>
              {currentOrder.payment_status === 'paid' && (
                <button
                  onClick={() => handleRefundOrder(currentOrder.id)}
                  className="btn-danger"
                >
                  Refund Order
                </button>
              )}
              <button onClick={handleUpdateStatus} className="btn-primary">
                Update Status
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminOrders;

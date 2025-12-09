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
  
  // Phase 1: Tracking modal state
  const [showTrackingModal, setShowTrackingModal] = useState(false);
  const [trackingData, setTrackingData] = useState({
    tracking_number: '',
    carrier: '',
    estimated_delivery: '',
    notes: ''
  });
  const [carriers, setCarriers] = useState([]);
  const [loadingCarriers, setLoadingCarriers] = useState(false);

  // Phase 1: Fulfillment modal state
  const [showFulfillmentModal, setShowFulfillmentModal] = useState(false);
  const [fulfillmentData, setFulfillmentData] = useState({
    role: 'packer',
    employee_id: '',
    notes: ''
  });
  const [employees, setEmployees] = useState([]);
  const [loadingEmployees, setLoadingEmployees] = useState(false);

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

  // Phase 1: Tracking functions
  const openTrackingModal = async (order) => {
    setCurrentOrder(order);
    setShowTrackingModal(true);
    
    // Reset form
    setTrackingData({
      tracking_number: order.tracking_number || '',
      carrier: order.carrier || '',
      estimated_delivery: order.estimated_delivery_date || '',
      notes: order.shipping_notes || ''
    });
    
    // Fetch carriers
    try {
      setLoadingCarriers(true);
      const data = await adminAPI.getShippingCarriers();
      setCarriers(data.carriers || []);
    } catch (err) {
      console.error('Failed to load carriers:', err);
      alert('Failed to load shipping carriers');
    } finally {
      setLoadingCarriers(false);
    }
  };

  const handleAddTracking = async () => {
    if (!currentOrder) return;
    
    // Validation
    if (!trackingData.tracking_number.trim()) {
      alert('Please enter a tracking number');
      return;
    }
    if (!trackingData.carrier) {
      alert('Please select a carrier');
      return;
    }

    try {
      await adminAPI.addOrderTracking(currentOrder.id, trackingData);
      setShowTrackingModal(false);
      fetchOrders();
      alert('Tracking information added successfully');
    } catch (err) {
      alert(err.message || 'Failed to add tracking information');
    }
  };

  // Phase 1: Fulfillment functions
  const openFulfillmentModal = async (order) => {
    setCurrentOrder(order);
    setShowFulfillmentModal(true);
    
    // Reset form
    setFulfillmentData({
      role: 'packer',
      employee_id: '',
      notes: ''
    });
    
    // Fetch employees
    try {
      setLoadingEmployees(true);
      const data = await adminAPI.getEmployees();
      setEmployees(data.employees || []);
    } catch (err) {
      console.error('Failed to load employees:', err);
      alert('Failed to load employees');
    } finally {
      setLoadingEmployees(false);
    }
  };

  const handleAssignOrder = async () => {
    if (!currentOrder) return;
    
    // Validation
    if (!fulfillmentData.employee_id) {
      alert('Please select an employee');
      return;
    }

    try {
      await adminAPI.assignOrder({
        order_id: currentOrder.id,
        employee_id: parseInt(fulfillmentData.employee_id),
        role: fulfillmentData.role,
        notes: fulfillmentData.notes
      });
      setShowFulfillmentModal(false);
      fetchOrders();
      alert(`Order assigned to ${fulfillmentData.role} successfully`);
    } catch (err) {
      alert(err.message || 'Failed to assign order');
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
          {order.status === 'processing' && (
            <button
              className="btn-icon"
              onClick={() => openFulfillmentModal(order)}
              title="Assign to Fulfillment"
            >
              👤
            </button>
          )}
          {(order.status === 'processing' || order.status === 'shipped') && (
            <button
              className="btn-icon"
              onClick={() => openTrackingModal(order)}
              title={order.tracking_number ? "Update Tracking" : "Add Tracking"}
            >
              📦
            </button>
          )}
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

      {/* Fulfillment Assignment Modal (Phase 1) */}
      {showFulfillmentModal && currentOrder && (
        <div className="modal-overlay" onClick={() => setShowFulfillmentModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Assign Order #{currentOrder.order_number} to Fulfillment</h2>
              <button onClick={() => setShowFulfillmentModal(false)} className="close-btn">
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label htmlFor="fulfillment_role">Assign To *</label>
                <select
                  id="fulfillment_role"
                  className="form-input"
                  value={fulfillmentData.role}
                  onChange={(e) => setFulfillmentData({...fulfillmentData, role: e.target.value, employee_id: ''})}
                >
                  <option value="packer">Packer (for packing)</option>
                  <option value="shipper">Shipper (for shipping)</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="employee_id">Employee *</label>
                {loadingEmployees ? (
                  <p>Loading employees...</p>
                ) : (
                  <select
                    id="employee_id"
                    className="form-input"
                    value={fulfillmentData.employee_id}
                    onChange={(e) => setFulfillmentData({...fulfillmentData, employee_id: e.target.value})}
                    required
                  >
                    <option value="">Select an employee</option>
                    {employees
                      .filter(emp => emp.role === fulfillmentData.role || emp.role === 'manager' || emp.role === 'admin')
                      .map((employee) => (
                        <option key={employee.id} value={employee.id}>
                          {employee.full_name} ({employee.role})
                        </option>
                      ))}
                  </select>
                )}
              </div>

              <div className="form-group">
                <label htmlFor="fulfillment_notes">Assignment Notes</label>
                <textarea
                  id="fulfillment_notes"
                  className="form-input"
                  value={fulfillmentData.notes}
                  onChange={(e) => setFulfillmentData({...fulfillmentData, notes: e.target.value})}
                  placeholder="e.g., Priority order, handle with care"
                  rows="3"
                />
              </div>

              <div className="info-box">
                <p><strong>Order Details:</strong></p>
                <p>Customer: {currentOrder.customer_name}</p>
                <p>Items: {currentOrder.items?.length || 0}</p>
                <p>Total: KES {currentOrder.total_amount?.toLocaleString()}</p>
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowFulfillmentModal(false)} className="btn-secondary">
                Cancel
              </button>
              <button onClick={handleAssignOrder} className="btn-primary">
                Assign Order
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tracking Modal (Phase 1) */}
      {showTrackingModal && currentOrder && (
        <div className="modal-overlay" onClick={() => setShowTrackingModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>
                {currentOrder.tracking_number ? 'Update' : 'Add'} Tracking - Order #{currentOrder.order_number}
              </h2>
              <button onClick={() => setShowTrackingModal(false)} className="close-btn">
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label htmlFor="tracking_number">Tracking Number *</label>
                <input
                  type="text"
                  id="tracking_number"
                  className="form-input"
                  value={trackingData.tracking_number}
                  onChange={(e) => setTrackingData({...trackingData, tracking_number: e.target.value})}
                  placeholder="e.g., DHL123456789KE"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="carrier">Shipping Carrier *</label>
                {loadingCarriers ? (
                  <p>Loading carriers...</p>
                ) : (
                  <select
                    id="carrier"
                    className="form-input"
                    value={trackingData.carrier}
                    onChange={(e) => setTrackingData({...trackingData, carrier: e.target.value})}
                    required
                  >
                    <option value="">Select a carrier</option>
                    {carriers.map((carrier) => (
                      <option key={carrier.id} value={carrier.name}>
                        {carrier.name}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div className="form-group">
                <label htmlFor="estimated_delivery">Estimated Delivery Date</label>
                <input
                  type="date"
                  id="estimated_delivery"
                  className="form-input"
                  value={trackingData.estimated_delivery}
                  onChange={(e) => setTrackingData({...trackingData, estimated_delivery: e.target.value})}
                  min={new Date().toISOString().split('T')[0]}
                />
              </div>

              <div className="form-group">
                <label htmlFor="notes">Shipping Notes</label>
                <textarea
                  id="notes"
                  className="form-input"
                  value={trackingData.notes}
                  onChange={(e) => setTrackingData({...trackingData, notes: e.target.value})}
                  placeholder="e.g., Package dispatched from Nairobi warehouse"
                  rows="3"
                />
              </div>

              {currentOrder.tracking_number && (
                <div className="info-box">
                  <p><strong>Current Tracking:</strong> {currentOrder.tracking_number}</p>
                  <p><strong>Carrier:</strong> {currentOrder.carrier}</p>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowTrackingModal(false)} className="btn-secondary">
                Cancel
              </button>
              <button onClick={handleAddTracking} className="btn-primary">
                {currentOrder.tracking_number ? 'Update' : 'Add'} Tracking
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminOrders;

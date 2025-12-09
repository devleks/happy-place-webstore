import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { adminAPI } from '../../services/adminAPI';
import DataTable from '../../components/admin/DataTable';
import StatusBadge from '../../components/admin/StatusBadge';
import '../../styles/AdminDashboard.css';

const AdminCustomers = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [customers, setCustomers] = useState([]);
  const [filteredCustomers, setFilteredCustomers] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [currentCustomer, setCurrentCustomer] = useState(null);
  const [customerOrders, setCustomerOrders] = useState([]);

  useEffect(() => {
    if (!user || (user.role !== 'admin' && user.role !== 'manager')) {
      navigate('/login');
      return;
    }

    fetchCustomers();
  }, [user, navigate]);

  useEffect(() => {
    filterCustomers();
  }, [searchTerm, customers]);

  const fetchCustomers = async () => {
    try {
      setLoading(true);
      const data = await adminAPI.getCustomers();
      // API returns {customers: [...], total, page, per_page, total_pages}
      setCustomers(data.customers || data || []);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load customers');
      console.error('Customers error:', err);
    } finally {
      setLoading(false);
    }
  };

  const filterCustomers = () => {
    let filtered = [...customers];

    if (searchTerm) {
      filtered = filtered.filter(
        (customer) =>
          customer.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          customer.email?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredCustomers(filtered);
  };

  const openCustomerDetails = async (customer) => {
    setCurrentCustomer(customer);
    try {
      const orders = await adminAPI.getCustomerOrders(customer.id);
      setCustomerOrders(orders);
    } catch (err) {
      console.error('Failed to fetch customer orders:', err);
      setCustomerOrders([]);
    }
    setShowModal(true);
  };

  const handleExportData = async (customerId) => {
    try {
      await adminAPI.exportCustomerData(customerId);
      alert('Customer data exported successfully');
    } catch (err) {
      alert(err.message || 'Failed to export customer data');
    }
  };

  const handleAnonymizeCustomer = async (customerId) => {
    if (!window.confirm('Are you sure you want to anonymize this customer? This action cannot be undone.')) {
      return;
    }

    try {
      await adminAPI.anonymizeCustomer(customerId);
      fetchCustomers();
      setShowModal(false);
      alert('Customer anonymized successfully');
    } catch (err) {
      alert(err.message || 'Failed to anonymize customer');
    }
  };

  const handleDeleteCustomer = async (customerId) => {
    if (!window.confirm('Are you sure you want to delete this customer? This action cannot be undone.')) {
      return;
    }

    try {
      await adminAPI.deleteCustomer(customerId);
      fetchCustomers();
      setShowModal(false);
      alert('Customer deleted successfully');
    } catch (err) {
      alert(err.message || 'Failed to delete customer');
    }
  };

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'name', label: 'Name' },
    { key: 'email', label: 'Email' },
    {
      key: 'created_at',
      label: 'Joined',
      render: (customer) => new Date(customer.created_at).toLocaleDateString(),
    },
    {
      key: 'total_orders',
      label: 'Orders',
      render: (customer) => customer.total_orders || 0,
    },
    {
      key: 'total_spent',
      label: 'Total Spent',
      render: (customer) => `$${(customer.total_spent || 0).toFixed(2)}`,
    },
    {
      key: 'status',
      label: 'Status',
      render: (customer) => (
        <StatusBadge status={customer.is_active ? 'active' : 'inactive'} />
      ),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (customer) => (
        <div className="action-buttons">
          <button
            className="btn-icon"
            onClick={() => openCustomerDetails(customer)}
            title="View Details"
          >
            👁️
          </button>
          <button
            className="btn-icon"
            onClick={() => handleExportData(customer.id)}
            title="Export Data (GDPR)"
          >
            📥
          </button>
        </div>
      ),
    },
  ];

  if (loading) {
    return <div className="loading-spinner">Loading customers...</div>;
  }

  return (
    <div className="admin-customers">
      <div className="page-header">
        <h1>Customer Management</h1>
      </div>

      {error && (
        <div className="error-message">
          {error}
          <button onClick={() => setError(null)} className="close-btn">×</button>
        </div>
      )}

      {/* Search */}
      <div className="filters-section">
        <input
          type="text"
          placeholder="Search by name or email..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
      </div>

      {/* Data Table */}
      <DataTable
        columns={columns}
        data={filteredCustomers}
        keyField="id"
        emptyMessage="No customers found"
      />

      {/* Customer Details Modal */}
      {showModal && currentCustomer && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Customer Details - {currentCustomer.name}</h2>
              <button onClick={() => setShowModal(false)} className="close-btn">
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="customer-details">
                <div className="detail-section">
                  <h3>Personal Information</h3>
                  <p><strong>Name:</strong> {currentCustomer.name}</p>
                  <p><strong>Email:</strong> {currentCustomer.email}</p>
                  <p><strong>Phone:</strong> {currentCustomer.phone || 'N/A'}</p>
                  <p>
                    <strong>Joined:</strong>{' '}
                    {new Date(currentCustomer.created_at).toLocaleDateString()}
                  </p>
                  <p>
                    <strong>Status:</strong>{' '}
                    <StatusBadge status={currentCustomer.is_active ? 'active' : 'inactive'} />
                  </p>
                </div>

                <div className="detail-section">
                  <h3>Statistics</h3>
                  <p><strong>Total Orders:</strong> {currentCustomer.total_orders || 0}</p>
                  <p>
                    <strong>Total Spent:</strong> $
                    {(currentCustomer.total_spent || 0).toFixed(2)}
                  </p>
                  <p>
                    <strong>Average Order Value:</strong> $
                    {currentCustomer.total_orders > 0
                      ? ((currentCustomer.total_spent || 0) / currentCustomer.total_orders).toFixed(2)
                      : '0.00'}
                  </p>
                </div>

                <div className="detail-section">
                  <h3>Order History</h3>
                  {customerOrders.length > 0 ? (
                    <div className="order-history">
                      {customerOrders.map((order) => (
                        <div key={order.id} className="order-item">
                          <span>{order.order_number}</span>
                          <span>{new Date(order.created_at).toLocaleDateString()}</span>
                          <span>${order.total_amount.toFixed(2)}</span>
                          <StatusBadge status={order.status} />
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p>No orders found</p>
                  )}
                </div>

                <div className="detail-section">
                  <h3>GDPR Actions</h3>
                  <p className="gdpr-note">
                    These actions are irreversible and should be used in compliance with GDPR regulations.
                  </p>
                  <div className="gdpr-actions">
                    <button
                      onClick={() => handleExportData(currentCustomer.id)}
                      className="btn-secondary"
                    >
                      Export Customer Data
                    </button>
                    <button
                      onClick={() => handleAnonymizeCustomer(currentCustomer.id)}
                      className="btn-warning"
                    >
                      Anonymize Customer
                    </button>
                    <button
                      onClick={() => handleDeleteCustomer(currentCustomer.id)}
                      className="btn-danger"
                    >
                      Delete Customer
                    </button>
                  </div>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setShowModal(false)} className="btn-primary">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminCustomers;

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { helpers } from '../services/api';
import toast from '../utils/toast';
import '../styles/OrderHistory.css';

const OrderHistory = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 10,
    total: 0,
    pages: 0,
  });
  const [filterStatus, setFilterStatus] = useState('all');

  useEffect(() => {
    if (!user) {
      toast.warning('Please log in to view order history');
      navigate('/login');
      return;
    }

    fetchOrders();
  }, [user, pagination.page, filterStatus, navigate]);

  const fetchOrders = async () => {
    try {
      setLoading(true);

      let url = `http://localhost:5001/api/orders?page=${pagination.page}&per_page=${pagination.per_page}`;

      if (filterStatus !== 'all') {
        url += `&status=${filterStatus}`;
      }

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setOrders(data.orders);
        setPagination({
          page: data.page,
          per_page: data.per_page,
          total: data.total,
          pages: data.pages,
        });
      } else {
        const errorData = await response.json();
        toast.error(errorData.error || 'Failed to load orders');
      }
    } catch (error) {
      console.error('Error fetching orders:', error);
      toast.error('Failed to load order history');
    } finally {
      setLoading(false);
    }
  };

  const handleViewOrder = (orderId) => {
    navigate(`/order-confirmation/${orderId}`);
  };

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= pagination.pages) {
      setPagination((prev) => ({ ...prev, page: newPage }));
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleFilterChange = (status) => {
    setFilterStatus(status);
    setPagination((prev) => ({ ...prev, page: 1 }));
  };

  const getStatusBadgeClass = (status) => {
    return `status-badge badge-${status}`;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  if (loading && orders.length === 0) {
    return (
      <div className="order-history-page">
        <div className="loading">Loading your orders...</div>
      </div>
    );
  }

  return (
    <div className="order-history-page">
      <div className="order-history-container">
        {/* Page Header */}
        <div className="page-header">
          <h1 className="page-title">Order History</h1>
          <p className="page-subtitle">
            View and track all your orders
          </p>
        </div>

        {/* Filter Tabs */}
        <div className="filter-tabs">
          <button
            className={`filter-tab ${filterStatus === 'all' ? 'active' : ''}`}
            onClick={() => handleFilterChange('all')}
          >
            All Orders
          </button>
          <button
            className={`filter-tab ${filterStatus === 'pending' ? 'active' : ''}`}
            onClick={() => handleFilterChange('pending')}
          >
            Pending
          </button>
          <button
            className={`filter-tab ${filterStatus === 'processing' ? 'active' : ''}`}
            onClick={() => handleFilterChange('processing')}
          >
            Processing
          </button>
          <button
            className={`filter-tab ${filterStatus === 'shipped' ? 'active' : ''}`}
            onClick={() => handleFilterChange('shipped')}
          >
            Shipped
          </button>
          <button
            className={`filter-tab ${filterStatus === 'delivered' ? 'active' : ''}`}
            onClick={() => handleFilterChange('delivered')}
          >
            Delivered
          </button>
        </div>

        {/* Orders List */}
        {orders.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect>
                <line x1="1" y1="10" x2="23" y2="10"></line>
              </svg>
            </div>
            <h2>No Orders Found</h2>
            <p>
              {filterStatus === 'all'
                ? "You haven't placed any orders yet."
                : `You don't have any ${filterStatus} orders.`}
            </p>
            <button
              className="btn-shop-now"
              onClick={() => navigate('/products')}
            >
              Start Shopping
            </button>
          </div>
        ) : (
          <>
            <div className="orders-list">
              {orders.map((order) => (
                <div
                  key={order.id}
                  className="order-card"
                  onClick={() => handleViewOrder(order.id)}
                >
                  <div className="order-card-header">
                    <div className="order-number">
                      <span className="label">Order Number:</span>
                      <span className="value">{order.order_number}</span>
                    </div>
                    <span className={getStatusBadgeClass(order.status)}>
                      {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                    </span>
                  </div>

                  <div className="order-card-body">
                    <div className="order-info-row">
                      <div className="info-item">
                        <svg className="info-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <circle cx="12" cy="12" r="10"></circle>
                          <polyline points="12 6 12 12 16 14"></polyline>
                        </svg>
                        <div>
                          <div className="info-label">Order Date</div>
                          <div className="info-value">{formatDate(order.created_at)}</div>
                        </div>
                      </div>

                      <div className="info-item">
                        <svg className="info-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                          <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
                          <line x1="12" y1="22.08" x2="12" y2="12"></line>
                        </svg>
                        <div>
                          <div className="info-label">Items</div>
                          <div className="info-value">{order.items?.length || 0} items</div>
                        </div>
                      </div>

                      <div className="info-item">
                        <svg className="info-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                          <circle cx="12" cy="7" r="4"></circle>
                        </svg>
                        <div>
                          <div className="info-label">Shipping</div>
                          <div className="info-value">
                            {order.is_nairobi ? 'Free (Nairobi)' : 'Upcountry'}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Order Items Preview */}
                    {order.items && order.items.length > 0 && (
                      <div className="order-items-preview">
                        {order.items.slice(0, 3).map((item) => (
                          <img
                            key={item.id}
                            src={item.product?.image_url}
                            alt={item.product?.name}
                            className="item-thumbnail"
                          />
                        ))}
                        {order.items.length > 3 && (
                          <div className="more-items">
                            +{order.items.length - 3}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="order-card-footer">
                    <div className="total-label">Total</div>
                    <div className="total-amount">{helpers.formatPrice(order.total)}</div>
                    {/* Phase 1: Track Order Button */}
                    {order.tracking_number && (order.status === 'shipped' || order.status === 'delivered') && (
                      <button
                        className="btn-track-order"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/track-order/${order.id}`);
                        }}
                      >
                        📦 Track Order
                      </button>
                    )}
                  </div>

                  <div className="view-details-arrow">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="9 18 15 12 9 6"></polyline>
                    </svg>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {pagination.pages > 1 && (
              <div className="pagination">
                <button
                  className="pagination-btn"
                  onClick={() => handlePageChange(pagination.page - 1)}
                  disabled={pagination.page === 1}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="15 18 9 12 15 6"></polyline>
                  </svg>
                  Previous
                </button>

                <div className="pagination-info">
                  Page {pagination.page} of {pagination.pages}
                  <span className="total-orders">({pagination.total} orders)</span>
                </div>

                <button
                  className="pagination-btn"
                  onClick={() => handlePageChange(pagination.page + 1)}
                  disabled={pagination.page === pagination.pages}
                >
                  Next
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="9 18 15 12 9 6"></polyline>
                  </svg>
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default OrderHistory;

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import '../styles/OrderHistory.css';

const TrackOrder = () => {
  const { orderId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [trackingInfo, setTrackingInfo] = useState(null);
  const [order, setOrder] = useState(null);

  const fetchTrackingInfo = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch order details
      const orderResponse = await api.get(`/orders/${orderId}`);
      setOrder(orderResponse.data);

      // Check if order has tracking
      if (orderResponse.data.tracking_number) {
        // Fetch tracking details from admin API (customers can view their own orders)
        try {
          const trackingResponse = await api.get(`/orders/${orderId}/tracking`);
          setTrackingInfo(trackingResponse.data);
        } catch (err) {
          // If tracking endpoint doesn't exist for customers, use order data
          setTrackingInfo({
            tracking_number: orderResponse.data.tracking_number,
            carrier: orderResponse.data.carrier,
            tracking_url: orderResponse.data.tracking_url,
            estimated_delivery_date: orderResponse.data.estimated_delivery_date,
            shipping_notes: orderResponse.data.shipping_notes,
            status: orderResponse.data.status,
            shipped_at: orderResponse.data.shipped_at,
            delivered_at: orderResponse.data.delivered_at,
            updates: []
          });
        }
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load tracking information');
      console.error('Tracking error:', err);
    } finally {
      setLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    fetchTrackingInfo();
  }, [user, navigate, fetchTrackingInfo]);

  const getStatusIcon = (status) => {
    const icons = {
      pending: '⏳',
      processing: '📋',
      shipped: '🚚',
      in_transit: '✈️',
      out_for_delivery: '🚛',
      delivered: '✅',
      exception: '⚠️'
    };
    return icons[status] || '📦';
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: '#ffc107',
      processing: '#2196F3',
      shipped: '#9C27B0',
      in_transit: '#FF9800',
      out_for_delivery: '#FF5722',
      delivered: '#4CAF50',
      exception: '#f44336'
    };
    return colors[status] || '#757575';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="container">
        <div className="loading-spinner">Loading tracking information...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container">
        <div className="error-message">
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={() => navigate('/orders')} className="btn-primary">
            Back to Orders
          </button>
        </div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="container">
        <div className="error-message">
          <h2>Order Not Found</h2>
          <p>We couldn't find this order.</p>
          <button onClick={() => navigate('/orders')} className="btn-primary">
            Back to Orders
          </button>
        </div>
      </div>
    );
  }

  if (!trackingInfo || !order.tracking_number) {
    return (
      <div className="container">
        <div className="track-order-page">
          <h1>Order Tracking</h1>
          <div className="tracking-card">
            <div className="no-tracking">
              <h2>📦 Order #{order.order_number}</h2>
              <p className="status-text">
                Status: <span style={{ color: getStatusColor(order.status) }}>
                  {order.status.toUpperCase()}
                </span>
              </p>
              <div className="info-box">
                <p>Tracking information is not yet available for this order.</p>
                <p>Your order is currently being processed. You'll receive tracking details once it ships.</p>
              </div>
              <button onClick={() => navigate('/orders')} className="btn-secondary">
                Back to Orders
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="track-order-page">
        <div className="page-header">
          <h1>Track Your Order</h1>
          <button onClick={() => navigate('/orders')} className="btn-secondary">
            ← Back to Orders
          </button>
        </div>

        {/* Order Summary */}
        <div className="tracking-card">
          <div className="tracking-header">
            <h2>Order #{order.order_number}</h2>
            <span className="status-badge" style={{ backgroundColor: getStatusColor(trackingInfo.status) }}>
              {getStatusIcon(trackingInfo.status)} {trackingInfo.status.replace('_', ' ').toUpperCase()}
            </span>
          </div>

          {/* Tracking Details */}
          <div className="tracking-details">
            <div className="detail-row">
              <div className="detail-item">
                <strong>Tracking Number:</strong>
                <span className="tracking-number">{trackingInfo.tracking_number}</span>
              </div>
              <div className="detail-item">
                <strong>Carrier:</strong>
                <span>{trackingInfo.carrier}</span>
              </div>
            </div>

            {trackingInfo.estimated_delivery_date && (
              <div className="detail-row">
                <div className="detail-item">
                  <strong>Estimated Delivery:</strong>
                  <span>{formatDate(trackingInfo.estimated_delivery_date)}</span>
                </div>
              </div>
            )}

            {trackingInfo.tracking_url && (
              <div className="detail-row">
                <a
                  href={trackingInfo.tracking_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-primary"
                  style={{ marginTop: '10px' }}
                >
                  🔗 Track on {trackingInfo.carrier} Website
                </a>
              </div>
            )}
          </div>

          {/* Shipping Notes */}
          {trackingInfo.shipping_notes && (
            <div className="shipping-notes">
              <strong>Shipping Notes:</strong>
              <p>{trackingInfo.shipping_notes}</p>
            </div>
          )}
        </div>

        {/* Tracking Timeline */}
        {trackingInfo.updates && trackingInfo.updates.length > 0 && (
          <div className="tracking-card">
            <h3>Shipment Timeline</h3>
            <div className="tracking-timeline">
              {trackingInfo.updates.map((update, index) => (
                <div key={update.id || index} className="timeline-item">
                  <div className="timeline-icon" style={{ backgroundColor: getStatusColor(update.status) }}>
                    {getStatusIcon(update.status)}
                  </div>
                  <div className="timeline-content">
                    <div className="timeline-header">
                      <strong>{update.status.replace('_', ' ').toUpperCase()}</strong>
                      <span className="timeline-date">{formatDate(update.timestamp)}</span>
                    </div>
                    {update.location && (
                      <p className="timeline-location">📍 {update.location}</p>
                    )}
                    {update.description && (
                      <p className="timeline-description">{update.description}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Default Timeline (if no updates) */}
        {(!trackingInfo.updates || trackingInfo.updates.length === 0) && (
          <div className="tracking-card">
            <h3>Shipment Timeline</h3>
            <div className="tracking-timeline">
              {trackingInfo.shipped_at && (
                <div className="timeline-item">
                  <div className="timeline-icon" style={{ backgroundColor: getStatusColor('shipped') }}>
                    🚚
                  </div>
                  <div className="timeline-content">
                    <div className="timeline-header">
                      <strong>SHIPPED</strong>
                      <span className="timeline-date">{formatDate(trackingInfo.shipped_at)}</span>
                    </div>
                    <p className="timeline-description">Your order has been shipped</p>
                  </div>
                </div>
              )}
              
              {trackingInfo.delivered_at && (
                <div className="timeline-item">
                  <div className="timeline-icon" style={{ backgroundColor: getStatusColor('delivered') }}>
                    ✅
                  </div>
                  <div className="timeline-content">
                    <div className="timeline-header">
                      <strong>DELIVERED</strong>
                      <span className="timeline-date">{formatDate(trackingInfo.delivered_at)}</span>
                    </div>
                    <p className="timeline-description">Package delivered successfully</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Order Items */}
        {order.items && order.items.length > 0 && (
          <div className="tracking-card">
            <h3>Order Items</h3>
            <div className="order-items-list">
              {order.items.map((item) => (
                <div key={item.id} className="order-item-row">
                  {item.product?.image_url && (
                    <img src={item.product.image_url} alt={item.product.name} className="item-image" />
                  )}
                  <div className="item-details">
                    <strong>{item.product?.name || 'Product'}</strong>
                    <p>Quantity: {item.quantity}</p>
                  </div>
                  <div className="item-price">
                    KES {(item.unit_price * item.quantity).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TrackOrder;

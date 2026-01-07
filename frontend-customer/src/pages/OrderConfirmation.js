import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { helpers } from '../services/api';
import toast from '../utils/toast';
import '../styles/OrderConfirmation.css';

const OrderConfirmation = () => {
  const { orderId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [confirmingCod, setConfirmingCod] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState(null);
  const [checkingPayment, setCheckingPayment] = useState(false);

  // Get M-Pesa data from location state (if passed from checkout)
  const mpesaData = location.state?.mpesa;
  const paymentMethod = location.state?.paymentMethod || order?.payment_method;

  const fetchOrderDetails = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`http://localhost:5001/api/orders/${orderId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setOrder(data.order);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to load order');
        toast.error('Failed to load order details');
      }
    } catch (err) {
      console.error('Error fetching order:', err);
      setError('Failed to load order');
      toast.error('Failed to load order details');
    } finally {
      setLoading(false);
    }
  }, [orderId]);

  // Check payment status (for M-Pesa)
  const checkPaymentStatus = useCallback(async () => {
    if (!order || !order.payment_id) return;

    try {
      setCheckingPayment(true);
      const response = await fetch(`http://localhost:5001/api/payments/${order.payment_id}/status`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setPaymentStatus(data.payment);

        // If payment completed, refresh order details
        if (data.payment?.status === 'completed') {
          toast.success('Payment completed successfully!');
          fetchOrderDetails();
        }
      }
    } catch (err) {
      console.error('Error checking payment status:', err);
    } finally {
      setCheckingPayment(false);
    }
  }, [order, fetchOrderDetails]);

  useEffect(() => {
    if (!user) {
      toast.warning('Please log in to view order');
      navigate('/login');
      return;
    }

    fetchOrderDetails();
  }, [user, navigate, fetchOrderDetails]);

  // Poll payment status for M-Pesa orders
  useEffect(() => {
    if (!order || paymentMethod !== 'mpesa') return;
    if (order.payment_status === 'completed') return;

    // Initial check
    checkPaymentStatus();

    // Poll every 5 seconds for 2 minutes
    const pollInterval = setInterval(checkPaymentStatus, 5000);
    const pollTimeout = setTimeout(() => {
      clearInterval(pollInterval);
      if (paymentStatus?.status !== 'completed') {
        toast.info('Payment still pending. You can check status in your order history.');
      }
    }, 120000); // 2 minutes

    return () => {
      clearInterval(pollInterval);
      clearTimeout(pollTimeout);
    };
  }, [order, paymentMethod, paymentStatus, checkPaymentStatus]);

  const handleConfirmCod = async () => {
    if (!orderId) return;
    if (!window.confirm('Confirm this Cash on Delivery order?')) return;

    try {
      setConfirmingCod(true);
      const response = await fetch(`http://localhost:5001/api/orders/${orderId}/confirm-cod`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();
      if (!response.ok) {
        toast.error(data.error || 'Failed to confirm COD order');
        return;
      }

      toast.success(data.message || 'COD confirmed');
      if (data.order) {
        setOrder(data.order);
      } else {
        fetchOrderDetails();
      }
    } catch (err) {
      console.error('Error confirming COD:', err);
      toast.error('Failed to confirm COD order');
    } finally {
      setConfirmingCod(false);
    }
  };

  if (loading) {
    return (
      <div className="order-confirmation-page">
        <div className="loading">Loading order details...</div>
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="order-confirmation-page">
        <div className="error-container">
          <div className="error-icon">✕</div>
          <h2>Order Not Found</h2>
          <p>{error || 'Unable to load order details'}</p>
          <Link to="/products" className="btn-primary">
            Continue Shopping
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="order-confirmation-page">
      <div className="confirmation-container">
        {/* Success Header */}
        <div className="success-header">
          <div className="success-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
              <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
          </div>
          <h1 className="success-title">Order Placed Successfully!</h1>
          <p className="success-subtitle">
            Thank you for your purchase. Your order has been confirmed.
          </p>
        </div>

        {/* M-Pesa Payment Status (if M-Pesa payment) */}
        {paymentMethod === 'mpesa' && (
          <div className={`mpesa-status-section ${paymentStatus?.status === 'completed' ? 'completed' : 'pending'}`}>
            <div className="mpesa-status-header">
              <svg className="mpesa-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
              </svg>
              <h3>M-Pesa Payment Status</h3>
            </div>

            {paymentStatus?.status === 'completed' ? (
              <div className="mpesa-success">
                <div className="mpesa-success-icon">✓</div>
                <p className="mpesa-success-text">
                  <strong>Payment Completed</strong><br />
                  Your M-Pesa payment has been processed successfully.
                </p>
              </div>
            ) : (
              <div className="mpesa-pending">
                {mpesaData?.success ? (
                  <>
                    <div className="mpesa-loading-icon">
                      <div className="spinner"></div>
                    </div>
                    <div className="mpesa-pending-text">
                      <strong>Awaiting Payment</strong>
                      <p>A payment request has been sent to your phone. Please:</p>
                      <ol>
                        <li>Check your phone for the M-Pesa STK Push prompt</li>
                        <li>Enter your M-Pesa PIN to complete payment</li>
                        <li>Wait for confirmation (this page will update automatically)</li>
                      </ol>
                      {mpesaData.CheckoutRequestID && (
                        <p className="checkout-request-id">
                          <small>Reference: {mpesaData.CheckoutRequestID}</small>
                        </p>
                      )}
                      {checkingPayment && (
                        <p className="checking-status">
                          <small>⟳ Checking payment status...</small>
                        </p>
                      )}
                    </div>
                  </>
                ) : (
                  <div className="mpesa-warning">
                    <p><strong>Payment Pending</strong></p>
                    <p>M-Pesa payment initiation may have failed. Please contact support or try placing a new order.</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Order Number */}
        <div className="order-number-section">
          <div className="order-number-label">Order Number</div>
          <div className="order-number">{order.order_number}</div>
          <div className="order-date">
            Placed on {new Date(order.created_at).toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </div>
        </div>

        {order.payment_method === 'cod' && (
          <div className="email-notice">
            <svg className="email-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
              <path d="M9 12l2 2 4-4"></path>
            </svg>
            <div className="email-notice-text">
              <strong>Cash on Delivery confirmation required</strong>
              <p>
                Please confirm your COD order to reserve your items.
                {order.cod_confirmation_expires_at && (
                  <> Confirmation expires on {new Date(order.cod_confirmation_expires_at).toLocaleString()}.</>
                )}
              </p>
              {!order.cod_confirmed_at ? (
                <button
                  type="button"
                  className="btn-primary"
                  onClick={handleConfirmCod}
                  disabled={confirmingCod}
                  style={{ marginTop: '8px' }}
                >
                  {confirmingCod ? 'Confirming...' : 'Confirm COD Order'}
                </button>
              ) : (
                <p style={{ marginTop: '8px' }}>
                  COD confirmed on {new Date(order.cod_confirmed_at).toLocaleString()}.
                </p>
              )}
            </div>
          </div>
        )}

        {/* Email Confirmation Notice */}
        <div className="email-notice">
          <svg className="email-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
            <polyline points="22,6 12,13 2,6"></polyline>
          </svg>
          <div className="email-notice-text">
            <strong>Confirmation email sent</strong>
            <p>We've sent a confirmation email to your registered email address with your order details.</p>
          </div>
        </div>

        <div className="confirmation-grid">
          {/* Left Column - Order Details */}
          <div className="order-details-section">
            {/* Order Items */}
            <div className="detail-card">
              <h2 className="card-title">Order Items</h2>
              <div className="order-items">
                {order.items && order.items.map((item) => (
                  <div key={item.id} className="order-item">
                    <img
                      src={item.product?.image_url}
                      alt={item.product?.name}
                      className="order-item-image"
                    />
                    <div className="order-item-details">
                      <h4 className="order-item-name">{item.product?.name}</h4>
                      <p className="order-item-variant">
                        Size: {item.variant?.size} | Color: {item.variant?.color}
                      </p>
                      <p className="order-item-quantity">Quantity: {item.quantity}</p>
                    </div>
                    <div className="order-item-price">
                      {helpers.formatPrice(item.total_price)}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Shipping Address */}
            <div className="detail-card">
              <h2 className="card-title">Shipping Address</h2>
              <div className="address-content">
                {order.shipping_address && (
                  <>
                    <p>{order.shipping_address.street}</p>
                    <p>
                      {order.shipping_address.city}, {order.shipping_address.state} {order.shipping_address.zip}
                    </p>
                    <p>Phone: {order.shipping_address.phone}</p>
                  </>
                )}
              </div>
            </div>

            {/* Next Steps */}
            <div className="detail-card next-steps-card">
              <h2 className="card-title">What's Next?</h2>
              <div className="next-steps">
                <div className="next-step">
                  <div className="step-number">1</div>
                  <div className="step-content">
                    <h4>Order Processing</h4>
                    <p>We're preparing your items for shipment. You'll receive an update once your order is dispatched.</p>
                  </div>
                </div>
                <div className="next-step">
                  <div className="step-number">2</div>
                  <div className="step-content">
                    <h4>Shipping</h4>
                    <p>
                      {order.is_nairobi
                        ? 'Free shipping within Nairobi. Delivery within 2-3 business days.'
                        : 'Shipping to upcountry. Delivery within 5-7 business days.'}
                    </p>
                  </div>
                </div>
                <div className="next-step">
                  <div className="step-number">3</div>
                  <div className="step-content">
                    <h4>Delivery</h4>
                    <p>Track your order status in your order history. We'll notify you upon delivery.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column - Order Summary */}
          <div className="order-summary-section">
            <div className="summary-sticky">
              <div className="detail-card">
                <h2 className="card-title">Order Summary</h2>

                <div className="summary-row">
                  <span>Subtotal</span>
                  <span>{helpers.formatPrice(order.subtotal)}</span>
                </div>

                <div className="summary-row">
                  <span>Shipping</span>
                  <span>
                    {order.is_nairobi ? (
                      <span className="free-badge">FREE</span>
                    ) : (
                      helpers.formatPrice(order.shipping_cost)
                    )}
                  </span>
                </div>

                <div className="summary-row">
                  <span>Tax</span>
                  <span>{helpers.formatPrice(order.tax || 0)}</span>
                </div>

                <div className="summary-divider"></div>

                <div className="summary-row summary-total">
                  <span>Total</span>
                  <span className="total-amount">{helpers.formatPrice(order.total)}</span>
                </div>

                <div className="status-badge">
                  <span className={`badge badge-${order.status || 'pending'}`}>
                    {order.status ? (order.status.charAt(0).toUpperCase() + order.status.slice(1)) : 'Pending'}
                  </span>
                </div>
              </div>

              {/* Actions */}
              <div className="confirmation-actions">
                <Link to="/orders" className="btn-view-orders">
                  View Order History
                </Link>
                <Link to="/products" className="btn-continue-shopping">
                  Continue Shopping
                </Link>
              </div>

              {/* Return Policy Notice */}
              <div className="policy-notice">
                <svg className="info-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="16" x2="12" y2="12"></line>
                  <line x1="12" y1="8" x2="12.01" y2="8"></line>
                </svg>
                <div className="policy-text">
                  <strong>Return Policy</strong>
                  <p>
                    Non-clearance items can be returned within 2 days of delivery.
                    A 10% restocking fee applies. FINAL SALE items cannot be returned.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrderConfirmation;

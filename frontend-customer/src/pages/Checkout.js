import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import { helpers } from '../services/api';
import toast from '../utils/toast';
import '../styles/Checkout.css';

const Checkout = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { cart, loading: cartLoading, clearCart } = useCart();
  const [submitting, setSubmitting] = useState(false);
  const [shippingPreview, setShippingPreview] = useState(null);
  const [loadingShipping, setLoadingShipping] = useState(false);
  const [sameAsBilling, setSameAsBilling] = useState(true);

  // Redirect if not logged in or cart is empty
  useEffect(() => {
    if (!user) {
      toast.warning('Please log in to checkout');
      navigate('/login');
      return;
    }

    if (!cartLoading && (!cart || !cart.items || cart.items.length === 0)) {
      toast.info('Your cart is empty');
      navigate('/cart');
    }
  }, [user, cart, cartLoading, navigate]);

  // Form validation schema
  const validationSchema = Yup.object({
    // Shipping address
    shipping_street: Yup.string()
      .required('Street address is required')
      .min(5, 'Street address must be at least 5 characters'),
    shipping_city: Yup.string()
      .required('City is required')
      .min(2, 'City must be at least 2 characters'),
    shipping_state: Yup.string()
      .required('State/County is required'),
    shipping_zip: Yup.string()
      .required('Postal code is required'),
    shipping_phone: Yup.string()
      .required('Phone number is required')
      .matches(/^(\+254|0)[17]\d{8}$/, 'Invalid Kenyan phone number'),

    // Billing address (only if different)
    billing_street: Yup.string().when('sameAsBilling', {
      is: false,
      then: (schema) => schema.required('Billing street is required').min(5, 'Must be at least 5 characters'),
    }),
    billing_city: Yup.string().when('sameAsBilling', {
      is: false,
      then: (schema) => schema.required('Billing city is required'),
    }),
    billing_state: Yup.string().when('sameAsBilling', {
      is: false,
      then: (schema) => schema.required('Billing state is required'),
    }),
    billing_zip: Yup.string().when('sameAsBilling', {
      is: false,
      then: (schema) => schema.required('Billing postal code is required'),
    }),
    billing_phone: Yup.string().when('sameAsBilling', {
      is: false,
      then: (schema) => schema.required('Billing phone is required')
        .matches(/^(\+254|0)[17]\d{8}$/, 'Invalid Kenyan phone number'),
    }),

    // M-Pesa phone (only if M-Pesa selected)
    mpesa_phone: Yup.string().when('payment_method', {
      is: 'mpesa',
      then: (schema) => schema
        .required('M-Pesa phone number is required')
        .matches(/^(\+?254|0)[17]\d{8}$/, 'Invalid Kenyan phone number (e.g., 254712345678)'),
    }),

    // Policy acceptance
    accept_terms: Yup.boolean()
      .oneOf([true], 'You must accept the Terms of Service to continue'),
    accept_privacy: Yup.boolean()
      .oneOf([true], 'You must accept the Privacy Policy to continue'),
  });

  // Formik form
  const formik = useFormik({
    initialValues: {
      shipping_street: '',
      shipping_city: '',
      shipping_state: '',
      shipping_zip: '',
      shipping_phone: '',
      billing_street: '',
      billing_city: '',
      billing_state: '',
      billing_zip: '',
      billing_phone: '',
      sameAsBilling: true,
      payment_method: 'cod', // Default to Cash on Delivery
      mpesa_phone: '', // M-Pesa phone number
      accept_terms: false,
      accept_privacy: false,
    },
    validationSchema,
    onSubmit: async (values) => {
      await handlePlaceOrder(values);
    },
  });

  // Preview shipping cost when city changes
  useEffect(() => {
    const previewShipping = async () => {
      if (!formik.values.shipping_city || !cart) return;

      setLoadingShipping(true);
      try {
        const response = await fetch('http://localhost:5001/api/orders/shipping-preview', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
          body: JSON.stringify({
            city: formik.values.shipping_city,
          }),
        });

        if (response.ok) {
          const data = await response.json();
          setShippingPreview(data);
        }
      } catch (error) {
        console.error('Shipping preview error:', error);
      } finally {
        setLoadingShipping(false);
      }
    };

    const debounceTimer = setTimeout(previewShipping, 500);
    return () => clearTimeout(debounceTimer);
  }, [formik.values.shipping_city, cart]);

  const handlePlaceOrder = async (values) => {
    setSubmitting(true);

    try {
      // Prepare shipping address
      const shippingAddress = {
        street: values.shipping_street,
        city: values.shipping_city,
        state: values.shipping_state,
        zip: values.shipping_zip,
        phone: values.shipping_phone,
      };

      // Prepare billing address
      const billingAddress = sameAsBilling ? null : {
        street: values.billing_street,
        city: values.billing_city,
        state: values.billing_state,
        zip: values.billing_zip,
        phone: values.billing_phone,
      };

      // Prepare order payload
      const orderPayload = {
        shipping_address: shippingAddress,
        billing_address: billingAddress,
        payment_method: values.payment_method || 'cod',
      };

      // Add M-Pesa phone if M-Pesa payment selected
      if (values.payment_method === 'mpesa' && values.mpesa_phone) {
        orderPayload.mpesa_phone = values.mpesa_phone;
      }

      // Create order
      const response = await fetch('http://localhost:5001/api/orders', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(orderPayload),
      });

      const data = await response.json();

      if (response.ok) {
        // Check if M-Pesa STK Push was initiated
        if (data.mpesa && data.mpesa.success) {
          toast.success('Order created! Please check your phone for M-Pesa payment prompt.');
        } else if (values.payment_method === 'cod') {
          toast.success('Order placed successfully!');
        } else {
          toast.success('Order created!');
        }

        // Clear cart
        await clearCart();

        // Navigate to order confirmation (pass M-Pesa data if available)
        navigate(`/order-confirmation/${data.order.id}`, {
          state: {
            order: data.order,
            mpesa: data.mpesa,
            paymentMethod: values.payment_method
          }
        });
      } else {
        console.error('Order creation failed:', data);
        const errorMsg = data.error || data.message || 'Failed to create order';
        toast.error(`Order failed: ${errorMsg}`);
      }
    } catch (error) {
      console.error('Order creation error:', error);
      toast.error('Failed to place order. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (cartLoading) {
    return <div className="loading">Loading checkout...</div>;
  }

  if (!cart || !cart.items || cart.items.length === 0) {
    return null; // Will redirect
  }

  const subtotal = cart.subtotal || 0;
  const shippingCost = shippingPreview?.shipping_cost || 0;

  // Calculate VAT (16%) - prices are VAT-inclusive
  // To extract VAT from inclusive price: VAT = (price * 16) / 116
  const taxRate = 0.16;
  const subtotalBeforeVAT = subtotal / (1 + taxRate);
  const tax = subtotal - subtotalBeforeVAT;

  const total = subtotal + shippingCost;

  return (
    <div className="checkout-page">
      <div className="checkout-container">
        <h1 className="checkout-title">Checkout</h1>

        <div className="checkout-grid">
          {/* Left Column - Forms */}
          <div className="checkout-forms">
            <form onSubmit={formik.handleSubmit}>
              {/* Shipping Address */}
              <div className="checkout-section">
                <h2 className="section-title">Shipping Address</h2>

                <div className="form-group">
                  <label htmlFor="shipping_street">Street Address *</label>
                  <input
                    type="text"
                    id="shipping_street"
                    name="shipping_street"
                    placeholder="123 Main Street, Apt 4B"
                    value={formik.values.shipping_street}
                    onChange={formik.handleChange}
                    onBlur={formik.handleBlur}
                    className={formik.touched.shipping_street && formik.errors.shipping_street ? 'error' : ''}
                  />
                  {formik.touched.shipping_street && formik.errors.shipping_street && (
                    <span className="error-message">{formik.errors.shipping_street}</span>
                  )}
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="shipping_city">City *</label>
                    <input
                      type="text"
                      id="shipping_city"
                      name="shipping_city"
                      placeholder="Nairobi"
                      value={formik.values.shipping_city}
                      onChange={formik.handleChange}
                      onBlur={formik.handleBlur}
                      className={formik.touched.shipping_city && formik.errors.shipping_city ? 'error' : ''}
                    />
                    {formik.touched.shipping_city && formik.errors.shipping_city && (
                      <span className="error-message">{formik.errors.shipping_city}</span>
                    )}
                  </div>

                  <div className="form-group">
                    <label htmlFor="shipping_state">State/County *</label>
                    <input
                      type="text"
                      id="shipping_state"
                      name="shipping_state"
                      placeholder="Nairobi County"
                      value={formik.values.shipping_state}
                      onChange={formik.handleChange}
                      onBlur={formik.handleBlur}
                      className={formik.touched.shipping_state && formik.errors.shipping_state ? 'error' : ''}
                    />
                    {formik.touched.shipping_state && formik.errors.shipping_state && (
                      <span className="error-message">{formik.errors.shipping_state}</span>
                    )}
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="shipping_zip">Postal Code *</label>
                    <input
                      type="text"
                      id="shipping_zip"
                      name="shipping_zip"
                      placeholder="00100"
                      value={formik.values.shipping_zip}
                      onChange={formik.handleChange}
                      onBlur={formik.handleBlur}
                      className={formik.touched.shipping_zip && formik.errors.shipping_zip ? 'error' : ''}
                    />
                    {formik.touched.shipping_zip && formik.errors.shipping_zip && (
                      <span className="error-message">{formik.errors.shipping_zip}</span>
                    )}
                  </div>

                  <div className="form-group">
                    <label htmlFor="shipping_phone">Phone Number *</label>
                    <input
                      type="tel"
                      id="shipping_phone"
                      name="shipping_phone"
                      placeholder="+254712345678"
                      value={formik.values.shipping_phone}
                      onChange={formik.handleChange}
                      onBlur={formik.handleBlur}
                      className={formik.touched.shipping_phone && formik.errors.shipping_phone ? 'error' : ''}
                    />
                    {formik.touched.shipping_phone && formik.errors.shipping_phone && (
                      <span className="error-message">{formik.errors.shipping_phone}</span>
                    )}
                  </div>
                </div>

                {/* Shipping preview */}
                {shippingPreview && (
                  <div className="shipping-preview">
                    {loadingShipping ? (
                      <span className="loading-text">Calculating shipping...</span>
                    ) : (
                      <span className={`shipping-info ${shippingPreview.is_nairobi ? 'free' : 'paid'}`}>
                        {shippingPreview.description}
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Billing Address */}
              <div className="checkout-section">
                <div className="section-header">
                  <h2 className="section-title">Billing Address</h2>
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={sameAsBilling}
                      onChange={(e) => {
                        setSameAsBilling(e.target.checked);
                        formik.setFieldValue('sameAsBilling', e.target.checked);
                      }}
                    />
                    <span>Same as shipping address</span>
                  </label>
                </div>

                {!sameAsBilling && (
                  <div className="billing-fields">
                    <div className="form-group">
                      <label htmlFor="billing_street">Street Address *</label>
                      <input
                        type="text"
                        id="billing_street"
                        name="billing_street"
                        placeholder="123 Main Street, Apt 4B"
                        value={formik.values.billing_street}
                        onChange={formik.handleChange}
                        onBlur={formik.handleBlur}
                        className={formik.touched.billing_street && formik.errors.billing_street ? 'error' : ''}
                      />
                      {formik.touched.billing_street && formik.errors.billing_street && (
                        <span className="error-message">{formik.errors.billing_street}</span>
                      )}
                    </div>

                    <div className="form-row">
                      <div className="form-group">
                        <label htmlFor="billing_city">City *</label>
                        <input
                          type="text"
                          id="billing_city"
                          name="billing_city"
                          placeholder="Nairobi"
                          value={formik.values.billing_city}
                          onChange={formik.handleChange}
                          onBlur={formik.handleBlur}
                          className={formik.touched.billing_city && formik.errors.billing_city ? 'error' : ''}
                        />
                        {formik.touched.billing_city && formik.errors.billing_city && (
                          <span className="error-message">{formik.errors.billing_city}</span>
                        )}
                      </div>

                      <div className="form-group">
                        <label htmlFor="billing_state">State/County *</label>
                        <input
                          type="text"
                          id="billing_state"
                          name="billing_state"
                          placeholder="Nairobi County"
                          value={formik.values.billing_state}
                          onChange={formik.handleChange}
                          onBlur={formik.handleBlur}
                          className={formik.touched.billing_state && formik.errors.billing_state ? 'error' : ''}
                        />
                        {formik.touched.billing_state && formik.errors.billing_state && (
                          <span className="error-message">{formik.errors.billing_state}</span>
                        )}
                      </div>
                    </div>

                    <div className="form-row">
                      <div className="form-group">
                        <label htmlFor="billing_zip">Postal Code *</label>
                        <input
                          type="text"
                          id="billing_zip"
                          name="billing_zip"
                          placeholder="00100"
                          value={formik.values.billing_zip}
                          onChange={formik.handleChange}
                          onBlur={formik.handleBlur}
                          className={formik.touched.billing_zip && formik.errors.billing_zip ? 'error' : ''}
                        />
                        {formik.touched.billing_zip && formik.errors.billing_zip && (
                          <span className="error-message">{formik.errors.billing_zip}</span>
                        )}
                      </div>

                      <div className="form-group">
                        <label htmlFor="billing_phone">Phone Number *</label>
                        <input
                          type="tel"
                          id="billing_phone"
                          name="billing_phone"
                          placeholder="+254712345678"
                          value={formik.values.billing_phone}
                          onChange={formik.handleChange}
                          onBlur={formik.handleBlur}
                          className={formik.touched.billing_phone && formik.errors.billing_phone ? 'error' : ''}
                        />
                        {formik.touched.billing_phone && formik.errors.billing_phone && (
                          <span className="error-message">{formik.errors.billing_phone}</span>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Payment Method */}
              <div className="checkout-section">
                <h2 className="section-title">Payment Method</h2>

                <div className="payment-methods">
                  <label className="payment-method-option">
                    <input
                      type="radio"
                      name="payment_method"
                      value="cod"
                      checked={formik.values.payment_method === 'cod'}
                      onChange={formik.handleChange}
                    />
                    <div className="payment-method-content">
                      <span className="payment-method-title">Cash on Delivery</span>
                      <span className="payment-method-description">Pay with cash when your order is delivered</span>
                    </div>
                  </label>

                  <label className="payment-method-option">
                    <input
                      type="radio"
                      name="payment_method"
                      value="mpesa"
                      checked={formik.values.payment_method === 'mpesa'}
                      onChange={formik.handleChange}
                    />
                    <div className="payment-method-content">
                      <span className="payment-method-title">M-Pesa</span>
                      <span className="payment-method-description">Pay via M-Pesa mobile money (instant STK Push)</span>
                    </div>
                  </label>
                </div>

                {/* M-Pesa Phone Number (conditional) */}
                {formik.values.payment_method === 'mpesa' && (
                  <div className="mpesa-phone-section">
                    <div className="form-group">
                      <label htmlFor="mpesa_phone">M-Pesa Phone Number *</label>
                      <input
                        type="tel"
                        id="mpesa_phone"
                        name="mpesa_phone"
                        placeholder="254712345678 or 0712345678"
                        value={formik.values.mpesa_phone}
                        onChange={formik.handleChange}
                        onBlur={formik.handleBlur}
                        className={formik.touched.mpesa_phone && formik.errors.mpesa_phone ? 'error' : ''}
                      />
                      {formik.touched.mpesa_phone && formik.errors.mpesa_phone && (
                        <span className="error-message">{formik.errors.mpesa_phone}</span>
                      )}
                      <span className="help-text">Enter the phone number registered with M-Pesa (Safaricom)</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Policy Acceptance */}
              <div className="checkout-section">
                <h2 className="section-title">Terms & Policies</h2>

                <div className="policy-checkboxes">
                  <label className={`policy-checkbox-label ${formik.touched.accept_terms && formik.errors.accept_terms ? 'error' : ''}`}>
                    <input
                      type="checkbox"
                      name="accept_terms"
                      checked={formik.values.accept_terms}
                      onChange={formik.handleChange}
                      onBlur={formik.handleBlur}
                    />
                    <span className="policy-text">
                      I have read and agree to the{' '}
                      <a href="/terms-of-service" target="_blank" rel="noopener noreferrer" className="policy-link">
                        Terms of Service
                      </a>
                    </span>
                  </label>
                  {formik.touched.accept_terms && formik.errors.accept_terms && (
                    <span className="error-message">{formik.errors.accept_terms}</span>
                  )}

                  <label className={`policy-checkbox-label ${formik.touched.accept_privacy && formik.errors.accept_privacy ? 'error' : ''}`}>
                    <input
                      type="checkbox"
                      name="accept_privacy"
                      checked={formik.values.accept_privacy}
                      onChange={formik.handleChange}
                      onBlur={formik.handleBlur}
                    />
                    <span className="policy-text">
                      I have read and agree to the{' '}
                      <a href="/privacy-policy" target="_blank" rel="noopener noreferrer" className="policy-link">
                        Privacy Policy
                      </a>
                    </span>
                  </label>
                  {formik.touched.accept_privacy && formik.errors.accept_privacy && (
                    <span className="error-message">{formik.errors.accept_privacy}</span>
                  )}

                  <div className="policy-info-box">
                    <p className="policy-info-text">
                      By placing this order, you also acknowledge our{' '}
                      <a href="/return-policy" target="_blank" rel="noopener noreferrer" className="policy-link">
                        Return & Refund Policy
                      </a>
                      . Please review it carefully before completing your purchase.
                    </p>
                  </div>
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                className="btn-place-order"
                disabled={submitting || !formik.isValid}
              >
                {submitting ? 'Placing Order...' : 'Place Order'}
              </button>
            </form>
          </div>

          {/* Right Column - Order Summary */}
          <div className="order-summary-sidebar">
            <div className="order-summary-sticky">
              <h2 className="summary-title">Order Summary</h2>

              {/* Cart Items */}
              <div className="summary-items">
                {cart.items.map((item) => (
                  <div key={item.id} className="summary-item">
                    <img
                      src={item.variant?.product?.primary_image?.image_url || item.variant?.product?.image_url}
                      alt={item.variant?.product?.name}
                      className="summary-item-image"
                    />
                    <div className="summary-item-details">
                      <h4 className="summary-item-name">{item.variant?.product?.name}</h4>
                      <p className="summary-item-variant">
                        {item.variant?.size} / {item.variant?.color}
                      </p>
                      <p className="summary-item-quantity">Qty: {item.quantity}</p>
                    </div>
                    <div className="summary-item-price">
                      {helpers.formatPrice(
                        (item.variant?.product?.sale_price || item.variant?.product?.price) * item.quantity
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Price Breakdown */}
              <div className="summary-totals">
                <div className="summary-row">
                  <span>Subtotal</span>
                  <span>{helpers.formatPrice(subtotal)}</span>
                </div>
                <div className="summary-row">
                  <span>Shipping</span>
                  <span>
                    {loadingShipping ? (
                      'Calculating...'
                    ) : shippingPreview ? (
                      shippingPreview.is_nairobi ? (
                        'FREE'
                      ) : (
                        helpers.formatPrice(shippingCost)
                      )
                    ) : (
                      'Enter city'
                    )}
                  </span>
                </div>
                <div className="summary-row">
                  <span>VAT (16% included)</span>
                  <span>{helpers.formatPrice(tax)}</span>
                </div>
                <div className="summary-row summary-total">
                  <span>Total</span>
                  <span className="total-amount">{helpers.formatPrice(total)}</span>
                </div>
              </div>

              {/* Security Notice */}
              <div className="security-notice">
                <svg className="security-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                </svg>
                <span>Your information is secure and encrypted</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Checkout;

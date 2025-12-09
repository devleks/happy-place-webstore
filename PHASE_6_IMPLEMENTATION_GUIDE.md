# Phase 6: Checkout & M-Pesa Payment - Implementation Guide

**Version:** 1.0  
**Date:** 2025-11-25  
**Status:** In Progress (Database Layer Complete)

---

## Table of Contents
1. [Overview](#overview)
2. [Completed Work](#completed-work)
3. [Backend Implementation](#backend-implementation)
4. [Frontend Implementation](#frontend-implementation)
5. [M-Pesa Integration](#m-pesa-integration)
6. [Testing Guide](#testing-guide)
7. [Security Checklist](#security-checklist)

---

## Overview

### Objectives
- ✅ Secure order creation with stored procedures
- ✅ Privacy by design (data minimization, encryption)
- ✅ Server-side validation (never trust client)
- ⏸️ M-Pesa STK Push integration (next iteration)
- ✅ Complete audit trail
- ✅ Atomic transactions with rollback

### Architecture Decisions
- **Database First:** Critical operations in stored procedures
- **Security First:** All calculations server-side
- **Iterative Approach:** MVP checkout first, payment later
- **Audit Everything:** Complete compliance logging

---

## Completed Work

### ✅ Database Layer (Complete)

**Stored Procedures Created:**

1. `generate_order_number()` - Order number generation
2. `deduct_inventory_atomic()` - Inventory management with locking
3. `create_order_secure()` - Complete order creation
4. `process_payment_secure()` - Payment initiation
5. `complete_payment()` - Payment completion

**Audit Tables Created:**

1. `order_audit_log` - Order lifecycle tracking
2. `payment_callback_log` - M-Pesa callback logging

**Security Features:**

- Row-level locking (SELECT FOR UPDATE)
- Atomic transactions
- Server-side price recalculation
- Automatic audit logging
- Idempotency checks

---

## Backend Implementation

### 1. Order Model Serialization

**File:** `backend/models/database_models.py`

Add to `Order` model:
```python
def to_dict(self, include_items=True, include_customer=False):
    """Serialize order for API response"""
    from services.encryption_service import address_encryption
    
    # Decrypt shipping address
    try:
        shipping_address = json.loads(
            address_encryption.decrypt(self.shipping_address_encrypted)
        )
    except:
        shipping_address = None
    
    data = {
        'id': self.id,
        'order_number': self.order_number,
        'status': self.status,
        'subtotal': float(self.subtotal),
        'tax': float(self.tax) if self.tax else 0,
        'shipping_cost': float(self.shipping_cost) if self.shipping_cost else 0,
        'total': float(self.total),
        'is_nairobi': self.is_nairobi,
        'shipping_address': shipping_address,  # Decrypted for customer
        'created_at': self.created_at.isoformat() if self.created_at else None,
        'updated_at': self.updated_at.isoformat() if self.updated_at else None,
    }
    
    if include_items and self.items:
        data['items'] = [item.to_dict() for item in self.items]
        data['items_count'] = len(self.items)
    
    if include_customer and self.customer:
        data['customer'] = {
            'id': self.customer.id,
            'email': self.customer.email
        }
    
    return data
```

Add to `OrderItem` model:
```python
def to_dict(self):
    """Serialize order item"""
    return {
        'id': self.id,
        'product_id': self.product_id,
        'variant_id': self.variant_id,
        'quantity': self.quantity,
        'price_at_purchase': float(self.price_at_purchase),
        'product': {
            'id': self.product.id,
            'name': self.product.name,
            'slug': self.product.slug,
            'image_url': self.product.primary_image.image_url if self.product.primary_image else None
        } if self.product else None,
        'variant': {
            'sku': self.variant.sku,
            'size': self.variant.size,
            'color': self.variant.color
        } if self.variant else None
    }
```

Add to `Payment` model:
```python
def to_dict(self):
    """Serialize payment (minimal exposure)"""
    return {
        'id': self.id,
        'order_id': self.order_id,
        'amount': float(self.amount),
        'payment_method': self.payment_method,
        'status': self.status,
        'created_at': self.created_at.isoformat() if self.created_at else None,
        'completed_at': self.completed_at.isoformat() if self.completed_at else None
    }
```

---

### 2. Shipping Calculation Service

**File:** `backend/services/shipping_service.py`

```python
"""
Shipping calculation service for Happy Place Boutique.
Calculates shipping costs based on location and weight.
"""

class ShippingService:
    """Service for calculating shipping costs"""
    
    # Nairobi regions (case-insensitive matching)
    NAIROBI_REGIONS = [
        'nairobi', 'nai', 'karen', 'westlands', 'kilimani',
        'lavington', 'upperhill', 'kileleshwa', 'parklands'
    ]
    
    # Shipping costs
    NAIROBI_COST = 0  # Free shipping in Nairobi
    UPCOUNTRY_BASE_COST = 300  # KSh 300 base
    UPCOUNTRY_COST_PER_KG = 50  # KSh 50 per kg
    
    @classmethod
    def is_nairobi(cls, city: str) -> bool:
        """Check if city is in Nairobi"""
        if not city:
            return False
        
        city_lower = city.lower().strip()
        return any(region in city_lower for region in cls.NAIROBI_REGIONS)
    
    @classmethod
    def calculate_shipping(cls, city: str, total_weight_kg: float) -> dict:
        """
        Calculate shipping cost based on city and weight.
        
        Args:
            city: Delivery city
            total_weight_kg: Total weight in kilograms
        
        Returns:
            {
                'cost': float,
                'is_nairobi': bool,
                'method': str,
                'description': str
            }
        """
        is_nairobi = cls.is_nairobi(city)
        
        if is_nairobi:
            return {
                'cost': cls.NAIROBI_COST,
                'is_nairobi': True,
                'method': 'Nairobi Delivery',
                'description': 'Free delivery within Nairobi'
            }
        else:
            # Upcountry: KSh 300 + (KSh 50 × weight)
            cost = cls.UPCOUNTRY_BASE_COST + (cls.UPCOUNTRY_COST_PER_KG * total_weight_kg)
            return {
                'cost': round(cost, 2),
                'is_nairobi': False,
                'method': 'Upcountry Delivery',
                'description': f'KSh {cls.UPCOUNTRY_BASE_COST} + KSh {cls.UPCOUNTRY_COST_PER_KG}/kg (Total: {total_weight_kg}kg)'
            }
    
    @classmethod
    def get_cart_weight(cls, cart_items: list) -> float:
        """
        Calculate total weight from cart items.
        
        Args:
            cart_items: List of cart items with variant info
        
        Returns:
            Total weight in kilograms
        """
        total_weight = 0.0
        
        for item in cart_items:
            variant = item.get('variant')
            if variant and 'product' in variant:
                product = variant['product']
                weight = product.get('weight', 0.2)  # Default 0.2kg if not specified
                quantity = item.get('quantity', 1)
                total_weight += (weight * quantity)
        
        return round(total_weight, 2)
```

---

### 3. Order Service (Business Logic)

**File:** `backend/services/order_service.py`

```python
"""
Order service for Happy Place Boutique.
Handles order creation, retrieval, and management.
"""

import json
from flask import request
from models import db, Order, Cart, CartItem
from services.encryption_service import address_encryption
from services.shipping_service import ShippingService

class OrderService:
    """Service for managing orders"""
    
    @staticmethod
    def create_order(customer_id: int, shipping_data: dict) -> dict:
        """
        Create order from cart using stored procedure.
        
        Args:
            customer_id: Customer ID
            shipping_data: {
                'full_name': str,
                'phone': str,
                'address_line1': str,
                'address_line2': str (optional),
                'city': str,
                'county': str,
                'postal_code': str (optional)
            }
        
        Returns:
            {
                'success': bool,
                'order_id': int,
                'order_number': str,
                'error': str (if failed)
            }
        """
        try:
            # 1. Get customer's cart
            cart = Cart.query.filter_by(customer_id=customer_id).first()
            if not cart or not cart.items:
                return {'success': False, 'error': 'Cart is empty'}
            
            # 2. Prepare cart items for stored procedure
            cart_items_json = []
            total_weight = 0.0
            subtotal = 0.0
            
            for cart_item in cart.items:
                variant = cart_item.variant
                if not variant or not variant.product:
                    continue
                
                product = variant.product
                price = float(product.sale_price if product.sale_price else product.price)
                weight = float(product.weight) if product.weight else 0.2
                
                cart_items_json.append({
                    'variant_id': variant.id,
                    'quantity': cart_item.quantity
                })
                
                subtotal += (price * cart_item.quantity)
                total_weight += (weight * cart_item.quantity)
            
            # 3. Calculate shipping
            shipping = ShippingService.calculate_shipping(
                shipping_data['city'],
                total_weight
            )
            shipping_cost = shipping['cost']
            is_nairobi = shipping['is_nairobi']
            
            # 4. Calculate totals
            tax = 0  # No tax for now
            total = subtotal + shipping_cost + tax
            
            # 5. Encrypt shipping address
            shipping_address_json = json.dumps({
                'full_name': shipping_data['full_name'],
                'phone': shipping_data['phone'],
                'address_line1': shipping_data['address_line1'],
                'address_line2': shipping_data.get('address_line2', ''),
                'city': shipping_data['city'],
                'county': shipping_data['county'],
                'postal_code': shipping_data.get('postal_code', '')
            })
            shipping_address_encrypted = address_encryption.encrypt(shipping_address_json)
            
            # 6. Get request metadata
            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent', '')[:255]
            
            # 7. Call stored procedure
            result = db.session.execute(
                """
                SELECT * FROM create_order_secure(
                    :customer_id,
                    :shipping_address_encrypted,
                    :billing_address_encrypted,
                    :shipping_method_id,
                    :is_nairobi,
                    :subtotal,
                    :shipping_cost,
                    :tax,
                    :total,
                    :cart_items,
                    :ip_address,
                    :user_agent
                )
                """,
                {
                    'customer_id': customer_id,
                    'shipping_address_encrypted': shipping_address_encrypted,
                    'billing_address_encrypted': None,  # Same as shipping for now
                    'shipping_method_id': None,  # Will add shipping methods later
                    'is_nairobi': is_nairobi,
                    'subtotal': subtotal,
                    'shipping_cost': shipping_cost,
                    'tax': tax,
                    'total': total,
                    'cart_items': json.dumps(cart_items_json),
                    'ip_address': ip_address,
                    'user_agent': user_agent
                }
            )
            
            order_row = result.fetchone()
            order_id = order_row[0]
            order_number = order_row[1]
            
            db.session.commit()
            
            # 8. Clear cart
            CartItem.query.filter_by(cart_id=cart.id).delete()
            db.session.commit()
            
            return {
                'success': True,
                'order_id': order_id,
                'order_number': order_number
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_order(order_id: int, customer_id: int) -> dict:
        """Get order by ID (verify ownership)"""
        order = Order.query.filter_by(
            id=order_id,
            customer_id=customer_id
        ).first()
        
        if not order:
            return {'success': False, 'error': 'Order not found'}
        
        return {
            'success': True,
            'order': order.to_dict(include_items=True)
        }
    
    @staticmethod
    def get_customer_orders(customer_id: int, page: int = 1, per_page: int = 10):
        """Get customer's orders with pagination"""
        orders = Order.query.filter_by(customer_id=customer_id)\
            .order_by(Order.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'success': True,
            'orders': [order.to_dict(include_items=False) for order in orders.items],
            'pagination': {
                'page': orders.page,
                'per_page': orders.per_page,
                'total': orders.total,
                'pages': orders.pages,
                'has_next': orders.has_next,
                'has_prev': orders.has_prev
            }
        }
```

---

### 4. Order Routes

**File:** `backend/routes/orders.py`

```python
"""
Order API routes for Happy Place Boutique.

Endpoints:
- POST /api/orders - Create order from cart
- GET /api/orders - List customer orders
- GET /api/orders/<order_id> - Get order details
"""

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.order_service import OrderService
from . import api

@api.route('/orders', methods=['POST'])
@jwt_required()
def create_order():
    """
    Create order from cart.
    
    Request body:
    {
        "shipping_address": {
            "full_name": "John Doe",
            "phone": "+254712345678",
            "address_line1": "123 Main St",
            "address_line2": "Apt 4B",
            "city": "Nairobi",
            "county": "Nairobi",
            "postal_code": "00100"
        }
    }
    """
    try:
        customer_id = int(get_jwt_identity())
        data = request.get_json()
        
        if not data or 'shipping_address' not in data:
            return jsonify({'error': 'Shipping address is required'}), 400
        
        shipping_data = data['shipping_address']
        
        # Validate required fields
        required_fields = ['full_name', 'phone', 'address_line1', 'city', 'county']
        for field in required_fields:
            if field not in shipping_data or not shipping_data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create order
        result = OrderService.create_order(customer_id, shipping_data)
        
        if not result['success']:
            return jsonify({'error': result['error']}), 400
        
        return jsonify({
            'message': 'Order created successfully',
            'order_id': result['order_id'],
            'order_number': result['order_number']
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/orders', methods=['GET'])
@jwt_required()
def get_orders():
    """Get customer's orders with pagination"""
    try:
        customer_id = int(get_jwt_identity())
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        result = OrderService.get_customer_orders(customer_id, page, per_page)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/orders/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    """Get order details"""
    try:
        customer_id = int(get_jwt_identity())
        
        result = OrderService.get_order(order_id, customer_id)
        
        if not result['success']:
            return jsonify({'error': result['error']}), 404
        
        return jsonify(result['order']), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

### 5. Register Order Routes

**File:** `backend/routes/__init__.py`

Add:
```python
from .orders import *
```

---

## Frontend Implementation

### 1. Checkout Page (Basic)

**File:** `frontend/src/pages/Checkout.js`

```javascript
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import { api, helpers } from '../services/api';
import toast from '../utils/toast';
import '../styles/Checkout.css';

const Checkout = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { cart, loading: cartLoading } = useCart();
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!user) {
      toast.warning('Please log in to checkout');
      navigate('/login');
    }
    
    if (!cartLoading && (!cart || !cart.items || cart.items.length === 0)) {
      toast.info('Your cart is empty');
      navigate('/cart');
    }
  }, [user, cart, cartLoading, navigate]);

  // Formik form validation
  const formik = useFormik({
    initialValues: {
      full_name: '',
      phone: '',
      address_line1: '',
      address_line2: '',
      city: '',
      county: '',
      postal_code: ''
    },
    validationSchema: Yup.object({
      full_name: Yup.string()
        .required('Full name is required')
        .min(3, 'Name must be at least 3 characters'),
      phone: Yup.string()
        .required('Phone number is required')
        .matches(/^(\+254|0)[17]\d{8}$/, 'Invalid Kenyan phone number'),
      address_line1: Yup.string()
        .required('Address is required')
        .min(5, 'Address must be at least 5 characters'),
      city: Yup.string()
        .required('City is required'),
      county: Yup.string()
        .required('County is required')
    }),
    onSubmit: async (values) => {
      setSubmitting(true);
      
      try {
        const response = await api.post('/orders', {
          shipping_address: values
        });
        
        const { order_id, order_number } = response.data;
        
        toast.success('Order placed successfully!');
        navigate(`/orders/${order_id}/confirmation`);
        
      } catch (error) {
        toast.error(error.response?.data?.error || 'Failed to create order');
      } finally {
        setSubmitting(false);
      }
    }
  });

  if (cartLoading || !cart) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="checkout-container">
      <h1>Checkout</h1>
      
      <div className="checkout-content">
        {/* Order Summary */}
        <div className="order-summary">
          <h2>Order Summary</h2>
          <div className="summary-items">
            {cart.items.map((item) => (
              <div key={item.id} className="summary-item">
                <span>{item.variant.product.name} × {item.quantity}</span>
                <span>{helpers.formatPrice(item.variant.product.price * item.quantity)}</span>
              </div>
            ))}
          </div>
          <div className="summary-total">
            <span>Subtotal</span>
            <span>{helpers.formatPrice(cart.subtotal)}</span>
          </div>
          <div className="summary-note">
            Shipping will be calculated based on your location
          </div>
        </div>

        {/* Shipping Form */}
        <div className="shipping-form">
          <h2>Shipping Address</h2>
          <form onSubmit={formik.handleSubmit}>
            <div className="form-group">
              <label htmlFor="full_name">Full Name *</label>
              <input
                type="text"
                id="full_name"
                {...formik.getFieldProps('full_name')}
                className={formik.touched.full_name && formik.errors.full_name ? 'error' : ''}
              />
              {formik.touched.full_name && formik.errors.full_name && (
                <div className="error-message">{formik.errors.full_name}</div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="phone">Phone Number *</label>
              <input
                type="tel"
                id="phone"
                placeholder="+254712345678"
                {...formik.getFieldProps('phone')}
                className={formik.touched.phone && formik.errors.phone ? 'error' : ''}
              />
              {formik.touched.phone && formik.errors.phone && (
                <div className="error-message">{formik.errors.phone}</div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="address_line1">Address Line 1 *</label>
              <input
                type="text"
                id="address_line1"
                {...formik.getFieldProps('address_line1')}
                className={formik.touched.address_line1 && formik.errors.address_line1 ? 'error' : ''}
              />
              {formik.touched.address_line1 && formik.errors.address_line1 && (
                <div className="error-message">{formik.errors.address_line1}</div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="address_line2">Address Line 2</label>
              <input
                type="text"
                id="address_line2"
                {...formik.getFieldProps('address_line2')}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="city">City *</label>
                <input
                  type="text"
                  id="city"
                  {...formik.getFieldProps('city')}
                  className={formik.touched.city && formik.errors.city ? 'error' : ''}
                />
                {formik.touched.city && formik.errors.city && (
                  <div className="error-message">{formik.errors.city}</div>
                )}
              </div>

              <div className="form-group">
                <label htmlFor="county">County *</label>
                <input
                  type="text"
                  id="county"
                  {...formik.getFieldProps('county')}
                  className={formik.touched.county && formik.errors.county ? 'error' : ''}
                />
                {formik.touched.county && formik.errors.county && (
                  <div className="error-message">{formik.errors.county}</div>
                )}
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="postal_code">Postal Code</label>
              <input
                type="text"
                id="postal_code"
                {...formik.getFieldProps('postal_code')}
              />
            </div>

            <div className="shipping-info">
              <p><strong>Shipping Costs:</strong></p>
              <p>• Nairobi: Free</p>
              <p>• Upcountry: KSh 300 + KSh 50/kg</p>
            </div>

            <button
              type="submit"
              disabled={submitting || !formik.isValid}
              className="btn-submit"
            >
              {submitting ? 'Processing...' : 'Place Order'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Checkout;
```

---

### 2. Order Confirmation Page

**File:** `frontend/src/pages/OrderConfirmation.js`

```javascript
import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api, helpers } from '../services/api';
import { FaCheckCircle } from 'react-icons/fa';
import '../styles/OrderConfirmation.css';

const OrderConfirmation = () => {
  const { orderId } = useParams();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrder();
  }, [orderId]);

  const fetchOrder = async () => {
    try {
      const response = await api.get(`/orders/${orderId}`);
      setOrder(response.data);
    } catch (error) {
      console.error('Error fetching order:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading order details...</div>;
  }

  if (!order) {
    return (
      <div className="error-container">
        <h2>Order not found</h2>
        <Link to="/orders">View all orders</Link>
      </div>
    );
  }

  return (
    <div className="confirmation-container">
      <div className="confirmation-header">
        <FaCheckCircle className="success-icon" />
        <h1>Order Confirmed!</h1>
        <p className="order-number">Order #{order.order_number}</p>
      </div>

      <div className="confirmation-message">
        <p>Thank you for your order! We've received it and will process it shortly.</p>
        <p>You'll receive an email confirmation at your registered email address.</p>
      </div>

      <div className="order-details">
        <h2>Order Details</h2>
        
        <div className="detail-section">
          <h3>Items Ordered</h3>
          {order.items && order.items.map((item) => (
            <div key={item.id} className="order-item">
              <span>{item.product.name} ({item.variant.size}, {item.variant.color})</span>
              <span>×{item.quantity}</span>
              <span>{helpers.formatPrice(item.price_at_purchase * item.quantity)}</span>
            </div>
          ))}
        </div>

        <div className="detail-section">
          <h3>Shipping Address</h3>
          {order.shipping_address && (
            <div className="address">
              <p>{order.shipping_address.full_name}</p>
              <p>{order.shipping_address.phone}</p>
              <p>{order.shipping_address.address_line1}</p>
              {order.shipping_address.address_line2 && (
                <p>{order.shipping_address.address_line2}</p>
              )}
              <p>{order.shipping_address.city}, {order.shipping_address.county}</p>
              {order.shipping_address.postal_code && (
                <p>{order.shipping_address.postal_code}</p>
              )}
            </div>
          )}
        </div>

        <div className="detail-section">
          <h3>Order Summary</h3>
          <div className="summary-row">
            <span>Subtotal</span>
            <span>{helpers.formatPrice(order.subtotal)}</span>
          </div>
          <div className="summary-row">
            <span>Shipping</span>
            <span>{order.shipping_cost > 0 ? helpers.formatPrice(order.shipping_cost) : 'Free'}</span>
          </div>
          {order.tax > 0 && (
            <div className="summary-row">
              <span>Tax</span>
              <span>{helpers.formatPrice(order.tax)}</span>
            </div>
          )}
          <div className="summary-row total">
            <span>Total</span>
            <span>{helpers.formatPrice(order.total)}</span>
          </div>
        </div>

        <div className="next-steps">
          <h3>What's Next?</h3>
          <ul>
            <li>We'll process your order within 24 hours</li>
            <li>You'll receive an SMS when your order ships</li>
            <li>Delivery typically takes 1-3 business days</li>
            <li>Track your order status in your account</li>
          </ul>
        </div>

        <div className="action-buttons">
          <Link to="/orders" className="btn-primary">View All Orders</Link>
          <Link to="/products" className="btn-secondary">Continue Shopping</Link>
        </div>
      </div>
    </div>
  );
};

export default OrderConfirmation;
```

---

### 3. Order History Page

**File:** `frontend/src/pages/OrderHistory.js`

```javascript
import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api, helpers } from '../services/api';
import '../styles/OrderHistory.css';

const OrderHistory = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState(null);

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    fetchOrders();
  }, [user, navigate]);

  const fetchOrders = async (page = 1) => {
    try {
      const response = await api.get(`/orders?page=${page}&per_page=10`);
      setOrders(response.data.orders);
      setPagination(response.data.pagination);
    } catch (error) {
      console.error('Error fetching orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      pending: { class: 'badge-pending', text: 'Pending' },
      processing: { class: 'badge-processing', text: 'Processing' },
      shipped: { class: 'badge-shipped', text: 'Shipped' },
      delivered: { class: 'badge-delivered', text: 'Delivered' },
      cancelled: { class: 'badge-cancelled', text: 'Cancelled' }
    };
    
    const badge = badges[status] || badges.pending;
    return <span className={`status-badge ${badge.class}`}>{badge.text}</span>;
  };

  if (loading) {
    return <div className="loading">Loading orders...</div>;
  }

  if (orders.length === 0) {
    return (
      <div className="empty-orders">
        <h2>No Orders Yet</h2>
        <p>You haven't placed any orders yet.</p>
        <Link to="/products" className="btn-primary">Start Shopping</Link>
      </div>
    );
  }

  return (
    <div className="order-history-container">
      <h1>My Orders</h1>

      <div className="orders-list">
        {orders.map((order) => (
          <div key={order.id} className="order-card">
            <div className="order-header">
              <div>
                <h3>Order #{order.order_number}</h3>
                <p className="order-date">
                  Placed on {new Date(order.created_at).toLocaleDateString()}
                </p>
              </div>
              {getStatusBadge(order.status)}
            </div>

            <div className="order-summary">
              <div className="summary-item">
                <span>Total</span>
                <span className="total-amount">{helpers.formatPrice(order.total)}</span>
              </div>
              {order.shipping_address && (
                <div className="summary-item">
                  <span>Shipping to</span>
                  <span>{order.shipping_address.city}, {order.shipping_address.county}</span>
                </div>
              )}
            </div>

            <div className="order-actions">
              <Link to={`/orders/${order.id}`} className="btn-view-details">
                View Details
              </Link>
            </div>
          </div>
        ))}
      </div>

      {pagination && pagination.pages > 1 && (
        <div className="pagination">
          {pagination.has_prev && (
            <button onClick={() => fetchOrders(pagination.page - 1)}>
              Previous
            </button>
          )}
          <span>Page {pagination.page} of {pagination.pages}</span>
          {pagination.has_next && (
            <button onClick={() => fetchOrders(pagination.page + 1)}>
              Next
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default OrderHistory;
```

---

### 4. Update App.js Routes

**File:** `frontend/src/App.js`

Add routes:
```javascript
import Checkout from './pages/Checkout';
import OrderConfirmation from './pages/OrderConfirmation';
import OrderHistory from './pages/OrderHistory';

// In Routes:
<Route path="/checkout" element={<Checkout />} />
<Route path="/orders/:orderId/confirmation" element={<OrderConfirmation />} />
<Route path="/orders" element={<OrderHistory />} />
```

---

### 5. Update Cart.js Checkout Button

**File:** `frontend/src/pages/Cart.js`

Update checkout button:
```javascript
<button 
  className="btn-checkout" 
  onClick={() => navigate('/checkout')}
  disabled={!cart || !cart.items || cart.items.length === 0}
>
  Proceed to Checkout
</button>
```

---

## M-Pesa Integration (Next Iteration)

**Reference:** See `backend/.env.example` for M-Pesa credentials

**Files to create:**
- `backend/services/mpesa_service.py` - M-Pesa API integration
- `backend/routes/payments.py` - Payment endpoints
- `frontend/src/components/MpesaPayment.js` - Payment UI

**Endpoints:**
- POST /api/payments/mpesa/initiate - STK Push
- POST /api/payments/mpesa/callback - M-Pesa callback
- GET /api/payments/:order_id/status - Payment status

---

## Testing Guide

### 1. Test Stored Procedures

```sql
-- Test order creation
SELECT * FROM create_order_secure(
    2,  -- customer_id
    'encrypted_address',
    NULL,
    NULL,
    TRUE,
    5000.00,
    0.00,
    0.00,
    5000.00,
    '[{"variant_id": 21, "quantity": 1}]'::jsonb,
    '127.0.0.1'::inet,
    'test-agent'
);

-- Check audit log
SELECT * FROM order_audit_log ORDER BY created_at DESC LIMIT 5;

-- Check inventory changes
SELECT * FROM inventory WHERE variant_id = 21;
```

### 2. Test Backend API

```bash
# Login
TOKEN=$(curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"customer@example.com","password":"password"}' \
  -s | python -m json.tool | grep access_token | cut -d'"' -f4)

# Create order
curl -X POST http://localhost:5001/api/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "shipping_address": {
      "full_name": "John Doe",
      "phone": "+254712345678",
      "address_line1": "123 Main St",
      "city": "Nairobi",
      "county": "Nairobi"
    }
  }' -s | python -m json.tool

# Get orders
curl -X GET http://localhost:5001/api/orders \
  -H "Authorization: Bearer $TOKEN" \
  -s | python -m json.tool
```

### 3. Test Frontend Flow

1. Add items to cart
2. Navigate to /checkout
3. Fill shipping form
4. Submit order
5. Verify redirect to confirmation
6. Check /orders page

---

## Security Checklist

- [x] Stored procedures for critical operations
- [x] Row-level locking (SELECT FOR UPDATE)
- [x] Server-side price recalculation
- [x] Address encryption
- [x] Audit logging
- [x] Input validation
- [ ] Rate limiting configured
- [ ] CSRF protection
- [ ] SQL injection testing
- [ ] XSS prevention testing

---

## Next Steps

1. ✅ Complete minimal viable checkout
2. ⏸️ Add M-Pesa integration
3. ⏸️ Implement rate limiting
4. ⏸️ Add order status updates
5. ⏸️ Email/SMS notifications
6. ⏸️ Admin order management

---

**Document Version:** 1.0  
**Last Updated:** 2025-11-25  
**Status:** Ready for implementation

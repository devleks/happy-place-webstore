# 📦 PHASE 1: CRITICAL FIXES
**Order Tracking & Fulfillment Workflow**

**Duration:** Week 1-2 (10 working days)  
**Priority:** P0 - Must Complete  
**Status:** 🔴 Not Started  
**Dependencies:** None

---

## 📋 PHASE OVERVIEW

Phase 1 addresses the two most critical gaps in the current system:
1. **Order Tracking System** - Enable customers to track deliveries
2. **Fulfillment Workflow** - Add dedicated roles and processes for order fulfillment

**Impact:** High - These features are essential for production readiness and customer satisfaction.

---

## 🎯 OBJECTIVES

### Primary Goals
- ✅ Implement complete order tracking with carrier integration
- ✅ Add fulfillment agent role and workflow
- ✅ Create order assignment system
- ✅ Enable real-time shipment updates

### Success Criteria
- [ ] 100% of shipped orders have tracking numbers
- [ ] Customers can view tracking information
- [ ] Fulfillment agents can manage their order queue
- [ ] Order assignment system is operational
- [ ] All tests pass

---

## 📅 TIMELINE

```
Week 1:
├── Day 1-2: Task 1.1.1 - Database schema updates
├── Day 2-3: Task 1.1.2 - Backend models and API
├── Day 3-4: Task 1.1.3 - Admin tracking UI
└── Day 4-5: Task 1.1.4 - Customer tracking page

Week 2:
├── Day 6-7: Task 1.2.1 - Fulfillment database & middleware
├── Day 7-8: Task 1.2.2 - Fulfillment API endpoints
├── Day 8-9: Task 1.2.3 - Fulfillment dashboard UI
└── Day 10: Testing & bug fixes
```

---

## 🔧 TASK 1.1: ORDER TRACKING SYSTEM

**Duration:** 3-4 days  
**Assignee:** Backend + Frontend Developer  
**Priority:** P0

### 1.1.1 Database Schema Updates

**File:** `backend/migrations/020_add_order_tracking.sql`

```sql
-- Add tracking fields to orders table
ALTER TABLE orders 
ADD COLUMN tracking_number VARCHAR(100),
ADD COLUMN carrier VARCHAR(50),
ADD COLUMN tracking_url TEXT,
ADD COLUMN estimated_delivery_date DATE,
ADD COLUMN shipping_notes TEXT;

-- Create shipment_updates table for tracking history
CREATE TABLE shipment_updates (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL,
    location VARCHAR(200),
    description TEXT,
    timestamp TIMESTAMP NOT NULL,
    created_by INTEGER REFERENCES employees(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_shipment_updates_order_id ON shipment_updates(order_id);
CREATE INDEX idx_shipment_updates_timestamp ON shipment_updates(timestamp);

-- Create shipping_carriers table
CREATE TABLE shipping_carriers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    tracking_url_template TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert Kenyan carriers
INSERT INTO shipping_carriers (name, tracking_url_template) VALUES
('DHL Express', 'https://www.dhl.com/ke-en/home/tracking.html?tracking-id={tracking_number}'),
('Posta Kenya', 'https://www.posta.co.ke/track?number={tracking_number}'),
('G4S Courier', 'https://www.g4s.co.ke/track/{tracking_number}'),
('Sendy', 'https://sendy.co.ke/track/{tracking_number}'),
('Uber Direct', 'https://www.uber.com/ke/en/delivery/track/{tracking_number}');
```

**Testing:**
```bash
# Run migration
psql -U postgres -d happy_place_dev -f backend/migrations/020_add_order_tracking.sql

# Verify tables created
psql -U postgres -d happy_place_dev -c "\dt shipment_updates"
psql -U postgres -d happy_place_dev -c "\dt shipping_carriers"
```

---

### 1.1.2 Backend Models

**File:** `backend/models/database_models.py`

Add to existing Order model:
```python
class Order(db.Model):
    __tablename__ = 'orders'
    
    # ... existing fields ...
    
    # NEW: Tracking fields
    tracking_number = db.Column(db.String(100))
    carrier = db.Column(db.String(50))
    tracking_url = db.Column(db.Text)
    estimated_delivery_date = db.Column(db.Date)
    shipping_notes = db.Column(db.Text)
    
    # Relationships
    shipment_updates = db.relationship('ShipmentUpdate', backref='order', 
                                      lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, include_items=True):
        data = {
            # ... existing fields ...
            'tracking_number': self.tracking_number,
            'carrier': self.carrier,
            'tracking_url': self.tracking_url,
            'estimated_delivery_date': self.estimated_delivery_date.isoformat() 
                if self.estimated_delivery_date else None,
            'shipping_notes': self.shipping_notes
        }
        
        if include_items:
            data['shipment_updates'] = [
                update.to_dict() for update in self.shipment_updates
            ]
        
        return data
```

Add new models:
```python
class ShipmentUpdate(db.Model):
    """Track shipment status updates"""
    __tablename__ = 'shipment_updates'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'))
    status = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200))
    description = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('employees.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'status': self.status,
            'location': self.location,
            'description': self.description,
            'timestamp': self.timestamp.isoformat()
        }


class ShippingCarrier(db.Model):
    """Available shipping carriers"""
    __tablename__ = 'shipping_carriers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    tracking_url_template = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'is_active': self.is_active
        }
```

---

### 1.1.3 Backend API Endpoints

**File:** `backend/routes/admin_routes.py`

```python
@admin_bp.route('/orders/<int:order_id>/tracking', methods=['POST'])
@jwt_required()
@manager_required
def add_tracking_info(current_employee, order_id):
    """
    Add tracking information to order.
    
    POST /api/admin/orders/123/tracking
    Body: {
        "tracking_number": "DHL123456789",
        "carrier": "DHL Express",
        "estimated_delivery": "2025-12-15",
        "notes": "Package dispatched from Nairobi hub"
    }
    
    Returns: 200 with tracking details
    """
    try:
        from models.database_models import Order, ShipmentUpdate, ShippingCarrier
        from services.notification_service import send_tracking_email
        
        data = request.get_json()
        order = Order.query.get(order_id)
        
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Update tracking info
        order.tracking_number = data.get('tracking_number')
        order.carrier = data.get('carrier')
        order.estimated_delivery_date = data.get('estimated_delivery')
        order.shipping_notes = data.get('notes')
        
        # Generate tracking URL
        if order.tracking_number and order.carrier:
            carrier_config = ShippingCarrier.query.filter_by(
                name=order.carrier
            ).first()
            if carrier_config:
                order.tracking_url = carrier_config.tracking_url_template.replace(
                    '{tracking_number}', order.tracking_number
                )
        
        # Update order status
        order.status = 'shipped'
        order.shipped_at = datetime.utcnow()
        
        # Create shipment update
        shipment_update = ShipmentUpdate(
            order_id=order_id,
            status='shipped',
            location='Nairobi Distribution Center',
            description=data.get('notes', 'Package shipped'),
            timestamp=datetime.utcnow(),
            created_by=current_employee.id
        )
        db.session.add(shipment_update)
        
        db.session.commit()
        
        # Send customer notification
        send_tracking_email(order)
        
        return jsonify({
            'success': True,
            'tracking_number': order.tracking_number,
            'tracking_url': order.tracking_url
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/orders/<int:order_id>/tracking', methods=['GET'])
@jwt_required()
def get_tracking_info(order_id):
    """Get tracking information for an order"""
    try:
        from models.database_models import Order
        
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        return jsonify({
            'tracking_number': order.tracking_number,
            'carrier': order.carrier,
            'tracking_url': order.tracking_url,
            'estimated_delivery_date': order.estimated_delivery_date.isoformat()
                if order.estimated_delivery_date else None,
            'shipping_notes': order.shipping_notes,
            'updates': [update.to_dict() for update in order.shipment_updates]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/shipping/carriers', methods=['GET'])
@jwt_required()
def get_carriers():
    """Get list of available shipping carriers"""
    try:
        from models.database_models import ShippingCarrier
        
        carriers = ShippingCarrier.query.filter_by(is_active=True).all()
        return jsonify([carrier.to_dict() for carrier in carriers]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**Testing:**
```bash
# Test add tracking
curl -X POST http://localhost:5001/api/admin/orders/1/tracking \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tracking_number": "DHL123456789",
    "carrier": "DHL Express",
    "estimated_delivery": "2025-12-15",
    "notes": "Package dispatched"
  }'

# Test get tracking
curl http://localhost:5001/api/admin/orders/1/tracking \
  -H "Authorization: Bearer $TOKEN"

# Test get carriers
curl http://localhost:5001/api/shipping/carriers \
  -H "Authorization: Bearer $TOKEN"
```

---

### 1.1.4 Frontend - Admin Tracking UI

**File:** `frontend/src/pages/admin/AdminOrders.js`

Add tracking modal state and handlers:

```javascript
// Add state
const [showTrackingModal, setShowTrackingModal] = useState(false);
const [trackingData, setTrackingData] = useState({
    tracking_number: '',
    carrier: '',
    estimated_delivery: '',
    notes: ''
});
const [carriers, setCarriers] = useState([]);

// Fetch carriers on mount
useEffect(() => {
    fetchCarriers();
}, []);

const fetchCarriers = async () => {
    try {
        const data = await adminAPI.getCarriers();
        setCarriers(data);
    } catch (err) {
        console.error('Failed to load carriers:', err);
    }
};

const openTrackingModal = (order) => {
    setCurrentOrder(order);
    setTrackingData({
        tracking_number: order.tracking_number || '',
        carrier: order.carrier || '',
        estimated_delivery: order.estimated_delivery_date || '',
        notes: order.shipping_notes || ''
    });
    setShowTrackingModal(true);
};

const handleAddTracking = async (e) => {
    e.preventDefault();
    try {
        await adminAPI.addTracking(currentOrder.id, trackingData);
        toast.success('Tracking information added successfully');
        setShowTrackingModal(false);
        fetchOrders();
    } catch (err) {
        toast.error(err.message || 'Failed to add tracking');
    }
};

// Add tracking button to order actions
<button 
    onClick={() => openTrackingModal(order)}
    className="btn-secondary"
    disabled={order.status === 'delivered'}
>
    {order.tracking_number ? '📝 Update Tracking' : '➕ Add Tracking'}
</button>

// Tracking Modal JSX (add before closing component)
{showTrackingModal && (
    <div className="modal-overlay" onClick={() => setShowTrackingModal(false)}>
        <div className="modal-content tracking-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
                <h2>Add Tracking Information</h2>
                <button onClick={() => setShowTrackingModal(false)} className="close-btn">×</button>
            </div>
            <form onSubmit={handleAddTracking}>
                <div className="modal-body">
                    <div className="form-group">
                        <label>Carrier *</label>
                        <select
                            value={trackingData.carrier}
                            onChange={(e) => setTrackingData({...trackingData, carrier: e.target.value})}
                            className="form-input"
                            required
                        >
                            <option value="">Select Carrier</option>
                            {carriers.map(carrier => (
                                <option key={carrier.id} value={carrier.name}>
                                    {carrier.name}
                                </option>
                            ))}
                        </select>
                    </div>
                    
                    <div className="form-group">
                        <label>Tracking Number *</label>
                        <input
                            type="text"
                            value={trackingData.tracking_number}
                            onChange={(e) => setTrackingData({...trackingData, tracking_number: e.target.value})}
                            className="form-input"
                            placeholder="e.g., DHL123456789"
                            required
                        />
                    </div>
                    
                    <div className="form-group">
                        <label>Estimated Delivery Date</label>
                        <input
                            type="date"
                            value={trackingData.estimated_delivery}
                            onChange={(e) => setTrackingData({...trackingData, estimated_delivery: e.target.value})}
                            className="form-input"
                            min={new Date().toISOString().split('T')[0]}
                        />
                    </div>
                    
                    <div className="form-group">
                        <label>Shipping Notes</label>
                        <textarea
                            value={trackingData.notes}
                            onChange={(e) => setTrackingData({...trackingData, notes: e.target.value})}
                            className="form-input"
                            rows="3"
                            placeholder="e.g., Package dispatched from Nairobi hub"
                        />
                    </div>
                </div>
                <div className="modal-footer">
                    <button type="button" onClick={() => setShowTrackingModal(false)} className="btn-secondary">
                        Cancel
                    </button>
                    <button type="submit" className="btn-primary">
                        🚚 Add Tracking & Mark as Shipped
                    </button>
                </div>
            </form>
        </div>
    </div>
)}
```

---

### 1.1.5 Frontend - Customer Tracking Page

**File:** `frontend/src/pages/TrackOrder.js` (NEW)

```javascript
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../services/api';
import '../styles/TrackOrder.css';

const TrackOrder = () => {
    const { orderId } = useParams();
    const [order, setOrder] = useState(null);
    const [tracking, setTracking] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    
    useEffect(() => {
        fetchOrderTracking();
    }, [orderId]);
    
    const fetchOrderTracking = async () => {
        try {
            setLoading(true);
            const response = await api.get(`/orders/${orderId}/tracking`);
            setOrder(response.data.order);
            setTracking(response.data.tracking);
        } catch (err) {
            setError(err.message || 'Failed to load tracking information');
        } finally {
            setLoading(false);
        }
    };
    
    if (loading) {
        return (
            <div className="track-order-page">
                <div className="loading">Loading tracking information...</div>
            </div>
        );
    }
    
    if (error) {
        return (
            <div className="track-order-page">
                <div className="error-message">{error}</div>
            </div>
        );
    }
    
    return (
        <div className="track-order-page">
            <div className="container">
                <h1>Track Your Order</h1>
                
                <div className="order-info-card">
                    <div className="order-header">
                        <h2>Order #{order?.order_number}</h2>
                        <span className={`status-badge status-${order?.status}`}>
                            {order?.status}
                        </span>
                    </div>
                    <div className="order-details">
                        <p><strong>Order Date:</strong> {new Date(order?.created_at).toLocaleDateString()}</p>
                        <p><strong>Total:</strong> KSh {order?.total}</p>
                    </div>
                </div>
                
                {tracking && tracking.tracking_number ? (
                    <div className="tracking-details">
                        <div className="tracking-header">
                            <h3>📦 Shipment Details</h3>
                            <span className="carrier-badge">{tracking.carrier}</span>
                        </div>
                        
                        <div className="tracking-info-grid">
                            <div className="info-item">
                                <label>Tracking Number:</label>
                                <div className="tracking-number">
                                    <span className="number">{tracking.tracking_number}</span>
                                    <button 
                                        onClick={() => navigator.clipboard.writeText(tracking.tracking_number)}
                                        className="btn-copy"
                                        title="Copy tracking number"
                                    >
                                        📋 Copy
                                    </button>
                                </div>
                            </div>
                            
                            {tracking.estimated_delivery_date && (
                                <div className="info-item">
                                    <label>Estimated Delivery:</label>
                                    <span className="delivery-date">
                                        {new Date(tracking.estimated_delivery_date).toLocaleDateString()}
                                    </span>
                                </div>
                            )}
                        </div>
                        
                        {tracking.tracking_url && (
                            <a 
                                href={tracking.tracking_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="btn-track-external"
                            >
                                🔗 Track on {tracking.carrier} Website →
                            </a>
                        )}
                        
                        {/* Shipment Timeline */}
                        {tracking.updates && tracking.updates.length > 0 && (
                            <div className="shipment-timeline">
                                <h3>📍 Shipment History</h3>
                                <div className="timeline">
                                    {tracking.updates.map((update, index) => (
                                        <div key={index} className="timeline-item">
                                            <div className="timeline-marker"></div>
                                            <div className="timeline-content">
                                                <div className="timeline-status">{update.status}</div>
                                                {update.location && (
                                                    <div className="timeline-location">
                                                        📍 {update.location}
                                                    </div>
                                                )}
                                                <div className="timeline-description">
                                                    {update.description}
                                                </div>
                                                <div className="timeline-time">
                                                    {new Date(update.timestamp).toLocaleString()}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="no-tracking">
                        <div className="no-tracking-icon">📦</div>
                        <h3>Tracking Not Available Yet</h3>
                        <p>Your order is being prepared for shipment.</p>
                        <p>Tracking information will be available once your order ships.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default TrackOrder;
```

---

### 1.1.6 Update API Services

**File:** `frontend/src/services/adminAPI.js`

```javascript
export const adminAPI = {
    // ... existing methods ...
    
    // Tracking methods
    getCarriers: async () => {
        try {
            const response = await api.get('/shipping/carriers');
            return response.data;
        } catch (error) {
            handleError(error);
        }
    },
    
    addTracking: async (orderId, trackingData) => {
        try {
            const response = await api.post(`/admin/orders/${orderId}/tracking`, trackingData);
            return response.data;
        } catch (error) {
            handleError(error);
        }
    },
    
    getTracking: async (orderId) => {
        try {
            const response = await api.get(`/admin/orders/${orderId}/tracking`);
            return response.data;
        } catch (error) {
            handleError(error);
        }
    },
};
```

---

## ✅ TASK 1.1 DELIVERABLES

- [x] Database migration script (`020_add_order_tracking.sql`)
- [x] Updated Order model with tracking fields
- [x] ShipmentUpdate model
- [x] ShippingCarrier model
- [x] 3 new API endpoints (add/get tracking, list carriers)
- [x] Admin tracking modal UI
- [x] Customer tracking page
- [x] Updated adminAPI service
- [ ] Email notification template
- [ ] Unit tests
- [ ] Integration tests

---

## 🔧 TASK 1.2: FULFILLMENT WORKFLOW

**Duration:** 4-5 days  
**Assignee:** Full Stack Developer  
**Priority:** P0

### 1.2.1 Database Schema - Fulfillment Roles

**File:** `backend/migrations/021_add_fulfillment_roles.sql`

```sql
-- Update employee role constraint
ALTER TABLE employees 
DROP CONSTRAINT IF EXISTS chk_employee_role;

ALTER TABLE employees 
ADD CONSTRAINT chk_employee_role 
CHECK (role IN ('admin', 'manager', 'fulfillment_agent', 'warehouse_staff', 'delivery_coordinator', 'cashier'));

-- Create role_definitions table
CREATE TABLE role_definitions (
    role VARCHAR(30) PRIMARY KEY,
    display_name VARCHAR(50) NOT NULL,
    description TEXT,
    permissions JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO role_definitions (role, display_name, description, permissions) VALUES
('admin', 'Administrator', 'Full system access', '["*"]'),
('manager', 'Store Manager', 'Business operations management', 
 '["orders.*", "inventory.view", "inventory.adjust", "reports.*", "employees.view"]'),
('fulfillment_agent', 'Fulfillment Agent', 'Online order processing', 
 '["orders.view", "orders.update_status", "orders.add_tracking", "inventory.view", "shipping.*"]'),
('warehouse_staff', 'Warehouse Staff', 'Inventory management', 
 '["inventory.view", "inventory.adjust", "inventory.receive", "inventory.count"]'),
('delivery_coordinator', 'Delivery Coordinator', 'Shipping logistics', 
 '["orders.view", "orders.update_delivery", "shipping.*", "customers.contact"]'),
('cashier', 'Cashier', 'Point of sale operations', '["pos.*"]');

-- Create order_assignments table
CREATE TABLE order_assignments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    employee_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by INTEGER REFERENCES employees(id),
    status VARCHAR(20) DEFAULT 'assigned',
    completed_at TIMESTAMP,
    notes TEXT,
    UNIQUE(order_id, employee_id)
);

CREATE INDEX idx_order_assignments_order_id ON order_assignments(order_id);
CREATE INDEX idx_order_assignments_employee_id ON order_assignments(employee_id);
CREATE INDEX idx_order_assignments_status ON order_assignments(status);
```

---

### 1.2.2 Backend Middleware

**File:** `backend/middleware/auth.py`

```python
def fulfillment_required(fn):
    """
    Decorator for fulfillment agent, manager, or admin.
    Used for online order processing routes.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        
        if claims.get('user_type') != 'employee':
            return jsonify({'error': 'Employee authentication required'}), 403
        
        employee_id = get_jwt_identity()
        employee = Employee.query.get(employee_id)
        
        if not employee or not employee.is_active:
            return jsonify({'error': 'Invalid employee'}), 403
        
        # Allow fulfillment_agent, manager, or admin
        if employee.role not in ['fulfillment_agent', 'manager', 'admin']:
            return jsonify({
                'error': 'Insufficient permissions',
                'required_role': 'fulfillment_agent, manager, or admin',
                'current_role': employee.role
            }), 403
        
        return fn(current_employee=employee, *args, **kwargs)
    
    return wrapper
```

---

### 1.2.3 Backend API - Fulfillment Endpoints

**File:** `backend/routes/fulfillment_routes.py` (NEW)

```python
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from middleware.auth import fulfillment_required
from models import db, Order, OrderAssignment, Employee, Payment
from datetime import datetime, date

fulfillment_bp = Blueprint('fulfillment', __name__, url_prefix='/api/fulfillment')

@fulfillment_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@fulfillment_required
def get_fulfillment_dashboard(current_employee):
    """Get fulfillment dashboard metrics"""
    try:
        # Pending orders (payment completed, not yet assigned)
        pending_orders = Order.query.filter_by(
            status='pending'
        ).join(Payment).filter(
            Payment.status == 'completed'
        ).count()
        
        # My assigned orders
        my_orders = OrderAssignment.query.filter_by(
            employee_id=current_employee.id,
            status='assigned'
        ).count()
        
        # Orders ready to ship (processing)
        ready_to_ship = Order.query.filter_by(
            status='processing'
        ).count()
        
        # Shipped today
        shipped_today = Order.query.filter(
            Order.status == 'shipped',
            db.func.date(Order.shipped_at) == date.today()
        ).count()
        
        return jsonify({
            'pending_orders': pending_orders,
            'my_orders': my_orders,
            'ready_to_ship': ready_to_ship,
            'shipped_today': shipped_today
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@fulfillment_bp.route('/orders/pending', methods=['GET'])
@jwt_required()
@fulfillment_required
def get_pending_orders(current_employee):
    """Get orders pending fulfillment"""
    try:
        orders = Order.query.filter_by(
            status='pending'
        ).join(Payment).filter(
            Payment.status == 'completed'
        ).order_by(Order.created_at.asc()).all()
        
        return jsonify([order.to_dict() for order in orders]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@fulfillment_bp.route('/orders/<int:order_id>/assign', methods=['POST'])
@jwt_required()
@fulfillment_required
def assign_order(current_employee, order_id):
    """Assign order to fulfillment agent"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Check if already assigned
        existing = OrderAssignment.query.filter_by(
            order_id=order_id,
            status='assigned'
        ).first()
        
        if existing:
            return jsonify({'error': 'Order already assigned'}), 400
        
        # Create assignment
        assignment = OrderAssignment(
            order_id=order_id,
            employee_id=current_employee.id,
            assigned_by=current_employee.id,
            status='assigned'
        )
        db.session.add(assignment)
        
        # Update order status
        order.status = 'processing'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Order assigned successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@fulfillment_bp.route('/orders/my-orders', methods=['GET'])
@jwt_required()
@fulfillment_required
def get_my_orders(current_employee):
    """Get orders assigned to current employee"""
    try:
        assignments = OrderAssignment.query.filter_by(
            employee_id=current_employee.id,
            status='assigned'
        ).all()
        
        orders = [assignment.order.to_dict() for assignment in assignments]
        
        return jsonify(orders), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@fulfillment_bp.route('/orders/<int:order_id>/complete', methods=['POST'])
@jwt_required()
@fulfillment_required
def complete_fulfillment(current_employee, order_id):
    """Mark order fulfillment as complete"""
    try:
        assignment = OrderAssignment.query.filter_by(
            order_id=order_id,
            employee_id=current_employee.id,
            status='assigned'
        ).first()
        
        if not assignment:
            return jsonify({'error': 'Order not assigned to you'}), 403
        
        # Update assignment
        assignment.status = 'completed'
        assignment.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Fulfillment completed'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
```

Register blueprint in `backend/app.py`:
```python
from routes.fulfillment_routes import fulfillment_bp
app.register_blueprint(fulfillment_bp)
```

---

### 1.2.4 Frontend - Fulfillment Dashboard

**File:** `frontend/src/pages/fulfillment/FulfillmentDashboard.js` (NEW)

```javascript
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { fulfillmentAPI } from '../../services/fulfillmentAPI';
import MetricCard from '../../components/admin/MetricCard';
import { toast } from 'react-toastify';
import '../../styles/FulfillmentDashboard.css';

const FulfillmentDashboard = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [metrics, setMetrics] = useState({
        pending_orders: 0,
        my_orders: 0,
        ready_to_ship: 0,
        shipped_today: 0
    });
    const [pendingOrders, setPendingOrders] = useState([]);
    const [myOrders, setMyOrders] = useState([]);
    
    useEffect(() => {
        if (!user || user.role !== 'fulfillment_agent') {
            navigate('/login');
            return;
        }
        
        fetchDashboardData();
    }, [user, navigate]);
    
    const fetchDashboardData = async () => {
        try {
            setLoading(true);
            const [metricsData, pendingData, myOrdersData] = await Promise.all([
                fulfillmentAPI.getDashboard(),
                fulfillmentAPI.getPendingOrders(),
                fulfillmentAPI.getMyOrders()
            ]);
            
            setMetrics(metricsData);
            setPendingOrders(pendingData);
            setMyOrders(myOrdersData);
        } catch (err) {
            console.error('Failed to load dashboard:', err);
            toast.error('Failed to load dashboard data');
        } finally {
            setLoading(false);
        }
    };
    
    const handleAssignOrder = async (orderId) => {
        try {
            await fulfillmentAPI.assignOrder(orderId);
            toast.success('Order assigned to you');
            fetchDashboardData();
        } catch (err) {
            toast.error(err.message || 'Failed to assign order');
        }
    };
    
    if (loading) return <div className="loading">Loading...</div>;
    
    return (
        <div className="fulfillment-dashboard">
            <h1>📦 Order Fulfillment</h1>
            
            {/* Metrics */}
            <div className="metrics-grid">
                <MetricCard
                    title="Pending Orders"
                    value={metrics.pending_orders}
                    icon="📦"
                    color="yellow"
                />
                <MetricCard
                    title="My Orders"
                    value={metrics.my_orders}
                    icon="👤"
                    color="blue"
                />
                <MetricCard
                    title="Ready to Ship"
                    value={metrics.ready_to_ship}
                    icon="🚚"
                    color="orange"
                />
                <MetricCard
                    title="Shipped Today"
                    value={metrics.shipped_today}
                    icon="✅"
                    color="green"
                />
            </div>
            
            {/* Pending Orders */}
            <section className="orders-section">
                <h2>Orders Awaiting Assignment</h2>
                {pendingOrders.length === 0 ? (
                    <p className="no-data">No pending orders</p>
                ) : (
                    <div className="orders-grid">
                        {pendingOrders.map(order => (
                            <div key={order.id} className="order-card">
                                <div className="order-header">
                                    <span className="order-number">#{order.order_number}</span>
                                    <span className="order-date">
                                        {new Date(order.created_at).toLocaleDateString()}
                                    </span>
                                </div>
                                <div className="order-body">
                                    <p><strong>Items:</strong> {order.items?.length || 0}</p>
                                    <p><strong>Total:</strong> KSh {order.total}</p>
                                    <p><strong>Location:</strong> {order.is_nairobi ? 'Nairobi' : 'Upcountry'}</p>
                                </div>
                                <button 
                                    onClick={() => handleAssignOrder(order.id)}
                                    className="btn-primary"
                                >
                                    Assign to Me
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </section>
            
            {/* My Orders */}
            <section className="orders-section">
                <h2>My Assigned Orders</h2>
                {myOrders.length === 0 ? (
                    <p className="no-data">No orders assigned to you</p>
                ) : (
                    <div className="orders-list">
                        {myOrders.map(order => (
                            <div key={order.id} className="order-item">
                                <div className="order-info">
                                    <h3>Order #{order.order_number}</h3>
                                    <p>{order.items?.length || 0} items</p>
                                </div>
                                <div className="order-actions">
                                    <button 
                                        onClick={() => navigate(`/fulfillment/orders/${order.id}`)}
                                        className="btn-secondary"
                                    >
                                        View Details
                                    </button>
                                    <button 
                                        onClick={() => navigate(`/fulfillment/orders/${order.id}/pack`)}
                                        className="btn-primary"
                                    >
                                        Start Packing
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </section>
        </div>
    );
};

export default FulfillmentDashboard;
```

---

### 1.2.5 Create Fulfillment API Service

**File:** `frontend/src/services/fulfillmentAPI.js` (NEW)

```javascript
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add token to requests
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

const handleError = (error) => {
    if (error.response) {
        throw new Error(error.response.data.message || error.response.data.error || 'An error occurred');
    } else if (error.request) {
        throw new Error('No response from server');
    } else {
        throw new Error(error.message);
    }
};

export const fulfillmentAPI = {
    getDashboard: async () => {
        try {
            const response = await api.get('/fulfillment/dashboard');
            return response.data;
        } catch (error) {
            handleError(error);
        }
    },
    
    getPendingOrders: async () => {
        try {
            const response = await api.get('/fulfillment/orders/pending');
            return response.data;
        } catch (error) {
            handleError(error);
        }
    },
    
    getMyOrders: async () => {
        try {
            const response = await api.get('/fulfillment/orders/my-orders');
            return response.data;
        } catch (error) {
            handleError(error);
        }
    },
    
    assignOrder: async (orderId) => {
        try {
            const response = await api.post(`/fulfillment/orders/${orderId}/assign`);
            return response.data;
        } catch (error) {
            handleError(error);
        }
    },
    
    completeOrder: async (orderId) => {
        try {
            const response = await api.post(`/fulfillment/orders/${orderId}/complete`);
            return response.data;
        } catch (error) {
            handleError(error);
        }
    },
};

export default fulfillmentAPI;
```

---

### 1.2.6 Update Employee Management

**File:** `frontend/src/pages/admin/AdminEmployees.js`

Update role dropdown:
```javascript
<select
    value={formData.role}
    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
    className="form-input"
    required
>
    <optgroup label="Management">
        <option value="admin">Admin - Full System Access</option>
        <option value="manager">Manager - Business Operations</option>
    </optgroup>
    
    <optgroup label="Online Operations">
        <option value="fulfillment_agent">
            Fulfillment Agent - Order Processing ⭐ NEW
        </option>
        <option value="warehouse_staff">
            Warehouse Staff - Inventory Management ⭐ NEW
        </option>
        <option value="delivery_coordinator">
            Delivery Coordinator - Shipping ⭐ NEW
        </option>
    </optgroup>
    
    <optgroup label="Store Operations">
        <option value="cashier">Cashier - POS Only</option>
    </optgroup>
</select>

{/* Role description */}
{formData.role && (
    <div className="role-description">
        <p>{getRoleDescription(formData.role)}</p>
    </div>
)}
```

Add helper function:
```javascript
const getRoleDescription = (role) => {
    const descriptions = {
        admin: 'Full system access including user management, settings, and all features.',
        manager: 'Business operations including orders, inventory, reports, and employee viewing.',
        fulfillment_agent: 'Process online orders: pick items, pack, add tracking, and ship.',
        warehouse_staff: 'Manage inventory: receive stock, adjust quantities, perform counts.',
        delivery_coordinator: 'Coordinate deliveries: manage shipping, update tracking, contact customers.',
        cashier: 'Point of sale operations: process in-store sales and handle payments.'
    };
    return descriptions[role] || '';
};
```

---

## ✅ TASK 1.2 DELIVERABLES

- [x] Database migration for new roles (`021_add_fulfillment_roles.sql`)
- [x] Role definitions table
- [x] Order assignments table
- [x] Fulfillment middleware decorators
- [x] Fulfillment API endpoints (5 new)
- [x] Fulfillment dashboard UI
- [x] Fulfillment API service
- [x] Updated employee management UI
- [ ] Unit tests
- [ ] Integration tests

---

## 📋 PHASE 1 TESTING CHECKLIST

### Order Tracking Tests
- [ ] Admin can add tracking number to order
- [ ] Tracking URL generates correctly for each carrier
- [ ] Customer can view tracking information
- [ ] Tracking page displays shipment history
- [ ] Email notification sent when tracking added
- [ ] Multiple carriers supported
- [ ] Invalid tracking number handled gracefully

### Fulfillment Workflow Tests
- [ ] Fulfillment agent can login
- [ ] Dashboard shows correct metrics
- [ ] Can view pending orders
- [ ] Can assign order to self
- [ ] Order status updates to 'processing' on assignment
- [ ] Can view assigned orders
- [ ] Can complete order fulfillment
- [ ] Cannot assign already assigned order

### Integration Tests
- [ ] Full order flow: create → assign → add tracking → ship
- [ ] Role permissions enforced correctly
- [ ] Database transactions atomic
- [ ] API error handling works
- [ ] Frontend error messages clear

---

## 🚀 DEPLOYMENT STEPS

1. **Backup Database**
   ```bash
   pg_dump happy_place_prod > backup_before_phase1.sql
   ```

2. **Run Migrations**
   ```bash
   psql -U postgres -d happy_place_prod -f backend/migrations/020_add_order_tracking.sql
   psql -U postgres -d happy_place_prod -f backend/migrations/021_add_fulfillment_roles.sql
   ```

3. **Deploy Backend**
   ```bash
   git pull origin main
   source venv/bin/activate
   pip install -r requirements.txt
   sudo systemctl restart happy-place-backend
   ```

4. **Deploy Frontend**
   ```bash
   cd frontend
   npm install
   npm run build
   sudo cp -r build/* /var/www/html/
   ```

5. **Verify Deployment**
   - Test tracking addition
   - Test fulfillment dashboard
   - Check error logs
   - Monitor performance

---

## 📊 SUCCESS METRICS

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Tracking Coverage | 100% | - | ⬜ |
| Fulfillment Time | < 24h | - | ⬜ |
| Order Assignment | 100% | - | ⬜ |
| API Response Time | < 200ms | - | ⬜ |
| Zero Critical Bugs | Yes | - | ⬜ |

---

## 📚 RELATED DOCUMENTS

- [Implementation Master Plan](../IMPLEMENTATION_MASTER_PLAN.md)
- [Admin Portal Analysis](../ADMIN_PORTAL_ANALYSIS_2025-12-09.md)
- [Phase 2: Portal Separation](./PHASE_2_PORTAL_SEPARATION.md)
- [Testing Checklist](./TESTING_CHECKLIST.md)

---

**Phase Status:** 🔴 Not Started  
**Last Updated:** December 9, 2025  
**Next Review:** End of Week 2

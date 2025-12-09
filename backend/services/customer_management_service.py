"""
Customer Management Service
Handles customer accounts, GDPR compliance, and data management
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import and_, or_, desc, func
from models.database_models import db, Customer, Order, CustomerAddress
import json


class CustomerManagementService:
    """Service for managing customers"""

    def get_customer_list(self, filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
        """Get paginated customer list with filters"""
        filters = filters or {}
        query = Customer.query

        if filters.get('status') == 'active':
            query = query.filter(Customer.is_active == True)
        elif filters.get('status') == 'inactive':
            query = query.filter(Customer.is_active == False)

        if filters.get('search'):
            search_term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    Customer.first_name.ilike(search_term),
                    Customer.last_name.ilike(search_term),
                    Customer.email.ilike(search_term)
                )
            )

        if filters.get('email_verified'):
            query = query.filter(Customer.email_verified == True)

        query = query.order_by(desc(Customer.created_at))

        total_count = query.count()
        customers = query.offset((page - 1) * per_page).limit(per_page).all()

        customer_list = []
        for customer in customers:
            # Get order count and total spent
            orders = Order.query.filter_by(customer_id=customer.id).all()
            order_count = len(orders)
            total_spent = sum(float(o.total or 0) for o in orders if o.status != 'cancelled')

            customer_list.append({
                'id': customer.id,
                'name': f"{customer.first_name} {customer.last_name}",
                'email': customer.email,
                'phone': customer.phone,
                'total_orders': order_count,
                'total_spent': total_spent,
                'created_at': customer.created_at.isoformat() if customer.created_at else None,
                'is_active': customer.is_active,
                'email_verified': customer.email_verified
            })

        return {
            'customers': customer_list,
            'total': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        }

    def get_customer_details(self, customer_id: int) -> Dict:
        """Get complete customer profile"""
        customer = Customer.query.get(customer_id)
        if not customer:
            return {'error': 'Customer not found'}

        # Get addresses
        addresses = CustomerAddress.query.filter_by(customer_id=customer_id).all()
        address_list = [{
            'id': addr.id,
            'type': addr.address_type,
            'street': addr.street_address,
            'city': addr.city,
            'postal_code': addr.postal_code,
            'country': addr.country,
            'is_default': addr.is_default
        } for addr in addresses]

        # Get order stats
        orders = Order.query.filter_by(customer_id=customer_id).all()
        completed_orders = [o for o in orders if o.status in ['delivered', 'completed']]
        total_spent = sum(float(o.total or 0) for o in completed_orders)
        avg_order_value = total_spent / len(completed_orders) if completed_orders else 0
        last_order = max(orders, key=lambda o: o.created_at) if orders else None

        return {
            'id': customer.id,
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'email': customer.email,
            'phone': customer.phone,
            'created_at': customer.created_at.isoformat() if customer.created_at else None,
            'last_login': customer.last_login.isoformat() if hasattr(customer, 'last_login') and customer.last_login else None,
            'is_active': customer.is_active,
            'email_verified': customer.email_verified,
            'gdpr_consent': customer.gdpr_consent if hasattr(customer, 'gdpr_consent') else False,
            'addresses': address_list,
            'order_stats': {
                'total_orders': len(orders),
                'completed_orders': len(completed_orders),
                'total_spent': total_spent,
                'average_order_value': avg_order_value,
                'last_order_date': last_order.created_at.isoformat() if last_order and last_order.created_at else None
            }
        }

    def update_customer(self, customer_id: int, data: Dict) -> bool:
        """Update customer information"""
        try:
            customer = Customer.query.get(customer_id)
            if not customer:
                return False

            if 'first_name' in data:
                customer.first_name = data['first_name']
            if 'last_name' in data:
                customer.last_name = data['last_name']
            if 'email' in data:
                customer.email = data['email']
            if 'phone' in data:
                customer.phone = data['phone']
            if 'is_active' in data:
                customer.is_active = data['is_active']

            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error updating customer: {e}")
            return False

    def get_customer_orders(self, customer_id: int, page: int = 1) -> Dict:
        """Get customer order history"""
        query = Order.query.filter_by(customer_id=customer_id).order_by(desc(Order.created_at))
        total = query.count()
        orders = query.offset((page - 1) * 20).limit(20).all()

        order_list = [{
            'id': o.id,
            'created_at': o.created_at.isoformat() if o.created_at else None,
            'status': o.status,
            'total': float(o.total or 0),
            'items_count': len(o.items) if o.items else 0
        } for o in orders]

        return {'orders': order_list, 'total': total, 'page': page}

    def get_customer_activity(self, customer_id: int, days: int = 30) -> List[Dict]:
        """Get customer activity log"""
        start_date = datetime.now() - timedelta(days=days)
        activities = []

        # Get recent orders
        orders = Order.query.filter(
            and_(
                Order.customer_id == customer_id,
                Order.created_at >= start_date
            )
        ).order_by(desc(Order.created_at)).all()

        for order in orders:
            activities.append({
                'type': 'order_placed',
                'timestamp': order.created_at.isoformat() if order.created_at else None,
                'description': f'Placed order #{order.id}',
                'amount': float(order.total or 0)
            })

        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return activities

    def export_customer_data(self, customer_id: int) -> Dict:
        """Export all customer data (GDPR compliance)"""
        customer = Customer.query.get(customer_id)
        if not customer:
            return {'error': 'Customer not found'}

        # Get all related data
        orders = Order.query.filter_by(customer_id=customer_id).all()
        addresses = CustomerAddress.query.filter_by(customer_id=customer_id).all()

        export_data = {
            'customer': {
                'id': customer.id,
                'first_name': customer.first_name,
                'last_name': customer.last_name,
                'email': customer.email,
                'phone': customer.phone,
                'created_at': customer.created_at.isoformat() if customer.created_at else None
            },
            'addresses': [{
                'type': addr.address_type,
                'street': addr.street_address,
                'city': addr.city,
                'postal_code': addr.postal_code,
                'country': addr.country
            } for addr in addresses],
            'orders': [{
                'id': o.id,
                'date': o.created_at.isoformat() if o.created_at else None,
                'total': float(o.total or 0),
                'status': o.status
            } for o in orders],
            'export_date': datetime.now().isoformat()
        }

        return export_data

    def anonymize_customer(self, customer_id: int, reason: str, performed_by: int = None) -> bool:
        """Anonymize customer account (GDPR Right to be Forgotten)"""
        try:
            customer = Customer.query.get(customer_id)
            if not customer:
                return False

            # Use comprehensive GDPR anonymization procedure
            # This handles validation, audit logging, order preservation, etc.
            anonymization_result = customer.anonymize(
                performed_by=performed_by,
                reason=reason
            )
            
            # Validate the stored procedure result
            if isinstance(anonymization_result, dict):
                return anonymization_result.get('success', False)
            else:
                # If result is not a dict, assume failure
                return False
                
        except Exception as e:
            print(f"Error anonymizing customer: {e}")
            return False

    def delete_customer(self, customer_id: int) -> bool:
        """Delete customer account completely"""
        try:
            customer = Customer.query.get(customer_id)
            if not customer:
                return False

            # Check if customer has orders
            order_count = Order.query.filter_by(customer_id=customer_id).count()
            if order_count > 0:
                # Can't delete customer with orders, anonymize instead
                return self.anonymize_customer(customer_id, "Account deletion requested")

            # Delete addresses
            CustomerAddress.query.filter_by(customer_id=customer_id).delete()

            # Delete customer
            db.session.delete(customer)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting customer: {e}")
            return False

    def get_consent_history(self, customer_id: int) -> List[Dict]:
        """Get GDPR consent change history (placeholder)"""
        # Would need consent_log table in production
        return [{
            'timestamp': datetime.now().isoformat(),
            'type': 'gdpr_consent',
            'value': True,
            'ip_address': '127.0.0.1'
        }]

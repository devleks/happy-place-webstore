"""
Promotion Service
Handles promotion management, validation, and analytics
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import func, and_, or_, desc
from models.database_models import db, Order, Customer
from models.extended_models import Promotion, OrderPromotion
from decimal import Decimal


class PromotionService:
    """Service for managing promotions and discount codes"""

    def get_promotion_list(self, filters: Dict = None) -> List[Dict]:
        """
        Get list of promotions with optional filters

        Args:
            filters: Dict with status ('active', 'expired', 'upcoming'),
                    search, discount_type, applies_to

        Returns:
            List of promotions
        """
        filters = filters or {}

        # Base query
        query = Promotion.query

        # Apply filters
        if filters.get('status'):
            now = datetime.utcnow()
            if filters['status'] == 'active':
                query = query.filter(
                    and_(
                        Promotion.is_active.is_(True),
                        Promotion.start_date <= now,
                        Promotion.end_date >= now
                    )
                )
            elif filters['status'] == 'expired':
                query = query.filter(Promotion.end_date < now)
            elif filters['status'] == 'upcoming':
                query = query.filter(Promotion.start_date > now)
            elif filters['status'] == 'inactive':
                query = query.filter(Promotion.is_active.is_(False))

        if filters.get('search'):
            search_term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    Promotion.code.ilike(search_term),
                    Promotion.name.ilike(search_term)
                )
            )

        if filters.get('discount_type'):
            query = query.filter(Promotion.discount_type == filters['discount_type'])

        if filters.get('applies_to'):
            query = query.filter(Promotion.applies_to == filters['applies_to'])

        # Order by most recent first
        query = query.order_by(desc(Promotion.created_at))

        promotions = query.all()

        return [promo.to_dict() for promo in promotions]

    def get_promotion_details(self, promotion_id: int) -> Dict:
        """
        Get detailed promotion information including usage statistics

        Args:
            promotion_id: Promotion ID

        Returns:
            Promotion details dictionary
        """
        promotion = Promotion.query.get(promotion_id)
        if not promotion:
            return {'error': 'Promotion not found'}

        # Get usage statistics
        total_uses = OrderPromotion.query.filter_by(promotion_id=promotion_id).count()

        total_discount_given = db.session.query(
            func.coalesce(func.sum(OrderPromotion.discount_amount), 0)
        ).filter(OrderPromotion.promotion_id == promotion_id).scalar() or Decimal(0)

        # Get recent uses
        recent_uses = OrderPromotion.query\
            .filter_by(promotion_id=promotion_id)\
            .order_by(desc(OrderPromotion.applied_at))\
            .limit(10)\
            .all()

        recent_usage = []
        for usage in recent_uses:
            order = usage.order
            customer = order.customer if order else None
            recent_usage.append({
                'order_id': usage.order_id,
                'customer_name': f"{customer.first_name} {customer.last_name}" if customer else 'Unknown',
                'discount_amount': float(usage.discount_amount),
                'applied_at': usage.applied_at.isoformat() if usage.applied_at else None
            })

        promo_dict = promotion.to_dict()
        promo_dict.update({
            'statistics': {
                'total_uses': total_uses,
                'total_discount_given': float(total_discount_given),
                'average_discount': float(total_discount_given / total_uses) if total_uses > 0 else 0,
                'remaining_uses': (promotion.usage_limit - promotion.current_usage_count) if promotion.usage_limit else None
            },
            'recent_usage': recent_usage
        })

        return promo_dict

    def create_promotion(self, data: Dict, created_by: int = None) -> Dict:
        """
        Create a new promotion

        Args:
            data: Promotion data (code, name, discount_type, discount_value, etc.)
            created_by: Employee ID creating the promotion

        Returns:
            Result dictionary with promotion data or error
        """
        try:
            # Validate required fields
            required_fields = ['code', 'name', 'discount_type', 'discount_value', 'start_date', 'end_date']
            for field in required_fields:
                if field not in data:
                    return {'success': False, 'error': f'Missing required field: {field}'}

            # Check if code already exists
            existing = Promotion.query.filter_by(code=data['code']).first()
            if existing:
                return {'success': False, 'error': 'Promotion code already exists'}

            # Parse dates
            try:
                start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return {'success': False, 'error': 'Invalid date format'}

            # Validate dates
            if start_date >= end_date:
                return {'success': False, 'error': 'End date must be after start date'}

            # Create promotion
            promotion = Promotion(
                code=data['code'].upper(),
                name=data['name'],
                description=data.get('description'),
                discount_type=data['discount_type'],
                discount_value=Decimal(str(data['discount_value'])),
                minimum_order_amount=Decimal(str(data['minimum_order_amount'])) if data.get('minimum_order_amount') else None,
                maximum_discount_amount=Decimal(str(data['maximum_discount_amount'])) if data.get('maximum_discount_amount') else None,
                applies_to=data.get('applies_to', 'all'),
                category_id=data.get('category_id'),
                product_id=data.get('product_id'),
                usage_limit=data.get('usage_limit'),
                usage_per_customer=data.get('usage_per_customer', 1),
                start_date=start_date,
                end_date=end_date,
                is_active=data.get('is_active', True)
            )

            db.session.add(promotion)
            db.session.commit()

            return {
                'success': True,
                'promotion': promotion.to_dict()
            }

        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def update_promotion(self, promotion_id: int, data: Dict) -> Dict:
        """
        Update existing promotion

        Args:
            promotion_id: Promotion ID
            data: Updated promotion data

        Returns:
            Result dictionary
        """
        try:
            promotion = Promotion.query.get(promotion_id)
            if not promotion:
                return {'success': False, 'error': 'Promotion not found'}

            # Update allowed fields
            if 'name' in data:
                promotion.name = data['name']
            if 'description' in data:
                promotion.description = data['description']
            if 'discount_value' in data:
                promotion.discount_value = Decimal(str(data['discount_value']))
            if 'minimum_order_amount' in data:
                promotion.minimum_order_amount = Decimal(str(data['minimum_order_amount'])) if data['minimum_order_amount'] else None
            if 'maximum_discount_amount' in data:
                promotion.maximum_discount_amount = Decimal(str(data['maximum_discount_amount'])) if data['maximum_discount_amount'] else None
            if 'usage_limit' in data:
                promotion.usage_limit = data['usage_limit']
            if 'usage_per_customer' in data:
                promotion.usage_per_customer = data['usage_per_customer']
            if 'start_date' in data:
                promotion.start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
            if 'end_date' in data:
                promotion.end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
            if 'is_active' in data:
                promotion.is_active = data['is_active']

            promotion.updated_at = datetime.utcnow()
            db.session.commit()

            return {
                'success': True,
                'promotion': promotion.to_dict()
            }

        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def delete_promotion(self, promotion_id: int) -> bool:
        """
        Delete a promotion (soft delete by deactivating)

        Args:
            promotion_id: Promotion ID

        Returns:
            Success boolean
        """
        try:
            promotion = Promotion.query.get(promotion_id)
            if not promotion:
                return False

            promotion.is_active = False
            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            print(f"Error deleting promotion: {e}")
            return False

    def enable_promotion(self, promotion_id: int) -> bool:
        """
        Enable a promotion

        Args:
            promotion_id: Promotion ID

        Returns:
            Success boolean
        """
        try:
            promotion = Promotion.query.get(promotion_id)
            if not promotion:
                return False

            promotion.is_active = True
            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            print(f"Error enabling promotion: {e}")
            return False

    def disable_promotion(self, promotion_id: int) -> bool:
        """
        Disable a promotion

        Args:
            promotion_id: Promotion ID

        Returns:
            Success boolean
        """
        try:
            promotion = Promotion.query.get(promotion_id)
            if not promotion:
                return False

            promotion.is_active = False
            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            print(f"Error disabling promotion: {e}")
            return False

    def validate_promotion(self, code: str, order_total: Decimal, customer_id: int) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Validate promotion code for use

        Args:
            code: Promotion code
            order_total: Current order total
            customer_id: Customer ID

        Returns:
            Tuple of (is_valid, promotion_dict, error_message)
        """
        promotion = Promotion.query.filter_by(code=code.upper()).first()

        if not promotion:
            return False, None, "Invalid promotion code"

        # Check if promotion is valid
        can_use, reason = promotion.can_use(customer_id, order_total)

        if not can_use:
            return False, None, reason

        # Calculate discount
        discount_amount = promotion.calculate_discount(order_total)

        return True, {
            'promotion_id': promotion.id,
            'code': promotion.code,
            'name': promotion.name,
            'discount_type': promotion.discount_type,
            'discount_amount': float(discount_amount)
        }, None

    def apply_promotion(self, promotion_id: int, order_id: int = None,
                       pos_transaction_id: int = None, customer_id: int = None,
                       discount_amount: Decimal = None) -> Dict:
        """
        Apply promotion to an order or POS transaction

        Args:
            promotion_id: Promotion ID
            order_id: Order ID (for online orders)
            pos_transaction_id: POS transaction ID (for in-store sales)
            customer_id: Customer ID
            discount_amount: Actual discount amount applied

        Returns:
            Result dictionary
        """
        try:
            promotion = Promotion.query.get(promotion_id)
            if not promotion:
                return {'success': False, 'error': 'Promotion not found'}

            # For online orders, create OrderPromotion record
            if order_id:
                order_promotion = OrderPromotion(
                    order_id=order_id,
                    promotion_id=promotion_id,
                    promotion_code=promotion.code,
                    discount_amount=discount_amount or Decimal(0),
                    applied_at=datetime.utcnow()
                )
                db.session.add(order_promotion)

            # Increment usage count
            promotion.current_usage_count += 1

            db.session.commit()

            return {
                'success': True,
                'promotion': promotion.to_dict()
            }

        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def get_promotion_analytics(self, promotion_id: int) -> Dict:
        """
        Get detailed analytics for a promotion

        Args:
            promotion_id: Promotion ID

        Returns:
            Analytics dictionary
        """
        promotion = Promotion.query.get(promotion_id)
        if not promotion:
            return {'error': 'Promotion not found'}

        # Total usage and discount given
        usage_stats = db.session.query(
            func.count(OrderPromotion.id).label('total_uses'),
            func.coalesce(func.sum(OrderPromotion.discount_amount), 0).label('total_discount'),
            func.coalesce(func.avg(OrderPromotion.discount_amount), 0).label('avg_discount'),
            func.min(OrderPromotion.discount_amount).label('min_discount'),
            func.max(OrderPromotion.discount_amount).label('max_discount')
        ).filter(OrderPromotion.promotion_id == promotion_id).first()

        # Usage by day (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        daily_usage = db.session.query(
            func.date(OrderPromotion.applied_at).label('date'),
            func.count(OrderPromotion.id).label('uses'),
            func.sum(OrderPromotion.discount_amount).label('discount')
        ).filter(
            and_(
                OrderPromotion.promotion_id == promotion_id,
                OrderPromotion.applied_at >= thirty_days_ago
            )
        ).group_by(func.date(OrderPromotion.applied_at))\
         .order_by(func.date(OrderPromotion.applied_at))\
         .all()

        daily_data = []
        for day in daily_usage:
            daily_data.append({
                'date': day.date.isoformat(),
                'uses': day.uses,
                'discount_given': float(day.discount or 0)
            })

        # Top customers using this promotion
        top_customers = db.session.query(
            Customer.id,
            Customer.first_name_encrypted,
            Customer.last_name_encrypted,
            func.count(OrderPromotion.id).label('uses'),
            func.sum(OrderPromotion.discount_amount).label('total_discount')
        ).join(Order, OrderPromotion.order_id == Order.id)\
         .join(Customer, Order.customer_id == Customer.id)\
         .filter(OrderPromotion.promotion_id == promotion_id)\
         .group_by(Customer.id, Customer.first_name_encrypted, Customer.last_name_encrypted)\
         .order_by(desc('uses'))\
         .limit(10)\
         .all()

        top_customers_list = []
        for customer in top_customers:
            top_customers_list.append({
                'customer_id': customer.id,
                'customer_name': f"{customer.first_name_encrypted} {customer.last_name_encrypted}",
                'uses': customer.uses,
                'total_discount': float(customer.total_discount or 0)
            })

        return {
            'promotion': promotion.to_dict(),
            'overall_stats': {
                'total_uses': usage_stats.total_uses,
                'total_discount_given': float(usage_stats.total_discount),
                'average_discount': float(usage_stats.avg_discount),
                'min_discount': float(usage_stats.min_discount or 0),
                'max_discount': float(usage_stats.max_discount or 0),
                'remaining_uses': (promotion.usage_limit - promotion.current_usage_count) if promotion.usage_limit else None
            },
            'daily_usage': daily_data,
            'top_customers': top_customers_list
        }

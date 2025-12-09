"""
Shipping Calculation Service
Handles shipping cost calculation for Happy Place Boutique.

Business Rules:
- Nairobi: Free shipping
- Upcountry: KSh 300 base + KSh 50 per kg
"""

from typing import Dict, List, Optional
from extensions import db


class ShippingService:
    """Service for calculating shipping costs"""

    # Shipping rates (in KES)
    NAIROBI_SHIPPING_COST = 0.00
    UPCOUNTRY_BASE_COST = 300.00
    UPCOUNTRY_PER_KG_COST = 50.00

    # Cities considered as Nairobi (case-insensitive)
    NAIROBI_VARIATIONS = [
        'nairobi',
        'nai',
        'nairobi county',
        'nairobi city'
    ]

    @classmethod
    def is_nairobi(cls, city: str) -> bool:
        """
        Check if the city is Nairobi (free shipping).

        Args:
            city: City name from shipping address

        Returns:
            bool: True if Nairobi, False otherwise
        """
        if not city:
            return False

        city_lower = city.strip().lower()
        return city_lower in cls.NAIROBI_VARIATIONS

    @classmethod
    def calculate_shipping(cls, city: str, total_weight_kg: float) -> Dict:
        """
        Calculate shipping cost based on city and weight.

        Args:
            city: City name from shipping address
            total_weight_kg: Total weight of items in kg

        Returns:
            dict: {
                'cost': float,
                'is_nairobi': bool,
                'description': str
            }
        """
        is_nairobi = cls.is_nairobi(city)

        if is_nairobi:
            return {
                'cost': cls.NAIROBI_SHIPPING_COST,
                'is_nairobi': True,
                'description': 'Free shipping within Nairobi'
            }
        else:
            # Upcountry: KSh 300 + (weight_kg * KSh 50)
            cost = cls.UPCOUNTRY_BASE_COST + (total_weight_kg * cls.UPCOUNTRY_PER_KG_COST)
            return {
                'cost': round(cost, 2),
                'is_nairobi': False,
                'description': f'Upcountry shipping: KSh {cls.UPCOUNTRY_BASE_COST} base + KSh {cls.UPCOUNTRY_PER_KG_COST}/kg ({total_weight_kg}kg)'
            }

    @classmethod
    def get_cart_weight(cls, cart_items: List) -> float:
        """
        Calculate total weight from cart items.

        Args:
            cart_items: List of CartItem objects with variant.product.weight

        Returns:
            float: Total weight in kg
        """
        total_weight = 0.0

        for item in cart_items:
            if item.variant and item.variant.product:
                product_weight = float(item.variant.product.weight or 0.0)
                total_weight += product_weight * float(item.quantity)

        return round(total_weight, 2)

    @classmethod
    def calculate_shipping_for_cart(cls, cart_items: List, city: str) -> Dict:
        """
        Calculate shipping for cart items.

        Args:
            cart_items: List of CartItem objects
            city: Destination city

        Returns:
            dict: Shipping calculation result
        """
        total_weight = cls.get_cart_weight(cart_items)
        return cls.calculate_shipping(city, total_weight)

    @staticmethod
    def calculate_shipping_sp(city: str, total_weight_kg: float) -> Dict:
        """
        Calculate shipping cost using stored procedure.

        More secure than Python calculation as business rules are enforced
        at the database level.

        Args:
            city: City name from shipping address
            total_weight_kg: Total weight of items in kg

        Returns:
            dict: {
                'cost': float,
                'is_nairobi': bool,
                'description': str,
                'city': str,
                'weight_kg': float
            }

        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If calculation fails

        Example:
            result = ShippingService.calculate_shipping_sp('Nairobi', 2.5)
            # Returns: {'cost': 0.0, 'is_nairobi': True, ...}
        """
        try:
            result = db.session.execute(
                db.text("""
                    SELECT * FROM sp_calculate_shipping(:city, :weight)
                """),
                {
                    'city': city,
                    'weight': total_weight_kg
                }
            )

            row = result.fetchone()
            if not row:
                raise RuntimeError('Shipping calculation procedure did not return result')

            shipping_data = row[0]  # JSONB result

            return {
                'cost': float(shipping_data.get('cost', 0)),
                'is_nairobi': shipping_data.get('is_nairobi', False),
                'description': shipping_data.get('description', ''),
                'city': shipping_data.get('city', ''),
                'weight_kg': float(shipping_data.get('weight_kg', 0))
            }

        except Exception as e:
            error_msg = str(e)

            if 'required' in error_msg.lower():
                raise ValueError(error_msg)

            raise RuntimeError(f'Shipping calculation failed: {error_msg}')

    @staticmethod
    def calculate_shipping_for_customer_cart(customer_id: int, city: str) -> Dict:
        """
        Calculate shipping for a customer's cart using stored procedure.

        This method uses the database to calculate cart weight and shipping cost,
        ensuring consistency and security.

        Args:
            customer_id: Customer ID
            city: Destination city

        Returns:
            dict: Shipping calculation result

        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If calculation fails

        Example:
            result = ShippingService.calculate_shipping_for_customer_cart(
                customer_id=123,
                city='Mombasa'
            )
        """
        try:
            result = db.session.execute(
                db.text("""
                    SELECT * FROM sp_calculate_shipping_for_cart(:customer_id, :city)
                """),
                {
                    'customer_id': customer_id,
                    'city': city
                }
            )

            row = result.fetchone()
            if not row:
                raise RuntimeError('Cart shipping calculation procedure did not return result')

            shipping_data = row[0]  # JSONB result

            return {
                'cost': float(shipping_data.get('cost', 0)),
                'is_nairobi': shipping_data.get('is_nairobi', False),
                'description': shipping_data.get('description', ''),
                'city': shipping_data.get('city', ''),
                'weight_kg': float(shipping_data.get('weight_kg', 0))
            }

        except Exception as e:
            error_msg = str(e)

            if 'required' in error_msg.lower():
                raise ValueError(error_msg)

            raise RuntimeError(f'Cart shipping calculation failed: {error_msg}')

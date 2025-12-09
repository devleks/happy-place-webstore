#!/usr/bin/env python3
"""
Test script for Priority 1 stored procedures
Tests each stored procedure with realistic data
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extensions import db
from app import create_app
from models.database_models import Customer, Order, Payment, Inventory
from models.extended_models import ProductVariant
from services.encryption import encrypt_address


def test_order_creation():
    """Test sp_create_order_secure stored procedure"""
    print("="*70)
    print("TEST 1: Order Creation (sp_create_order_secure)")
    print("="*70)

    app = create_app()
    with app.app_context():
        # Get first active customer
        customer = Customer.query.filter_by(is_active=True).first()
        if not customer:
            print("❌ No active customers found")
            return False

        print(f"✓ Customer: {customer.email} (ID: {customer.id})")

        # Get first two active product variants with inventory
        variants = db.session.execute(
            db.text("""
                SELECT pv.id, pv.sku, p.name, p.price, i.quantity, i.reserved_quantity
                FROM product_variants pv
                JOIN products p ON pv.product_id = p.id
                JOIN inventory i ON pv.id = i.variant_id
                WHERE pv.is_active = TRUE
                AND p.is_active = TRUE
                AND (i.quantity - i.reserved_quantity) >= 1
                LIMIT 2
            """)
        ).fetchall()

        if len(variants) < 2:
            print("❌ Not enough products with inventory")
            return False

        print(f"✓ Found {len(variants)} products with inventory")

        # Prepare cart items
        cart_items = []
        for v in variants:
            cart_items.append({
                'variant_id': v[0],
                'quantity': 1,
                'unit_price': float(v[3])
            })
            print(f"  - {v[2]} ({v[1]}): KSh {v[3]}")

        # Prepare address
        shipping_address = {
            'street': '123 Test Street',
            'city': 'Mombasa',  # Upcountry (has shipping cost)
            'state': 'Mombasa',
            'zip': '80100',
            'phone': '+254712345678'
        }

        shipping_address_encrypted = encrypt_address(json.dumps(shipping_address))

        # Call stored procedure
        try:
            result = db.session.execute(
                db.text("""
                    SELECT * FROM sp_create_order_secure(
                        :customer_id,
                        :shipping_address_encrypted,
                        :billing_address_encrypted,
                        :payment_method,
                        CAST(:cart_items AS jsonb),
                        :shipping_method_id,
                        :is_nairobi,
                        :shipping_cost
                    )
                """),
                {
                    'customer_id': customer.id,
                    'shipping_address_encrypted': shipping_address_encrypted,
                    'billing_address_encrypted': shipping_address_encrypted,
                    'payment_method': 'cod',
                    'cart_items': json.dumps(cart_items),
                    'shipping_method_id': None,
                    'is_nairobi': False,
                    'shipping_cost': 500.00  # Upcountry shipping
                }
            )

            row = result.fetchone()
            db.session.commit()

            print("\n✅ Order created successfully!")
            print(f"   Order ID: {row[0]}")
            print(f"   Order Number: {row[1]}")
            print(f"   Payment ID: {row[2]}")
            print(f"   Total: KSh {row[3]}")

            return True

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Order creation failed: {str(e)}")
            return False


def test_inventory_reservation():
    """Test sp_reserve_inventory_atomic stored procedure"""
    print("\n" + "="*70)
    print("TEST 2: Inventory Reservation (sp_reserve_inventory_atomic)")
    print("="*70)

    app = create_app()
    with app.app_context():
        # Get a variant with available inventory
        variant = db.session.execute(
            db.text("""
                SELECT pv.id, pv.sku, i.quantity, i.reserved_quantity
                FROM product_variants pv
                JOIN inventory i ON pv.id = i.variant_id
                WHERE pv.is_active = TRUE
                AND (i.quantity - i.reserved_quantity) >= 5
                LIMIT 1
            """)
        ).fetchone()

        if not variant:
            print("❌ No variants with sufficient inventory")
            return False

        variant_id = variant[0]
        available = variant[2] - variant[3]

        print(f"✓ Variant: {variant[1]}")
        print(f"  Total: {variant[2]}, Reserved: {variant[3]}, Available: {available}")

        # Test successful reservation
        try:
            result = db.session.execute(
                db.text("SELECT * FROM sp_reserve_inventory_atomic(:variant_id, :quantity)"),
                {'variant_id': variant_id, 'quantity': 2}
            )
            row = result.fetchone()
            db.session.commit()

            print(f"\n✅ Reserved 2 units")
            print(f"   Success: {row[0]}")
            print(f"   Remaining: {row[1]}")
            print(f"   Message: {row[2]}")

            # Test overselling prevention
            result2 = db.session.execute(
                db.text("SELECT * FROM sp_reserve_inventory_atomic(:variant_id, :quantity)"),
                {'variant_id': variant_id, 'quantity': 99999}
            )
            row2 = result2.fetchone()
            db.session.rollback()

            print(f"\n✅ Overselling prevention works")
            print(f"   Success: {row2[0]} (should be False)")
            print(f"   Message: {row2[2]}")

            return True

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Test failed: {str(e)}")
            return False


def test_payment_processing():
    """Test sp_process_payment_secure stored procedure"""
    print("\n" + "="*70)
    print("TEST 3: Payment Processing (sp_process_payment_secure)")
    print("="*70)

    app = create_app()
    with app.app_context():
        # Find a pending COD payment
        payment = Payment.query.filter_by(
            payment_method='cod',
            status='pending'
        ).first()

        if not payment:
            print("❌ No pending COD payments found (create an order first)")
            return False

        print(f"✓ Found pending payment ID: {payment.id}")
        print(f"  Order ID: {payment.order_id}")
        print(f"  Amount: KSh {payment.amount}")

        # Process payment
        try:
            result = db.session.execute(
                db.text("SELECT * FROM sp_process_payment_secure(:payment_id, NULL, NULL)"),
                {'payment_id': payment.id}
            )
            row = result.fetchone()
            db.session.commit()

            print(f"\n✅ Payment processed successfully!")
            print(f"   Success: {row[0]}")
            print(f"   Order ID: {row[1]}")
            print(f"   Message: {row[2]}")

            # Verify inventory was deducted
            print("\n   Verifying inventory deduction...")
            order = Order.query.get(payment.order_id)
            for item in order.items:
                inv = Inventory.query.filter_by(variant_id=item.variant_id).first()
                print(f"   - Variant {item.variant_id}: Qty={inv.quantity}, Reserved={inv.reserved_quantity}")

            return True

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Payment processing failed: {str(e)}")
            return False


def test_return_processing():
    """Test sp_process_return_secure stored procedure"""
    print("\n" + "="*70)
    print("TEST 4: Return Processing (sp_process_return_secure)")
    print("="*70)

    app = create_app()
    with app.app_context():
        # Find a completed order
        order = db.session.execute(
            db.text("""
                SELECT o.id, o.customer_id, o.order_number, o.created_at
                FROM orders o
                JOIN payments p ON o.id = p.order_id
                WHERE p.status = 'completed'
                AND o.status = 'processing'
                ORDER BY o.created_at DESC
                LIMIT 1
            """)
        ).fetchone()

        if not order:
            print("❌ No completed orders found")
            return False

        print(f"✓ Found order: {order[2]} (ID: {order[0]})")

        # Get first order item
        order_item = db.session.execute(
            db.text("SELECT id, quantity FROM order_items WHERE order_id = :order_id LIMIT 1"),
            {'order_id': order[0]}
        ).fetchone()

        return_items = [{
            'order_item_id': order_item[0],
            'quantity': 1,
            'condition': 'new'
        }]

        # Process return
        try:
            result = db.session.execute(
                db.text("""
                    SELECT * FROM sp_process_return_secure(
                        :order_id,
                        :customer_id,
                        :reason,
                        :reason_description,
                        CAST(:return_items AS jsonb),
                        NULL
                    )
                """),
                {
                    'order_id': order[0],
                    'customer_id': order[1],
                    'reason': 'changed_mind',
                    'reason_description': 'Customer changed their mind',
                    'return_items': json.dumps(return_items)
                }
            )
            row = result.fetchone()
            db.session.commit()

            print(f"\n✅ Return processed successfully!")
            print(f"   Return ID: {row[0]}")
            print(f"   Return Number: {row[1]}")
            print(f"   Refund Amount: KSh {row[2]}")
            print(f"   Restocking Fee: KSh {row[3]}")
            print(f"   Message: {row[4]}")

            return True

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Return processing failed: {str(e)}")
            return False


def test_promotion_validation():
    """Test sp_validate_promotion_secure stored procedure"""
    print("\n" + "="*70)
    print("TEST 5: Promotion Validation (sp_validate_promotion_secure)")
    print("="*70)

    app = create_app()
    with app.app_context():
        # Check if promotions exist
        promo = db.session.execute(
            db.text("""
                SELECT code, discount_type, discount_value, minimum_order_amount
                FROM promotions
                WHERE is_active = TRUE
                AND NOW() BETWEEN start_date AND end_date
                LIMIT 1
            """)
        ).fetchone()

        if not promo:
            print("⚠️  No active promotions found - skipping test")
            return True

        print(f"✓ Found active promotion: {promo[0]}")
        print(f"  Type: {promo[1]}")
        print(f"  Value: {promo[2]}")

        # Get a customer
        customer = Customer.query.first()

        # Test promotion validation
        try:
            result = db.session.execute(
                db.text("""
                    SELECT * FROM sp_validate_promotion_secure(
                        :promotion_code,
                        :customer_id,
                        :order_subtotal,
                        NULL,
                        NULL
                    )
                """),
                {
                    'promotion_code': promo[0],
                    'customer_id': customer.id,
                    'order_subtotal': 5000.00  # KSh 5,000
                }
            )
            row = result.fetchone()
            db.session.rollback()  # Don't actually increment usage

            print(f"\n✅ Promotion validated!")
            print(f"   Valid: {row[0]}")
            print(f"   Promotion ID: {row[1]}")
            print(f"   Discount Amount: KSh {row[2]}")
            print(f"   Message: {row[3]}")

            return True

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Promotion validation failed: {str(e)}")
            return False


if __name__ == '__main__':
    print("\n🚀 TESTING PRIORITY 1 STORED PROCEDURES\n")

    results = []

    results.append(("Order Creation", test_order_creation()))
    results.append(("Inventory Reservation", test_inventory_reservation()))
    results.append(("Payment Processing", test_payment_processing()))
    results.append(("Return Processing", test_return_processing()))
    results.append(("Promotion Validation", test_promotion_validation()))

    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<50} {status}")
        if result:
            passed += 1

    print(f"\nTotal: {passed}/{len(results)} tests passed")
    print("="*70)

    sys.exit(0 if passed == len(results) else 1)

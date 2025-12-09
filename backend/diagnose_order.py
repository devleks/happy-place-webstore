#!/usr/bin/env python3
"""
Diagnostic script to check order creation issues
"""

from extensions import db
from models import Cart, CartItem, Customer, ProductVariant, Product
from app import create_app

def diagnose():
    app = create_app()

    with app.app_context():
        print("=== Order Creation Diagnostics ===\n")

        # Check customers
        customers = Customer.query.all()
        print(f"✓ Total customers: {len(customers)}")
        if customers:
            customer = customers[0]
            print(f"  - Sample customer: {customer.email} (ID: {customer.id})\n")

            # Check cart for this customer
            cart = Cart.query.filter_by(customer_id=customer.id).first()
            if cart:
                print(f"✓ Cart found for customer {customer.id}")
                cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
                print(f"  - Cart has {len(cart_items)} items\n")

                if cart_items:
                    for i, item in enumerate(cart_items, 1):
                        print(f"  Item {i}:")
                        print(f"    - Cart Item ID: {item.id}")
                        print(f"    - Variant ID: {item.variant_id}")
                        print(f"    - Quantity: {item.quantity}")

                        # Check variant relationship
                        if hasattr(item, 'variant'):
                            variant = item.variant
                            print(f"    - Variant loaded: {variant is not None}")
                            if variant:
                                print(f"      - Variant size/color: {variant.size}/{variant.color}")
                                print(f"      - Product ID: {variant.product_id}")

                                # Check product relationship
                                if hasattr(variant, 'product'):
                                    product = variant.product
                                    print(f"      - Product loaded: {product is not None}")
                                    if product:
                                        print(f"        - Product name: {product.name}")
                                        print(f"        - Product active: {product.is_active}")
                                        print(f"        - Product price: ${product.price}")
                                else:
                                    print(f"      ❌ Variant doesn't have product relationship!")
                        else:
                            print(f"    ❌ CartItem doesn't have variant relationship!")
                        print()
                else:
                    print("  ❌ Cart is empty\n")
            else:
                print(f"❌ No cart found for customer {customer.id}\n")
        else:
            print("❌ No customers found\n")

        # Check variants
        variants = ProductVariant.query.all()
        print(f"✓ Total product variants: {len(variants)}\n")

        # Check products
        products = Product.query.all()
        print(f"✓ Total products: {len(products)}\n")

if __name__ == '__main__':
    diagnose()

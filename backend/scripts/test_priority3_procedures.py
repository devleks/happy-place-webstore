"""
Test Script for Priority 3 Stored Procedures
Tests shipping calculation and product creation procedures.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from extensions import db
from app import create_app
from services.shipping_service import ShippingService
from services.product_service import ProductService

# Create app instance
app = create_app()


def print_header(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_result(test_name, passed, details=""):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {test_name}")
    if details:
        print(f"        {details}")


def test_shipping_calculation():
    """Test shipping calculation stored procedures"""
    print_header("TEST 1: Shipping Calculation")

    tests_passed = 0
    tests_total = 0

    with app.app_context():
        # Test 1.1: Nairobi shipping (free)
        tests_total += 1
        try:
            result = ShippingService.calculate_shipping_sp('Nairobi', 5.0)
            passed = (
                result['cost'] == 0.0 and
                result['is_nairobi'] is True and
                'Free shipping' in result['description']
            )
            print_result(
                "Nairobi shipping (free)",
                passed,
                f"Cost: KSh {result['cost']}, Description: {result['description']}"
            )
            if passed:
                tests_passed += 1
        except Exception as e:
            print_result("Nairobi shipping (free)", False, str(e))

        # Test 1.2: Upcountry shipping calculation
        tests_total += 1
        try:
            result = ShippingService.calculate_shipping_sp('Mombasa', 3.0)
            expected_cost = 300.0 + (3.0 * 50.0)  # 450.0
            passed = (
                result['cost'] == expected_cost and
                result['is_nairobi'] is False and
                result['weight_kg'] == 3.0
            )
            print_result(
                "Upcountry shipping (Mombasa, 3kg)",
                passed,
                f"Cost: KSh {result['cost']} (expected {expected_cost})"
            )
            if passed:
                tests_passed += 1
        except Exception as e:
            print_result("Upcountry shipping", False, str(e))

        # Test 1.3: Case-insensitive city matching
        tests_total += 1
        try:
            result = ShippingService.calculate_shipping_sp('NAIROBI', 2.0)
            passed = result['is_nairobi'] is True and result['cost'] == 0.0
            print_result(
                "Case-insensitive city (NAIROBI)",
                passed,
                f"Is Nairobi: {result['is_nairobi']}"
            )
            if passed:
                tests_passed += 1
        except Exception as e:
            print_result("Case-insensitive city", False, str(e))

        # Test 1.4: City variations
        tests_total += 1
        try:
            result = ShippingService.calculate_shipping_sp('nai', 1.0)
            passed = result['is_nairobi'] is True
            print_result(
                "City variation ('nai' = Nairobi)",
                passed,
                f"Is Nairobi: {result['is_nairobi']}"
            )
            if passed:
                tests_passed += 1
        except Exception as e:
            print_result("City variation", False, str(e))

        # Test 1.5: Zero weight
        tests_total += 1
        try:
            result = ShippingService.calculate_shipping_sp('Kisumu', 0.0)
            expected_cost = 300.0  # Base cost only
            passed = result['cost'] == expected_cost
            print_result(
                "Zero weight (base cost only)",
                passed,
                f"Cost: KSh {result['cost']}"
            )
            if passed:
                tests_passed += 1
        except Exception as e:
            print_result("Zero weight", False, str(e))

        # Test 1.6: Invalid inputs (should raise error)
        tests_total += 1
        try:
            result = ShippingService.calculate_shipping_sp('', 5.0)
            print_result("Empty city validation", False, "Should have raised error")
        except ValueError as e:
            print_result("Empty city validation", True, "Correctly raised ValueError")
            tests_passed += 1
        except Exception as e:
            print_result("Empty city validation", False, f"Wrong error type: {e}")

        print(f"\n📊 Shipping Tests: {tests_passed}/{tests_total} passed")
        return tests_passed, tests_total


def test_product_creation():
    """Test product creation with variants stored procedure"""
    print_header("TEST 2: Product Creation with Variants")

    tests_passed = 0
    tests_total = 0

    with app.app_context():
        # Test 2.1: Create product with variants
        tests_total += 1
        try:
            result = ProductService.create_product_with_variants(
                name='Test Floral Dress',
                slug='test-floral-dress-001',
                price=2500.00,
                category_id=1,  # Assuming category 1 exists
                sku='TEST-FD-001',
                created_by=1,  # Assuming employee 1 exists
                description='Beautiful floral dress for testing',
                weight=0.5,
                is_active=True,
                is_featured=False,
                is_clearance=False,
                variants=[
                    {
                        'size': 'S',
                        'color': 'Blue',
                        'sku': 'TEST-FD-001-S-BLU',
                        'initial_quantity': 10
                    },
                    {
                        'size': 'M',
                        'color': 'Blue',
                        'sku': 'TEST-FD-001-M-BLU',
                        'initial_quantity': 15
                    },
                    {
                        'size': 'L',
                        'color': 'Red',
                        'sku': 'TEST-FD-001-L-RED',
                        'initial_quantity': 5
                    }
                ]
            )

            passed = (
                result['success'] is True and
                result['variants_created'] == 3 and
                result['total_inventory'] == 30 and
                result['product_id'] is not None
            )

            print_result(
                "Create product with 3 variants",
                passed,
                f"Product ID: {result.get('product_id')}, Variants: {result.get('variants_created')}, Inventory: {result.get('total_inventory')}"
            )

            if passed:
                tests_passed += 1
                # Store product_id for cleanup
                test_product_id = result['product_id']
        except Exception as e:
            print_result("Create product with variants", False, str(e))

        # Test 2.2: Duplicate slug validation
        tests_total += 1
        try:
            result = ProductService.create_product_with_variants(
                name='Duplicate Slug Test',
                slug='test-floral-dress-001',  # Same slug as above
                price=1000.00,
                category_id=1,
                sku='TEST-DUP-001',
                created_by=1
            )
            print_result("Duplicate slug validation", False, "Should have raised error")
        except ValueError as e:
            if 'already exists' in str(e).lower():
                print_result("Duplicate slug validation", True, "Correctly prevented duplicate")
                tests_passed += 1
            else:
                print_result("Duplicate slug validation", False, f"Wrong error: {e}")
        except Exception as e:
            print_result("Duplicate slug validation", False, f"Unexpected error: {e}")

        # Test 2.3: Missing required fields
        tests_total += 1
        try:
            result = ProductService.create_product_with_variants(
                name='',  # Empty name
                slug='test-empty-name',
                price=1000.00,
                category_id=1,
                sku='TEST-EMPTY-001',
                created_by=1
            )
            print_result("Empty name validation", False, "Should have raised error")
        except ValueError as e:
            if 'required' in str(e).lower():
                print_result("Empty name validation", True, "Correctly validated empty name")
                tests_passed += 1
            else:
                print_result("Empty name validation", False, f"Wrong error: {e}")
        except Exception as e:
            print_result("Empty name validation", False, f"Unexpected error: {e}")

        # Test 2.4: Sale price validation
        tests_total += 1
        try:
            result = ProductService.create_product_with_variants(
                name='Sale Price Test',
                slug='test-sale-price-001',
                price=1000.00,
                sale_price=1500.00,  # Sale price > regular price
                category_id=1,
                sku='TEST-SALE-001',
                created_by=1
            )
            print_result("Sale price validation", False, "Should have raised error")
        except ValueError as e:
            if 'sale price' in str(e).lower():
                print_result("Sale price validation", True, "Correctly validated sale price")
                tests_passed += 1
            else:
                print_result("Sale price validation", False, f"Wrong error: {e}")
        except Exception as e:
            print_result("Sale price validation", False, f"Unexpected error: {e}")

        # Test 2.5: Product without variants
        tests_total += 1
        try:
            result = ProductService.create_product_with_variants(
                name='No Variants Product',
                slug='test-no-variants-001',
                price=500.00,
                category_id=1,
                sku='TEST-NV-001',
                created_by=1,
                variants=None  # No variants
            )

            passed = (
                result['success'] is True and
                result['variants_created'] == 0 and
                result['product_id'] is not None
            )

            print_result(
                "Create product without variants",
                passed,
                f"Product ID: {result.get('product_id')}, Variants: {result.get('variants_created')}"
            )

            if passed:
                tests_passed += 1
        except Exception as e:
            print_result("Create product without variants", False, str(e))

        # Test 2.6: Duplicate variant SKU
        tests_total += 1
        try:
            result = ProductService.create_product_with_variants(
                name='Duplicate Variant SKU Test',
                slug='test-dup-variant-001',
                price=1000.00,
                category_id=1,
                sku='TEST-DUPV-001',
                created_by=1,
                variants=[
                    {
                        'size': 'S',
                        'color': 'Blue',
                        'sku': 'TEST-FD-001-S-BLU',  # Same as first test
                        'initial_quantity': 5
                    }
                ]
            )
            print_result("Duplicate variant SKU validation", False, "Should have raised error")
        except ValueError as e:
            if 'already exists' in str(e).lower():
                print_result("Duplicate variant SKU validation", True, "Correctly prevented duplicate")
                tests_passed += 1
            else:
                print_result("Duplicate variant SKU validation", False, f"Wrong error: {e}")
        except Exception as e:
            print_result("Duplicate variant SKU validation", False, f"Unexpected error: {e}")

    print(f"\n📊 Product Creation Tests: {tests_passed}/{tests_total} passed")
    return tests_passed, tests_total


def main():
    """Run all Priority 3 tests"""
    print("\n" + "🧪" * 40)
    print("PRIORITY 3 STORED PROCEDURES TEST SUITE")
    print("🧪" * 40)

    total_passed = 0
    total_tests = 0

    # Test shipping calculation
    passed, total = test_shipping_calculation()
    total_passed += passed
    total_tests += total

    # Test product creation
    passed, total = test_product_creation()
    total_passed += passed
    total_tests += total

    # Final summary
    print_header("FINAL RESULTS")
    percentage = (total_passed / total_tests * 100) if total_tests > 0 else 0
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_tests - total_passed}")
    print(f"Success Rate: {percentage:.1f}%")

    if total_passed == total_tests:
        print("\n✅ ALL TESTS PASSED! Priority 3 procedures are working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed. Review the output above.")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

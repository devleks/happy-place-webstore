"""
Test Script for Inventory Enhancements
Tests Phase 1 inventory management features.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from services.inventory_service import InventoryService

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


def test_available_inventory():
    """Test sp_get_available_inventory function"""
    print_header("TEST 1: Get Available Inventory")

    tests_passed = 0
    tests_total = 0

    with app.app_context():
        # Test 1.1: Get availability for online channel
        tests_total += 1
        try:
            # Assuming variant_id 1 exists
            available = InventoryService.get_available_inventory(1, 'online')
            passed = isinstance(available, int) and available >= 0
            print_result(
                "Get online availability",
                passed,
                f"Available: {available} units"
            )
            if passed:
                tests_passed += 1
        except Exception as e:
            print_result("Get online availability", False, str(e))

        # Test 1.2: Get availability for store channel
        tests_total += 1
        try:
            available = InventoryService.get_available_inventory(1, 'store')
            passed = isinstance(available, int) and available >= 0
            print_result(
                "Get store availability",
                passed,
                f"Available: {available} units"
            )
            if passed:
                tests_passed += 1
        except Exception as e:
            print_result("Get store availability", False, str(e))

    print(f"\n📊 Available Inventory Tests: {tests_passed}/{tests_total} passed")
    return tests_passed, tests_total


def test_inventory_deduction():
    """Test sp_deduct_inventory function"""
    print_header("TEST 2: Inventory Deduction with Logging")

    tests_passed = 0
    tests_total = 0

    with app.app_context():
        # Test 2.1: Deduct inventory (simulate online sale)
        tests_total += 1
        try:
            result = InventoryService.deduct_inventory(
                variant_id=1,
                quantity=1,
                channel='online',
                reference_type='order',
                reference_id=999,
                customer_id=1,
                notes='Test online sale'
            )

            passed = result.get('success') is True and result.get('movement_id') is not None
            print_result(
                "Deduct inventory (online sale)",
                passed,
                f"New quantity: {result.get('new_quantity')}, Movement ID: {result.get('movement_id')}"
            )
            if passed:
                tests_passed += 1
        except Exception as e:
            print_result("Deduct inventory", False, str(e))

    print(f"\n📊 Deduction Tests: {tests_passed}/{tests_total} passed")
    return tests_passed, tests_total


def test_inventory_addition():
    """Test sp_add_inventory function"""
    print_header("TEST 3: Inventory Addition with Logging")

    tests_passed = 0
    tests_total = 0

    with app.app_context():
        # Test 3.1: Add inventory (simulate restock)
        tests_total += 1
        try:
            result = InventoryService.add_inventory(
                variant_id=1,
                quantity=10,
                channel='admin',
                movement_type='restock',
                performed_by=None,
                notes='Test restock'
            )

            passed = result.get('success') is True and result.get('movement_id') is not None
            print_result(
                "Add inventory (restock)",
                passed,
                f"New quantity: {result.get('new_quantity')}, Added: {result.get('added')}"
            )
            if passed:
                tests_passed += 1
        except Exception as e:
            print_result("Add inventory", False, str(e))

    print(f"\n📊 Addition Tests: {tests_passed}/{tests_total} passed")
    return tests_passed, tests_total


def test_inventory_summary():
    """Test inventory summary view"""
    print_header("TEST 4: Inventory Summary")

    tests_passed = 0
    tests_total = 0

    with app.app_context():
        # Test 4.1: Get summary for variant
        tests_total += 1
        try:
            summary = InventoryService.get_inventory_summary(1)

            if summary:
                passed = all(key in summary for key in [
                    'total_quantity', 'online_available',
                    'store_available', 'stock_status'
                ])
                print_result(
                    "Get inventory summary",
                    passed,
                    f"Product: {summary.get('product_name')}, Stock: {summary.get('stock_status')}"
                )
                if passed:
                    tests_passed += 1
                    print(f"        Total: {summary.get('total_quantity')}")
                    print(f"        Online Available: {summary.get('online_available')}")
                    print(f"        Store Available: {summary.get('store_available')}")
                    print(f"        Display Units: {summary.get('store_display_units')}")
            else:
                print_result("Get inventory summary", False, "No summary returned")
        except Exception as e:
            print_result("Get inventory summary", False, str(e))

    print(f"\n📊 Summary Tests: {tests_passed}/{tests_total} passed")
    return tests_passed, tests_total


def test_movement_history():
    """Test movement history retrieval"""
    print_header("TEST 5: Movement History")

    tests_passed = 0
    tests_total = 0

    with app.app_context():
        # Test 5.1: Get recent movements
        tests_total += 1
        try:
            movements = InventoryService.get_movement_history(
                variant_id=1,
                days=30,
                limit=10
            )

            passed = isinstance(movements, list)
            print_result(
                "Get movement history",
                passed,
                f"Found {len(movements)} movements in last 30 days"
            )

            if passed and len(movements) > 0:
                print(f"        Latest movement: {movements[0].get('movement_type')} - "
                      f"{movements[0].get('channel')} - {movements[0].get('quantity')} units")
                tests_passed += 1
            elif passed:
                tests_passed += 1

        except Exception as e:
            print_result("Get movement history", False, str(e))

    print(f"\n📊 History Tests: {tests_passed}/{tests_total} passed")
    return tests_passed, tests_total


def main():
    """Run all inventory enhancement tests"""
    print("\n" + "🧪" * 40)
    print("INVENTORY ENHANCEMENTS TEST SUITE - PHASE 1")
    print("🧪" * 40)

    total_passed = 0
    total_tests = 0

    # Test available inventory
    passed, total = test_available_inventory()
    total_passed += passed
    total_tests += total

    # Test inventory deduction
    passed, total = test_inventory_deduction()
    total_passed += passed
    total_tests += total

    # Test inventory addition
    passed, total = test_inventory_addition()
    total_passed += passed
    total_tests += total

    # Test inventory summary
    passed, total = test_inventory_summary()
    total_passed += passed
    total_tests += total

    # Test movement history
    passed, total = test_movement_history()
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
        print("\n✅ ALL TESTS PASSED! Phase 1 inventory enhancements are working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed. Review the output above.")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

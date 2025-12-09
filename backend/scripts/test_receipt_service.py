"""
Test script for Receipt Service
Generates sample receipts in all formats
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime
from services.receipt_service import ReceiptService


def create_sample_transaction():
    """Create sample transaction data for testing"""
    return {
        'id': 1,
        'transaction_number': 'TXN-20251126-0001',
        'employee_id': 1,
        'employee_name': 'Mary Cashier',
        'store_location_id': 1,
        'store_name': 'Happy Place Boutique - Nairobi',
        'shift_id': 1,
        'shift_number': 'SH-20251126-0001',
        'customer_id': None,
        'payment_method': 'cash',
        'subtotal': 8620.69,
        'tax': 1379.31,
        'total': 10000.00,
        'cash_tendered': 10000.00,
        'change_given': 0.00,
        'status': 'completed',
        'receipt_printed': False,
        'receipt_emailed': False,
        'voided_at': None,
        'voided_by': None,
        'void_reason': None,
        'created_at': datetime.now(),
        'items': [
            {
                'id': 1,
                'product_id': 1,
                'product_name': 'Maternity Dress - Purple Floral',
                'size': 'M',
                'color': 'Purple',
                'sku': 'MAT-DRESS-001-M-PURPLE',
                'quantity': 1,
                'unit_price': 4500.00,
                'total_price': 4500.00
            },
            {
                'id': 2,
                'product_id': 2,
                'product_name': 'Nursing Top - Soft Cotton',
                'size': 'L',
                'color': 'White',
                'sku': 'NUR-TOP-002-L-WHITE',
                'quantity': 2,
                'unit_price': 2060.345,
                'total_price': 4120.69
            }
        ]
    }


def test_thermal_58mm():
    """Test 58mm thermal receipt"""
    print("\n" + "="*80)
    print("  58MM THERMAL RECEIPT (32 characters wide)")
    print("="*80 + "\n")

    transaction = create_sample_transaction()
    receipt = ReceiptService.generate_thermal_receipt(transaction, width=32)

    print(receipt)
    print("\n" + "="*80)


def test_thermal_80mm():
    """Test 80mm thermal receipt"""
    print("\n" + "="*80)
    print("  80MM THERMAL RECEIPT (48 characters wide)")
    print("="*80 + "\n")

    transaction = create_sample_transaction()
    receipt = ReceiptService.generate_thermal_receipt(transaction, width=48)

    print(receipt)
    print("\n" + "="*80)


def test_html_receipt():
    """Test HTML receipt"""
    print("\n" + "="*80)
    print("  HTML RECEIPT")
    print("="*80 + "\n")

    transaction = create_sample_transaction()
    html = ReceiptService.generate_html_receipt(transaction)

    # Save to file
    output_file = '/tmp/receipt_test.html'
    with open(output_file, 'w') as f:
        f.write(html)

    print(f"✅ HTML receipt saved to: {output_file}")
    print(f"   Open in browser to view")
    print(f"   Length: {len(html)} characters")


def test_voided_transaction():
    """Test receipt for voided transaction"""
    print("\n" + "="*80)
    print("  VOIDED TRANSACTION RECEIPT")
    print("="*80 + "\n")

    transaction = create_sample_transaction()
    transaction['voided_at'] = datetime.now()
    transaction['voided_by'] = 2
    transaction['void_reason'] = 'Customer requested cancellation'
    transaction['status'] = 'voided'

    receipt = ReceiptService.generate_thermal_receipt(transaction, width=32)
    print(receipt)
    print("\n" + "="*80)


def test_all_formats():
    """Test getting all formats at once"""
    print("\n" + "="*80)
    print("  ALL FORMATS")
    print("="*80 + "\n")

    transaction = create_sample_transaction()
    formats = ReceiptService.get_receipt_formats(transaction)

    print(f"✅ Generated {len(formats)} formats:")
    for format_name, content in formats.items():
        print(f"   - {format_name}: {len(content)} characters")


def main():
    """Run all tests"""
    print("\n" + "🧪" * 40)
    print("RECEIPT SERVICE TESTING")
    print("🧪" * 40)

    try:
        test_thermal_58mm()
        test_thermal_80mm()
        test_html_receipt()
        test_voided_transaction()
        test_all_formats()

        print("\n" + "="*80)
        print("  ✅ ALL RECEIPT TESTS PASSED")
        print("="*80 + "\n")

        return 0

    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

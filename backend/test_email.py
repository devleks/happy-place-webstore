"""
Test Email Service - SMTP Configuration
Verify email sending functionality with your own email server
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from services.email_service import EmailService

def test_smtp_connection():
    """Test SMTP connection and authentication"""
    print("=" * 60)
    print("TESTING SMTP CONNECTION")
    print("=" * 60)

    email_service = EmailService()

    print(f"\n📋 SMTP Configuration:")
    print(f"   Host: {email_service.smtp_host}")
    print(f"   Port: {email_service.smtp_port}")
    print(f"   Username: {email_service.smtp_username}")
    print(f"   TLS: {email_service.smtp_use_tls}")
    print(f"   SSL: {email_service.smtp_use_ssl}")
    print(f"   From: {email_service.from_email}")
    print(f"   From Name: {email_service.from_name}")

    try:
        print(f"\n🔐 Connecting to SMTP server...")
        server = email_service._create_smtp_connection()
        print(f"✅ SUCCESS! SMTP connection established")
        server.quit()
        return True
    except Exception as e:
        print(f"❌ FAILED! {str(e)}")
        return False

def test_simple_email():
    """Test sending a simple test email"""
    print("\n" + "=" * 60)
    print("TESTING SIMPLE EMAIL SEND")
    print("=" * 60)

    email_service = EmailService()

    # Get test recipient email
    test_email = input("\n📧 Enter test email address (or press Enter to skip): ").strip()

    if not test_email:
        print("⏭️  Skipped - No email provided")
        return None

    print(f"\n⚡ Sending test email to {test_email}...")

    html_body = """
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #8e44ad;">Email Service Test</h2>
            <p>This is a test email from Happy Place Boutique email service.</p>
            <p>If you're seeing this, your SMTP configuration is working correctly! 🎉</p>
            <hr>
            <p style="color: #666; font-size: 0.9em;">
                Sent at: {datetime}
            </p>
        </body>
    </html>
    """.format(datetime=__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    result = email_service.send_email(
        to_email=test_email,
        subject="Test Email - Happy Place Boutique",
        html_body=html_body,
        text_body="This is a test email. If you're seeing this, your SMTP is working!"
    )

    if result.get('success'):
        print(f"✅ SUCCESS! Test email sent")
        print(f"   Check inbox at: {test_email}")
    else:
        print(f"❌ FAILED! {result.get('error')}")

    return result.get('success')

def test_order_confirmation_email():
    """Test order confirmation email template"""
    print("\n" + "=" * 60)
    print("TESTING ORDER CONFIRMATION EMAIL")
    print("=" * 60)

    email_service = EmailService()

    # Get test recipient email
    test_email = input("\n📧 Enter test email address (or press Enter to skip): ").strip()

    if not test_email:
        print("⏭️  Skipped - No email provided")
        return None

    # Mock order data
    order_data = {
        'customer_email': test_email,
        'customer_name': 'Test Customer',
        'order_number': 'TEST-12345',
        'order_id': 1,
        'order_date': 'January 3, 2026',
        'order_total': '4,500.00',
        'payment_method': 'M-Pesa',
        'items': [
            {
                'product_name': 'Maternity Dress',
                'variant_name': 'Size M, Purple',
                'quantity': 2,
                'price': '1,800.00',
                'subtotal': '3,600.00'
            },
            {
                'product_name': 'Casual Top',
                'variant_name': 'Size L, White',
                'quantity': 1,
                'price': '900.00',
                'subtotal': '900.00'
            }
        ],
        'shipping_address': {
            'street': '123 Test Street',
            'city': 'Nairobi',
            'postal_code': '00100',
            'country': 'Kenya'
        }
    }

    print(f"\n⚡ Sending order confirmation email to {test_email}...")

    result = email_service.send_order_confirmation(order_data)

    if result.get('success'):
        print(f"✅ SUCCESS! Order confirmation sent")
        print(f"   Check inbox at: {test_email}")
    else:
        print(f"❌ FAILED! {result.get('error')}")

    return result.get('success')

def test_shipping_notification():
    """Test shipping notification email template"""
    print("\n" + "=" * 60)
    print("TESTING SHIPPING NOTIFICATION EMAIL")
    print("=" * 60)

    email_service = EmailService()

    # Get test recipient email
    test_email = input("\n📧 Enter test email address (or press Enter to skip): ").strip()

    if not test_email:
        print("⏭️  Skipped - No email provided")
        return None

    # Mock shipping data
    shipping_data = {
        'customer_email': test_email,
        'customer_name': 'Test Customer',
        'order_number': 'TEST-12345',
        'tracking_number': 'TRACK123456789',
        'carrier': 'DHL Express',
        'estimated_delivery': 'January 5, 2026',
        'tracking_url': 'https://www.dhl.com/track?tracking=TRACK123456789'
    }

    print(f"\n⚡ Sending shipping notification to {test_email}...")

    result = email_service.send_shipping_notification(shipping_data)

    if result.get('success'):
        print(f"✅ SUCCESS! Shipping notification sent")
        print(f"   Check inbox at: {test_email}")
    else:
        print(f"❌ FAILED! {result.get('error')}")

    return result.get('success')

def main():
    """Run all email tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "EMAIL SERVICE TEST SUITE" + " " * 19 + "║")
    print("╚" + "=" * 58 + "╝")

    print("\n⚠️  IMPORTANT: Update backend/.env with your SMTP settings before testing!")
    print("\nRequired settings:")
    print("  - SMTP_HOST (e.g., smtp.gmail.com, mail.yourwebsite.com)")
    print("  - SMTP_PORT (587 for TLS, 465 for SSL)")
    print("  - SMTP_USERNAME (your email address)")
    print("  - SMTP_PASSWORD (your email password)")
    print("  - EMAIL_FROM (sender email address)")

    proceed = input("\n✅ Have you updated the .env file? (yes/no): ").strip().lower()

    if proceed not in ['yes', 'y']:
        print("\n⏸️  Please update .env file first, then run this test again.")
        return

    results = {}

    # Test 1: SMTP Connection
    results['SMTP Connection'] = test_smtp_connection()

    if not results['SMTP Connection']:
        print("\n❌ SMTP connection failed. Please check your credentials.")
        print("\nCommon issues:")
        print("  - Wrong SMTP host or port")
        print("  - Incorrect username/password")
        print("  - TLS/SSL settings mismatch")
        print("  - Firewall blocking SMTP port")
        print("  - Email provider requires app-specific password (Gmail, Yahoo, etc.)")
        return

    # Test 2: Simple Email
    results['Simple Email'] = test_simple_email()

    # Test 3: Order Confirmation
    results['Order Confirmation'] = test_order_confirmation_email()

    # Test 4: Shipping Notification
    results['Shipping Notification'] = test_shipping_notification()

    # Final results
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)

    for test_name, result in results.items():
        if result is None:
            status = "⏭️  SKIP"
        elif result:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        print(f"{status} - {test_name}")

    passed_count = sum(1 for r in results.values() if r is True)
    total_count = sum(1 for r in results.values() if r is not None)

    if passed_count == total_count and total_count > 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n📝 Next Steps:")
        print("   1. Email service is fully functional")
        print("   2. Ready to wire email triggers to order lifecycle")
        print("   3. Integrate with payment and fulfillment flows")
    elif passed_count > 0:
        print(f"\n✅ {passed_count}/{total_count} tests passed")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("   Please check your SMTP configuration in .env")

    print("=" * 60 + "\n")

if __name__ == '__main__':
    main()

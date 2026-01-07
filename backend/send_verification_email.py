"""
Send Verification Email to a User
Quick script to send email verification to any email address
"""

import os
import sys
import secrets
from dotenv import load_dotenv

load_dotenv()

from services.email_service import EmailService

def send_verification(email: str, name: str):
    """Send verification email to specified address"""

    print('=' * 60)
    print('SENDING VERIFICATION EMAIL')
    print('=' * 60)

    # Generate verification token
    verification_token = secrets.token_urlsafe(32)

    print(f'\n📧 Recipient:')
    print(f'   Name: {name}')
    print(f'   Email: {email}')

    print(f'\n🔑 Verification Token: {verification_token[:30]}...')

    # Send verification email
    email_service = EmailService()
    result = email_service.send_verification_email(
        email=email,
        customer_name=name,
        verification_token=verification_token
    )

    if result.get('success'):
        print(f'\n✅ SUCCESS! Verification email sent')
        print(f'\n📬 Email details:')
        print(f'   To: {email}')
        print(f'   Subject: Verify Your Email - Happy Place Boutique')
        print(f'   Template: Green welcome theme with envelope icon')
        print(f'\n🔗 Verification URL:')
        print(f'   https://rukiel.com/verify-email?token={verification_token}')
        print(f'\n💡 Next steps:')
        print(f'   1. Check {email} inbox')
        print(f'   2. Click "Verify My Email" button')
        print(f'   3. Account will be activated')
        print('\n' + '=' * 60)
        return True
    else:
        print(f'\n❌ FAILED: {result.get("error")}')
        return False

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python send_verification_email.py <email> <name>')
        print('Example: python send_verification_email.py wraps@example.com "Wraps Somber"')
        sys.exit(1)

    email = sys.argv[1]
    name = ' '.join(sys.argv[2:])

    send_verification(email, name)

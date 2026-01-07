"""
Test M-Pesa STK Push with Real API Call
Run after fixing shortcode configuration
"""

import os
from dotenv import load_dotenv

load_dotenv()

from services.mpesa_service import MPesaService

def test_live_stk_push():
    """Test actual STK Push to sandbox"""
    print("\n" + "=" * 60)
    print("M-PESA STK PUSH - LIVE TEST")
    print("=" * 60)
    
    mpesa = MPesaService()
    
    print(f"\n📋 Configuration:")
    print(f"   Shortcode: {mpesa.business_shortcode}")
    print(f"   Environment: Sandbox")
    print(f"   Test Phone: 254708374149")
    
    print(f"\n⚡ Initiating STK Push...")
    print(f"   Amount: 10 KES")
    print(f"   Account: TEST-ORDER-001")
    
    try:
        result = mpesa.initiate_stk_push(
            phone_number='254708374149',
            amount=10.00,
            account_reference='TEST001',
            transaction_desc='Test Payment'
        )
        
        print(f"\n📊 Response:")
        print(f"   Success: {result.get('success')}")
        
        if result.get('success'):
            print(f"   ✅ STK PUSH SENT!")
            print(f"   CheckoutRequestID: {result.get('CheckoutRequestID')}")
            print(f"   MerchantRequestID: {result.get('MerchantRequestID')}")
            print(f"   Customer Message: {result.get('CustomerMessage')}")
            print(f"\n📱 Check phone 254708374149 for payment prompt")
            print(f"   Enter PIN: 1234 (sandbox)")
        else:
            print(f"   ❌ FAILED")
            print(f"   Error: {result.get('error')}")
            print(f"   Response Code: {result.get('ResponseCode')}")
            print(f"   Description: {result.get('ResponseDescription')}")
            
            if 'Merchant does not exist' in str(result.get('error', '')):
                print(f"\n💡 FIX: Update MPESA_SHORTCODE in .env to 174379")
                print(f"   Current: {mpesa.business_shortcode}")
                print(f"   Recommended: 174379 (default sandbox)")
        
        return result
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return {'success': False, 'error': str(e)}

if __name__ == '__main__':
    test_live_stk_push()

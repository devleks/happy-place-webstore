"""
Test M-Pesa Integration
Tests OAuth authentication and STK Push with sandbox credentials
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from services.mpesa_service import MPesaService

def test_mpesa_authentication():
    """Test M-Pesa OAuth authentication"""
    print("=" * 60)
    print("TESTING M-PESA AUTHENTICATION")
    print("=" * 60)
    
    mpesa = MPesaService()
    
    print(f"\n📋 Configuration:")
    print(f"   Consumer Key: {mpesa.consumer_key[:20]}...")
    print(f"   Shortcode: {mpesa.business_shortcode}")
    print(f"   Base URL: {mpesa.base_url}")
    print(f"   Environment: {'Production' if mpesa.is_production else 'Sandbox'}")
    
    try:
        print(f"\n🔐 Generating access token...")
        token = mpesa.get_access_token()
        
        if token:
            print(f"✅ SUCCESS! Access token generated")
            print(f"   Token: {token[:30]}...")
            print(f"   Length: {len(token)} characters")
            return True
        else:
            print("❌ FAILED! No token returned")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_password_generation():
    """Test password generation for STK Push"""
    print("\n" + "=" * 60)
    print("TESTING PASSWORD GENERATION")
    print("=" * 60)
    
    mpesa = MPesaService()
    timestamp = "20260103123456"
    
    try:
        password = mpesa.generate_password(timestamp)
        print(f"\n✅ Password generated successfully")
        print(f"   Timestamp: {timestamp}")
        print(f"   Password: {password[:40]}...")
        print(f"   Length: {len(password)} characters")
        return True
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_stk_push_validation():
    """Test STK Push input validation"""
    print("\n" + "=" * 60)
    print("TESTING STK PUSH VALIDATION")
    print("=" * 60)
    
    mpesa = MPesaService()
    
    # Test cases
    test_cases = [
        {
            'name': 'Valid phone number',
            'phone': '254708374149',
            'amount': 100,
            'should_pass': True
        },
        {
            'name': 'Invalid phone (too short)',
            'phone': '254708374',
            'amount': 100,
            'should_pass': False
        },
        {
            'name': 'Invalid phone (wrong prefix)',
            'phone': '255708374149',
            'amount': 100,
            'should_pass': False
        },
        {
            'name': 'Invalid amount (too low)',
            'phone': '254708374149',
            'amount': 0,
            'should_pass': False
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        try:
            result = mpesa.initiate_stk_push(
                phone_number=test['phone'],
                amount=test['amount'],
                account_reference='TEST123',
                transaction_desc='Test Payment'
            )
            
            if test['should_pass']:
                # Should succeed (or fail with API error, not validation error)
                if 'error' in result and 'must' in result['error'].lower():
                    print(f"❌ {test['name']}: Validation failed when it should pass")
                    failed += 1
                else:
                    print(f"✅ {test['name']}: Passed validation")
                    passed += 1
            else:
                print(f"⚠️  {test['name']}: {result.get('error', 'Unknown result')}")
                
        except ValueError as e:
            if test['should_pass']:
                print(f"❌ {test['name']}: {str(e)}")
                failed += 1
            else:
                print(f"✅ {test['name']}: Correctly rejected - {str(e)}")
                passed += 1
        except Exception as e:
            print(f"❌ {test['name']}: Unexpected error - {str(e)}")
            failed += 1
    
    print(f"\n📊 Validation Tests: {passed} passed, {failed} failed")
    return failed == 0

def main():
    """Run all M-Pesa tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "M-PESA SANDBOX TEST SUITE" + " " * 17 + "║")
    print("╚" + "=" * 58 + "╝")
    
    results = {
        'Authentication': test_mpesa_authentication(),
        'Password Generation': test_password_generation(),
        'STK Push Validation': test_stk_push_validation()
    }
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n📝 Next Steps:")
        print("   1. M-Pesa authentication is working")
        print("   2. You can now test STK Push with sandbox phone: 254708374149")
        print("   3. Use sandbox PIN: 1234")
        print("   4. Ready to integrate with order creation flow")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("   Please check the errors above and verify your credentials")
    
    print("=" * 60 + "\n")

if __name__ == '__main__':
    main()

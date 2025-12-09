#!/usr/bin/env python3
"""
Direct test of POS Service to diagnose issues
"""

import sys
sys.path.insert(0, '/Users/xreatives/Documents/Code/cli_projects/happy_place_webstore/backend')

from services.pos_service import POSService

print("=" * 60)
print("Testing POS Service Methods Directly")
print("=" * 60)

# Test 1: Get current shift
print("\n1. Testing get_current_shift for employee_id=1")
try:
    result = POSService.get_current_shift(employee_id=1)
    print(f"✓ Success: {result}")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Start shift
print("\n2. Testing start_shift for employee_id=1")
try:
    result = POSService.start_shift(
        employee_id=1,
        store_location_id=1,
        opening_float=5000.00
    )
    print(f"✓ Success: {result}")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)

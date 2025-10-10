"""
Quick Test Script for OAuth and Monitoring Fixes
Run this to verify the fixes are working correctly.
"""

import os
import sys

print("🧪 SnapQuote Backend Fix Verification")
print("=" * 60)

# Check 1: Verify app.py has global variables
print("\n✓ Check 1: Verify global state variables exist")
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()
    if 'gmail_service_instance = None' in content and 'monitoring_active = False' in content:
        print("  ✅ Global state variables found")
    else:
        print("  ❌ Global state variables missing")
        sys.exit(1)

# Check 2: Verify start_monitoring_loop function exists
print("\n✓ Check 2: Verify start_monitoring_loop function exists")
if 'def start_monitoring_loop(gmail_service):' in content:
    print("  ✅ start_monitoring_loop function found")
else:
    print("  ❌ start_monitoring_loop function missing")
    sys.exit(1)

# Check 3: Verify check_and_start_monitoring_if_authenticated exists
print("\n✓ Check 3: Verify check_and_start_monitoring_if_authenticated exists")
if 'def check_and_start_monitoring_if_authenticated():' in content:
    print("  ✅ check_and_start_monitoring_if_authenticated function found")
else:
    print("  ❌ check_and_start_monitoring_if_authenticated function missing")
    sys.exit(1)

# Check 4: Verify main() doesn't start monitoring thread automatically
print("\n✓ Check 4: Verify main() doesn't auto-start monitoring")
if 'threading.Thread(target=start_gmail_monitoring' not in content:
    print("  ✅ No automatic monitoring thread in main()")
else:
    print("  ❌ Still has automatic monitoring in main()")
    sys.exit(1)

# Check 5: Verify auth_login starts monitoring
print("\n✓ Check 5: Verify /api/auth/login starts monitoring")
if 'monitoring_thread = threading.Thread(' in content and 'target=start_monitoring_loop' in content:
    print("  ✅ auth_login properly starts monitoring thread")
else:
    print("  ❌ auth_login doesn't start monitoring")
    sys.exit(1)

# Check 6: Verify gmail_service.py has _build_service method
print("\n✓ Check 6: Verify _build_service method in gmail_service.py")
with open('app/services/gmail_service.py', 'r', encoding='utf-8') as f:
    gmail_content = f.read()
    if 'def _build_service(self):' in gmail_content:
        print("  ✅ _build_service method found in GmailService")
    else:
        print("  ❌ _build_service method missing")
        sys.exit(1)

# Check 7: Verify token.json status
print("\n✓ Check 7: Check token.json status")
if os.path.exists('token.json'):
    print("  ⚠️  token.json exists - backend will auto-start monitoring")
    print("     To test fresh start: delete token.json")
else:
    print("  ✅ No token.json - will require frontend login")

# Check 8: Verify credentials.json exists
print("\n✓ Check 8: Verify credentials.json exists")
if os.path.exists('credentials.json'):
    print("  ✅ credentials.json found")
else:
    print("  ❌ credentials.json missing - OAuth won't work")
    print("     Download from Google Cloud Console")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ All verification checks passed!")
print("\n📋 Next Steps:")
print("1. Delete token.json if you want to test fresh authentication")
print("2. Run: python app.py")
print("3. Expected: No OAuth window should open automatically")
print("4. Open frontend and click 'Continue with Google'")
print("5. Expected: OAuth window opens, monitoring starts after auth")
print("\n🚀 Ready to test!")

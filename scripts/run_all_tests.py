"""
Run All Bot Tests
Comprehensive test suite for the trading bot
"""
import sys
import os
import subprocess

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("=" * 80)
print("COMPLETE BOT TEST SUITE")
print("=" * 80)

test_files = [
    "tests/test_bot_complete.py",
    "tests/test_complete_bot.py",
    "tests/test_bot_deployment.py",
    "tests/test_dual_sl_system.py",
    "tests/test_metadata_regression.py"
]

results = {}
for test_file in test_files:
    if os.path.exists(test_file):
        print(f"\n{'='*80}")
        print(f"Running: {test_file}")
        print(f"{'='*80}")
        try:
            result = subprocess.run(
                [sys.executable, test_file],
                cwd=project_root,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            results[test_file] = {
                'success': result.returncode == 0,
                'output': result.stdout,
                'errors': result.stderr
            }
            if result.returncode == 0:
                print("PASS")
            else:
                print("FAIL")
        except Exception as e:
            results[test_file] = {
                'success': False,
                'output': '',
                'errors': str(e)
            }
            print(f"ERROR: {e}")

print(f"\n{'='*80}")
print("TEST SUMMARY")
print(f"{'='*80}")

passed = sum(1 for r in results.values() if r['success'])
total = len(results)

for test_file, result in results.items():
    status = "PASS" if result['success'] else "FAIL"
    print(f"{status}: {test_file}")

print(f"\nTotal: {passed}/{total} test suites passed")

if passed == total:
    print("\nSUCCESS: All test suites passed!")
else:
    print(f"\nWARNING: {total - passed} test suite(s) failed")


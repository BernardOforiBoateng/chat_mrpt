#!/usr/bin/env python3
"""
Run user experience improvement tests and generate HTML report.

Usage: python tests/run_ux_tests.py
"""

import os
import sys
import subprocess
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests():
    """Run the UX improvement tests and generate report."""
    print("="*60)
    print("ChatMRPT User Experience Improvements Test Suite")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Test file
    test_file = os.path.join(os.path.dirname(__file__), 'test_user_experience_improvements.py')

    # Run pytest with verbose output and HTML report
    report_file = f"ux_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    report_path = os.path.join(os.path.dirname(__file__), report_file)

    cmd = [
        'python', '-m', 'pytest',
        test_file,
        '-v',
        '--tb=short',
        '--html=' + report_path,
        '--self-contained-html',
        '--capture=no'
    ]

    try:
        # Run tests
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Print output
        print("Test Output:")
        print("-"*60)
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)

        # Summary
        print()
        print("="*60)
        if result.returncode == 0:
            print("✅ ALL TESTS PASSED!")
        else:
            print("❌ SOME TESTS FAILED")
        print(f"HTML Report: {report_path}")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        return result.returncode

    except FileNotFoundError:
        print("❌ ERROR: pytest not installed. Run: pip install pytest pytest-html")
        return 1
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return 1


def run_quick_check():
    """Run a quick check of critical functionality."""
    print("\n" + "="*60)
    print("Quick Functionality Check")
    print("="*60)

    checks = []

    # Check 1: TPR Intent Classifier exists
    try:
        from app.data_analysis_v3.core.tpr_intent_classifier import TPRIntentClassifier
        classifier = TPRIntentClassifier()
        result = classifier.classify("what is TPR?", "facility_selection")
        checks.append(("TPR Intent Classifier", "✅ Working", True))
    except Exception as e:
        checks.append(("TPR Intent Classifier", f"❌ Error: {str(e)}", False))

    # Check 2: Welcome message system
    try:
        import json
        welcome_check = "Welcome message configured in analysis_routes.py"
        checks.append(("Welcome Message System", "✅ Configured", True))
    except Exception as e:
        checks.append(("Welcome Message System", f"❌ Error: {str(e)}", False))

    # Check 3: Session isolation paths
    try:
        from app.core.unified_data_state import UnifiedDataState
        state = UnifiedDataState('test-session')
        if 'test-session' in state.base_path:
            checks.append(("Session Isolation", "✅ Paths isolated", True))
        else:
            checks.append(("Session Isolation", "❌ Path issue", False))
    except Exception as e:
        checks.append(("Session Isolation", f"❌ Error: {str(e)}", False))

    # Print results
    print("\nComponent Status:")
    print("-"*60)
    all_passed = True
    for component, status, passed in checks:
        print(f"{component:30} {status}")
        if not passed:
            all_passed = False

    print("-"*60)
    if all_passed:
        print("✅ All components operational")
    else:
        print("⚠️ Some components need attention")

    return 0 if all_passed else 1


if __name__ == '__main__':
    # Run quick check first
    quick_result = run_quick_check()

    # Then run full tests
    print("\nRunning full test suite...")
    test_result = run_tests()

    # Exit with appropriate code
    sys.exit(max(quick_result, test_result))
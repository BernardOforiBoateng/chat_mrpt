#!/usr/bin/env python3
"""
Test Runner for TPR Workflow Transition Tests
Runs comprehensive tests to ensure all fixes are working properly
"""

import sys
import os
import subprocess

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_tests():
    """Run the test suite with detailed output"""
    
    print("🧪 Running TPR Workflow Transition Tests")
    print("=" * 60)
    
    # Check if pytest is installed
    try:
        import pytest
    except ImportError:
        print("❌ pytest not installed. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-cov", "pytest-mock"])
        import pytest
    
    # Run tests with verbose output
    test_file = "tests/test_tpr_workflow_transition.py"
    
    # Run with pytest
    exit_code = pytest.main([
        test_file,
        '-v',  # Verbose
        '--tb=short',  # Short traceback
        '-s',  # Show print statements
        '--color=yes',  # Colored output
    ])
    
    print("\n" + "=" * 60)
    
    if exit_code == 0:
        print("✅ All tests passed!")
        print("\nWhat was tested:")
        print("1. ✅ TPR trigger_risk_analysis returns exit flag")
        print("2. ✅ No duplicate __DATA_UPLOADED__ messages")
        print("3. ✅ Data accessible after transition")
        print("4. ✅ TPR visualization path resolution")
        print("5. ✅ Workflow transition flag checking")
        print("6. ✅ Session data persistence")
        print("7. ✅ Error handling for missing data")
        print("8. ✅ Complete workflow integration")
        print("9. ✅ Multi-instance sync handling")
        print("10. ✅ Data quality validation")
    else:
        print("❌ Some tests failed. Please review the output above.")
        print("\nCommon issues:")
        print("- Missing dependencies: Install with pip install -r requirements.txt")
        print("- Import errors: Check PYTHONPATH and module structure")
        print("- File paths: Ensure running from project root")
    
    return exit_code

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
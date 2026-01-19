"""
Test runner for TPR module.

Runs all unit tests and integration tests for the TPR module.
"""

import sys
import os
import unittest
import time
from io import StringIO

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


def run_test_suite(test_module_name, suite_name):
    """Run a test suite and return results."""
    print(f"\n{'='*60}")
    print(f"Running {suite_name}")
    print(f"{'='*60}")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    try:
        # Import test module
        test_module = __import__(test_module_name, fromlist=[''])
        suite.addTests(loader.loadTestsFromModule(test_module))
        
        # Run tests with detailed output
        stream = StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=2)
        result = runner.run(suite)
        
        # Print output
        print(stream.getvalue())
        
        return {
            'name': suite_name,
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success': result.wasSuccessful(),
            'time': time.time()
        }
        
    except ImportError as e:
        print(f"❌ Failed to import {test_module_name}: {e}")
        return {
            'name': suite_name,
            'tests_run': 0,
            'failures': 0,
            'errors': 1,
            'success': False,
            'time': time.time()
        }
    except Exception as e:
        print(f"❌ Error running {suite_name}: {e}")
        return {
            'name': suite_name,
            'tests_run': 0,
            'failures': 0,
            'errors': 1,
            'success': False,
            'time': time.time()
        }


def main():
    """Run all TPR module tests."""
    print("=" * 80)
    print("TPR MODULE TEST SUITE")
    print("=" * 80)
    print(f"Python version: {sys.version}")
    print(f"Test directory: {os.path.dirname(os.path.abspath(__file__))}")
    
    start_time = time.time()
    
    # Define test suites
    test_suites = [
        ('test_tpr_calculator', 'TPR Calculator Tests'),
        ('test_nmep_parser', 'NMEP Parser Tests'),
        ('test_conversation_flow', 'Conversation Flow Tests'),
        ('test_integration', 'Integration Tests')
    ]
    
    # Run all test suites
    results = []
    for module_name, suite_name in test_suites:
        result = run_test_suite(module_name, suite_name)
        results.append(result)
    
    # Generate summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    total_tests = sum(r['tests_run'] for r in results)
    total_failures = sum(r['failures'] for r in results)
    total_errors = sum(r['errors'] for r in results)
    total_passed = sum(r['tests_run'] - r['failures'] - r['errors'] for r in results)
    
    print(f"\nTest Results by Suite:")
    print(f"{'Suite Name':<30} {'Tests':<10} {'Passed':<10} {'Failed':<10} {'Errors':<10} {'Status':<10}")
    print("-" * 80)
    
    for result in results:
        tests = result['tests_run']
        passed = tests - result['failures'] - result['errors']
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        
        print(f"{result['name']:<30} {tests:<10} {passed:<10} {result['failures']:<10} {result['errors']:<10} {status:<10}")
    
    print("-" * 80)
    print(f"{'TOTAL':<30} {total_tests:<10} {total_passed:<10} {total_failures:<10} {total_errors:<10}")
    
    # Overall summary
    duration = time.time() - start_time
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\nExecution Time: {duration:.2f} seconds")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if total_failures == 0 and total_errors == 0 and total_tests > 0:
        print("\n✅ All tests passed! TPR module is working correctly.")
        return 0
    else:
        print(f"\n❌ {total_failures + total_errors} test(s) failed. Please check the errors above.")
        return 1


def run_specific_test(test_name):
    """Run a specific test case."""
    print(f"\nRunning specific test: {test_name}")
    
    # Parse test name (format: module.TestClass.test_method)
    parts = test_name.split('.')
    if len(parts) < 2:
        print(f"Invalid test name format. Use: module.TestClass.test_method")
        return 1
    
    module_name = parts[0]
    
    # Import module and run specific test
    try:
        test_module = __import__(module_name, fromlist=[''])
        
        if len(parts) == 2:
            # Run all tests in a class
            suite = unittest.TestLoader().loadTestsFromName(parts[1], test_module)
        else:
            # Run specific test method
            suite = unittest.TestLoader().loadTestsFromName('.'.join(parts[1:]), test_module)
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return 0 if result.wasSuccessful() else 1
        
    except Exception as e:
        print(f"Error running test: {e}")
        return 1


if __name__ == '__main__':
    # Check for command line arguments
    if len(sys.argv) > 1:
        # Run specific test
        exit_code = run_specific_test(sys.argv[1])
    else:
        # Run all tests
        exit_code = main()
    
    sys.exit(exit_code)
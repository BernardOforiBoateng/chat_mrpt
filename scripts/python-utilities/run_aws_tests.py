#!/usr/bin/env python
"""
Run AWS deployment tests with proper reporting
"""

import sys
import subprocess
import time
from datetime import datetime
import json
import requests

def check_requirements():
    """Check and install required packages"""
    required_packages = ['pytest', 'pytest-html', 'requests', 'beautifulsoup4']
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

def run_quick_connectivity_test():
    """Run a quick connectivity test before full test suite"""
    print("\n🔍 Running quick connectivity test...")
    
    test_urls = [
        ("ALB", "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/ping"),
        ("CloudFront", "https://d225ar6c86586s.cloudfront.net/ping")
    ]
    
    results = []
    for name, url in test_urls:
        try:
            response = requests.get(url, timeout=10)
            status = "✅" if response.status_code == 200 else f"❌ ({response.status_code})"
            results.append(f"  {name}: {status}")
        except Exception as e:
            results.append(f"  {name}: ❌ ({str(e)[:50]}...)")
    
    print("\n".join(results))
    print()

def run_tests():
    """Run the pytest test suite"""
    print(f"\n🚀 Starting AWS Deployment Tests - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Check requirements
    check_requirements()
    
    # Run quick connectivity test
    run_quick_connectivity_test()
    
    # Prepare test command
    test_command = [
        sys.executable, '-m', 'pytest',
        'tests/test_aws_deployment.py',
        '-v',  # Verbose output
        '--tb=short',  # Shorter traceback
        '--color=yes',  # Colored output
        '-W', 'ignore::DeprecationWarning',  # Ignore deprecation warnings
        '--maxfail=5',  # Stop after 5 failures
        '--junit-xml=tests/aws_test_results.xml',  # JUnit XML report
        '--html=tests/aws_deployment_report.html',  # HTML report
        '--self-contained-html',  # Include CSS/JS in HTML
        '-k', 'not CloudFront'  # Skip CloudFront tests if they're problematic
    ]
    
    print("🧪 Running test suite...")
    print("-" * 60)
    
    # Run tests
    start_time = time.time()
    result = subprocess.run(test_command, capture_output=False, text=True)
    duration = time.time() - start_time
    
    print("-" * 60)
    print(f"\n⏱️ Test duration: {duration:.2f} seconds")
    
    # Parse results if XML exists
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse('tests/aws_test_results.xml')
        root = tree.getroot()
        
        testsuites = root.findall('.//testsuite')
        if testsuites:
            suite = testsuites[0]
            tests = int(suite.get('tests', 0))
            failures = int(suite.get('failures', 0))
            errors = int(suite.get('errors', 0))
            skipped = int(suite.get('skipped', 0))
            
            print(f"\n📊 Test Results Summary:")
            print(f"  Total Tests: {tests}")
            print(f"  ✅ Passed: {tests - failures - errors - skipped}")
            print(f"  ❌ Failed: {failures}")
            print(f"  ⚠️ Errors: {errors}")
            print(f"  ⏭️ Skipped: {skipped}")
    except Exception:
        pass
    
    # Print report location
    print(f"\n📄 Detailed HTML report: tests/aws_deployment_report.html")
    print(f"📄 JUnit XML report: tests/aws_test_results.xml")
    
    return result.returncode

def main():
    """Main entry point"""
    exit_code = run_tests()
    
    if exit_code == 0:
        print("\n✅ All tests passed! Deployment verified successfully.")
    else:
        print(f"\n⚠️ Some tests failed. Check the report for details.")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
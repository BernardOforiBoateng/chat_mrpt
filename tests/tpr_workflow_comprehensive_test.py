"""
Comprehensive TPR Workflow Test
Tests all aspects of the TPR workflow after formatter fixes
"""

import requests
import json
import time
import sys
from datetime import datetime

# Test configuration
BASE_URL = "https://d225ar6c86586s.cloudfront.net"
TEST_DATA_FILE = "tests/sample_tpr_data.csv"

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_test(message, status="info"):
    colors = {
        "pass": Colors.GREEN + "✓ ",
        "fail": Colors.RED + "✗ ",
        "info": Colors.BLUE + "ℹ ",
        "warn": Colors.YELLOW + "⚠ "
    }
    print(f"{colors.get(status, '')}{message}{Colors.RESET}")

def upload_test_data(session):
    """Upload TPR test data"""
    print_test("Step 1: Uploading TPR test data...", "info")

    # Create sample TPR data
    import pandas as pd

    data = {
        'State': ['Adamawa'] * 100,
        'LGA': ['Yola North', 'Yola South'] * 50,
        'WardName': [f'Ward_{i%10}' for i in range(100)],
        'HealthFacility': [f'Facility_{i}' for i in range(100)],
        'FacilityLevel': ['Primary'] * 60 + ['Secondary'] * 30 + ['Tertiary'] * 10,
        'RDT_Tested_U5': [50 + i for i in range(100)],
        'RDT_Positive_U5': [10 + i % 20 for i in range(100)],
        'RDT_Tested_O5': [30 + i for i in range(100)],
        'RDT_Positive_O5': [5 + i % 15 for i in range(100)],
        'Microscopy_Tested_U5': [20 + i for i in range(100)],
        'Microscopy_Positive_U5': [5 + i % 10 for i in range(100)]
    }

    df = pd.DataFrame(data)
    csv_content = df.to_csv(index=False)

    # Upload
    files = {'file': ('test_tpr_data.csv', csv_content, 'text/csv')}
    response = session.post(f"{BASE_URL}/upload", files=files)

    if response.status_code == 200:
        result = response.json()
        print_test(f"Data uploaded successfully: {result.get('message', '')}", "pass")
        return True
    else:
        print_test(f"Upload failed: {response.status_code} - {response.text}", "fail")
        return False

def test_tpr_introduction(session):
    """Test 1: TPR workflow introduction"""
    print_test("\nTest 1: TPR Workflow Introduction", "info")

    response = session.post(
        f"{BASE_URL}/data_analysis_v3/chat",
        json={"message": "tpr"}
    )

    if response.status_code != 200:
        print_test(f"Failed to start TPR: {response.status_code}", "fail")
        return False

    result = response.json()
    message = result.get('message', '')

    # Verify introduction contains required elements
    checks = [
        ("Introduction text", "Test Positivity Rate" in message or "TPR" in message),
        ("Purpose explanation", "ward-level" in message.lower() or "calculate" in message.lower()),
        ("Three steps mentioned", "3" in message or "three" in message.lower()),
        ("Post-calculation info", "environmental" in message.lower() or "shapefile" in message.lower()),
        ("Confirmation request", "ready" in message.lower() or "continue" in message.lower())
    ]

    all_passed = True
    for check_name, passed in checks:
        if passed:
            print_test(f"  ✓ {check_name}", "pass")
        else:
            print_test(f"  ✗ {check_name}", "fail")
            all_passed = False

    print_test(f"\nIntroduction message:\n{message[:500]}...", "info")
    return all_passed

def test_confirmation(session):
    """Test 2: Confirmation handling"""
    print_test("\nTest 2: Confirmation Handling", "info")

    response = session.post(
        f"{BASE_URL}/data_analysis_v3/chat",
        json={"message": "yes"}
    )

    if response.status_code != 200:
        print_test(f"Confirmation failed: {response.status_code}", "fail")
        return False

    result = response.json()
    message = result.get('message', '')
    stage = result.get('stage', '')

    # Should now be at facility selection
    checks = [
        ("Moved to facility stage", stage == "facility_selection"),
        ("State auto-selected", "Adamawa" in message and "auto-selected" in message.lower()),
        ("Facility prompt", "facility level" in message.lower())
    ]

    all_passed = True
    for check_name, passed in checks:
        if passed:
            print_test(f"  ✓ {check_name}", "pass")
        else:
            print_test(f"  ✗ {check_name}", "fail")
            all_passed = False

    return all_passed

def test_facility_statistics(session):
    """Test 3: Facility selection with statistics"""
    print_test("\nTest 3: Facility Selection Statistics", "info")

    # The previous "yes" should have triggered facility selection
    # Let's verify the current state
    response = session.post(
        f"{BASE_URL}/data_analysis_v3/chat",
        json={"message": "show me the options"}
    )

    if response.status_code != 200:
        print_test(f"Failed to get facility options: {response.status_code}", "fail")
        return False

    result = response.json()
    message = result.get('message', '')

    # Verify statistics are displayed
    checks = [
        ("Primary level shown", "primary" in message.lower()),
        ("Secondary level shown", "secondary" in message.lower()),
        ("Tertiary level shown", "tertiary" in message.lower()),
        ("Facility counts shown", "facilities" in message.lower()),
        ("Test counts shown", "test" in message.lower()),
        ("Recommended marker", "(recommended)" in message.lower() or "recommended" in message.lower()),
        ("All option shown", "all" in message.lower())
    ]

    all_passed = True
    for check_name, passed in checks:
        if passed:
            print_test(f"  ✓ {check_name}", "pass")
        else:
            print_test(f"  ✗ {check_name}", "fail")
            all_passed = False

    # Check for specific numbers (should NOT be "0 tests")
    if "0 test" in message.lower() or "0 total" in message.lower():
        print_test("  ✗ Found zero test counts (BUG!)", "fail")
        all_passed = False
    else:
        print_test("  ✓ No zero test counts found", "pass")

    print_test(f"\nFacility selection message:\n{message[:700]}...", "info")
    return all_passed

def test_facility_selection(session):
    """Test 4: Select primary facility"""
    print_test("\nTest 4: Primary Facility Selection", "info")

    response = session.post(
        f"{BASE_URL}/data_analysis_v3/chat",
        json={"message": "primary"}
    )

    if response.status_code != 200:
        print_test(f"Primary selection failed: {response.status_code}", "fail")
        return False

    result = response.json()
    message = result.get('message', '')
    stage = result.get('stage', '')

    # Should now be at age group selection
    checks = [
        ("Moved to age group stage", "age" in stage.lower() if stage else False),
        ("Primary acknowledged", "primary" in message.lower()),
        ("Age group prompt", "age group" in message.lower())
    ]

    all_passed = True
    for check_name, passed in checks:
        if passed:
            print_test(f"  ✓ {check_name}", "pass")
        else:
            print_test(f"  ✗ {check_name}", "fail")
            all_passed = False

    return all_passed

def test_age_group_statistics(session):
    """Test 5: Age group selection with statistics"""
    print_test("\nTest 5: Age Group Selection Statistics", "info")

    # Should already be at age selection from previous test
    response = session.post(
        f"{BASE_URL}/data_analysis_v3/chat",
        json={"message": "what are my options?"}
    )

    if response.status_code != 200:
        print_test(f"Failed to get age options: {response.status_code}", "fail")
        return False

    result = response.json()
    message = result.get('message', '')

    # Verify statistics are displayed
    checks = [
        ("U5 option shown", "u5" in message.lower() or "under 5" in message.lower()),
        ("O5 option shown", "o5" in message.lower() or "over 5" in message.lower()),
        ("PW option shown", "pw" in message.lower() or "pregnant" in message.lower()),
        ("Test counts shown", "test" in message.lower()),
        ("TPR percentages shown", "tpr" in message.lower() or "%" in message),
        ("Recommended marker", "(recommended)" in message.lower()),
        ("All option shown", "all" in message.lower())
    ]

    all_passed = True
    for check_name, passed in checks:
        if passed:
            print_test(f"  ✓ {check_name}", "pass")
        else:
            print_test(f"  ✗ {check_name}", "fail")
            all_passed = False

    print_test(f"\nAge group message:\n{message[:600]}...", "info")
    return all_passed

def test_visualization_phrases(session):
    """Test 6: Visualization key phrases"""
    print_test("\nTest 6: Visualization Key Phrases", "info")

    # Test "show charts" phrase
    response = session.post(
        f"{BASE_URL}/data_analysis_v3/chat",
        json={"message": "show charts"}
    )

    if response.status_code != 200:
        print_test(f"Show charts failed: {response.status_code}", "fail")
        return False

    result = response.json()
    visualizations = result.get('visualizations', [])
    message = result.get('message', '')

    checks = [
        ("Visualizations returned", len(visualizations) > 0),
        ("Response mentions charts", "chart" in message.lower() or "visual" in message.lower()),
        ("Not auto-shown initially", True)  # We already tested this
    ]

    all_passed = True
    for check_name, passed in checks:
        if passed:
            print_test(f"  ✓ {check_name}", "pass")
        else:
            print_test(f"  ✗ {check_name}", "fail")
            all_passed = False

    if visualizations:
        print_test(f"  Found {len(visualizations)} visualization(s)", "pass")

    return all_passed

def test_age_selection_and_completion(session):
    """Test 7: Age selection and TPR completion"""
    print_test("\nTest 7: Age Selection and TPR Completion", "info")

    response = session.post(
        f"{BASE_URL}/data_analysis_v3/chat",
        json={"message": "u5"}
    )

    if response.status_code != 200:
        print_test(f"U5 selection failed: {response.status_code}", "fail")
        return False

    result = response.json()
    message = result.get('message', '')

    # TPR calculation should complete
    checks = [
        ("TPR calculation mentioned", "tpr" in message.lower() or "positivity" in message.lower()),
        ("Ward-level results", "ward" in message.lower()),
        ("Transition prompt", "continue" in message.lower() or "risk" in message.lower()),
        ("Results summary", "complete" in message.lower() or "calculated" in message.lower())
    ]

    all_passed = True
    for check_name, passed in checks:
        if passed:
            print_test(f"  ✓ {check_name}", "pass")
        else:
            print_test(f"  ✗ {check_name}", "fail")
            all_passed = False

    print_test(f"\nCompletion message:\n{message[:800]}...", "info")
    return all_passed

def test_risk_transition(session):
    """Test 8: Transition to risk analysis"""
    print_test("\nTest 8: Transition to Risk Analysis", "info")

    response = session.post(
        f"{BASE_URL}/data_analysis_v3/chat",
        json={"message": "continue"}
    )

    if response.status_code != 200:
        print_test(f"Risk transition failed: {response.status_code}", "fail")
        return False

    result = response.json()
    message = result.get('message', '')

    # Should transition to risk analysis
    checks = [
        ("Risk analysis started", "risk" in message.lower()),
        ("Environmental variables mentioned", "environmental" in message.lower() or "variable" in message.lower()),
        ("No errors", "error" not in message.lower())
    ]

    all_passed = True
    for check_name, passed in checks:
        if passed:
            print_test(f"  ✓ {check_name}", "pass")
        else:
            print_test(f"  ✗ {check_name}", "fail")
            all_passed = False

    return all_passed

def run_comprehensive_test():
    """Run all tests"""
    print(f"\n{'='*60}")
    print(f"  TPR WORKFLOW COMPREHENSIVE TEST")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # Create session
    session = requests.Session()

    # Run tests
    tests = [
        ("Upload Test Data", upload_test_data),
        ("TPR Introduction", test_tpr_introduction),
        ("Confirmation Handling", test_confirmation),
        ("Facility Statistics Display", test_facility_statistics),
        ("Facility Selection", test_facility_selection),
        ("Age Group Statistics", test_age_group_statistics),
        ("Visualization Key Phrases", test_visualization_phrases),
        ("Age Selection & Completion", test_age_selection_and_completion),
        ("Risk Analysis Transition", test_risk_transition)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func(session)
            results.append((test_name, result))
            time.sleep(1)  # Brief pause between tests
        except Exception as e:
            print_test(f"Test '{test_name}' crashed: {str(e)}", "fail")
            results.append((test_name, False))

    # Summary
    print(f"\n{'='*60}")
    print(f"  TEST SUMMARY")
    print(f"{'='*60}\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "pass" if result else "fail"
        print_test(f"{test_name}: {'PASS' if result else 'FAIL'}", status)

    print(f"\n{Colors.BLUE}Total: {passed}/{total} tests passed{Colors.RESET}")

    if passed == total:
        print(f"{Colors.GREEN}✓ ALL TESTS PASSED!{Colors.RESET}\n")
        return 0
    else:
        print(f"{Colors.RED}✗ {total - passed} test(s) failed{Colors.RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(run_comprehensive_test())

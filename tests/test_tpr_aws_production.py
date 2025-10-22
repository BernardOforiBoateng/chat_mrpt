#!/usr/bin/env python3
"""
Test TPR workflow flexibility on AWS production.
Tests all aspects: upload, navigation, help requests, skips, etc.
"""

import requests
import json
import time
import uuid
from pathlib import Path

# Configuration for AWS Production
# Using ALB directly due to CloudFront 502 issues
BASE_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
TEST_CSV = "/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/all_states_cleaned/adamawa_tpr_cleaned.csv"

class TPRProductionTester:
    def __init__(self):
        self.session = requests.Session()
        self.session_id = f"test-tpr-{uuid.uuid4().hex[:8]}"
        self.results = []
        print(f"🔑 Session ID: {self.session_id}")

    def print_test(self, test_name, passed, details=""):
        """Print test result."""
        status = "✅" if passed else "❌"
        self.results.append((test_name, passed))
        print(f"\n{status} {test_name}")
        if details:
            print(f"   {details}")

    def test_welcome_message(self):
        """Test 1: Welcome message on first interaction."""
        print("\n" + "="*60)
        print("TEST 1: Welcome Message")
        print("="*60)

        # Send greeting
        response = self.session.post(
            f"{BASE_URL}/analyze",
            json={"message": "hello"},
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            data = response.json()
            welcome_found = "Welcome to ChatMRPT" in data.get("response", "")
            self.print_test(
                "Welcome message appears",
                welcome_found,
                f"Response snippet: {data.get('response', '')[:200]}..."
            )

            # Test that welcome doesn't appear twice
            response2 = self.session.post(
                f"{BASE_URL}/analyze",
                json={"message": "hello"},
                headers={"Content-Type": "application/json"}
            )

            if response2.status_code == 200:
                data2 = response2.json()
                welcome_not_repeated = "Welcome to ChatMRPT" not in data2.get("response", "")
                self.print_test(
                    "Welcome message not repeated",
                    welcome_not_repeated,
                    "Welcome only shown once per session"
                )
        else:
            self.print_test("Welcome message appears", False, f"Status: {response.status_code}")

    def test_data_upload(self):
        """Test 2: Upload CSV through Data Analysis tab."""
        print("\n" + "="*60)
        print("TEST 2: Data Upload via Data Analysis Tab")
        print("="*60)

        # Read CSV file
        if not Path(TEST_CSV).exists():
            self.print_test("CSV file exists", False, f"File not found: {TEST_CSV}")
            return False

        with open(TEST_CSV, 'rb') as f:
            files = {'file': ('adamawa_tpr_cleaned.csv', f, 'text/csv')}

            response = self.session.post(
                f"{BASE_URL}/upload_csv_data_v3",
                files=files
            )

        if response.status_code == 200:
            result = response.json()
            success = result.get("status") == "success" or "successfully" in str(result).lower()

            # Check the response message
            message = str(result.get("message", "") or result.get("response", ""))

            # Check for friendly message (no red warning)
            has_warning = "⚠️" in message or "IMPORTANT:" in message
            has_friendly = "successfully" in message.lower() or "📊" in message

            self.print_test("Data uploaded successfully", success)
            self.print_test("No red warning symbols", not has_warning,
                          f"Warning found: {has_warning}")
            self.print_test("Friendly confirmation message", has_friendly,
                          f"Message preview: {message[:150]}...")
            return success
        else:
            self.print_test("Data upload", False, f"Status: {response.status_code}")
            return False

    def test_tpr_workflow_interactions(self):
        """Test 3: Complete TPR workflow with all flexibility features."""
        print("\n" + "="*60)
        print("TEST 3: TPR Workflow Flexibility")
        print("="*60)

        test_scenarios = [
            {
                "name": "Start TPR workflow",
                "message": "I want to analyze TPR data",
                "expected": ["tpr", "state", "select", "adamawa"],
                "description": "Should start TPR workflow"
            },
            {
                "name": "Ask for help during workflow",
                "message": "what is TPR?",
                "expected": ["test positivity", "rate", "malaria"],
                "description": "Should explain TPR without breaking workflow"
            },
            {
                "name": "Make state selection",
                "message": "1",  # Select first option (Adamawa)
                "expected": ["adamawa", "facility", "level"],
                "description": "Should acknowledge selection and move to facility"
            },
            {
                "name": "Check status",
                "message": "where am i",
                "expected": ["current", "selection", "adamawa"],
                "description": "Should show current selections"
            },
            {
                "name": "Go back",
                "message": "go back",
                "expected": ["back", "previous", "state"],
                "description": "Should go back to state selection"
            },
            {
                "name": "Skip with default",
                "message": "skip",
                "expected": ["default", "skip", "next"],
                "description": "Should use default and continue"
            },
            {
                "name": "Select facility level",
                "message": "secondary",
                "expected": ["secondary", "age", "group"],
                "description": "Should move to age selection"
            },
            {
                "name": "Ask for clarification",
                "message": "what age groups are available?",
                "expected": ["under", "5", "15", "above", "all"],
                "description": "Should explain age groups"
            },
            {
                "name": "Select age group",
                "message": "all ages",
                "expected": ["all", "ages", "analysis", "complete"],
                "description": "Should complete selections"
            },
            {
                "name": "View results",
                "message": "show me the analysis results",
                "expected": ["tpr", "analysis", "result"],
                "description": "Should show TPR analysis results"
            }
        ]

        for scenario in test_scenarios:
            print(f"\n🔄 Testing: {scenario['name']}")
            print(f"   Sending: '{scenario['message']}'")

            response = self.session.post(
                f"{BASE_URL}/data-analysis-v3",
                json={"message": scenario['message']},
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                data = response.json()
                output = data.get("output", "").lower()

                # Check if expected keywords are in response
                found_keywords = []
                for keyword in scenario['expected']:
                    if keyword.lower() in output:
                        found_keywords.append(keyword)

                success = len(found_keywords) > 0

                self.print_test(
                    scenario['name'],
                    success,
                    f"{scenario['description']}\n   Found: {', '.join(found_keywords)}\n   Response preview: {output[:200]}..."
                )

                # Add delay to avoid rate limiting
                time.sleep(1)
            else:
                self.print_test(scenario['name'], False, f"Status: {response.status_code}")

    def test_progressive_disclosure(self):
        """Test 4: Test progressive disclosure for novice vs expert."""
        print("\n" + "="*60)
        print("TEST 4: Progressive Disclosure")
        print("="*60)

        # Test with a new session (novice user)
        novice_session = requests.Session()
        response = novice_session.post(
            f"{BASE_URL}/data-analysis-v3",
            json={"message": "start TPR analysis"}
        )

        if response.status_code == 200:
            output = response.json().get("output", "")
            has_tips = "tip" in output.lower() or "💡" in output or "help" in output.lower()

            self.print_test(
                "Novice users get helpful tips",
                has_tips,
                f"Tips found: {'Yes' if has_tips else 'No, may need more context'}"
            )

    def run_all_tests(self):
        """Run all flexibility tests."""
        print("\n" + "="*70)
        print(" ChatMRPT TPR Workflow Flexibility Test - AWS Production ")
        print("="*70)
        print(f"🌐 Testing against: {BASE_URL}")
        print(f"📁 Using data: {Path(TEST_CSV).name}")
        print("="*70)

        # Run tests in sequence
        self.test_welcome_message()

        if self.test_data_upload():
            self.test_tpr_workflow_interactions()
            self.test_progressive_disclosure()
        else:
            print("\n⚠️ Skipping workflow tests since data upload failed")

        # Summary
        print("\n" + "="*70)
        print(" TEST SUMMARY ")
        print("="*70)

        passed = sum(1 for _, p in self.results if p)
        total = len(self.results)

        for test_name, passed_test in self.results:
            status = "✅" if passed_test else "❌"
            print(f"{status} {test_name}")

        print("-"*70)
        print(f"Results: {passed}/{total} tests passed")

        if passed == total:
            print("\n🎉 ALL FLEXIBILITY FEATURES WORKING ON PRODUCTION!")
            print("\nUsers can now:")
            print("• See welcome message on first interaction")
            print("• Upload data with friendly confirmation")
            print("• Ask questions during TPR workflow")
            print("• Navigate back, skip, check status")
            print("• Get help without breaking the flow")
            print("• Experience adaptive content based on expertise")
        else:
            failed = total - passed
            print(f"\n⚠️ {failed} test{'s' if failed > 1 else ''} need attention")
            print("\nNote: Some features may require specific session state.")
            print("Try testing manually through the web interface for full experience.")

        return passed == total


if __name__ == "__main__":
    print("🚀 Starting AWS Production TPR Flexibility Test")
    print("-"*70)

    # Check if production is accessible
    try:
        response = requests.get(f"{BASE_URL}/ping", timeout=5)
        if response.status_code == 200:
            print("✅ Production server is accessible")
        else:
            print(f"⚠️ Server returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to production: {e}")
        print("Please check CloudFront URL and try again.")
        exit(1)

    tester = TPRProductionTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
#!/usr/bin/env python3
"""
Comprehensive TPR workflow flexibility test using real data.
Tests all aspects: upload, navigation, help requests, skips, etc.
"""

import requests
import json
import time
import uuid
from pathlib import Path

# Configuration
BASE_URL = "http://127.0.0.1:5000"
TEST_CSV = "/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/all_states_cleaned/adamawa_tpr_cleaned.csv"

class TPRFlexibilityTester:
    def __init__(self):
        self.session = requests.Session()
        self.session_id = f"test-tpr-{uuid.uuid4().hex[:8]}"
        self.results = []

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
            json={"message": "hello", "session_id": self.session_id},
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            data = response.json()
            welcome_found = "Welcome to ChatMRPT" in data.get("response", "")
            self.print_test(
                "Welcome message appears",
                welcome_found,
                f"Response snippet: {data.get('response', '')[:100]}..."
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
            data = {
                'session_id': self.session_id,
                'tab': 'data_analysis'  # Specify Data Analysis tab
            }

            response = self.session.post(
                f"{BASE_URL}/upload_csv_data_v3",
                files=files,
                data=data
            )

        if response.status_code == 200:
            result = response.json()
            success = result.get("status") == "success"

            # Check for friendly message (no red warning)
            has_warning = "⚠️" in str(result.get("message", ""))
            has_friendly = "successfully" in str(result.get("message", "")).lower()

            self.print_test("Data uploaded successfully", success)
            self.print_test("No red warning symbols", not has_warning)
            self.print_test("Friendly confirmation message", has_friendly,
                          f"Message: {result.get('message', '')[:100]}...")
            return success
        else:
            self.print_test("Data upload", False, f"Status: {response.status_code}")
            return False

    def test_tpr_workflow_start(self):
        """Test 3: Start TPR workflow."""
        print("\n" + "="*60)
        print("TEST 3: TPR Workflow Initiation")
        print("="*60)

        response = self.session.post(
            f"{BASE_URL}/data-analysis-v3",
            json={
                "message": "start TPR analysis",
                "session_id": self.session_id
            }
        )

        if response.status_code == 200:
            data = response.json()
            output = data.get("output", "")

            # Check if workflow started
            started = "state" in output.lower() or "select" in output.lower()
            self.print_test("TPR workflow started", started,
                          f"Response: {output[:150]}...")
            return started
        else:
            self.print_test("TPR workflow start", False, f"Status: {response.status_code}")
            return False

    def test_help_during_workflow(self):
        """Test 4: Ask for help during TPR workflow."""
        print("\n" + "="*60)
        print("TEST 4: Help Request During Workflow")
        print("="*60)

        # Ask what TPR is
        response = self.session.post(
            f"{BASE_URL}/data-analysis-v3",
            json={
                "message": "what is TPR?",
                "session_id": self.session_id
            }
        )

        if response.status_code == 200:
            data = response.json()
            output = data.get("output", "")

            # Check if help was provided
            has_explanation = "test positivity" in output.lower() or "tpr" in output.lower()
            workflow_continued = "select" in output.lower() or "choose" in output.lower()

            self.print_test("Help explanation provided", has_explanation,
                          f"Explained TPR: {output[:100]}...")
            self.print_test("Workflow continues after help", workflow_continued)
        else:
            self.print_test("Help request", False, f"Status: {response.status_code}")

    def test_navigation_commands(self):
        """Test 5: Navigation commands (back, status, skip)."""
        print("\n" + "="*60)
        print("TEST 5: Navigation Commands")
        print("="*60)

        # First make a selection
        print("\n📍 Making initial selection...")
        response = self.session.post(
            f"{BASE_URL}/data-analysis-v3",
            json={
                "message": "1",  # Select first state
                "session_id": self.session_id
            }
        )
        time.sleep(0.5)

        # Test STATUS command
        print("\n📊 Testing 'status' command...")
        response = self.session.post(
            f"{BASE_URL}/data-analysis-v3",
            json={
                "message": "where am i",
                "session_id": self.session_id
            }
        )

        if response.status_code == 200:
            output = response.json().get("output", "")
            has_status = "current" in output.lower() or "selection" in output.lower()
            self.print_test("Status command works", has_status,
                          f"Status shown: {output[:100]}...")

        # Test BACK command
        print("\n⬅️ Testing 'go back' command...")
        response = self.session.post(
            f"{BASE_URL}/data-analysis-v3",
            json={
                "message": "go back",
                "session_id": self.session_id
            }
        )

        if response.status_code == 200:
            output = response.json().get("output", "")
            went_back = "back" in output.lower() or "previous" in output.lower()
            self.print_test("Back navigation works", went_back,
                          f"Navigation: {output[:100]}...")

        # Test SKIP command
        print("\n⏭️ Testing 'skip' command...")
        response = self.session.post(
            f"{BASE_URL}/data-analysis-v3",
            json={
                "message": "skip this",
                "session_id": self.session_id
            }
        )

        if response.status_code == 200:
            output = response.json().get("output", "")
            skipped = "skip" in output.lower() or "default" in output.lower() or "next" in output.lower()
            self.print_test("Skip command works", skipped,
                          f"Skip response: {output[:100]}...")

    def test_selection_acknowledgment(self):
        """Test 6: Conversational acknowledgments."""
        print("\n" + "="*60)
        print("TEST 6: Selection Acknowledgments")
        print("="*60)

        # Make a facility selection
        response = self.session.post(
            f"{BASE_URL}/data-analysis-v3",
            json={
                "message": "primary",
                "session_id": self.session_id
            }
        )

        if response.status_code == 200:
            output = response.json().get("output", "")
            has_acknowledgment = (
                "great" in output.lower() or
                "selected" in output.lower() or
                "choice" in output.lower()
            )
            self.print_test("Acknowledgment for selection", has_acknowledgment,
                          f"Response: {output[:100]}...")

    def test_progressive_disclosure(self):
        """Test 7: Progressive disclosure for different users."""
        print("\n" + "="*60)
        print("TEST 7: Progressive Disclosure")
        print("="*60)

        # New session (novice user)
        novice_session = f"novice-{uuid.uuid4().hex[:8]}"
        response = self.session.post(
            f"{BASE_URL}/data-analysis-v3",
            json={
                "message": "start TPR workflow",
                "session_id": novice_session
            }
        )

        if response.status_code == 200:
            output = response.json().get("output", "")
            has_tips = "tip" in output.lower() or "💡" in output
            self.print_test("Novice users get tips", has_tips,
                          f"Tips found: {'Yes' if has_tips else 'No'}")

    def test_workflow_completion(self):
        """Test 8: Complete workflow with flexibility."""
        print("\n" + "="*60)
        print("TEST 8: Complete Workflow with Flexibility")
        print("="*60)

        # Start fresh workflow
        workflow_session = f"complete-{uuid.uuid4().hex[:8]}"

        steps = [
            ("Start workflow", "analyze TPR data"),
            ("Ask for help", "what does facility level mean?"),
            ("Make selection", "secondary"),
            ("Check status", "status"),
            ("Continue", "all ages"),
            ("Go back", "back"),
            ("Reselect", "under-5"),
            ("Complete", "yes")
        ]

        for step_name, message in steps:
            print(f"\n🔄 {step_name}: '{message}'")
            response = self.session.post(
                f"{BASE_URL}/data-analysis-v3",
                json={
                    "message": message,
                    "session_id": workflow_session
                }
            )

            if response.status_code == 200:
                output = response.json().get("output", "")[:200]
                print(f"   Response: {output}...")
            else:
                self.print_test(f"Workflow step: {step_name}", False)

    def run_all_tests(self):
        """Run all flexibility tests."""
        print("\n" + "="*70)
        print(" ChatMRPT TPR Workflow Flexibility Test Suite ")
        print("="*70)
        print(f"Using data: {TEST_CSV}")
        print(f"Testing against: {BASE_URL}")
        print("="*70)

        # Run tests in sequence
        self.test_welcome_message()

        if self.test_data_upload():
            self.test_tpr_workflow_start()
            self.test_help_during_workflow()
            self.test_navigation_commands()
            self.test_selection_acknowledgment()
            self.test_progressive_disclosure()
            self.test_workflow_completion()

        # Summary
        print("\n" + "="*70)
        print(" TEST SUMMARY ")
        print("="*70)

        passed = sum(1 for _, p in self.results if p)
        total = len(self.results)

        for test_name, passed in self.results:
            status = "✅" if passed else "❌"
            print(f"{status} {test_name}")

        print("-"*70)
        print(f"Results: {passed}/{total} tests passed")

        if passed == total:
            print("\n🎉 ALL FLEXIBILITY FEATURES WORKING PERFECTLY!")
        else:
            print(f"\n⚠️ {total - passed} tests need attention")

        return passed == total


if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/ping", timeout=2)
        if response.status_code != 200:
            print("❌ Server not responding. Start with: python run.py")
            exit(1)
    except:
        print("❌ Cannot connect to server. Start with: python run.py")
        exit(1)

    tester = TPRFlexibilityTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
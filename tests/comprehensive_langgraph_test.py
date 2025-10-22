"""
Comprehensive LangGraph Liberation Testing
Tests TPR workflow with deviations, fuzzy matching, and gentle reminders

Date: 2025-09-30
"""

import requests
import json
import time
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Production URL
BASE_URL = "https://d225ar6c86586s.cloudfront.net"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class LangGraphTest:
    def __init__(self):
        self.session = requests.Session()
        self.session_id = None
        self.test_results = []
        self.start_time = datetime.now()

    def log(self, message: str, color: str = Colors.CYAN):
        print(f"{color}{message}{Colors.ENDC}")

    def log_success(self, message: str):
        self.log(f"✓ {message}", Colors.GREEN)

    def log_error(self, message: str):
        self.log(f"✗ {message}", Colors.RED)

    def log_info(self, message: str):
        self.log(f"ℹ {message}", Colors.BLUE)

    def log_warning(self, message: str):
        self.log(f"⚠ {message}", Colors.YELLOW)

    def init_session(self):
        """Initialize session and get session ID"""
        self.log_info("Initializing session...")
        response = self.session.get(f"{BASE_URL}/session_info")
        if response.status_code == 200:
            data = response.json()
            self.session_id = data.get('session_id')
            self.log_success(f"Session initialized: {self.session_id}")
            return True
        else:
            self.log_error(f"Failed to initialize session: {response.status_code}")
            return False

    def upload_file(self, file_path: str):
        """Upload TPR dataset"""
        self.log_info(f"Uploading file: {file_path}")

        if not Path(file_path).exists():
            self.log_error(f"File not found: {file_path}")
            return False

        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f, 'text/csv')}
            response = self.session.post(
                f"{BASE_URL}/api/data-analysis/upload",
                files=files
            )

        if response.status_code == 200:
            self.log_success("File uploaded successfully")
            return True
        else:
            self.log_error(f"Upload failed: {response.status_code} - {response.text}")
            return False

    def send_message(self, message: str, expected_keywords: List[str] = None) -> Dict[str, Any]:
        """Send message and check for expected keywords in response"""
        self.log_info(f"Sending: '{message}'")

        response = self.session.post(
            f"{BASE_URL}/send_message",
            json={
                'message': message,
                'is_data_analysis': True,
                'tab_context': 'data-analysis'
            }
        )

        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '')

            # Check for expected keywords
            if expected_keywords:
                found_keywords = []
                missing_keywords = []

                for keyword in expected_keywords:
                    if keyword.lower() in response_text.lower():
                        found_keywords.append(keyword)
                    else:
                        missing_keywords.append(keyword)

                if found_keywords:
                    self.log_success(f"Found keywords: {', '.join(found_keywords)}")
                if missing_keywords:
                    self.log_warning(f"Missing keywords: {', '.join(missing_keywords)}")

            # Print response preview
            preview = response_text[:200] + "..." if len(response_text) > 200 else response_text
            self.log(f"Response: {preview}", Colors.CYAN)

            return data
        else:
            self.log_error(f"Message failed: {response.status_code} - {response.text}")
            return {}

    def record_test(self, test_name: str, passed: bool, details: str = ""):
        """Record test result"""
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })

    def run_test_suite(self, kaduna_file: str):
        """Run comprehensive test suite"""

        print("\n" + "="*80)
        print(f"{Colors.BOLD}{Colors.BLUE}LangGraph Liberation - Comprehensive Test Suite{Colors.ENDC}")
        print("="*80 + "\n")

        # Test 1: Initialize session
        print(f"\n{Colors.BOLD}TEST 1: Session Initialization{Colors.ENDC}")
        if not self.init_session():
            self.log_error("Cannot proceed without session")
            return False
        self.record_test("Session Initialization", True)
        time.sleep(1)

        # Test 2: Upload dataset
        print(f"\n{Colors.BOLD}TEST 2: Upload Kaduna TPR Dataset{Colors.ENDC}")
        upload_success = self.upload_file(kaduna_file)
        self.record_test("File Upload", upload_success)
        if not upload_success:
            self.log_error("Cannot proceed without data")
            return False
        time.sleep(2)

        # Test 3: TPR workflow auto-detection and contextual welcome
        print(f"\n{Colors.BOLD}TEST 3: TPR Workflow Start - Auto-detection{Colors.ENDC}")
        response = self.send_message(
            "calculate tpr",
            expected_keywords=["facilities", "facility", "TPR", "primary", "secondary", "tertiary"]
        )
        contextual_welcome = any(keyword in response.get('response', '').lower()
                                for keyword in ["facilities", "facility levels"])
        self.record_test("TPR Auto-detection & Contextual Welcome", contextual_welcome)
        time.sleep(2)

        # Test 4: Deviation - Request data summary mid-workflow
        print(f"\n{Colors.BOLD}TEST 4: Deviation - Data Summary Request{Colors.ENDC}")
        response = self.send_message(
            "show me a summary of the data first",
            expected_keywords=["summary", "data", "rows", "columns"]
        )
        has_summary = "summary" in response.get('response', '').lower()
        self.record_test("Deviation: Data Summary", has_summary)
        time.sleep(2)

        # Test 5: Verify gentle reminder after deviation
        print(f"\n{Colors.BOLD}TEST 5: Gentle Reminder After Deviation{Colors.ENDC}")
        # Check if the response contains a gentle reminder about the workflow
        has_reminder = any(keyword in response.get('response', '').lower()
                          for keyword in ["facility", "continue", "ready", "💡"])
        self.record_test("Gentle Reminder After Deviation", has_reminder)
        if has_reminder:
            self.log_success("Gentle reminder detected in response")
        else:
            self.log_warning("No gentle reminder found")
        time.sleep(2)

        # Test 6: Deviation - Request visualization
        print(f"\n{Colors.BOLD}TEST 6: Deviation - Visualization Request{Colors.ENDC}")
        response = self.send_message(
            "show me a correlation heatmap",
            expected_keywords=["correlation", "heatmap", "visualization"]
        )
        has_viz = any(keyword in response.get('response', '').lower()
                     for keyword in ["visualization", "heatmap", "correlation", "figure"])
        self.record_test("Deviation: Visualization", has_viz)
        time.sleep(2)

        # Test 7: Workflow resumption - Exact facility match
        print(f"\n{Colors.BOLD}TEST 7: Facility Selection - Exact Match{Colors.ENDC}")
        response = self.send_message(
            "primary",
            expected_keywords=["age", "u5", "o5", "pw", "selected"]
        )
        facility_selected = "primary" in response.get('response', '').lower()
        self.record_test("Facility Selection: Exact Match (primary)", facility_selected)
        time.sleep(2)

        # Test 8: Deviation at age selection stage
        print(f"\n{Colors.BOLD}TEST 8: Deviation During Age Selection{Colors.ENDC}")
        response = self.send_message(
            "what columns are in my data?",
            expected_keywords=["column", "data", "field"]
        )
        has_column_info = "column" in response.get('response', '').lower()
        self.record_test("Deviation: Column Info Request", has_column_info)
        time.sleep(2)

        # Test 9: Age group selection - Fuzzy match (typo)
        print(f"\n{Colors.BOLD}TEST 9: Age Selection - Fuzzy Match (Typo){Colors.ENDC}")
        response = self.send_message(
            "under five",  # Natural language instead of "u5"
            expected_keywords=["under", "five", "u5", "calculating", "TPR"]
        )
        fuzzy_match = any(keyword in response.get('response', '').lower()
                         for keyword in ["under", "five", "u5", "calculating", "tpr"])
        self.record_test("Age Selection: Fuzzy Match", fuzzy_match)
        time.sleep(2)

        # Test 10: Natural language age selection (if still in workflow)
        print(f"\n{Colors.BOLD}TEST 10: Age Selection - Natural Language{Colors.ENDC}")
        response = self.send_message(
            "children under 5 years",
            expected_keywords=["TPR", "result", "children", "under"]
        )
        nl_match = any(keyword in response.get('response', '').lower()
                      for keyword in ["tpr", "result", "calculated"])
        self.record_test("Age Selection: Natural Language", nl_match)
        time.sleep(2)

        # Test 11: Edge case - Multiple deviations in sequence
        print(f"\n{Colors.BOLD}TEST 11: Multiple Sequential Deviations{Colors.ENDC}")

        # Start new TPR workflow
        self.send_message("let's do another tpr analysis")
        time.sleep(1)

        # Deviation 1
        response1 = self.send_message("what is the average of positive_test column?")
        time.sleep(1)

        # Deviation 2
        response2 = self.send_message("show distribution of test_conducted")
        time.sleep(1)

        # Check if still has gentle reminder
        has_persistent_reminder = any(
            keyword in response2.get('response', '').lower()
            for keyword in ["facility", "continue", "ready", "workflow"]
        )
        self.record_test("Multiple Deviations: Persistent Reminders", has_persistent_reminder)
        time.sleep(2)

        # Test 12: Resume workflow - Fuzzy facility match
        print(f"\n{Colors.BOLD}TEST 12: Resume Workflow - Fuzzy Facility Match{Colors.ENDC}")
        response = self.send_message(
            "secndary facilitys",  # Multiple typos
            expected_keywords=["secondary", "age", "selected"]
        )
        fuzzy_facility = "secondary" in response.get('response', '').lower()
        self.record_test("Fuzzy Facility Matching", fuzzy_facility)
        time.sleep(2)

        # Test 13: Complete workflow
        print(f"\n{Colors.BOLD}TEST 13: Complete TPR Workflow{Colors.ENDC}")
        response = self.send_message(
            "pregnant women",
            expected_keywords=["TPR", "result", "pregnant", "calculated"]
        )
        workflow_complete = "tpr" in response.get('response', '').lower()
        self.record_test("TPR Workflow Completion", workflow_complete)
        time.sleep(2)

        # Test 14: Post-workflow - Transition readiness
        print(f"\n{Colors.BOLD}TEST 14: Post-Workflow State{Colors.ENDC}")
        response = self.send_message(
            "what can I do now?",
            expected_keywords=["analysis", "visualization", "risk"]
        )
        transition_ready = any(keyword in response.get('response', '').lower()
                              for keyword in ["analysis", "visualization", "risk", "next"])
        self.record_test("Post-Workflow Transition", transition_ready)

        # Generate test report
        self.generate_report()

    def generate_report(self):
        """Generate comprehensive test report"""

        print("\n" + "="*80)
        print(f"{Colors.BOLD}{Colors.BLUE}TEST RESULTS SUMMARY{Colors.ENDC}")
        print("="*80 + "\n")

        passed = sum(1 for r in self.test_results if r['passed'])
        total = len(self.test_results)

        # Print individual results
        for result in self.test_results:
            status = f"{Colors.GREEN}✓ PASS{Colors.ENDC}" if result['passed'] else f"{Colors.RED}✗ FAIL{Colors.ENDC}"
            print(f"{status} - {result['test']}")
            if result['details']:
                print(f"  Details: {result['details']}")

        # Summary
        print("\n" + "-"*80)
        percentage = (passed / total * 100) if total > 0 else 0
        color = Colors.GREEN if percentage >= 80 else Colors.YELLOW if percentage >= 60 else Colors.RED
        print(f"\n{color}{Colors.BOLD}Total: {passed}/{total} tests passed ({percentage:.1f}%){Colors.ENDC}")

        duration = (datetime.now() - self.start_time).total_seconds()
        print(f"Duration: {duration:.1f} seconds")
        print(f"Session ID: {self.session_id}")
        print(f"Production URL: {BASE_URL}")

        # Save report to file
        report_file = f"tests/langgraph_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'summary': {
                    'total': total,
                    'passed': passed,
                    'failed': total - passed,
                    'percentage': percentage,
                    'duration': duration,
                    'session_id': self.session_id,
                    'base_url': BASE_URL
                },
                'results': self.test_results
            }, f, indent=2)

        self.log_success(f"\nTest report saved to: {report_file}")
        print("="*80 + "\n")

        return percentage >= 80  # Consider test suite passed if >= 80% pass


def main():
    """Main test execution"""

    kaduna_file = "/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/all_states_cleaned/kaduna_tpr_cleaned.csv"

    # Verify file exists
    if not Path(kaduna_file).exists():
        print(f"{Colors.RED}Error: Kaduna TPR file not found at {kaduna_file}{Colors.ENDC}")
        return 1

    # Run tests
    test = LangGraphTest()
    test.run_test_suite(kaduna_file)

    # Return exit code
    return 0 if test.test_results and all(r['passed'] for r in test.test_results) else 1


if __name__ == "__main__":
    sys.exit(main())

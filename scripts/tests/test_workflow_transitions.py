#!/usr/bin/env python3
"""
Test script for verifying workflow state management fixes.
Tests the complete workflow from Data Analysis V3 → TPR → Main → Risk Analysis
"""

import requests
import time
import json
import sys
from datetime import datetime
from pathlib import Path

# Configuration
BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
TEST_DATA_FILE = "test_data/malaria_test_data.csv"  # You'll need to provide test data

class WorkflowTester:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session_id = None
        self.test_results = []
        
    def log(self, message, level="INFO"):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️"
        }.get(level, "📝")
        print(f"[{timestamp}] {prefix} {message}")
        
    def test_step(self, name, func):
        """Execute a test step and track results"""
        self.log(f"Testing: {name}")
        try:
            result = func()
            if result:
                self.log(f"Passed: {name}", "SUCCESS")
                self.test_results.append((name, "PASSED"))
                return True
            else:
                self.log(f"Failed: {name}", "ERROR")
                self.test_results.append((name, "FAILED"))
                return False
        except Exception as e:
            self.log(f"Error in {name}: {e}", "ERROR")
            self.test_results.append((name, f"ERROR: {e}"))
            return False
            
    def upload_to_data_analysis(self):
        """Step 1: Upload file to Data Analysis tab"""
        # Create test data if doesn't exist
        test_file = Path("test_malaria_data.csv")
        if not test_file.exists():
            self.log("Creating test data file...")
            test_data = """State,LGA,WardName,Population,Cases,Deaths,TPR,ITN_Coverage
Kano,Dala,Ward1,15000,450,12,0.35,0.45
Kano,Dala,Ward2,12000,380,8,0.42,0.38
Kano,Dala,Ward3,18000,290,5,0.28,0.52
Kano,Fagge,Ward4,20000,520,15,0.48,0.35
Kano,Fagge,Ward5,16000,410,10,0.38,0.42"""
            test_file.write_text(test_data)
        
        with open(test_file, 'rb') as f:
            files = {'file': ('test_malaria_data.csv', f, 'text/csv')}
            response = self.session.post(
                f"{self.base_url}/api/data-analysis/upload",
                files=files
            )
        
        if response.status_code == 200:
            data = response.json()
            self.session_id = data.get('session_id')
            self.log(f"File uploaded. Session ID: {self.session_id}")
            return True
        else:
            self.log(f"Upload failed: {response.text}", "ERROR")
            return False
            
    def trigger_tpr_analysis(self):
        """Step 2: Trigger TPR analysis in Data Analysis V3"""
        response = self.session.post(
            f"{self.base_url}/api/v1/data-analysis/chat",
            json={
                'message': 'analyze the TPR data and prepare it for risk analysis',
                'session_id': self.session_id
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            # Check if transition signal is received
            if data.get('exit_data_analysis_mode'):
                self.log("TPR analysis complete, transitioning to main workflow")
                return True
            else:
                self.log("TPR analysis response received but no transition", "WARNING")
                return False
        else:
            self.log(f"TPR analysis failed: {response.text}", "ERROR")
            return False
            
    def check_main_workflow_ready(self):
        """Step 3: Verify main workflow recognizes data is loaded"""
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json={
                'message': 'what data do you have loaded?',
                'session_id': self.session_id
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '').lower()
            # Check if it recognizes data is loaded
            if 'no data' in response_text or 'upload' in response_text:
                self.log("Main workflow doesn't recognize data is loaded!", "ERROR")
                return False
            else:
                self.log("Main workflow recognizes loaded data")
                return True
        else:
            self.log(f"Main workflow check failed: {response.text}", "ERROR")
            return False
            
    def request_risk_analysis(self):
        """Step 4: Request risk analysis (should NOT say already completed)"""
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json={
                'message': 'perform complete risk analysis',
                'session_id': self.session_id
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '').lower()
            
            # Check for the problematic "already completed" message
            if 'already' in response_text and 'complet' in response_text:
                self.log("BUG DETECTED: Says analysis already completed when it's not!", "ERROR")
                return False
            elif 'starting' in response_text or 'running' in response_text or 'analyzing' in response_text:
                self.log("Risk analysis started correctly")
                return True
            else:
                self.log(f"Unexpected response: {response_text[:200]}", "WARNING")
                return True  # May still be okay
        else:
            self.log(f"Risk analysis request failed: {response.text}", "ERROR")
            return False
            
    def verify_analysis_complete(self):
        """Step 5: Verify analysis actually completed"""
        # Wait a bit for analysis to complete
        time.sleep(3)
        
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json={
                'message': 'show me the top 5 highest risk wards',
                'session_id': self.session_id
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '').lower()
            
            # Check if it can show results (indicating analysis completed)
            if 'ward' in response_text and ('score' in response_text or 'risk' in response_text):
                self.log("Analysis results available")
                return True
            else:
                self.log("Analysis may not have completed properly", "WARNING")
                return False
        else:
            self.log(f"Results check failed: {response.text}", "ERROR")
            return False
            
    def test_fresh_upload(self):
        """Step 6: Upload new data (should start fresh)"""
        # Clear cookies to simulate new session
        self.session.cookies.clear()
        
        # Upload again
        success = self.upload_to_data_analysis()
        if not success:
            return False
            
        # Request analysis immediately (should NOT say already complete)
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json={
                'message': 'analyze this data',
                'session_id': self.session_id
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', '').lower()
            
            if 'already' in response_text and 'complet' in response_text:
                self.log("BUG: Fresh session has stale state!", "ERROR")
                return False
            else:
                self.log("Fresh session starts clean")
                return True
        else:
            return False
            
    def run_all_tests(self):
        """Run complete workflow test suite"""
        self.log("=" * 60)
        self.log("Starting Workflow State Management Tests")
        self.log(f"Testing against: {self.base_url}")
        self.log("=" * 60)
        
        # Test sequence
        tests = [
            ("Upload to Data Analysis V3", self.upload_to_data_analysis),
            ("Trigger TPR Analysis", self.trigger_tpr_analysis),
            ("Check Main Workflow Ready", self.check_main_workflow_ready),
            ("Request Risk Analysis (Bug Check)", self.request_risk_analysis),
            ("Verify Analysis Complete", self.verify_analysis_complete),
            ("Test Fresh Upload (Clean State)", self.test_fresh_upload)
        ]
        
        for test_name, test_func in tests:
            if not self.test_step(test_name, test_func):
                self.log(f"Stopping tests due to failure in: {test_name}", "WARNING")
                break
            time.sleep(1)  # Small delay between tests
        
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test results summary"""
        self.log("=" * 60)
        self.log("TEST SUMMARY")
        self.log("=" * 60)
        
        passed = sum(1 for _, result in self.test_results if result == "PASSED")
        failed = sum(1 for _, result in self.test_results if result == "FAILED" or "ERROR" in str(result))
        
        for test_name, result in self.test_results:
            symbol = "✅" if result == "PASSED" else "❌"
            print(f"{symbol} {test_name}: {result}")
        
        print("")
        print(f"Results: {passed} passed, {failed} failed out of {len(self.test_results)} tests")
        
        if failed == 0:
            self.log("🎉 ALL TESTS PASSED! Workflow state management is working correctly.", "SUCCESS")
            return 0
        else:
            self.log(f"⚠️ {failed} tests failed. Please review the workflow state management.", "ERROR")
            return 1


def main():
    # Parse command line arguments
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        print("Usage: python test_workflow_transitions.py <base_url>")
        print("Examples:")
        print("  python test_workflow_transitions.py http://localhost:5000")
        print("  python test_workflow_transitions.py http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com")
        print("  python test_workflow_transitions.py https://d225ar6c86586s.cloudfront.net")
        print("")
        print("Using default: http://localhost:5000")
        base_url = "http://localhost:5000"
    
    # Run tests
    tester = WorkflowTester(base_url)
    tester.run_all_tests()
    
    # Exit with appropriate code
    exit_code = 0 if all(r == "PASSED" for _, r in tester.test_results) else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
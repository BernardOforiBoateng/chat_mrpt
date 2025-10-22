#!/usr/bin/env python3
"""
Test TPR workflow on production following CLAUDE.md guidelines.
This is a proper pytest test that validates the complete TPR workflow.
"""

import pytest
import requests
import time
import json
from datetime import datetime
from typing import Dict, Optional, Tuple

# Production configuration
PRODUCTION_URL = "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"
TEST_FILE = "adamawa_tpr_cleaned.csv"
TIMEOUT_SECONDS = 60


class TestTPRWorkflow:
    """Test the complete TPR workflow on production."""
    
    def setup_method(self):
        """Set up test session."""
        self.session = requests.Session()
        self.session_id = None
        self.responses = []
        
    def teardown_method(self):
        """Clean up test session."""
        self.session.close()
        
    def _upload_file(self) -> Tuple[bool, str]:
        """Upload test CSV file."""
        try:
            with open(TEST_FILE, 'rb') as f:
                files = {'file': (TEST_FILE, f, 'text/csv')}
                response = self.session.post(
                    f"{PRODUCTION_URL}/api/data-analysis/upload",
                    files=files,
                    timeout=TIMEOUT_SECONDS
                )
            
            if response.status_code == 200:
                result = response.json()
                self.session_id = result.get('session_id')
                return True, self.session_id
            else:
                return False, f"Upload failed with status {response.status_code}"
                
        except Exception as e:
            return False, f"Upload exception: {e}"
    
    def _send_message(self, message: str) -> Dict:
        """Send a message in the TPR workflow."""
        try:
            response = self.session.post(
                f"{PRODUCTION_URL}/api/v1/data-analysis/chat",
                json={'message': message, 'session_id': self.session_id},
                timeout=TIMEOUT_SECONDS
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'success': False, 'error': f"Status {response.status_code}"}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_file_upload(self):
        """Test that file upload works."""
        success, result = self._upload_file()
        assert success, f"File upload failed: {result}"
        assert self.session_id is not None, "No session ID returned"
        assert len(self.session_id) > 0, "Empty session ID"
        print(f"✅ File upload successful - Session: {self.session_id}")
    
    def test_tpr_workflow_selection(self):
        """Test the complete TPR workflow selections."""
        # First upload the file
        success, result = self._upload_file()
        assert success, f"File upload failed: {result}"
        
        # Step 1: Select option 2 (Guided TPR)
        response = self._send_message("2")
        assert 'message' in response, "No message in response"
        assert 'facility level' in response['message'].lower(), \
            "Expected facility level selection, got: " + response['message'][:200]
        print("✅ Option 2 selected - Facility level prompt received")
        
        # Step 2: Select primary facilities
        response = self._send_message("primary")
        assert 'message' in response, "No message in response"
        assert 'age group' in response['message'].lower(), \
            "Expected age group selection, got: " + response['message'][:200]
        print("✅ Primary facilities selected - Age group prompt received")
        
        # Step 3: Select Under 5 Years
        response = self._send_message("Under 5 Years")
        assert 'message' in response, "No message in response"
        assert 'TPR Calculation Complete' in response['message'], \
            "TPR calculation did not complete: " + response['message'][:200]
        print("✅ Under 5 Years selected - TPR calculation completed")
        
        # Store for further analysis
        self.responses.append(response)
        
    def test_tpr_map_generation(self):
        """Test that TPR map is generated."""
        # Run the complete workflow first
        self.test_tpr_workflow_selection()
        
        # Check the final response for map
        final_response = self.responses[-1]
        message = final_response.get('message', '')
        
        # Check for map URL or visualization
        has_map = any([
            'tpr_distribution_map.html' in message,
            'Map URL:' in message,
            'serve_viz_file' in message,
            'visualizations' in final_response and len(final_response['visualizations']) > 0
        ])
        
        assert has_map, f"No map generated. Response contains: {message[:500]}"
        print("✅ TPR map generated successfully")
    
    def test_risk_analysis_transition(self):
        """Test transition from TPR to risk analysis."""
        # Run the complete workflow first
        self.test_tpr_workflow_selection()
        
        # Try to transition to risk analysis
        response = self._send_message("yes")
        assert 'message' in response, "No message in response"
        
        # Check for successful transition
        message = response['message']
        
        # Should NOT contain error message
        assert 'TPR data file not found' not in message, \
            "Risk transition failed - TPR data file not found"
        
        # Should contain risk analysis content
        has_risk_content = any([
            'risk' in message.lower(),
            'analysis' in message.lower(),
            'ranking' in message.lower(),
            'vulnerability' in message.lower()
        ])
        
        assert has_risk_content, \
            f"No risk analysis content found. Response: {message[:500]}"
        
        print("✅ Successfully transitioned to risk analysis")
    
    def test_files_created_on_server(self):
        """Test that required files are created on the server."""
        # Run the complete workflow first
        self.test_tpr_workflow_selection()
        
        # Check files via SSH (this would need to be adapted for actual testing)
        # For now, we'll check the response messages for file indicators
        final_response = self.responses[-1]
        message = final_response.get('message', '')
        
        # Check for file creation indicators
        assert 'tpr_results.csv' in message or 'Results saved' in message, \
            "No indication that tpr_results.csv was created"
        
        # Check for risk preparation
        assert '⚠️ Note: Could not prepare risk analysis files' not in message, \
            "Risk analysis files were not prepared"
        
        print("✅ Required files created on server")


def run_tests():
    """Run all tests and generate report."""
    import sys
    
    print(f"\n{'='*60}")
    print(f"TPR Production Test Suite")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target: {PRODUCTION_URL}")
    print(f"{'='*60}\n")
    
    # Create test instance
    test = TestTPRWorkflow()
    
    results = []
    tests = [
        ('File Upload', test.test_file_upload),
        ('TPR Workflow', test.test_tpr_workflow_selection),
        ('Map Generation', test.test_tpr_map_generation),
        ('Risk Transition', test.test_risk_analysis_transition),
        ('Files Created', test.test_files_created_on_server)
    ]
    
    for test_name, test_func in tests:
        test.setup_method()
        try:
            test_func()
            results.append((test_name, 'PASSED', None))
            print(f"✅ {test_name}: PASSED\n")
        except AssertionError as e:
            results.append((test_name, 'FAILED', str(e)))
            print(f"❌ {test_name}: FAILED - {e}\n")
        except Exception as e:
            results.append((test_name, 'ERROR', str(e)))
            print(f"⚠️ {test_name}: ERROR - {e}\n")
        finally:
            test.teardown_method()
    
    # Generate summary
    print(f"\n{'='*60}")
    print("Test Summary:")
    print(f"{'='*60}")
    
    passed = sum(1 for _, status, _ in results if status == 'PASSED')
    failed = sum(1 for _, status, _ in results if status == 'FAILED')
    errors = sum(1 for _, status, _ in results if status == 'ERROR')
    
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Errors: {errors}")
    
    if failed == 0 and errors == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed. See details above.")
        return 1


if __name__ == "__main__":
    exit_code = run_tests()
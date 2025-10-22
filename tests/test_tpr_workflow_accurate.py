#!/usr/bin/env python
"""
Accurate TPR Workflow Test
Tests the TPR workflow exactly as the frontend does it.
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import re

# Configuration
BASE_URL = "http://localhost:3094"
TPR_FILE_PATH = "instance/uploads/6e90b139-5d30-40fd-91ad-4af66fec5f00/tpr_data.xlsx"

class TPRWorkflowTest:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.conversation_log = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log test progress."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def log_conversation(self, role: str, message: str):
        """Log conversation for analysis."""
        self.conversation_log.append({
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "message": message[:500] + "..." if len(message) > 500 else message
        })
        
    def test_step(self, name: str, func, *args, **kwargs) -> bool:
        """Execute a test step and track results."""
        self.log(f"Testing: {name}")
        try:
            result = func(*args, **kwargs)
            self.test_results.append((name, "PASS", None))
            self.log(f"✓ {name} passed", "SUCCESS")
            return result
        except Exception as e:
            self.test_results.append((name, "FAIL", str(e)))
            self.log(f"✗ {name} failed: {e}", "ERROR")
            return False
    
    def initialize_session(self) -> bool:
        """Initialize session by visiting index page."""
        response = self.session.get(f"{BASE_URL}/")
        
        # Check if TPR state was reset
        if response.status_code == 200:
            self.log(f"Session initialized: {self.session.cookies.get('session', 'Unknown')}")
            return True
        return False
    
    def send_streaming_message(self, message: str) -> Optional[str]:
        """Send message through streaming endpoint exactly as frontend does."""
        self.log_conversation("User", message)
        
        response = self.session.post(
            f"{BASE_URL}/send_message_streaming",
            json={"message": message},
            stream=True
        )
        
        full_response = ""
        chunks = []
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        chunk_data = json.loads(line_str[6:])  # Remove 'data: ' prefix
                        if 'content' in chunk_data:
                            full_response += chunk_data['content']
                        chunks.append(chunk_data)
                        
                        # Check if done
                        if chunk_data.get('done', False):
                            break
                    except json.JSONDecodeError:
                        continue
        
        self.log_conversation("Assistant", full_response)
        
        # Return the full response and metadata from last chunk
        if chunks:
            last_chunk = chunks[-1]
            return {
                'response': full_response,
                'status': last_chunk.get('status', 'success'),
                'stage': last_chunk.get('stage'),
                'workflow': last_chunk.get('workflow'),
                'full_chunks': chunks
            }
        return None
    
    def upload_tpr_file(self) -> Dict:
        """Upload TPR file exactly as frontend does."""
        with open(TPR_FILE_PATH, 'rb') as f:
            files = {
                'csv_file': ('nmep_malaria_data.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            }
            response = self.session.post(f"{BASE_URL}/upload", files=files)
        
        if response.status_code == 200:
            data = response.json()
            
            # Log what we got back
            self.log(f"Upload response status: {data.get('status')}")
            self.log(f"Upload type: {data.get('upload_type')}")
            self.log(f"Workflow: {data.get('workflow')}")
            
            # Check for TPR response
            if 'tpr_response' in data:
                self.log_conversation("System", data['tpr_response'])
                
            return data
        else:
            raise Exception(f"Upload failed with status {response.status_code}: {response.text}")
    
    def validate_tpr_summary(self, response: Dict) -> bool:
        """Validate the TPR summary matches expected format."""
        tpr_response = response.get('tpr_response', '')
        
        # Check for expected content
        expected_patterns = [
            r"I've analyzed your NMEP TPR data file",
            r"Geographic Coverage:",
            r"(\d+) states:",
            r"Time Period:",
            r"State-Level Breakdown:",
            r"Data Quality by State:",
            r"Which state would you like to analyze\?"
        ]
        
        missing = []
        for pattern in expected_patterns:
            if not re.search(pattern, tpr_response, re.IGNORECASE):
                missing.append(pattern)
        
        if missing:
            self.log(f"Missing patterns in TPR summary: {missing}", "WARNING")
        
        return len(missing) == 0
    
    def validate_state_overview(self, response: str) -> bool:
        """Validate state overview matches expected format."""
        expected_patterns = [
            r"Perfect! I'll focus on .* for TPR analysis",
            r"Overview:",
            r"Geographic.*LGAs.*wards",
            r"Facilities.*health facilities",
            r"Facility Distribution",
            r"Data Quality",
            r"Ward Distribution",
            r"Would you like to proceed with TPR calculation"
        ]
        
        missing = []
        for pattern in expected_patterns:
            if not re.search(pattern, response, re.IGNORECASE | re.DOTALL):
                missing.append(pattern)
        
        if missing:
            self.log(f"Missing patterns in state overview: {missing}", "WARNING")
        
        return len(missing) == 0
    
    def validate_facility_selection(self, response: str) -> bool:
        """Validate facility selection prompt."""
        expected_patterns = [
            r"For TPR analysis in.*I recommend focusing on Primary Health Facilities",
            r"They represent.*% of your.*data",
            r"Current Selection:",
            r"Do you want to:",
            r"1\. Use Primary Health Facilities only \(recommended\)",
            r"2\. Include Secondary facilities",
            r"3\. Include all facility types"
        ]
        
        missing = []
        for pattern in expected_patterns:
            if not re.search(pattern, response, re.IGNORECASE | re.DOTALL):
                missing.append(pattern)
        
        return len(missing) == 0
    
    def run_complete_workflow(self):
        """Run the complete TPR workflow test."""
        self.log("\n" + "="*60)
        self.log("STARTING TPR WORKFLOW TEST")
        self.log("="*60 + "\n")
        
        # Step 1: Initialize session
        if not self.test_step("Initialize session", self.initialize_session):
            return False
        
        # Step 2: Send initial greeting
        greeting_result = self.test_step(
            "Send initial greeting",
            self.send_streaming_message,
            "Hi, I'd like to analyze some malaria data"
        )
        if not greeting_result:
            return False
        
        time.sleep(1)  # Give server time to process
        
        # Step 3: Upload TPR file
        upload_result = self.test_step("Upload TPR file", self.upload_tpr_file)
        if not upload_result:
            return False
        
        # Validate TPR summary
        self.test_step("Validate TPR summary format", self.validate_tpr_summary, upload_result)
        
        time.sleep(2)  # Give server time to process
        
        # Step 4: Select state
        state_result = self.test_step(
            "Select Osun State",
            self.send_streaming_message,
            "I would like to analyze Osun State"
        )
        if not state_result:
            return False
        
        # Validate state overview
        if state_result:
            self.test_step(
                "Validate state overview",
                self.validate_state_overview,
                state_result['response']
            )
        
        time.sleep(1)
        
        # Step 5: Confirm to proceed
        confirm_result = self.test_step(
            "Confirm state selection",
            self.send_streaming_message,
            "Yes, let's proceed"
        )
        if not confirm_result:
            return False
        
        # Validate facility selection prompt
        if confirm_result:
            self.test_step(
                "Validate facility selection prompt",
                self.validate_facility_selection,
                confirm_result['response']
            )
        
        time.sleep(1)
        
        # Step 6: Select facility level
        facility_result = self.test_step(
            "Select Primary facilities",
            self.send_streaming_message,
            "1"  # Select Primary facilities
        )
        if not facility_result:
            return False
        
        time.sleep(1)
        
        # Step 7: Select age group
        age_result = self.test_step(
            "Select Under 5 age group",
            self.send_streaming_message,
            "under 5"
        )
        if not age_result:
            return False
        
        # Check if TPR calculation completed
        if age_result and "Calculated TPR for" in age_result['response']:
            self.log("✓ TPR calculation completed successfully!", "SUCCESS")
        
        return True
    
    def generate_report(self):
        """Generate test report."""
        self.log("\n" + "="*60)
        self.log("TEST REPORT")
        self.log("="*60 + "\n")
        
        # Summary
        passed = sum(1 for _, status, _ in self.test_results if status == "PASS")
        failed = sum(1 for _, status, _ in self.test_results if status == "FAIL")
        total = len(self.test_results)
        
        self.log(f"Total tests: {total}")
        self.log(f"Passed: {passed}")
        self.log(f"Failed: {failed}")
        self.log(f"Success rate: {(passed/total*100):.1f}%")
        
        # Detailed results
        self.log("\nDetailed Results:")
        for test_name, status, error in self.test_results:
            if status == "PASS":
                self.log(f"  ✓ {test_name}")
            else:
                self.log(f"  ✗ {test_name}: {error}")
        
        # Save conversation log
        log_filename = f"tpr_workflow_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_filename, 'w') as f:
            json.dump({
                "test_run": datetime.now().isoformat(),
                "results": {
                    "total": total,
                    "passed": passed,
                    "failed": failed
                },
                "test_details": self.test_results,
                "conversation": self.conversation_log
            }, f, indent=2)
        
        self.log(f"\nDetailed log saved to: {log_filename}")
        
        return passed == total

def main():
    """Main test runner."""
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/ping", timeout=2)
        if response.status_code != 200:
            print(f"ERROR: Server not responding properly at {BASE_URL}")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print(f"ERROR: Server not running at {BASE_URL}")
        print("Please start the server with: python run.py")
        sys.exit(1)
    
    # Run test
    tester = TPRWorkflowTest()
    
    try:
        success = tester.run_complete_workflow()
        tester.generate_report()
        
        if success:
            print("\n✅ TPR WORKFLOW TEST PASSED!")
            sys.exit(0)
        else:
            print("\n❌ TPR WORKFLOW TEST FAILED!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
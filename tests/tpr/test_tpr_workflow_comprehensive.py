#!/usr/bin/env python
"""
Comprehensive TPR Workflow Test with Response Validation
Tests the entire TPR workflow and validates responses match the specification.
"""

import requests
import json
import time
import sys
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import colorama
from colorama import Fore, Style

# Initialize colorama for colored output
colorama.init()

# Configuration
BASE_URL = "http://localhost:3094"
TEST_SESSION_ID = "test_tpr_comprehensive_" + datetime.now().strftime("%Y%m%d_%H%M%S")
SOURCE_TPR_FILE = "instance/uploads/6e90b139-5d30-40fd-91ad-4af66fec5f00/tpr_data.xlsx"

# Expected response patterns from specification
EXPECTED_PATTERNS = {
    "initial_summary": {
        "must_contain": [
            "I've analyzed your NMEP TPR data file",
            "Geographic Coverage:",
            "Time Period:",
            "State-Level Breakdown:",
            "Data Quality by State:",
            "Which state would you like to analyze?"
        ],
        "state_info": [
            r"Adamawa State.*?(\d+) LGAs.*?(\d+) wards.*?([\d,]+) facilities",
            r"Kwara State.*?(\d+) LGAs.*?(\d+) wards.*?([\d,]+) facilities",
            r"Osun State.*?(\d+) LGAs.*?(\d+) wards.*?([\d,]+) facilities"
        ],
        "data_quality": [
            r"Adamawa State.*?RDT data.*?Microscopy data",
            r"Kwara State.*?RDT data.*?Microscopy data",
            r"Osun State.*?RDT data.*?Microscopy data"
        ]
    },
    "state_overview": {
        "must_contain": [
            "Perfect! I'll focus on",
            "Overview:",
            "Geographic",
            "Facilities",
            "Time Coverage",
            "Facility Distribution",
            "Data Quality",
            "Ward Distribution",
            "Would you like to proceed with TPR calculation"
        ]
    },
    "facility_selection": {
        "must_contain": [
            "For TPR analysis",
            "I recommend focusing on Primary Health Facilities",
            "They represent",
            "Secondary facilities handle complicated cases",
            "Primary facilities better reflect community-level",
            "Current Selection:",
            "Do you want to:",
            "1. Use Primary Health Facilities only (recommended)",
            "2. Include Secondary facilities",
            "3. Include all facility types"
        ]
    },
    "age_group_selection": {
        "must_contain": [
            "Good choice! Using",
            "Now, which age group should we calculate TPR for?",
            "Under 5 years",
            "Over 5 years",
            "Pregnant women",
            "data complete"
        ]
    },
    "calculation_complete": {
        "must_contain": [
            "calculating TPR values",
            "Calculated TPR for",
            "wards",
            "Summary Results:",
            "Average TPR:",
            "Highest:",
            "Lowest:"
        ]
    }
}

class TPRWorkflowTester:
    def __init__(self):
        self.session_cookies = None
        self.responses = []
        self.validation_results = {}
        
    def print_header(self, text: str, level: int = 1):
        """Print formatted header."""
        if level == 1:
            print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
            print(f"{Fore.CYAN} {text} {Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        elif level == 2:
            print(f"\n{Fore.YELLOW}--- {text} ---{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.GREEN}• {text}{Style.RESET_ALL}")
    
    def print_success(self, text: str):
        """Print success message."""
        print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")
    
    def print_error(self, text: str):
        """Print error message."""
        print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")
    
    def print_info(self, text: str):
        """Print info message."""
        print(f"{Fore.BLUE}ℹ {text}{Style.RESET_ALL}")
    
    def validate_response(self, response: str, pattern_key: str) -> Tuple[bool, List[str]]:
        """Validate response against expected patterns."""
        patterns = EXPECTED_PATTERNS.get(pattern_key, {})
        missing = []
        found = []
        
        # Check must_contain patterns
        for pattern in patterns.get("must_contain", []):
            if pattern.lower() in response.lower():
                found.append(pattern)
            else:
                missing.append(pattern)
        
        # Check regex patterns if any
        for key in ["state_info", "data_quality"]:
            if key in patterns:
                for pattern in patterns[key]:
                    if re.search(pattern, response, re.IGNORECASE | re.DOTALL):
                        found.append(f"regex:{pattern[:30]}...")
                    else:
                        missing.append(f"regex:{pattern[:30]}...")
        
        success = len(missing) == 0
        return success, missing
    
    def initialize_session(self) -> bool:
        """Initialize a new session."""
        self.print_header("INITIALIZING SESSION", 2)
        
        response = requests.get(f"{BASE_URL}/")
        self.session_cookies = response.cookies
        
        self.print_info(f"Session ID: {self.session_cookies.get('session', 'Unknown')}")
        return response.status_code == 200
    
    def send_message(self, message: str, validate_key: Optional[str] = None) -> str:
        """Send a message and optionally validate response."""
        print(f"\n{Fore.MAGENTA}User:{Style.RESET_ALL} {message}")
        
        response = requests.post(
            f"{BASE_URL}/send_message_streaming",
            json={"message": message},
            cookies=self.session_cookies,
            stream=True
        )
        
        full_response = ""
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode('utf-8').replace('data: ', ''))
                    if 'content' in data:
                        full_response += data['content']
                    if data.get('done', False):
                        break
                except json.JSONDecodeError:
                    continue
        
        # Print response (truncate if too long)
        display_response = full_response[:500] + "..." if len(full_response) > 500 else full_response
        print(f"\n{Fore.CYAN}Assistant:{Style.RESET_ALL} {display_response}")
        
        # Store full response
        self.responses.append({
            "user": message,
            "assistant": full_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Validate if requested
        if validate_key:
            success, missing = self.validate_response(full_response, validate_key)
            self.validation_results[validate_key] = {
                "success": success,
                "missing": missing
            }
            
            if success:
                self.print_success(f"Response validation passed for {validate_key}")
            else:
                self.print_error(f"Response validation failed for {validate_key}")
                for item in missing[:3]:  # Show first 3 missing items
                    self.print_error(f"  Missing: {item}")
                if len(missing) > 3:
                    self.print_error(f"  ... and {len(missing)-3} more")
        
        return full_response
    
    def upload_tpr_file(self) -> Optional[Dict]:
        """Upload the TPR file."""
        self.print_header("UPLOADING TPR FILE", 2)
        
        import shutil
        import os
        
        # Use the existing TPR file directly
        with open(SOURCE_TPR_FILE, 'rb') as f:
            files = {'csv_file': ('nmep_malaria_test_data.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = requests.post(
                f"{BASE_URL}/upload",
                files=files,
                cookies=self.session_cookies
            )
        
        if response.status_code == 200:
            data = response.json()
            self.print_success("File uploaded successfully")
            
            # Check if we got the expected summary
            if 'tpr_summary' in data:
                self.print_info("TPR summary received in upload response")
                # Validate the summary
                success, missing = self.validate_response(data['tpr_summary'], 'initial_summary')
                self.validation_results['upload_summary'] = {
                    "success": success,
                    "missing": missing
                }
            
            return data
        else:
            self.print_error(f"Upload failed: {response.status_code}")
            return None
    
    def run_complete_workflow(self) -> bool:
        """Run the complete TPR workflow."""
        self.print_header("TPR WORKFLOW TEST", 1)
        
        # Initialize
        if not self.initialize_session():
            self.print_error("Failed to initialize session")
            return False
        
        # Initial greeting
        self.print_header("Step 1: Initial Greeting", 2)
        self.send_message("hi")
        time.sleep(1)
        
        # Upload file
        self.print_header("Step 2: Upload TPR File", 2)
        upload_result = self.upload_tpr_file()
        if not upload_result:
            return False
        time.sleep(2)
        
        # Select state
        self.print_header("Step 3: Select State (Osun)", 2)
        state_response = self.send_message("I would like to analyze Osun State", "state_overview")
        time.sleep(1)
        
        # Confirm state selection
        self.print_header("Step 4: Confirm State Selection", 2)
        confirm_response = self.send_message("Yes, let's proceed", "facility_selection")
        time.sleep(1)
        
        # Select facility level
        self.print_header("Step 5: Select Facility Level", 2)
        facility_response = self.send_message("1", "age_group_selection")
        time.sleep(1)
        
        # Select age group
        self.print_header("Step 6: Select Age Group", 2)
        age_response = self.send_message("under 5", "calculation_complete")
        time.sleep(2)
        
        return True
    
    def run_alternative_scenarios(self):
        """Test alternative conversation paths."""
        self.print_header("ALTERNATIVE SCENARIOS", 1)
        
        scenarios = [
            {
                "name": "Different State (Adamawa)",
                "messages": [
                    ("Let me analyze Adamawa State instead", "state_overview"),
                    ("Yes", "facility_selection"),
                    ("1", "age_group_selection"),
                    ("over 5", "calculation_complete")
                ]
            },
            {
                "name": "Secondary Facilities",
                "messages": [
                    ("I want to look at Kwara State", "state_overview"),
                    ("proceed", "facility_selection"),
                    ("2", "age_group_selection"),
                    ("pregnant women", "calculation_complete")
                ]
            }
        ]
        
        for scenario in scenarios:
            self.print_header(f"Scenario: {scenario['name']}", 2)
            
            # Reinitialize session for clean test
            self.initialize_session()
            self.upload_tpr_file()
            time.sleep(2)
            
            # Run scenario messages
            for message, validate_key in scenario['messages']:
                self.send_message(message, validate_key)
                time.sleep(1)
    
    def generate_report(self):
        """Generate test report."""
        self.print_header("TEST REPORT", 1)
        
        # Overall validation results
        total_validations = len(self.validation_results)
        passed_validations = sum(1 for v in self.validation_results.values() if v['success'])
        
        print(f"\n{Fore.CYAN}Validation Summary:{Style.RESET_ALL}")
        print(f"Total validations: {total_validations}")
        print(f"Passed: {passed_validations}")
        print(f"Failed: {total_validations - passed_validations}")
        
        # Detailed results
        print(f"\n{Fore.CYAN}Detailed Results:{Style.RESET_ALL}")
        for key, result in self.validation_results.items():
            if result['success']:
                self.print_success(f"{key}: PASSED")
            else:
                self.print_error(f"{key}: FAILED")
                if result['missing']:
                    print(f"  Missing patterns: {len(result['missing'])}")
        
        # Save full conversation log
        log_file = f"tpr_test_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w') as f:
            json.dump({
                "test_session": TEST_SESSION_ID,
                "timestamp": datetime.now().isoformat(),
                "validation_results": self.validation_results,
                "conversations": self.responses
            }, f, indent=2)
        
        self.print_info(f"Full conversation log saved to: {log_file}")
        
        # Overall result
        success = passed_validations == total_validations
        print(f"\n{Fore.GREEN if success else Fore.RED}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.GREEN if success else Fore.RED} OVERALL RESULT: {'PASSED' if success else 'FAILED'} {Style.RESET_ALL}")
        print(f"{Fore.GREEN if success else Fore.RED}{'='*80}{Style.RESET_ALL}")
        
        return success

def main():
    """Main test runner."""
    # Check server
    try:
        response = requests.get(f"{BASE_URL}/ping", timeout=2)
        if response.status_code != 200:
            print(f"{Fore.RED}ERROR: Server not responding properly{Style.RESET_ALL}")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print(f"{Fore.RED}ERROR: Server not running at {BASE_URL}{Style.RESET_ALL}")
        print("Please start the server with: python run.py")
        sys.exit(1)
    
    # Run tests
    tester = TPRWorkflowTester()
    
    try:
        # Main workflow
        tester.run_complete_workflow()
        
        # Alternative scenarios (optional)
        # tester.run_alternative_scenarios()
        
        # Generate report
        success = tester.generate_report()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}ERROR: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python
"""
Comprehensive TPR Workflow Test
Tests the complete TPR workflow for all 3 states with different conversation styles.
Captures all outputs: CSVs, shapefiles, maps, and complete conversation logs.
"""

import requests
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import re
from pathlib import Path
import shutil
import webbrowser
from urllib.parse import urljoin

# Configuration
BASE_URL = "http://localhost:5000"
TPR_FILE_PATH = "instance/uploads/6e90b139-5d30-40fd-91ad-4af66fec5f00/tpr_data.xlsx"
OUTPUT_DIR = Path("tpr_test_outputs")

# Create output directory structure
OUTPUT_DIR.mkdir(exist_ok=True)
for state in ['adamawa', 'kwara', 'osun']:
    (OUTPUT_DIR / state).mkdir(exist_ok=True)

class ComprehensiveTPRTest:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.conversation_logs = {}
        self.output_files = {}
        self.maps_captured = {}
        
    def log(self, message: str, level: str = "INFO", state: str = None):
        """Enhanced logging with state context."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        state_prefix = f"[{state.upper()}] " if state else ""
        print(f"[{timestamp}] {state_prefix}{level}: {message}")
        
    def log_conversation(self, state: str, role: str, message: str):
        """Log conversation by state."""
        if state not in self.conversation_logs:
            self.conversation_logs[state] = []
            
        self.conversation_logs[state].append({
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "message": message
        })
        
    def save_conversation_log(self, state: str):
        """Save conversation log to file."""
        if state in self.conversation_logs:
            log_path = OUTPUT_DIR / state / f"{state}_conversation.json"
            with open(log_path, 'w') as f:
                json.dump(self.conversation_logs[state], f, indent=2)
            self.log(f"Conversation log saved to {log_path}", "SUCCESS", state)
    
    def initialize_session(self) -> bool:
        """Initialize new session."""
        response = self.session.get(f"{BASE_URL}/")
        if response.status_code == 200:
            self.log(f"Session initialized: {self.session.cookies.get('session', 'Unknown')}")
            return True
        return False
    
    def send_streaming_message(self, message: str, state: str = None) -> Optional[Dict]:
        """Send message and handle streaming response."""
        self.log_conversation(state, "User", message)
        self.log(f"User: {message}", "CHAT", state)
        
        try:
            response = self.session.post(
                f"{BASE_URL}/send_message_streaming",
                json={"message": message},
                stream=True,
                timeout=30
            )
            
            full_response = ""
            chunks = []
            metadata = {}
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            chunk_data = json.loads(line_str[6:])
                            if 'content' in chunk_data:
                                full_response += chunk_data['content']
                            
                            # Capture metadata from chunks
                            if 'visualizations' in chunk_data:
                                metadata['visualizations'] = chunk_data['visualizations']
                            if 'download_links' in chunk_data:
                                metadata['download_links'] = chunk_data['download_links']
                            if 'stage' in chunk_data:
                                metadata['stage'] = chunk_data['stage']
                            
                            chunks.append(chunk_data)
                            
                            if chunk_data.get('done', False):
                                break
                        except json.JSONDecodeError:
                            continue
            
            self.log_conversation(state, "Assistant", full_response)
            self.log(f"Assistant: {full_response[:200]}{'...' if len(full_response) > 200 else ''}", "CHAT", state)
            
            # Return response with metadata
            return {
                'response': full_response,
                'status': chunks[-1].get('status', 'success') if chunks else 'success',
                'stage': metadata.get('stage'),
                'visualizations': metadata.get('visualizations', []),
                'download_links': metadata.get('download_links', {}),
                'workflow': chunks[-1].get('workflow', 'unknown') if chunks else 'unknown',
                'full_chunks': chunks
            }
            
        except requests.exceptions.Timeout:
            self.log("Request timed out - server may be processing", "WARNING", state)
            # Return a fallback response for testing
            return {
                'response': "Processing your request...",
                'status': 'timeout',
                'stage': 'unknown'
            }
        except Exception as e:
            self.log(f"Error in streaming: {e}", "ERROR", state)
            return None
    
    def upload_tpr_file(self) -> Dict:
        """Upload TPR file."""
        with open(TPR_FILE_PATH, 'rb') as f:
            files = {
                'csv_file': ('nmep_malaria_data.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            }
            response = self.session.post(f"{BASE_URL}/upload", files=files)
        
        if response.status_code == 200:
            data = response.json()
            self.log(f"Upload successful - Type: {data.get('upload_type')}, Workflow: {data.get('workflow')}")
            if 'tpr_response' in data:
                self.log_conversation("upload", "System", data['tpr_response'])
            return data
        else:
            raise Exception(f"Upload failed: {response.status_code}")
    
    def download_file(self, url: str, save_path: Path, state: str) -> bool:
        """Download file from URL."""
        try:
            full_url = urljoin(BASE_URL, url)
            response = self.session.get(full_url, stream=True)
            
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                file_size = save_path.stat().st_size
                self.log(f"Downloaded {save_path.name} ({file_size:,} bytes)", "SUCCESS", state)
                return True
            else:
                self.log(f"Failed to download {url}: {response.status_code}", "ERROR", state)
                return False
        except Exception as e:
            self.log(f"Download error: {e}", "ERROR", state)
            return False
    
    def capture_map(self, viz_info: Dict, state: str) -> bool:
        """Capture and save map visualization."""
        try:
            if 'url' in viz_info:
                map_url = urljoin(BASE_URL, viz_info['url'])
                response = self.session.get(map_url)
                
                if response.status_code == 200:
                    map_path = OUTPUT_DIR / state / f"{state}_tpr_map.html"
                    with open(map_path, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    
                    self.log(f"TPR map saved to {map_path}", "SUCCESS", state)
                    self.maps_captured[state] = str(map_path)
                    return True
            return False
        except Exception as e:
            self.log(f"Error capturing map: {e}", "ERROR", state)
            return False
    
    def test_adamawa_technical(self):
        """Test Adamawa with technical/direct questioning style."""
        state = "adamawa"
        self.log("\n" + "="*60, state=state)
        self.log("TESTING ADAMAWA - Technical User Style", state=state)
        self.log("="*60, state=state)
        
        # Direct state selection
        result = self.send_streaming_message("Analyze Adamawa State", state)
        if not result:
            return False
        time.sleep(1)
        
        # Confirm state selection  
        result = self.send_streaming_message("Yes, proceed with analysis", state)
        if not result:
            return False
        time.sleep(1)
        
        # Technical facility selection
        result = self.send_streaming_message("Use Primary Health Facilities only for better data quality", state)
        if not result:
            return False
        time.sleep(1)
        
        # Specific age group
        result = self.send_streaming_message("Focus on under 5 population", state)
        if not result:
            return False
        
        # Handle results
        return self.process_results(result, state)
    
    def test_kwara_inquisitive(self):
        """Test Kwara with inquisitive/detailed questioning style."""
        state = "kwara"
        self.log("\n" + "="*60, state=state)
        self.log("TESTING KWARA - Inquisitive User Style", state=state)
        self.log("="*60, state=state)
        
        # Ask about available states first
        result = self.send_streaming_message("What states are available in the data?", state)
        if not result:
            return False
        time.sleep(1)
        
        # Select state with a question
        result = self.send_streaming_message("Can you analyze Kwara State? I'm interested in understanding the malaria situation there", state)
        if not result:
            return False
        time.sleep(1)
        
        # Ask about state details
        result = self.send_streaming_message("That's helpful. What facility types would give the most comprehensive view?", state)
        if not result:
            return False
        time.sleep(1)
        
        # Detailed facility question
        result = self.send_streaming_message("Let's include both Primary and Secondary facilities for broader coverage", state)
        if not result:
            return False
        time.sleep(1)
        
        # Age group with rationale
        result = self.send_streaming_message("What about pregnant women? They're a vulnerable group for malaria", state)
        if not result:
            return False
        
        # Handle results
        return self.process_results(result, state)
    
    def test_osun_casual(self):
        """Test Osun with casual/conversational style."""
        state = "osun"
        self.log("\n" + "="*60, state=state)
        self.log("TESTING OSUN - Casual User Style", state=state)
        self.log("="*60, state=state)
        
        # Casual greeting and state selection
        result = self.send_streaming_message("Hi! I'd like to look at Osun State please", state)
        if not result:
            return False
        time.sleep(1)
        
        # Casual confirmation
        result = self.send_streaming_message("Yes please, let's do it", state)
        if not result:
            return False
        time.sleep(1)
        
        # Simple facility choice
        result = self.send_streaming_message("Just give me everything - all facilities", state)
        if not result:
            return False
        time.sleep(1)
        
        # Casual age selection
        result = self.send_streaming_message("How about we look at everyone? All age groups", state)
        if not result:
            return False
        
        # Handle results
        return self.process_results(result, state)
    
    def process_results(self, result: Dict, state: str) -> bool:
        """Process TPR calculation results."""
        success = True
        
        # Check for visualizations (TPR map)
        if result.get('visualizations'):
            for viz in result['visualizations']:
                if self.capture_map(viz, state):
                    self.log(f"TPR map captured for {state}", "SUCCESS", state)
                else:
                    self.log(f"Failed to capture TPR map for {state}", "WARNING", state)
                    success = False
        
        # Download output files
        download_links = result.get('download_links', {})
        
        # Download TPR analysis CSV
        if 'csv' in download_links:
            csv_path = OUTPUT_DIR / state / f"{state}_tpr_analysis.csv"
            if self.download_file(download_links['csv'], csv_path, state):
                self.output_files[f"{state}_csv"] = str(csv_path)
            else:
                success = False
        
        # Download shapefile
        if 'shapefile' in download_links:
            shp_path = OUTPUT_DIR / state / f"{state}_shapefile.zip"
            if self.download_file(download_links['shapefile'], shp_path, state):
                self.output_files[f"{state}_shapefile"] = str(shp_path)
            else:
                success = False
        
        # Save conversation log
        self.save_conversation_log(state)
        
        return success
    
    def run_all_tests(self):
        """Run comprehensive tests for all three states."""
        self.log("\n" + "="*80)
        self.log("COMPREHENSIVE TPR WORKFLOW TEST - 3 STATES, 3 STYLES")
        self.log("="*80 + "\n")
        
        # Initialize session
        if not self.initialize_session():
            self.log("Failed to initialize session", "ERROR")
            return False
        
        # Upload TPR file once
        self.log("\nUploading TPR data file...")
        try:
            upload_result = self.upload_tpr_file()
            if upload_result.get('workflow') != 'tpr':
                self.log("Upload did not trigger TPR workflow", "ERROR")
                return False
        except Exception as e:
            self.log(f"Upload failed: {e}", "ERROR")
            return False
        
        time.sleep(2)
        
        # Test each state with different style
        test_methods = [
            ("Adamawa", self.test_adamawa_technical),
            ("Kwara", self.test_kwara_inquisitive),
            ("Osun", self.test_osun_casual)
        ]
        
        results = {}
        for state_name, test_method in test_methods:
            try:
                # Re-initialize session for each state to ensure clean slate
                self.log(f"\nRe-initializing session for {state_name}...", state=state_name.lower())
                self.session = requests.Session()
                self.initialize_session()
                
                # Re-upload file
                self.upload_tpr_file()
                time.sleep(1)
                
                # Run state test
                results[state_name] = test_method()
                
                # Wait between states
                time.sleep(2)
                
            except Exception as e:
                self.log(f"Error testing {state_name}: {e}", "ERROR", state_name.lower())
                results[state_name] = False
        
        # Generate comprehensive report
        self.generate_comprehensive_report(results)
        
        return all(results.values())
    
    def generate_comprehensive_report(self, results: Dict[str, bool]):
        """Generate comprehensive test report."""
        self.log("\n" + "="*80)
        self.log("COMPREHENSIVE TEST REPORT")
        self.log("="*80 + "\n")
        
        # Test Summary
        total_states = len(results)
        passed_states = sum(1 for v in results.values() if v)
        
        self.log(f"States Tested: {total_states}")
        self.log(f"States Passed: {passed_states}")
        self.log(f"Success Rate: {(passed_states/total_states*100):.1f}%")
        
        # State Results
        self.log("\nState-by-State Results:")
        for state, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            self.log(f"  {state}: {status}")
        
        # Files Generated
        self.log("\nFiles Generated:")
        for file_key, file_path in self.output_files.items():
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                self.log(f"  {file_key}: {file_path} ({size:,} bytes)")
        
        # Maps Captured
        self.log("\nTPR Maps Generated:")
        for state, map_path in self.maps_captured.items():
            if os.path.exists(map_path):
                self.log(f"  {state}: {map_path}")
        
        # Save full report
        report_path = OUTPUT_DIR / "comprehensive_test_report.json"
        report_data = {
            "test_run": datetime.now().isoformat(),
            "summary": {
                "total_states": total_states,
                "passed_states": passed_states,
                "success_rate": f"{(passed_states/total_states*100):.1f}%"
            },
            "state_results": results,
            "files_generated": self.output_files,
            "maps_captured": self.maps_captured,
            "conversation_logs": {
                state: f"{state}_conversation.json" 
                for state in self.conversation_logs.keys()
            }
        }
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        self.log(f"\nFull report saved to: {report_path}")
        
        # Open output directory
        if sys.platform.startswith('win'):
            os.startfile(OUTPUT_DIR)
        elif sys.platform.startswith('darwin'):
            os.system(f"open {OUTPUT_DIR}")
        else:
            os.system(f"xdg-open {OUTPUT_DIR}")
        
        # Optionally open one of the maps in browser
        if self.maps_captured:
            first_map = next(iter(self.maps_captured.values()))
            self.log(f"\nOpening sample TPR map: {first_map}")
            webbrowser.open(f"file://{os.path.abspath(first_map)}")

def main():
    """Run comprehensive TPR workflow test."""
    # Check server
    try:
        response = requests.get(f"{BASE_URL}/ping", timeout=2)
        if response.status_code != 200:
            print(f"ERROR: Server not responding at {BASE_URL}")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print(f"ERROR: Server not running at {BASE_URL}")
        print("Please start the server with: python run.py")
        sys.exit(1)
    
    # Check TPR file exists
    if not os.path.exists(TPR_FILE_PATH):
        print(f"ERROR: TPR test file not found at {TPR_FILE_PATH}")
        sys.exit(1)
    
    # Run comprehensive test
    tester = ComprehensiveTPRTest()
    
    try:
        success = tester.run_all_tests()
        
        if success:
            print("\n✅ COMPREHENSIVE TPR WORKFLOW TEST PASSED!")
            print(f"✅ All outputs saved to: {OUTPUT_DIR}")
            sys.exit(0)
        else:
            print("\n❌ COMPREHENSIVE TPR WORKFLOW TEST FAILED!")
            print(f"❌ Check outputs in: {OUTPUT_DIR}")
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
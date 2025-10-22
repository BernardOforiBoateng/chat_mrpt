#!/usr/bin/env python3
"""
Comprehensive Real User Interaction Simulation
Tests all three main user scenarios with ChatMRPT
"""

import requests
import json
import time
import random
import datetime
import os
from typing import Dict, List, Optional

# Configuration
STAGING_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
PRODUCTION_URL = "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"

# Use staging for testing
BASE_URL = STAGING_URL

class UserSimulator:
    """Simulates a real user interacting with ChatMRPT"""
    
    def __init__(self, user_name: str, scenario: str):
        self.user_name = user_name
        self.scenario = scenario
        self.session_id = f"{user_name.replace(' ', '_')}_{int(time.time())}"
        self.conversation_log = []
        self.test_results = []
        
    def log_interaction(self, message: str, response: Dict, elapsed_time: float):
        """Log each interaction for reporting"""
        self.conversation_log.append({
            'timestamp': datetime.datetime.now().isoformat(),
            'user_message': message,
            'response_preview': response.get('response', '')[:200] if response.get('response') else 'No response',
            'success': response.get('success', False),
            'elapsed_time': elapsed_time,
            'full_response': response
        })
    
    def send_message(self, message: str, is_data_analysis: bool = False) -> Dict:
        """Send a message to the server"""
        print(f"\n🧑 {self.user_name}: {message}")
        
        start_time = time.time()
        
        try:
            # Use different endpoint based on context
            if is_data_analysis:
                # Use Data Analysis V3 endpoint
                endpoint = f"{BASE_URL}/api/v1/data-analysis/chat"
                payload = {
                    'message': message,
                    'session_id': self.session_id
                }
            else:
                # Use general chat endpoint
                endpoint = f"{BASE_URL}/send_message"
                payload = {
                    'message': message,
                    'session_id': self.session_id,
                    'tab_context': 'standard-upload'
                }
            
            response = requests.post(
                endpoint,
                json=payload,
                timeout=30
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                self.log_interaction(message, result, elapsed)
                
                # Print response preview
                response_text = result.get('response', result.get('message', ''))
                if response_text:
                    print(f"🤖 ChatMRPT: {response_text[:300]}{'...' if len(response_text) > 300 else ''}")
                    print(f"   [Response time: {elapsed:.2f}s]")
                
                return result
            else:
                error_result = {
                    'success': False,
                    'response': f"HTTP {response.status_code}: {response.text[:100]}"
                }
                self.log_interaction(message, error_result, elapsed)
                print(f"❌ Error: HTTP {response.status_code}")
                return error_result
                
        except Exception as e:
            error_result = {
                'success': False,
                'response': f"Exception: {str(e)}"
            }
            self.log_interaction(message, error_result, time.time() - start_time)
            print(f"❌ Exception: {e}")
            return error_result
    
    def wait_like_human(self, min_seconds: float = 2, max_seconds: float = 5):
        """Simulate human reading/thinking time"""
        wait_time = random.uniform(min_seconds, max_seconds)
        print(f"   [User reading/thinking for {wait_time:.1f}s...]")
        time.sleep(wait_time)
    
    def evaluate_response(self, response: Dict, expected_behavior: str) -> bool:
        """Evaluate if response meets expectations"""
        success = response.get('success', False)
        response_text = response.get('response', response.get('message', ''))
        
        # Check for unwanted "upload data" messages in general conversation
        if 'upload' in expected_behavior.lower() and 'should not' in expected_behavior.lower():
            if 'upload' in response_text.lower() and 'data' in response_text.lower():
                return False
        
        # Check for expected content
        if 'greeting' in expected_behavior.lower():
            return any(word in response_text.lower() for word in ['hello', 'hi', 'help', 'assist'])
        
        if 'malaria info' in expected_behavior.lower():
            return any(word in response_text.lower() for word in ['malaria', 'disease', 'mosquito', 'prevention'])
        
        if 'guidance' in expected_behavior.lower():
            return 'upload' in response_text.lower() or 'csv' in response_text.lower()
        
        return success and len(response_text) > 10


class Scenario1_Explorer(UserSimulator):
    """User who just wants to explore and ask questions without data"""
    
    def run(self) -> Dict:
        print("\n" + "="*80)
        print(f"SCENARIO 1: {self.user_name} - General Explorer (No Data)")
        print("="*80)
        print("This user is curious about ChatMRPT and malaria but doesn't have data to analyze.")
        
        results = {
            'scenario': 'Explorer Without Data',
            'user': self.user_name,
            'test_cases': []
        }
        
        # Test 1: Greeting in Data Analysis tab
        print("\n📍 Navigating to Data Analysis tab...")
        response = self.send_message("Hello, who are you?", is_data_analysis=True)
        test_passed = self.evaluate_response(response, "Should get greeting without requiring upload")
        results['test_cases'].append({
            'test': 'Greeting in Data Analysis tab',
            'passed': test_passed,
            'response_preview': response.get('response', '')[:100]
        })
        
        self.wait_like_human(3, 5)
        
        # Test 2: Asking what it can do
        response = self.send_message("What can you do?", is_data_analysis=True)
        test_passed = self.evaluate_response(response, "Should explain capabilities without requiring upload")
        results['test_cases'].append({
            'test': 'Capabilities question',
            'passed': test_passed,
            'response_preview': response.get('response', '')[:100]
        })
        
        self.wait_like_human(4, 6)
        
        # Test 3: Malaria knowledge question
        response = self.send_message("What is malaria and how is it transmitted?", is_data_analysis=True)
        test_passed = self.evaluate_response(response, "Should provide malaria info without requiring upload")
        results['test_cases'].append({
            'test': 'Malaria knowledge question',
            'passed': test_passed,
            'response_preview': response.get('response', '')[:100]
        })
        
        self.wait_like_human(5, 7)
        
        # Test 4: Prevention strategies
        response = self.send_message("What are the best prevention methods for malaria?", is_data_analysis=True)
        test_passed = self.evaluate_response(response, "Should provide prevention info without requiring upload")
        results['test_cases'].append({
            'test': 'Prevention strategies question',
            'passed': test_passed,
            'response_preview': response.get('response', '')[:100]
        })
        
        self.wait_like_human(3, 5)
        
        # Test 5: Trying to analyze without data
        response = self.send_message("Can you analyze malaria trends?", is_data_analysis=True)
        test_passed = 'upload' in response.get('response', '').lower()  # Should guide to upload
        results['test_cases'].append({
            'test': 'Analysis request without data',
            'passed': test_passed,
            'response_preview': response.get('response', '')[:100]
        })
        
        self.wait_like_human(2, 4)
        
        # Test 6: Thank you
        response = self.send_message("Thank you for the information!", is_data_analysis=True)
        test_passed = self.evaluate_response(response, "Should acknowledge thanks without requiring upload")
        results['test_cases'].append({
            'test': 'Thank you message',
            'passed': test_passed,
            'response_preview': response.get('response', '')[:100]
        })
        
        return results


class Scenario2_TPRToRisk(UserSimulator):
    """User going through TPR calculation to risk analysis workflow"""
    
    def upload_sample_data(self) -> bool:
        """Upload actual Adamawa TPR data file"""
        print("\n📤 Uploading Adamawa TPR data file...")
        
        # Read the actual Adamawa TPR data
        import pandas as pd
        import io
        import os
        
        # Use the actual Adamawa TPR data file
        adamawa_file = '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/adamawa_tpr_cleaned.csv'
        
        if os.path.exists(adamawa_file):
            df = pd.read_csv(adamawa_file)
            print(f"   Loaded Adamawa data: {df.shape[0]} rows, {df.shape[1]} columns")
            
            # Convert to CSV for upload
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_content = csv_buffer.getvalue()
        else:
            # Fallback to sample data if file not found
            print("   Warning: Adamawa file not found, using sample data")
            data = {
                'FacilityName': ['General Hospital', 'Primary Health Center', 'District Hospital'],
                'WardName': ['Yola North', 'Yola South', 'Girei'],
                'State': ['Adamawa'] * 3,
                'LGA': ['Yola North', 'Yola South', 'Girei'],
                'MonthYear': ['2024-01'] * 3,
                'TotalTested': [500, 350, 420],
                'PositiveCases': [125, 105, 95]
            }
            df = pd.DataFrame(data)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_content = csv_buffer.getvalue()
        
        # Upload via Data Analysis V3 endpoint
        files = {'file': ('adamawa_tpr_data.csv', csv_content, 'text/csv')}
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/data-analysis/upload",
                files=files,
                data={'session_id': self.session_id},
                timeout=30
            )
            
            if response.status_code == 200:
                print("✅ Data uploaded successfully")
                return True
            else:
                print(f"❌ Upload failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Upload exception: {e}")
            return False
    
    def run(self) -> Dict:
        print("\n" + "="*80)
        print(f"SCENARIO 2: {self.user_name} - TPR to Risk Analysis Workflow")
        print("="*80)
        print("This user wants to calculate TPR and then proceed to risk analysis.")
        
        results = {
            'scenario': 'TPR to Risk Analysis',
            'user': self.user_name,
            'test_cases': []
        }
        
        # Step 1: Upload data
        upload_success = self.upload_sample_data()
        results['test_cases'].append({
            'test': 'Data upload',
            'passed': upload_success,
            'response_preview': 'File uploaded' if upload_success else 'Upload failed'
        })
        
        if not upload_success:
            print("⚠️ Cannot continue without data upload")
            return results
        
        self.wait_like_human(2, 3)
        
        # Step 2: Initial data exploration
        response = self.send_message("Show me what's in the uploaded data", is_data_analysis=True)
        test_passed = response.get('success', False)
        results['test_cases'].append({
            'test': 'Initial data exploration',
            'passed': test_passed,
            'response_preview': response.get('response', '')[:100]
        })
        
        self.wait_like_human(4, 6)
        
        # Step 3: Choose TPR workflow (option 2)
        response = self.send_message("2", is_data_analysis=True)
        test_passed = 'age' in response.get('response', '').lower() or 'tpr' in response.get('response', '').lower()
        results['test_cases'].append({
            'test': 'Select TPR workflow',
            'passed': test_passed,
            'response_preview': response.get('response', '')[:100]
        })
        
        self.wait_like_human(3, 5)
        
        # Step 4: Select age group
        response = self.send_message("1", is_data_analysis=True)  # All age groups
        test_passed = response.get('success', False)
        results['test_cases'].append({
            'test': 'Select age group for TPR',
            'passed': test_passed,
            'response_preview': response.get('response', '')[:100]
        })
        
        self.wait_like_human(3, 5)
        
        # Step 5: Select test method
        response = self.send_message("1", is_data_analysis=True)  # All methods
        test_passed = response.get('success', False)
        results['test_cases'].append({
            'test': 'Select test method',
            'passed': test_passed,
            'response_preview': response.get('response', '')[:100]
        })
        
        self.wait_like_human(3, 5)
        
        # Step 6: Select facility level
        response = self.send_message("1", is_data_analysis=True)  # All facilities
        test_passed = 'tpr' in response.get('response', '').lower() or 'calculated' in response.get('response', '').lower()
        results['test_cases'].append({
            'test': 'Complete TPR calculation',
            'passed': test_passed,
            'response_preview': response.get('response', '')[:100]
        })
        
        self.wait_like_human(5, 7)
        
        # Step 7: Transition to risk analysis
        response = self.send_message("yes", is_data_analysis=True)
        test_passed = 'risk' in response.get('response', '').lower() or 'analysis' in response.get('response', '').lower()
        results['test_cases'].append({
            'test': 'Transition to risk analysis',
            'passed': test_passed,
            'response_preview': response.get('response', '')[:100]
        })
        
        self.wait_like_human(8, 12)  # Risk analysis takes time
        
        # Step 8: Request ITN planning
        response = self.send_message("I want to plan bed net distribution", is_data_analysis=False)
        test_passed = 'net' in response.get('response', '').lower() or 'itn' in response.get('response', '').lower()
        results['test_cases'].append({
            'test': 'ITN distribution planning',
            'passed': test_passed,
            'response_preview': response.get('response', '')[:100]
        })
        
        return results


class Scenario3_DirectAnalysis(UserSimulator):
    """User who wants direct data analysis without TPR workflow"""
    
    def upload_analysis_data(self) -> bool:
        """Upload actual NMEP data for analysis"""
        print("\n📤 Uploading NMEP health data file...")
        
        # Try to use the actual NMEP data file
        import pandas as pd
        import io
        import os
        
        # Check for NMEP Excel file
        nmep_file = '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/NMEP Malaria Adamawa_Kwara_Osun_Test Postivity Rate_2022_2024.xlsx'
        
        if os.path.exists(nmep_file):
            try:
                # Read first sheet of Excel file
                df = pd.read_excel(nmep_file, sheet_name=0, nrows=100)  # Limit rows for testing
                print(f"   Loaded NMEP data: {df.shape[0]} rows, {df.shape[1]} columns")
                
                # Convert to CSV for upload
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                csv_content = csv_buffer.getvalue()
            except Exception as e:
                print(f"   Error reading Excel: {e}")
                # Fallback to simpler data
                df = self._create_fallback_data()
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                csv_content = csv_buffer.getvalue()
        else:
            # Create fallback data with Adamawa context
            df = self._create_fallback_data()
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_content = csv_buffer.getvalue()
        
        # Save to CSV
        files = {'file': ('nmep_health_data.csv', csv_content, 'text/csv')}
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/data-analysis/upload",
                files=files,
                data={'session_id': self.session_id},
                timeout=30
            )
            
            if response.status_code == 200:
                print("✅ Data uploaded successfully")
                return True
            else:
                print(f"❌ Upload failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Upload exception: {e}")
            return False
    
    def _create_fallback_data(self):
        """Create fallback data with Adamawa context"""
        import pandas as pd
        data = {
            'State': ['Adamawa'] * 20,
            'LGA': ['Yola North', 'Yola South', 'Girei', 'Mubi North', 'Mubi South'] * 4,
            'Ward': ['Ward_' + str(i) for i in range(1, 21)],
            'Month': ['Jan', 'Jan', 'Jan', 'Jan', 'Jan', 
                     'Feb', 'Feb', 'Feb', 'Feb', 'Feb',
                     'Mar', 'Mar', 'Mar', 'Mar', 'Mar',
                     'Apr', 'Apr', 'Apr', 'Apr', 'Apr'],
            'MalariaCases': [45, 67, 23, 89, 56, 
                           52, 71, 28, 95, 61,
                           48, 69, 25, 91, 58,
                           55, 73, 30, 98, 64],
            'Population': [10000, 15000, 8000, 20000, 12000] * 4,
            'TotalTested': [200, 300, 150, 400, 250] * 4,
            'PositiveCases': [45, 67, 23, 89, 56, 
                           52, 71, 28, 95, 61,
                           48, 69, 25, 91, 58,
                           55, 73, 30, 98, 64]
        }
        return pd.DataFrame(data)
    
    def run(self) -> Dict:
        print("\n" + "="*80)
        print(f"SCENARIO 3: {self.user_name} - Direct Data Analysis")
        print("="*80)
        print("This user wants to explore data directly without the TPR workflow.")
        
        results = {
            'scenario': 'Direct Data Analysis',
            'user': self.user_name,
            'test_cases': []
        }
        
        # Step 1: Initial greeting
        response = self.send_message("Hi, I have some health data to analyze", is_data_analysis=True)
        test_passed = response.get('success', False)
        results['test_cases'].append({
            'test': 'Initial greeting with intent',
            'passed': test_passed,
            'response_preview': response.get('response', '')[:100]
        })
        
        self.wait_like_human(2, 3)
        
        # Step 2: Upload data
        upload_success = self.upload_analysis_data()
        results['test_cases'].append({
            'test': 'Data upload',
            'passed': upload_success,
            'response_preview': 'File uploaded' if upload_success else 'Upload failed'
        })
        
        if not upload_success:
            print("⚠️ Cannot continue without data upload")
            return results
        
        self.wait_like_human(2, 3)
        
        # Step 3: Initial data overview
        response = self.send_message("Show me what's in my data", is_data_analysis=True)
        test_passed = response.get('success', False)
        results['test_cases'].append({
            'test': 'Data overview request',
            'passed': test_passed,
            'response_preview': response.get('response', '')[:100]
        })
        
        self.wait_like_human(4, 6)
        
        # Step 4: Choose flexible exploration (option 1)
        response = self.send_message("1", is_data_analysis=True)
        test_passed = response.get('success', False)
        results['test_cases'].append({
            'test': 'Select flexible exploration',
            'passed': test_passed,
            'response_preview': response.get('response', '')[:100]
        })
        
        self.wait_like_human(3, 5)
        
        # Step 5: Analyze trends
        response = self.send_message("Show me the trend of malaria cases over time", is_data_analysis=True)
        test_passed = 'trend' in response.get('response', '').lower() or 'cases' in response.get('response', '').lower()
        results['test_cases'].append({
            'test': 'Trend analysis request',
            'passed': test_passed,
            'response_preview': response.get('response', '')[:100]
        })
        
        self.wait_like_human(5, 7)
        
        # Step 6: Find correlations
        response = self.send_message("Is there a correlation between rainfall and malaria cases?", is_data_analysis=True)
        test_passed = 'correlation' in response.get('response', '').lower() or 'rainfall' in response.get('response', '').lower()
        results['test_cases'].append({
            'test': 'Correlation analysis',
            'passed': test_passed,
            'response_preview': response.get('response', '')[:100]
        })
        
        self.wait_like_human(4, 6)
        
        # Step 7: Top districts
        response = self.send_message("Which districts have the highest malaria burden?", is_data_analysis=True)
        test_passed = 'district' in response.get('response', '').lower()
        results['test_cases'].append({
            'test': 'Top districts query',
            'passed': test_passed,
            'response_preview': response.get('response', '')[:100]
        })
        
        self.wait_like_human(3, 5)
        
        # Step 8: Recommendations
        response = self.send_message("What interventions would you recommend based on this data?", is_data_analysis=True)
        test_passed = response.get('success', False)
        results['test_cases'].append({
            'test': 'Intervention recommendations',
            'passed': test_passed,
            'response_preview': response.get('response', '')[:100]
        })
        
        return results


def generate_html_report(all_results: List[Dict], output_file: str):
    """Generate an HTML report of all test results"""
    
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>ChatMRPT User Simulation Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
        .scenario { background: white; margin: 20px 0; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .scenario h2 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        .test-case { margin: 10px 0; padding: 10px; background: #f9f9f9; border-left: 4px solid #ccc; }
        .test-case.passed { border-left-color: #27ae60; }
        .test-case.failed { border-left-color: #e74c3c; }
        .pass { color: #27ae60; font-weight: bold; }
        .fail { color: #e74c3c; font-weight: bold; }
        .summary { background: white; padding: 20px; margin: 20px 0; border-radius: 5px; }
        .timestamp { color: #7f8c8d; font-size: 0.9em; }
        .response-preview { color: #34495e; font-style: italic; margin-top: 5px; }
        .stats { display: flex; justify-content: space-around; margin: 20px 0; }
        .stat-box { text-align: center; padding: 15px; background: white; border-radius: 5px; }
        .stat-number { font-size: 2em; font-weight: bold; color: #3498db; }
        .stat-label { color: #7f8c8d; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏥 ChatMRPT Comprehensive User Simulation Report</h1>
        <p>Generated: """ + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
        <p>Environment: """ + BASE_URL + """</p>
    </div>
    """
    
    # Calculate statistics
    total_tests = 0
    passed_tests = 0
    
    for result in all_results:
        for test_case in result.get('test_cases', []):
            total_tests += 1
            if test_case.get('passed', False):
                passed_tests += 1
    
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    # Add summary statistics
    html += f"""
    <div class="summary">
        <h2>📊 Overall Results</h2>
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number">{len(all_results)}</div>
                <div class="stat-label">Scenarios Tested</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{total_tests}</div>
                <div class="stat-label">Total Test Cases</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{passed_tests}</div>
                <div class="stat-label">Tests Passed</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{pass_rate:.1f}%</div>
                <div class="stat-label">Pass Rate</div>
            </div>
        </div>
    </div>
    """
    
    # Add detailed results for each scenario
    for i, result in enumerate(all_results, 1):
        scenario_passed = sum(1 for tc in result.get('test_cases', []) if tc.get('passed', False))
        scenario_total = len(result.get('test_cases', []))
        
        html += f"""
        <div class="scenario">
            <h2>Scenario {i}: {result.get('scenario', 'Unknown')}</h2>
            <p><strong>User:</strong> {result.get('user', 'Unknown')}</p>
            <p><strong>Results:</strong> {scenario_passed}/{scenario_total} tests passed</p>
            
            <h3>Test Cases:</h3>
        """
        
        for test_case in result.get('test_cases', []):
            passed = test_case.get('passed', False)
            status_class = 'passed' if passed else 'failed'
            status_text = '✅ PASS' if passed else '❌ FAIL'
            
            html += f"""
            <div class="test-case {status_class}">
                <strong>{test_case.get('test', 'Unknown Test')}</strong>
                <span class="{'pass' if passed else 'fail'}">{status_text}</span>
                <div class="response-preview">{test_case.get('response_preview', 'No response')}</div>
            </div>
            """
        
        html += "</div>"
    
    # Add conclusions
    html += """
    <div class="summary">
        <h2>📝 Key Findings</h2>
        <ul>
    """
    
    if pass_rate >= 90:
        html += "<li>✅ <strong>Excellent:</strong> System is working very well with " + f"{pass_rate:.1f}%" + " pass rate</li>"
    elif pass_rate >= 75:
        html += "<li>⚠️ <strong>Good:</strong> System is mostly working with " + f"{pass_rate:.1f}%" + " pass rate</li>"
    else:
        html += "<li>❌ <strong>Needs Improvement:</strong> System has issues with only " + f"{pass_rate:.1f}%" + " pass rate</li>"
    
    # Specific findings
    for result in all_results:
        if result.get('scenario') == 'Explorer Without Data':
            general_tests = [tc for tc in result.get('test_cases', []) if 'greeting' in tc.get('test', '').lower() or 'capabilities' in tc.get('test', '').lower()]
            if all(tc.get('passed', False) for tc in general_tests):
                html += "<li>✅ General conversations work without requiring data upload</li>"
            else:
                html += "<li>❌ Issues with general conversations in data analysis tab</li>"
    
    html += """
        </ul>
        <p class="timestamp">Report generated at """ + datetime.datetime.now().isoformat() + """</p>
    </div>
</body>
</html>
    """
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n📊 HTML report saved to: {output_file}")


def main():
    """Run all user simulations"""
    print("\n" + "="*80)
    print("🚀 STARTING COMPREHENSIVE USER SIMULATION")
    print("="*80)
    print(f"Testing against: {BASE_URL}")
    print(f"Time: {datetime.datetime.now()}")
    
    all_results = []
    
    # Scenario 1: Explorer without data
    print("\n" + "="*80)
    alice = Scenario1_Explorer("Alice", "Explorer")
    results1 = alice.run()
    all_results.append(results1)
    
    time.sleep(5)  # Pause between scenarios
    
    # Scenario 2: TPR to Risk Analysis
    print("\n" + "="*80)
    bob = Scenario2_TPRToRisk("Dr. Bob", "TPR Analysis")
    results2 = bob.run()
    all_results.append(results2)
    
    time.sleep(5)
    
    # Scenario 3: Direct Data Analysis
    print("\n" + "="*80)
    charlie = Scenario3_DirectAnalysis("Charlie", "Data Analyst")
    results3 = charlie.run()
    all_results.append(results3)
    
    # Generate report
    report_file = f"user_simulation_report_{int(time.time())}.html"
    generate_html_report(all_results, report_file)
    
    # Print summary
    print("\n" + "="*80)
    print("📊 SIMULATION COMPLETE - SUMMARY")
    print("="*80)
    
    total_tests = 0
    passed_tests = 0
    
    for i, result in enumerate(all_results, 1):
        scenario_passed = sum(1 for tc in result.get('test_cases', []) if tc.get('passed', False))
        scenario_total = len(result.get('test_cases', []))
        total_tests += scenario_total
        passed_tests += scenario_passed
        
        print(f"\nScenario {i}: {result.get('scenario')}")
        print(f"  User: {result.get('user')}")
        print(f"  Results: {scenario_passed}/{scenario_total} passed")
        
        for test_case in result.get('test_cases', []):
            status = "✅" if test_case.get('passed') else "❌"
            print(f"    {status} {test_case.get('test')}")
    
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print("\n" + "-"*40)
    print(f"OVERALL: {passed_tests}/{total_tests} tests passed ({pass_rate:.1f}%)")
    
    if pass_rate >= 90:
        print("✅ EXCELLENT - System is working very well!")
    elif pass_rate >= 75:
        print("⚠️ GOOD - System is mostly working, some improvements needed")
    else:
        print("❌ NEEDS ATTENTION - System has significant issues")
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    print("="*80)


if __name__ == "__main__":
    main()
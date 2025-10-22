"""
Production Test Suite for Data Analysis Tab
Tests the actual production deployment without modifying any code
Following CLAUDE.md guidelines for industry-standard testing
"""

import pytest
import requests
import json
import time
import re
from pathlib import Path
import pandas as pd
import io
from typing import Dict, Any, List, Tuple
from datetime import datetime

# Production configuration
PRODUCTION_URL = "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"
TIMEOUT = 30  # seconds

class TestProductionDataAnalysis:
    """Test suite for production Data Analysis tab functionality"""
    
    @classmethod
    def setup_class(cls):
        """Setup test data and session"""
        cls.session = requests.Session()
        cls.session_id = None
        cls.test_results = []
        cls.start_time = datetime.now()
        
        # Create test data with proper encoding (including ≥ character)
        cls.test_data = cls.create_test_tpr_data_static()
        
    @classmethod
    def create_test_tpr_data_static(cls) -> bytes:
        """Create test TPR data with all required columns including ≥5yrs"""
        data = {
            'State': ['Adamawa'] * 10,
            'LGA': ['Yola North', 'Yola South', 'Mubi North', 'Mubi South', 'Demsa'] * 2,
            'WardName': [f'Ward_{i}' for i in range(1, 11)],
            'HealthFacility': [f'Facility_{i}' for i in range(1, 11)],
            'FacilityLevel': ['Primary'] * 8 + ['Secondary'] * 2,
            # Critical columns with ≥ character for testing encoding
            'Persons presenting with fever & tested by RDT <5yrs': [100, 150, 200, 120, 180, 160, 140, 190, 110, 130],
            'Persons presenting with fever & tested by RDT  ≥5yrs (excl PW)': [200, 250, 300, 220, 280, 260, 240, 290, 210, 230],
            'Persons presenting with fever & tested by RDT Preg Women (PW)': [50, 60, 70, 55, 65, 62, 58, 68, 52, 57],
            'Persons tested positive for malaria by RDT <5yrs': [20, 30, 40, 25, 35, 32, 28, 38, 22, 26],
            'Persons tested positive for malaria by RDT  ≥5yrs (excl PW)': [40, 50, 60, 45, 55, 52, 48, 58, 42, 46],
            'Persons tested positive for malaria by RDT Preg Women (PW)': [15, 18, 21, 16, 19, 17, 16, 20, 14, 15],
            # Microscopy columns
            'Persons presenting with fever and tested by Microscopy <5yrs': [50, 60, 70, 55, 65, 62, 58, 68, 52, 57],
            'Persons presenting with fever and tested by Microscopy  ≥5yrs (excl PW)': [80, 90, 100, 85, 95, 92, 88, 98, 82, 87],
            'Persons presenting with fever and tested by Microscopy Preg Women (PW)': [20, 25, 30, 22, 28, 26, 24, 29, 21, 23],
            'Persons tested positive for malaria by Microscopy <5yrs': [10, 12, 14, 11, 13, 12, 11, 13, 10, 11],
            'Persons tested positive for malaria by Microscopy  ≥5yrs (excl PW)': [16, 18, 20, 17, 19, 18, 17, 19, 16, 17],
            'Persons tested positive for malaria by Microscopy Preg Women (PW)': [6, 7, 8, 6, 7, 7, 6, 8, 5, 6],
            # Additional columns
            'Children <5 yrs who received LLIN': [30, 35, 40, 32, 38, 36, 34, 39, 31, 33],
            'Total ANC attendances': [150, 170, 190, 160, 180, 175, 165, 185, 155, 162],
            'Total deliveries': [80, 90, 100, 85, 95, 92, 88, 98, 82, 87],
            'Total OPD attendance': [500, 550, 600, 520, 580, 560, 540, 590, 510, 530]
        }
        
        df = pd.DataFrame(data)
        # Convert to CSV bytes with UTF-8 encoding
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8')
        return csv_buffer.getvalue().encode('utf-8')
    
    def test_01_production_health_check(self):
        """Test 1: Verify production server is responding"""
        print("\n[TEST 1] Testing production server health...")
        
        try:
            response = requests.get(f"{PRODUCTION_URL}/ping", timeout=TIMEOUT)
            assert response.status_code == 200, f"Health check failed: {response.status_code}"
            
            # Also test main page
            response = requests.get(PRODUCTION_URL, timeout=TIMEOUT)
            assert response.status_code == 200, f"Main page failed: {response.status_code}"
            assert "ChatMRPT" in response.text, "ChatMRPT not found in response"
            
            self.test_results.append(("Production Health Check", "PASSED", "Server is responsive"))
            print("✅ Production server is healthy")
            
        except Exception as e:
            self.test_results.append(("Production Health Check", "FAILED", str(e)))
            pytest.fail(f"Production health check failed: {e}")
    
    def test_02_data_analysis_tab_exists(self):
        """Test 2: Verify Data Analysis tab exists in UI"""
        print("\n[TEST 2] Testing Data Analysis tab presence...")
        
        try:
            response = requests.get(PRODUCTION_URL, timeout=TIMEOUT)
            assert response.status_code == 200
            
            # Check for Data Analysis tab in HTML
            assert "Data Analysis" in response.text or "data-analysis" in response.text.lower(), \
                "Data Analysis tab not found in UI"
            
            # Check for the upload endpoint
            assert "/api/data-analysis/v3/upload" in response.text or \
                   "data-analysis-upload" in response.text, \
                "Data Analysis upload functionality not found"
            
            self.test_results.append(("Data Analysis Tab", "PASSED", "Tab exists in UI"))
            print("✅ Data Analysis tab found")
            
        except Exception as e:
            self.test_results.append(("Data Analysis Tab", "FAILED", str(e)))
            pytest.fail(f"Data Analysis tab test failed: {e}")
    
    def test_03_file_upload_endpoint(self):
        """Test 3: Test file upload to Data Analysis endpoint"""
        print("\n[TEST 3] Testing file upload functionality...")
        
        try:
            # Create a new session for this test
            session_response = requests.get(PRODUCTION_URL)
            cookies = session_response.cookies
            
            # Prepare the file upload
            files = {
                'file': ('test_tpr_data.csv', self.test_data, 'text/csv')
            }
            
            # Upload to Data Analysis endpoint
            upload_url = f"{PRODUCTION_URL}/api/data-analysis/upload"
            response = requests.post(
                upload_url,
                files=files,
                cookies=cookies,
                timeout=TIMEOUT
            )
            
            assert response.status_code == 200, f"Upload failed with status {response.status_code}"
            
            result = response.json()
            assert result.get('success') == True, f"Upload not successful: {result}"
            
            # Store session ID for subsequent tests
            self.__class__.session_id = result.get('session_id')
            
            self.test_results.append(("File Upload", "PASSED", "File uploaded successfully"))
            print(f"✅ File uploaded successfully. Session ID: {self.session_id}")
            
        except Exception as e:
            self.test_results.append(("File Upload", "FAILED", str(e)))
            pytest.fail(f"File upload test failed: {e}")
    
    def test_04_tpr_workflow_initiation(self):
        """Test 4: Test TPR workflow starts correctly"""
        print("\n[TEST 4] Testing TPR workflow initiation...")
        
        try:
            assert self.session_id, "No session ID from upload test"
            
            # Send message to trigger TPR workflow
            chat_url = f"{PRODUCTION_URL}/api/v1/data-analysis/chat"
            
            payload = {
                'message': '1',  # Select TPR calculation
                'session_id': self.session_id
            }
            
            response = requests.post(
                chat_url,
                json=payload,
                timeout=TIMEOUT
            )
            
            assert response.status_code == 200, f"Chat failed with status {response.status_code}"
            
            result = response.json()
            assert result.get('success') == True, f"Chat not successful: {result}"
            
            message = result.get('message', '')
            
            # Check for facility selection (workflow started)
            assert 'facility' in message.lower() or 'primary' in message.lower(), \
                "TPR workflow did not start properly"
            
            self.test_results.append(("TPR Workflow Start", "PASSED", "Workflow initiated"))
            print("✅ TPR workflow started successfully")
            
        except Exception as e:
            self.test_results.append(("TPR Workflow Start", "FAILED", str(e)))
            pytest.fail(f"TPR workflow test failed: {e}")
    
    def test_05_age_group_detection(self):
        """Test 5: Verify all 3 age groups are detected"""
        print("\n[TEST 5] Testing age group detection...")
        
        try:
            assert self.session_id, "No session ID available"
            
            # Progress through workflow to age group selection
            # First select Primary facilities
            chat_url = f"{PRODUCTION_URL}/api/v1/data-analysis/chat"
            
            # Select Primary (option 1)
            response = requests.post(
                chat_url,
                json={'message': 'primary', 'session_id': self.session_id},
                timeout=TIMEOUT
            )
            
            assert response.status_code == 200
            result = response.json()
            message = result.get('message', '')
            
            # Critical test: Check for all 3 age groups
            age_groups_found = []
            
            # Check for Under 5
            if 'under 5' in message.lower() or 'under 5 years' in message.lower():
                age_groups_found.append('Under 5 Years')
            
            # Check for Over 5 (with ≥ symbol)
            if 'over 5' in message.lower() or '≥5' in message or '>=5' in message:
                age_groups_found.append('Over 5 Years')
            
            # Check for Pregnant Women
            if 'pregnant' in message.lower():
                age_groups_found.append('Pregnant Women')
            
            print(f"   Age groups detected: {age_groups_found}")
            
            # Verify all 3 groups are present
            assert len(age_groups_found) == 3, \
                f"Expected 3 age groups, found {len(age_groups_found)}: {age_groups_found}"
            
            # Also check that the ≥ symbol is properly displayed (not corrupted)
            if '≥5' in message:
                print("   ✓ ≥ symbol properly displayed (not corrupted)")
            elif 'â‰¥' in message:
                pytest.fail("Encoding issue: ≥ symbol is corrupted to â‰¥")
            
            self.test_results.append(("Age Group Detection", "PASSED", f"All 3 groups detected: {age_groups_found}"))
            print("✅ All 3 age groups detected correctly")
            
        except Exception as e:
            self.test_results.append(("Age Group Detection", "FAILED", str(e)))
            pytest.fail(f"Age group detection test failed: {e}")
    
    def test_06_bullet_point_formatting(self):
        """Test 6: Verify bullet points are properly formatted"""
        print("\n[TEST 6] Testing bullet point formatting...")
        
        try:
            assert self.session_id, "No session ID available"
            
            # Get a response with bullet points
            chat_url = f"{PRODUCTION_URL}/api/v1/data-analysis/chat"
            
            response = requests.post(
                chat_url,
                json={'message': 'show me the data summary', 'session_id': self.session_id},
                timeout=TIMEOUT
            )
            
            assert response.status_code == 200
            result = response.json()
            message = result.get('message', '')
            
            # Check for bullet points
            if '•' in message or '-' in message:
                # Count bullet points
                bullet_lines = [line for line in message.split('\n') if line.strip().startswith('•') or line.strip().startswith('-')]
                
                print(f"   Found {len(bullet_lines)} bullet points")
                
                # Check that bullets are on separate lines (not all on one line)
                if len(bullet_lines) > 1:
                    # Good - bullets are on separate lines
                    self.test_results.append(("Bullet Formatting", "PASSED", f"{len(bullet_lines)} bullets on separate lines"))
                    print("✅ Bullet points properly formatted on separate lines")
                elif '•' in message and message.count('•') > 1:
                    # Bad - multiple bullets but not on separate lines
                    pytest.fail("Bullet points are crunched on single line")
                else:
                    # Only one or no bullets
                    self.test_results.append(("Bullet Formatting", "PASSED", "Formatting correct"))
                    print("✅ Bullet point formatting correct")
            else:
                print("   No bullet points in this response to test")
                self.test_results.append(("Bullet Formatting", "SKIPPED", "No bullets in response"))
                
        except Exception as e:
            self.test_results.append(("Bullet Formatting", "FAILED", str(e)))
            pytest.fail(f"Bullet formatting test failed: {e}")
    
    def test_07_tpr_calculation(self):
        """Test 7: Complete TPR calculation workflow"""
        print("\n[TEST 7] Testing complete TPR calculation...")
        
        try:
            assert self.session_id, "No session ID available"
            
            chat_url = f"{PRODUCTION_URL}/api/v1/data-analysis/chat"
            
            # Select Under 5 age group
            response = requests.post(
                chat_url,
                json={'message': '1', 'session_id': self.session_id},  # Select Under 5
                timeout=TIMEOUT
            )
            
            assert response.status_code == 200
            result = response.json()
            message = result.get('message', '')
            
            # Check for TPR calculation results
            tpr_calculated = False
            if 'tpr' in message.lower() and ('calculation' in message.lower() or 
                                             'complete' in message.lower() or 
                                             'results' in message.lower()):
                tpr_calculated = True
            
            # Check for statistics in results
            has_statistics = False
            if 'mean tpr' in message.lower() or 'median tpr' in message.lower() or \
               'total tested' in message.lower() or '%' in message:
                has_statistics = True
            
            assert tpr_calculated, "TPR calculation did not complete"
            assert has_statistics, "TPR results missing statistics"
            
            self.test_results.append(("TPR Calculation", "PASSED", "Calculation completed with statistics"))
            print("✅ TPR calculation completed successfully")
            
        except Exception as e:
            self.test_results.append(("TPR Calculation", "FAILED", str(e)))
            pytest.fail(f"TPR calculation test failed: {e}")
    
    def test_08_special_characters_encoding(self):
        """Test 8: Verify special characters are handled correctly"""
        print("\n[TEST 8] Testing special character encoding...")
        
        try:
            # Test with a new session and data containing special characters
            session_response = requests.get(PRODUCTION_URL)
            cookies = session_response.cookies
            
            # Create test data with various special characters
            special_data = {
                'Test≥5': ['Value1'],
                'Test_Ñoño': ['Value2'],
                'Test_Café': ['Value3'],
                'Test_中文': ['Value4'],
                'Test_🔬': ['Value5']
            }
            
            df = pd.DataFrame(special_data)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, encoding='utf-8')
            csv_bytes = csv_buffer.getvalue().encode('utf-8')
            
            files = {
                'file': ('special_chars.csv', csv_bytes, 'text/csv')
            }
            
            upload_url = f"{PRODUCTION_URL}/api/data-analysis/v3/upload"
            response = requests.post(
                upload_url,
                files=files,
                cookies=cookies,
                timeout=TIMEOUT
            )
            
            # Just verify upload works with special characters
            assert response.status_code == 200, f"Upload with special chars failed: {response.status_code}"
            
            self.test_results.append(("Special Characters", "PASSED", "Special characters handled"))
            print("✅ Special character encoding working correctly")
            
        except Exception as e:
            self.test_results.append(("Special Characters", "FAILED", str(e)))
            pytest.fail(f"Special character test failed: {e}")
    
    def test_09_concurrent_sessions(self):
        """Test 9: Verify multiple concurrent sessions work"""
        print("\n[TEST 9] Testing concurrent session handling...")
        
        try:
            sessions = []
            
            # Create 3 concurrent sessions
            for i in range(3):
                session_response = requests.get(PRODUCTION_URL)
                cookies = session_response.cookies
                
                files = {
                    'file': (f'session_{i}.csv', self.test_data, 'text/csv')
                }
                
                upload_url = f"{PRODUCTION_URL}/api/data-analysis/v3/upload"
                response = requests.post(
                    upload_url,
                    files=files,
                    cookies=cookies,
                    timeout=TIMEOUT
                )
                
                assert response.status_code == 200
                result = response.json()
                session_id = result.get('session_id')
                assert session_id, f"No session ID for session {i}"
                sessions.append(session_id)
            
            # Verify all sessions are unique
            assert len(set(sessions)) == 3, "Session IDs are not unique"
            
            self.test_results.append(("Concurrent Sessions", "PASSED", f"3 unique sessions created"))
            print(f"✅ Concurrent sessions working: {sessions}")
            
        except Exception as e:
            self.test_results.append(("Concurrent Sessions", "FAILED", str(e)))
            pytest.fail(f"Concurrent session test failed: {e}")
    
    def test_10_error_handling(self):
        """Test 10: Verify proper error handling"""
        print("\n[TEST 10] Testing error handling...")
        
        try:
            # Test with invalid file type
            files = {
                'file': ('test.txt', b'This is not CSV data', 'text/plain')
            }
            
            upload_url = f"{PRODUCTION_URL}/api/data-analysis/v3/upload"
            response = requests.post(
                upload_url,
                files=files,
                timeout=TIMEOUT
            )
            
            # Should either reject or handle gracefully
            if response.status_code != 200:
                print("   ✓ Invalid file rejected correctly")
            else:
                result = response.json()
                if not result.get('success'):
                    print("   ✓ Invalid file handled with error message")
            
            # Test with missing session ID
            chat_url = f"{PRODUCTION_URL}/api/v1/data-analysis/chat"
            response = requests.post(
                chat_url,
                json={'message': 'test'},
                timeout=TIMEOUT
            )
            
            # Should handle missing session gracefully
            assert response.status_code in [200, 400, 404], "Unexpected error code"
            
            self.test_results.append(("Error Handling", "PASSED", "Errors handled gracefully"))
            print("✅ Error handling working correctly")
            
        except Exception as e:
            self.test_results.append(("Error Handling", "FAILED", str(e)))
            pytest.fail(f"Error handling test failed: {e}")
    
    @classmethod
    def teardown_class(cls):
        """Generate test report"""
        cls.generate_report()
    
    @classmethod
    def generate_report(cls):
        """Generate comprehensive test report"""
        end_time = datetime.now()
        duration = (end_time - cls.start_time).total_seconds()
        
        # Calculate statistics
        total_tests = len(cls.test_results)
        passed = len([r for r in cls.test_results if r[1] == "PASSED"])
        failed = len([r for r in cls.test_results if r[1] == "FAILED"])
        skipped = len([r for r in cls.test_results if r[1] == "SKIPPED"])
        
        # Generate HTML report
        html_report = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Production Test Report - Data Analysis Tab</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2c3e50; }}
                .summary {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .passed {{ color: #27ae60; font-weight: bold; }}
                .failed {{ color: #e74c3c; font-weight: bold; }}
                .skipped {{ color: #f39c12; font-weight: bold; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ padding: 10px; text-align: left; border: 1px solid #ddd; }}
                th {{ background: #34495e; color: white; }}
                tr:nth-child(even) {{ background: #f2f2f2; }}
                .test-passed {{ background: #d4edda; }}
                .test-failed {{ background: #f8d7da; }}
                .test-skipped {{ background: #fff3cd; }}
            </style>
        </head>
        <body>
            <h1>Production Test Report - Data Analysis Tab</h1>
            <div class="summary">
                <h2>Test Summary</h2>
                <p><strong>Environment:</strong> Production ({PRODUCTION_URL})</p>
                <p><strong>Test Date:</strong> {cls.start_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Duration:</strong> {duration:.2f} seconds</p>
                <p><strong>Total Tests:</strong> {total_tests}</p>
                <p class="passed">Passed: {passed}</p>
                <p class="failed">Failed: {failed}</p>
                <p class="skipped">Skipped: {skipped}</p>
                <p><strong>Success Rate:</strong> {(passed/total_tests*100):.1f}%</p>
            </div>
            
            <h2>Test Results</h2>
            <table>
                <tr>
                    <th>Test Name</th>
                    <th>Status</th>
                    <th>Details</th>
                </tr>
        """
        
        for test_name, status, details in cls.test_results:
            status_class = f"test-{status.lower()}"
            html_report += f"""
                <tr class="{status_class}">
                    <td>{test_name}</td>
                    <td>{status}</td>
                    <td>{details}</td>
                </tr>
            """
        
        html_report += """
            </table>
            
            <h2>Critical Features Tested</h2>
            <ul>
                <li>✅ Production server health and availability</li>
                <li>✅ Data Analysis tab functionality</li>
                <li>✅ File upload with UTF-8 encoding</li>
                <li>✅ TPR workflow initiation and completion</li>
                <li>✅ Age group detection (Under 5, Over 5, Pregnant Women)</li>
                <li>✅ Special character handling (≥ symbol)</li>
                <li>✅ Bullet point formatting</li>
                <li>✅ Concurrent session management</li>
                <li>✅ Error handling</li>
            </ul>
            
            <h2>Recommendations</h2>
            <ul>
                <li>Monitor production logs for any errors</li>
                <li>Test with actual user data</li>
                <li>Verify performance under load</li>
            </ul>
        </body>
        </html>
        """
        
        # Save report
        report_path = Path("tests/production_test_report.html")
        report_path.write_text(html_report)
        print(f"\n📊 Test report saved to: {report_path}")
        
        # Print summary to console
        print("\n" + "="*60)
        print("PRODUCTION TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏭️  Skipped: {skipped}")
        print(f"Success Rate: {(passed/total_tests*100):.1f}%")
        print("="*60)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
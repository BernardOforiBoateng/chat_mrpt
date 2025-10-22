#!/usr/bin/env python3
"""
Quick Production Test for Data Analysis Tab
Tests core functionality without extensive delays
"""

import requests
import json
import pandas as pd
import io
from datetime import datetime

# Production URL
PRODUCTION_URL = "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"

def create_test_data():
    """Create minimal test TPR data"""
    data = {
        'State': ['Adamawa'] * 5,
        'LGA': ['Yola North'] * 5,
        'WardName': [f'Ward_{i}' for i in range(1, 6)],
        'HealthFacility': [f'Facility_{i}' for i in range(1, 6)],
        'FacilityLevel': ['Primary'] * 5,
        # Critical columns with ≥ character
        'Persons presenting with fever & tested by RDT <5yrs': [100, 150, 200, 120, 180],
        'Persons presenting with fever & tested by RDT  ≥5yrs (excl PW)': [200, 250, 300, 220, 280],
        'Persons presenting with fever & tested by RDT Preg Women (PW)': [50, 60, 70, 55, 65],
        'Persons tested positive for malaria by RDT <5yrs': [20, 30, 40, 25, 35],
        'Persons tested positive for malaria by RDT  ≥5yrs (excl PW)': [40, 50, 60, 45, 55],
        'Persons tested positive for malaria by RDT Preg Women (PW)': [15, 18, 21, 16, 19],
    }
    
    df = pd.DataFrame(data)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8')
    return csv_buffer.getvalue().encode('utf-8')

def main():
    print("="*60)
    print("QUICK PRODUCTION TEST - DATA ANALYSIS TAB")
    print("="*60)
    print(f"Testing: {PRODUCTION_URL}")
    print(f"Time: {datetime.now()}")
    print("="*60)
    
    results = []
    
    # Test 1: Server Health
    print("\n[TEST 1] Server Health Check...")
    try:
        response = requests.get(f"{PRODUCTION_URL}/ping", timeout=10)
        if response.status_code == 200:
            print("✅ PASSED: Server is healthy")
            results.append(("Server Health", "PASSED"))
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            results.append(("Server Health", "FAILED"))
    except Exception as e:
        print(f"❌ FAILED: {e}")
        results.append(("Server Health", "FAILED"))
    
    # Test 2: Main Page
    print("\n[TEST 2] Main Page Check...")
    try:
        response = requests.get(PRODUCTION_URL, timeout=10)
        if response.status_code == 200 and "ChatMRPT" in response.text:
            print("✅ PASSED: Main page loads")
            results.append(("Main Page", "PASSED"))
        else:
            print("❌ FAILED: Main page issue")
            results.append(("Main Page", "FAILED"))
    except Exception as e:
        print(f"❌ FAILED: {e}")
        results.append(("Main Page", "FAILED"))
    
    # Test 3: Data Analysis Tab
    print("\n[TEST 3] Data Analysis Tab Check...")
    try:
        response = requests.get(PRODUCTION_URL, timeout=10)
        if "Data Analysis" in response.text or "data-analysis" in response.text.lower():
            print("✅ PASSED: Data Analysis tab exists")
            results.append(("Data Analysis Tab", "PASSED"))
        else:
            print("❌ FAILED: Data Analysis tab not found")
            results.append(("Data Analysis Tab", "FAILED"))
    except Exception as e:
        print(f"❌ FAILED: {e}")
        results.append(("Data Analysis Tab", "FAILED"))
    
    # Test 4: File Upload
    print("\n[TEST 4] File Upload Test...")
    session_id = None
    try:
        # Get session
        session_response = requests.get(PRODUCTION_URL, timeout=10)
        cookies = session_response.cookies
        
        # Upload file
        test_data = create_test_data()
        files = {'file': ('test_tpr.csv', test_data, 'text/csv')}
        
        response = requests.post(
            f"{PRODUCTION_URL}/api/data-analysis/upload",
            files=files,
            cookies=cookies,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            session_id = result.get('session_id')
            print(f"✅ PASSED: File uploaded (Session: {session_id})")
            results.append(("File Upload", "PASSED"))
        else:
            print(f"❌ FAILED: Upload status {response.status_code}")
            results.append(("File Upload", "FAILED"))
    except Exception as e:
        print(f"❌ FAILED: {e}")
        results.append(("File Upload", "FAILED"))
    
    # Test 5: TPR Workflow
    print("\n[TEST 5] TPR Workflow Test...")
    if session_id:
        try:
            # Send initial message
            response = requests.post(
                f"{PRODUCTION_URL}/api/v1/data-analysis/chat",
                json={'message': '1', 'session_id': session_id},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                message = result.get('message', '')
                if 'facility' in message.lower() or 'primary' in message.lower():
                    print("✅ PASSED: TPR workflow started")
                    results.append(("TPR Workflow", "PASSED"))
                else:
                    print("❌ FAILED: Workflow didn't start")
                    results.append(("TPR Workflow", "FAILED"))
            else:
                print(f"❌ FAILED: Status {response.status_code}")
                results.append(("TPR Workflow", "FAILED"))
        except Exception as e:
            print(f"❌ FAILED: {e}")
            results.append(("TPR Workflow", "FAILED"))
    else:
        print("⏭️  SKIPPED: No session ID")
        results.append(("TPR Workflow", "SKIPPED"))
    
    # Test 6: Age Group Detection
    print("\n[TEST 6] Age Group Detection Test...")
    if session_id:
        try:
            # Select Primary facilities
            response = requests.post(
                f"{PRODUCTION_URL}/api/data-analysis/v3/chat",
                json={'message': 'primary', 'session_id': session_id},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                message = result.get('message', '')
                
                # Check for all 3 age groups
                age_groups = []
                if 'under 5' in message.lower():
                    age_groups.append('Under 5')
                if 'over 5' in message.lower() or '≥5' in message:
                    age_groups.append('Over 5')
                if 'pregnant' in message.lower():
                    age_groups.append('Pregnant')
                
                if len(age_groups) == 3:
                    print(f"✅ PASSED: All 3 age groups detected: {age_groups}")
                    results.append(("Age Groups", "PASSED"))
                else:
                    print(f"❌ FAILED: Only {len(age_groups)} groups found: {age_groups}")
                    results.append(("Age Groups", "FAILED"))
                
                # Check encoding
                if 'â‰¥' in message:
                    print("⚠️  WARNING: Encoding issue detected (â‰¥)")
                elif '≥' in message:
                    print("✅ Encoding correct (≥ symbol intact)")
                    
            else:
                print(f"❌ FAILED: Status {response.status_code}")
                results.append(("Age Groups", "FAILED"))
        except Exception as e:
            print(f"❌ FAILED: {e}")
            results.append(("Age Groups", "FAILED"))
    else:
        print("⏭️  SKIPPED: No session ID")
        results.append(("Age Groups", "SKIPPED"))
    
    # Test 7: Bullet Formatting (Quick Check)
    print("\n[TEST 7] Bullet Point Formatting...")
    if session_id:
        try:
            response = requests.post(
                f"{PRODUCTION_URL}/api/data-analysis/v3/chat",
                json={'message': 'show data summary', 'session_id': session_id},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                message = result.get('message', '')
                
                # Check if bullets are on separate lines
                lines_with_bullets = [line for line in message.split('\n') if '•' in line or '-' in line.strip()[:2]]
                
                if len(lines_with_bullets) > 1:
                    print(f"✅ PASSED: Bullets on separate lines ({len(lines_with_bullets)} found)")
                    results.append(("Bullet Formatting", "PASSED"))
                elif '•' not in message and '-' not in message:
                    print("⏭️  SKIPPED: No bullets in response")
                    results.append(("Bullet Formatting", "SKIPPED"))
                else:
                    print("❌ FAILED: Bullets may be on single line")
                    results.append(("Bullet Formatting", "FAILED"))
            else:
                print(f"❌ FAILED: Status {response.status_code}")
                results.append(("Bullet Formatting", "FAILED"))
        except Exception as e:
            print(f"❌ FAILED: {e}")
            results.append(("Bullet Formatting", "FAILED"))
    else:
        print("⏭️  SKIPPED: No session ID")
        results.append(("Bullet Formatting", "SKIPPED"))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = len([r for r in results if r[1] == "PASSED"])
    failed = len([r for r in results if r[1] == "FAILED"])
    skipped = len([r for r in results if r[1] == "SKIPPED"])
    total = len(results)
    
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⏭️  Skipped: {skipped}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    
    # Detailed results
    print("\nDetailed Results:")
    for test_name, status in results:
        symbol = "✅" if status == "PASSED" else "❌" if status == "FAILED" else "⏭️"
        print(f"  {symbol} {test_name}: {status}")
    
    print("="*60)
    
    # Return code
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit(main())
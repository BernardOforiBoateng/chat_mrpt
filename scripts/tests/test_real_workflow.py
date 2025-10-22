#!/usr/bin/env python3
"""
Comprehensive Real Workflow Test for Data Analysis Tab
"""

import requests
import json
import pandas as pd
import io
import time
from datetime import datetime

PRODUCTION_URL = "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"

print("="*60)
print("   REAL WORKFLOW TEST - PRODUCTION")
print("="*60)
print(f"Started: {datetime.now().strftime('%H:%M:%S')}\n")

session = requests.Session()
tests_passed = 0
tests_total = 0

# Test 1: UI Check
print("🔍 Test 1: Checking UI...")
tests_total += 1
try:
    response = session.get(PRODUCTION_URL, timeout=10)
    html = response.text
    
    if 'id="data-analysis-tab"' in html and "Data Analysis" in html and "TPR Analysis" not in html:
        print("✅ UI shows 'Data Analysis' tab correctly\n")
        tests_passed += 1
    else:
        print("❌ UI issue detected\n")
except Exception as e:
    print(f"❌ UI test failed: {e}\n")

# Test 2: File Upload with Special Characters
print("🔍 Test 2: Uploading file with ≥ character...")
tests_total += 1
try:
    # Create test data with special characters
    data = {
        'State': ['Adamawa', 'Adamawa', 'Adamawa'],
        'LGA': ['Yola North', 'Yola South', 'Mubi North'],
        'WardName': ['Ward_1', 'Ward_2', 'Ward_3'],
        'Persons presenting with fever & tested by RDT <5yrs': [100, 150, 200],
        'Persons presenting with fever & tested by RDT ≥5yrs (excl PW)': [250, 300, 350],
        'Persons presenting with fever & tested by RDT Preg Women (PW)': [50, 75, 100],
        'Confirmed cases by RDT/Microscopy <5yrs': [20, 30, 40],
        'Confirmed cases by RDT/Microscopy ≥5yrs (excl PW)': [45, 55, 65],
        'Confirmed cases by RDT/Microscopy Preg Women (PW)': [10, 15, 20]
    }
    
    df = pd.DataFrame(data)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode('utf-8')
    
    files = {'file': ('test.csv', csv_bytes, 'text/csv')}
    response = session.post(f"{PRODUCTION_URL}/api/data-analysis/upload", files=files, timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        session_id = result.get('session_id')
        print(f"✅ File uploaded. Session: {session_id}\n")
        tests_passed += 1
    else:
        print(f"❌ Upload failed: {response.status_code}\n")
        session_id = None
except Exception as e:
    print(f"❌ Upload failed: {e}\n")
    session_id = None

# Test 3: Check Encoding (≥ should not be corrupted)
if session_id:
    print("🔍 Test 3: Testing encoding fix...")
    tests_total += 1
    try:
        response = session.post(
            f"{PRODUCTION_URL}/api/v1/data-analysis/chat",
            json={'message': 'Show me the age groups in the data', 'session_id': session_id},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            message = result.get('message', '')
            
            # Check for corruption
            if 'â‰¥' in message:
                print("❌ Encoding corrupted: â‰¥ found\n")
            else:
                # Count age groups mentioned
                age_groups = 0
                if 'under 5' in message.lower() or '<5' in message:
                    age_groups += 1
                if 'over 5' in message.lower() or '≥5' in message or 'greater' in message.lower():
                    age_groups += 1
                if 'pregnant' in message.lower():
                    age_groups += 1
                    
                if age_groups >= 2:
                    print(f"✅ Encoding correct! Found {age_groups} age groups\n")
                    tests_passed += 1
                else:
                    print(f"⚠️ Only found {age_groups} age groups\n")
        else:
            print(f"❌ Chat failed: {response.status_code}\n")
    except Exception as e:
        print(f"❌ Encoding test failed: {e}\n")

# Test 4: Bullet Formatting
if session_id:
    print("🔍 Test 4: Testing bullet formatting...")
    tests_total += 1
    try:
        response = session.post(
            f"{PRODUCTION_URL}/api/v1/data-analysis/chat",
            json={'message': 'List the key statistics from the data', 'session_id': session_id},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            message = result.get('message', '')
            
            # Check for single-line bullets
            lines = message.split('\n')
            single_bullets = sum(1 for line in lines if line.strip() in ['•', '-', '*'])
            
            if single_bullets == 0:
                print("✅ Bullet formatting correct!\n")
                tests_passed += 1
            else:
                print(f"❌ Found {single_bullets} single-line bullets\n")
        else:
            print(f"❌ Chat failed: {response.status_code}\n")
    except Exception as e:
        print(f"❌ Bullet test failed: {e}\n")

# Test 5: TPR Calculation
if session_id:
    print("🔍 Test 5: Testing TPR calculation...")
    tests_total += 1
    try:
        response = session.post(
            f"{PRODUCTION_URL}/api/v1/data-analysis/chat",
            json={'message': 'Calculate the TPR for each ward', 'session_id': session_id},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            message = result.get('message', '')
            
            if 'tpr' in message.lower() or 'positivity' in message.lower():
                print("✅ TPR calculation working!\n")
                tests_passed += 1
            else:
                print("⚠️ TPR calculation unclear\n")
        else:
            print(f"❌ Chat failed: {response.status_code}\n")
    except Exception as e:
        print(f"❌ TPR test failed: {e}\n")

# Summary
print("="*60)
print("   TEST SUMMARY")
print("="*60)
print(f"Results: {tests_passed}/{tests_total} tests passed")

if tests_passed == tests_total:
    print("\n🎉 SUCCESS! All tests passed!")
    print("✅ Data Analysis tab is fully functional")
    print("✅ Encoding fixes working")
    print("✅ Bullet formatting correct")
else:
    print(f"\n⚠️ {tests_total - tests_passed} tests failed")
    
print(f"\nCompleted: {datetime.now().strftime('%H:%M:%S')}")

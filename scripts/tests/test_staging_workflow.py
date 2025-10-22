#!/usr/bin/env python3
"""
Test Staging Environment
"""

import requests
import json
import pandas as pd
import io
import time
from datetime import datetime

STAGING_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

print("="*60)
print("   REAL WORKFLOW TEST - STAGING")
print("="*60)
print(f"Started: {datetime.now().strftime('%H:%M:%S')}\n")

session = requests.Session()
tests_passed = 0
tests_total = 0

# Test 1: UI Check
print("🔍 Test 1: Checking UI...")
tests_total += 1
try:
    response = session.get(STAGING_URL, timeout=10)
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
        'State': ['Kano', 'Kano', 'Kano'],
        'LGA': ['Fagge', 'Nassarawa', 'Dala'],
        'WardName': ['Fagge A', 'Tudun Wada', 'Dala'],
        'Persons presenting with fever & tested by RDT <5yrs': [120, 180, 250],
        'Persons presenting with fever & tested by RDT ≥5yrs (excl PW)': [280, 320, 400],
        'Persons presenting with fever & tested by RDT Preg Women (PW)': [60, 85, 110],
        'Confirmed cases by RDT/Microscopy <5yrs': [25, 35, 50],
        'Confirmed cases by RDT/Microscopy ≥5yrs (excl PW)': [50, 60, 75],
        'Confirmed cases by RDT/Microscopy Preg Women (PW)': [12, 18, 25]
    }
    
    df = pd.DataFrame(data)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode('utf-8')
    
    files = {'file': ('test_staging.csv', csv_bytes, 'text/csv')}
    response = session.post(f"{STAGING_URL}/api/data-analysis/upload", files=files, timeout=30)
    
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

# Test 3: Check Encoding
if session_id:
    print("🔍 Test 3: Testing encoding fix...")
    tests_total += 1
    try:
        response = session.post(
            f"{STAGING_URL}/api/v1/data-analysis/chat",
            json={'message': 'What age groups are in the data?', 'session_id': session_id},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            message = result.get('message', '')
            
            # Check for corruption
            if 'â‰¥' in message:
                print("❌ Encoding corrupted: â‰¥ found\n")
            else:
                # Count age groups
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
            f"{STAGING_URL}/api/v1/data-analysis/chat",
            json={'message': 'Provide a summary with bullet points', 'session_id': session_id},
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

# Summary
print("="*60)
print("   TEST SUMMARY - STAGING")
print("="*60)
print(f"Results: {tests_passed}/{tests_total} tests passed")

if tests_passed == tests_total:
    print("\n🎉 SUCCESS! All staging tests passed!")
else:
    print(f"\n⚠️ {tests_total - tests_passed} tests failed")
    
print(f"\nCompleted: {datetime.now().strftime('%H:%M:%S')}")

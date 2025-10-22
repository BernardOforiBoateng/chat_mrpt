#!/usr/bin/env python3
"""
Debug Production Test - See actual responses
"""

import requests
import json
import pandas as pd
import io

PRODUCTION_URL = "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"

def create_test_data():
    """Create minimal test TPR data"""
    data = {
        'State': ['Adamawa'] * 3,
        'LGA': ['Yola North'] * 3,
        'WardName': ['Ward_1', 'Ward_2', 'Ward_3'],
        'HealthFacility': ['Facility_1', 'Facility_2', 'Facility_3'],
        'FacilityLevel': ['Primary'] * 3,
        'Persons presenting with fever & tested by RDT <5yrs': [100, 150, 200],
        'Persons presenting with fever & tested by RDT  ≥5yrs (excl PW)': [200, 250, 300],
        'Persons presenting with fever & tested by RDT Preg Women (PW)': [50, 60, 70],
        'Persons tested positive for malaria by RDT <5yrs': [20, 30, 40],
        'Persons tested positive for malaria by RDT  ≥5yrs (excl PW)': [40, 50, 60],
        'Persons tested positive for malaria by RDT Preg Women (PW)': [15, 18, 21],
    }
    
    df = pd.DataFrame(data)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8')
    return csv_buffer.getvalue().encode('utf-8')

def main():
    print("="*60)
    print("DEBUG PRODUCTION TEST")
    print("="*60)
    
    # Get session
    session_response = requests.get(PRODUCTION_URL, timeout=10)
    cookies = session_response.cookies
    
    # Upload file
    print("\n1. UPLOAD TEST")
    test_data = create_test_data()
    files = {'file': ('test_tpr.csv', test_data, 'text/csv')}
    
    response = requests.post(
        f"{PRODUCTION_URL}/api/data-analysis/upload",
        files=files,
        cookies=cookies,
        timeout=15
    )
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        session_id = result.get('session_id')
        print(f"   Session ID: {session_id}")
        print(f"   Response: {json.dumps(result, indent=2)[:500]}")
    else:
        print(f"   Error: {response.text[:200]}")
        return
    
    # Try chat endpoints
    print("\n2. CHAT ENDPOINT TEST")
    
    endpoints = [
        "/api/v1/data-analysis/chat",
        "/api/data-analysis/chat",
        "/api/data-analysis/v3/chat"
    ]
    
    for endpoint in endpoints:
        print(f"\n   Testing: {endpoint}")
        try:
            response = requests.post(
                f"{PRODUCTION_URL}{endpoint}",
                json={'message': '1', 'session_id': session_id},
                timeout=15
            )
            
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   Success: {result.get('success')}")
                message = result.get('message', '')
                print(f"   Message preview: {message[:200]}...")
                
                # Check for key indicators
                if 'facility' in message.lower():
                    print("   ✅ TPR workflow detected")
                if 'primary' in message.lower():
                    print("   ✅ Facility selection detected")
                break
            elif response.status_code == 404:
                print(f"   ❌ Endpoint not found")
            else:
                print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"   Exception: {e}")
    
    # If we got a working endpoint, test age group detection
    if response.status_code == 200:
        print("\n3. AGE GROUP DETECTION TEST")
        
        # Send "primary" to select facility
        response = requests.post(
            f"{PRODUCTION_URL}{endpoint}",
            json={'message': 'primary', 'session_id': session_id},
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            message = result.get('message', '')
            
            print(f"   Status: {response.status_code}")
            print(f"   Message length: {len(message)}")
            
            # Check for age groups
            age_groups = []
            if 'under 5' in message.lower():
                age_groups.append('Under 5')
            if 'over 5' in message.lower() or '≥5' in message:
                age_groups.append('Over 5')
            if 'pregnant' in message.lower():
                age_groups.append('Pregnant')
            
            print(f"   Age groups found: {age_groups}")
            
            # Check for encoding issues
            if 'â‰¥' in message:
                print("   ⚠️ ENCODING ISSUE: â‰¥ detected")
            elif '≥' in message:
                print("   ✅ Encoding correct: ≥ symbol intact")
            
            # Check bullet formatting
            lines = message.split('\n')
            bullet_lines = [line for line in lines if '•' in line]
            print(f"   Bullet lines: {len(bullet_lines)}")
            if len(bullet_lines) > 3:
                print("   ✅ Bullets appear to be on separate lines")

if __name__ == "__main__":
    main()
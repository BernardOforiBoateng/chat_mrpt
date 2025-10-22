#!/usr/bin/env python3
"""
Simple ITN test - check if ITN tool is called correctly
"""

import requests
import time

BASE_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

def test_itn_selection():
    session_id = f"itn_test_{int(time.time())}"
    print(f"Testing ITN tool selection with session: {session_id}")
    
    # Step 1: Quick data upload
    print("\n1. Uploading minimal data...")
    csv_data = "WardName,Population,PfPR\nWard1,10000,0.5\nWard2,15000,0.4"
    
    files = {'file': ('test.csv', csv_data, 'text/csv')}
    
    try:
        response = requests.post(
            f"{BASE_URL}/upload",
            files=files,
            data={'session_id': session_id},
            timeout=30
        )
        print(f"Upload status: {response.status_code}")
    except Exception as e:
        print(f"Upload error: {e}")
        return
    
    time.sleep(2)
    
    # Step 2: Run analysis
    print("\n2. Running quick analysis...")
    try:
        response = requests.post(
            f"{BASE_URL}/send_message",
            json={
                'message': "Run complete malaria risk analysis",
                'session_id': session_id,
                'tab_context': 'standard-upload'
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Analysis completed: {result.get('status')}")
        else:
            print(f"Analysis failed: {response.status_code}")
            return
    except Exception as e:
        print(f"Analysis error: {e}")
        return
    
    time.sleep(3)
    
    # Step 3: Test ITN request
    print("\n3. Testing ITN planning request...")
    try:
        response = requests.post(
            f"{BASE_URL}/send_message", 
            json={
                'message': "I want to plan bed net distribution",
                'session_id': session_id,
                'tab_context': 'standard-upload'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '').lower()
            
            print(f"Status: {result.get('status')}")
            print(f"Response preview: {response_text[:200]}...")
            
            # Check what happened
            if 'already complete' in response_text:
                print("❌ PROBLEM: System thinks analysis already complete!")
            elif 'itn distribution' in response_text or 'bed net' in response_text or 'how many' in response_text:
                print("✅ SUCCESS: ITN planning activated!")
            elif 'running' in response_text and 'analysis' in response_text:
                print("❌ PROBLEM: System re-running analysis instead of ITN!")
            else:
                print("⚠️ UNCLEAR: Unexpected response")
        else:
            print(f"Request failed: {response.status_code}")
    except Exception as e:
        print(f"ITN request error: {e}")

if __name__ == "__main__":
    print("="*50)
    print("ITN TOOL SELECTION TEST")
    print("="*50)
    test_itn_selection()
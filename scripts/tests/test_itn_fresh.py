#!/usr/bin/env python3
"""
Test ITN Planning with Fresh Session
"""

import requests
import time
import json

BASE_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

def test_itn_fresh():
    session_id = f"itn_fresh_{int(time.time())}"
    print(f"Session: {session_id}")
    
    # Step 1: Upload data
    print("\n1. Uploading data...")
    csv_data = """WardName,State,LGA,Population,PfPR,HousingQuality
Ward1,TestState,TestLGA,10000,0.5,0.3
Ward2,TestState,TestLGA,15000,0.4,0.4
Ward3,TestState,TestLGA,12000,0.6,0.2"""
    
    files = {'file': ('test_data.csv', csv_data, 'text/csv')}
    
    response = requests.post(
        f"{BASE_URL}/upload",
        files=files,
        data={'session_id': session_id},
        timeout=10
    )
    print(f"Upload status: {response.status_code}")
    
    time.sleep(2)
    
    # Step 2: Run analysis
    print("\n2. Running analysis...")
    response = requests.post(
        f"{BASE_URL}/send_message",
        json={
            'message': "Run complete malaria risk analysis",
            'session_id': session_id,
            'tab_context': 'standard-upload'
        },
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Analysis status: {result.get('status')}")
        # Check if analysis mentions ITN
        if 'itn' in result.get('response', '').lower():
            print("✓ ITN mentioned in response")
    else:
        print(f"Analysis failed: {response.status_code}")
        return
    
    time.sleep(3)
    
    # Step 3: Request ITN planning
    print("\n3. Requesting ITN planning...")
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
        print(f"ITN status: {result.get('status')}")
        response_text = result.get('response', '')
        
        # Check what happened
        if 'itn distribution plan' in response_text.lower():
            print("✅ ITN planning activated!")
        elif 'analysis complete' in response_text.lower():
            print("❌ System re-ran analysis instead of ITN")
        elif 'how many' in response_text.lower():
            print("ℹ️ System asking for parameters")
            
            # Provide parameters
            print("\n4. Providing parameters...")
            response = requests.post(
                f"{BASE_URL}/send_message",
                json={
                    'message': "I have 10000 nets and average household size is 5",
                    'session_id': session_id,
                    'tab_context': 'standard-upload'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'distribution plan' in result.get('response', '').lower():
                    print("✅ ITN plan generated!")
                else:
                    print("⚠️ Unexpected response")
        else:
            print(f"⚠️ Unexpected response: {response_text[:100]}...")
    else:
        print(f"ITN request failed: {response.status_code}")

if __name__ == "__main__":
    print("="*50)
    print("ITN FRESH SESSION TEST")
    print("="*50)
    test_itn_fresh()
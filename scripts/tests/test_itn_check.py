#!/usr/bin/env python3
"""
Check ITN tool selection more carefully
"""

import requests
import time
import json

BASE_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

def test_itn_after_analysis():
    session_id = f"itn_check_{int(time.time())}"
    print(f"Session: {session_id}\n")
    
    # Step 1: Upload data
    print("1. Uploading data...")
    csv_data = """WardName,State,LGA,Population,PfPR
Ward1,TestState,TestLGA,10000,0.5
Ward2,TestState,TestLGA,15000,0.4
Ward3,TestState,TestLGA,12000,0.6"""
    
    files = {'file': ('test.csv', csv_data, 'text/csv')}
    
    response = requests.post(
        f"{BASE_URL}/upload",
        files=files,
        data={'session_id': session_id},
        timeout=30
    )
    print(f"   Upload: {response.status_code}")
    
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
        timeout=90
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   Status: {result.get('status')}")
        response_text = result.get('response', '')
        if 'complete' in response_text.lower():
            print("   ✓ Analysis completed")
    
    time.sleep(5)
    
    # Step 3: Try ITN planning
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
        response_text = result.get('response', '')
        
        print(f"   Status: {result.get('status')}")
        
        # Print first 300 chars to see what's happening
        print(f"\n   Full response start:\n   {response_text[:300]}")
        
        # Analyze response
        print("\n   Analysis of response:")
        if 'need to complete' in response_text.lower():
            print("   ❌ FAIL: System says analysis not complete")
        elif 'already complete' in response_text.lower():
            print("   ⚠️ System says analysis already complete (when it shouldn't)")
        elif 'how many' in response_text.lower() or 'nets available' in response_text.lower():
            print("   ✅ SUCCESS: ITN planning activated, asking for parameters")
        elif 'itn distribution plan' in response_text.lower():
            print("   ✅ SUCCESS: ITN plan generated")
        elif 'running' in response_text.lower() and 'analysis' in response_text.lower():
            print("   ❌ FAIL: Re-running analysis instead of ITN")
        else:
            print("   ⚠️ UNCLEAR response")
            
        # Check tools used
        tools = result.get('tools_used', [])
        if tools:
            print(f"   Tools used: {tools}")

if __name__ == "__main__":
    print("="*50)
    print("ITN AFTER ANALYSIS TEST")
    print("="*50)
    test_itn_after_analysis()
#!/usr/bin/env python3
"""
Test ITN Workflow - Upload, Analyze, then Plan ITN Distribution
"""

import requests
import time
import json

BASE_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

def test_full_itn_workflow():
    """Test the complete ITN workflow from data upload to distribution planning"""
    
    session_id = f"itn_test_{int(time.time())}"
    print(f"Session ID: {session_id}")
    
    # Step 1: Upload sample data
    print("\n1️⃣ Uploading sample malaria data...")
    
    csv_data = """WardName,State,LGA,Population,PfPR,HousingQuality,HealthcareDensity,UrbanPercent,Rainfall,Temperature
Gwale,Kano,Gwale,50000,0.67,0.3,0.2,80,850,28.5
Kumbotso,Kano,Kumbotso,45000,0.45,0.4,0.3,60,820,29.0
Tarauni,Kano,Tarauni,60000,0.38,0.5,0.4,90,800,28.8
Nassarawa,Kano,Nassarawa,55000,0.52,0.35,0.25,75,830,28.7
Fagge,Kano,Fagge,70000,0.41,0.45,0.35,95,810,28.9"""
    
    files = {'file': ('kano_data.csv', csv_data, 'text/csv')}
    
    response = requests.post(
        f"{BASE_URL}/upload",
        files=files,
        data={'session_id': session_id},
        timeout=15
    )
    
    if response.status_code == 200:
        print("✅ Data uploaded successfully")
    else:
        print(f"❌ Upload failed: {response.status_code}")
        return
    
    time.sleep(2)
    
    # Step 2: Run malaria risk analysis
    print("\n2️⃣ Running malaria risk analysis...")
    
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
        if result.get('status') == 'success':
            print("✅ Analysis completed successfully")
            # Extract key info from response
            response_text = result.get('response', '')
            if 'ranked' in response_text.lower():
                print("   ✓ Wards ranked by risk")
            if 'itn' in response_text.lower() or 'bed net' in response_text.lower():
                print("   ✓ ITN planning suggested")
        else:
            print(f"⚠️ Analysis status: {result.get('status')}")
    else:
        print(f"❌ Analysis failed: {response.status_code}")
        return
    
    time.sleep(3)
    
    # Step 3: Check analysis status
    print("\n3️⃣ Checking analysis completion status...")
    
    response = requests.post(
        f"{BASE_URL}/send_message",
        json={
            'message': "Is the analysis complete?",
            'session_id': session_id,
            'tab_context': 'standard-upload'
        },
        timeout=15
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   Status check response: {result.get('response', '')[:100]}...")
    
    time.sleep(2)
    
    # Step 4: Request ITN distribution planning
    print("\n4️⃣ Requesting ITN distribution planning...")
    
    test_messages = [
        "I want to plan bed net distribution",
        "Help me distribute ITNs based on the rankings",
        "I have 50000 nets available and average household size is 5"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n   Attempt {i}: '{message}'")
        
        response = requests.post(
            f"{BASE_URL}/send_message",
            json={
                'message': message,
                'session_id': session_id,
                'tab_context': 'standard-upload'
            },
            timeout=20
        )
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('status')
            response_text = result.get('response', '')
            
            print(f"   Status: {status}")
            print(f"   Response preview: {response_text[:200]}...")
            
            # Check if ITN planning was activated
            if 'itn distribution plan' in response_text.lower():
                print("   ✅ ITN planning activated!")
                
                # Check for specific ITN details
                if 'wards covered' in response_text.lower():
                    print("      ✓ Ward coverage calculated")
                if 'nets per ward' in response_text.lower():
                    print("      ✓ Net allocation determined")
                if 'population covered' in response_text.lower():
                    print("      ✓ Population coverage estimated")
                    
                # Extract visualizations if any
                viz = result.get('visualizations', [])
                if viz:
                    print(f"      ✓ {len(viz)} visualization(s) generated")
                    for v in viz:
                        print(f"         - {v.get('type', 'unknown')}: {v.get('path', 'N/A')}")
                
                break
            elif 'ready to help' in response_text.lower() and 'how many' in response_text.lower():
                print("   ℹ️ System asking for parameters")
            elif 'analysis has not been completed' in response_text.lower():
                print("   ❌ System thinks analysis is not complete!")
            else:
                print("   ⚠️ Unexpected response - ITN not activated")
        else:
            print(f"   ❌ Request failed: {response.status_code}")
        
        time.sleep(2)
    
    # Final status check
    print("\n" + "="*60)
    print("FINAL STATUS:")
    print("="*60)
    
    # Check if ITN files were created
    print("\n📁 Checking for generated files...")
    
    response = requests.post(
        f"{BASE_URL}/send_message",
        json={
            'message': "What files have been generated?",
            'session_id': session_id,
            'tab_context': 'standard-upload'
        },
        timeout=15
    )
    
    if response.status_code == 200:
        result = response.json()
        response_text = result.get('response', '')
        if 'itn' in response_text.lower():
            print("✅ ITN distribution files found")
        else:
            print("⚠️ No ITN files mentioned")

if __name__ == "__main__":
    print("="*60)
    print("ITN WORKFLOW TEST")
    print("="*60)
    print(f"Target: {BASE_URL}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_full_itn_workflow()
    
    print("\n✅ Test complete!")
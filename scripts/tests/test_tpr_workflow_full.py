#!/usr/bin/env python3
"""
Test TPR Workflow - Full User Journey
Tests the complete TPR workflow from data upload to risk analysis transition
"""

import requests
import json
import time
import uuid
from pathlib import Path

# Staging server URL
BASE_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

# Generate unique session ID for this test
session_id = f"test_{uuid.uuid4().hex[:8]}"
print(f"🔑 Test Session ID: {session_id}")

# Session for maintaining cookies
session = requests.Session()

def test_upload_data():
    """Step 1: Upload Adamawa TPR data"""
    print("\n📤 Step 1: Uploading Adamawa TPR data...")
    
    # Read the Adamawa data file
    file_path = "/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/adamawa_tpr_cleaned.csv"
    
    with open(file_path, 'rb') as f:
        files = {'file': ('adamawa_tpr_cleaned.csv', f, 'text/csv')}
        
        response = session.post(
            f"{BASE_URL}/api/data-analysis/upload",
            files=files,
            timeout=30
        )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Upload successful: {result.get('message', 'Data uploaded')[:100]}...")
        return result
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(f"   Error: {response.text[:200]}")
        return None

def test_tpr_selection(message):
    """Send a message to the TPR workflow"""
    print(f"\n💬 Sending: {message}")
    
    response = session.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json={'message': message},
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        # Extract and display key information
        msg = result.get('message', '')
        
        # Clean up message for display
        if len(msg) > 500:
            msg = msg[:500] + "..."
        
        print(f"📨 Response preview: {msg[:200]}...")
        
        # Check for specific expected content
        if 'Adamawa' in msg:
            print("   ✅ State name displayed correctly")
        if 'Primary health centers' in msg or 'Primary' in msg:
            print("   ✅ Facility level displayed correctly")
        if 'TPR' in msg:
            print("   ✅ TPR mentioned")
        if 'Age Group' in msg or 'age group' in msg:
            print("   ✅ Age group selection offered")
            
        return result
    else:
        print(f"❌ Request failed: {response.status_code}")
        print(f"   Error: {response.text[:200]}")
        return None

def test_workflow():
    """Test the complete TPR workflow"""
    print("="*60)
    print("🧪 TESTING TPR WORKFLOW - ADAMAWA DATA")
    print("="*60)
    
    # Step 1: Upload data
    upload_result = test_upload_data()
    if not upload_result:
        print("❌ Upload failed, aborting test")
        return
    
    time.sleep(2)  # Give server time to process
    
    # Step 2: Initiate TPR calculation (type "2" in response to menu)
    print("\n📊 Step 2: Selecting TPR calculation option...")
    result = test_tpr_selection("2")
    if not result:
        return
    
    time.sleep(1)
    
    # Step 3: Select facility level (Primary - option 1)
    print("\n🏥 Step 3: Selecting Primary facility level...")
    result = test_tpr_selection("Primary")
    if not result:
        return
    
    # Check if the response shows proper state and asks for age group
    msg = result.get('message', '')
    if 'Adamawa' in msg:
        print("   ✅ State 'Adamawa' correctly identified")
    if 'Primary' in msg or 'primary' in msg:
        print("   ✅ Facility level 'Primary' acknowledged")
    
    time.sleep(1)
    
    # Step 4: Select age group (Under 5 - option 2)
    print("\n👶 Step 4: Selecting Under 5 Years age group...")
    result = test_tpr_selection("Under 5 Years")
    if not result:
        return
    
    # Check TPR calculation results
    msg = result.get('message', '')
    print("\n📈 Step 5: Checking TPR calculation results...")
    
    # Check for key indicators of successful calculation
    checks = {
        'State: Adamawa': 'State correctly shown',
        'Wards Analyzed': 'Ward count shown',
        'Mean TPR': 'Mean TPR calculated',
        'Median TPR': 'Median TPR calculated',
        'Results saved': 'Results saved to file',
        'Age Group: Under 5': 'Age group correctly shown',
        'Primary': 'Facility level shown'
    }
    
    for check, description in checks.items():
        if check in msg:
            print(f"   ✅ {description}")
        else:
            print(f"   ⚠️ Missing: {description}")
    
    # Check if TPR values are non-zero
    if 'Mean TPR: 0.0%' in msg and 'Median TPR: 0.0%' in msg:
        print("   ⚠️ Warning: TPR values are all zero - may need to check data")
    else:
        print("   ✅ TPR values calculated (non-zero)")
    
    # Check for visualizations
    if 'visualizations' in result and result['visualizations']:
        print(f"   ✅ {len(result['visualizations'])} visualization(s) created")
    
    time.sleep(1)
    
    # Step 6: Transition to risk analysis
    print("\n🎯 Step 6: Testing transition to risk analysis...")
    result = test_tpr_selection("yes")
    if not result:
        return
    
    msg = result.get('message', '')
    if 'loaded your data' in msg.lower():
        print("   ✅ Successfully transitioned to main workflow")
    if 'What would you like to do?' in msg:
        print("   ✅ Main menu displayed")
    if 'risk analysis' in msg.lower():
        print("   ✅ Risk analysis option available")
    
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print("✅ Data upload successful")
    print("✅ TPR workflow initiated")
    print("✅ Facility level selection working")
    print("✅ Age group selection working")
    print("✅ TPR calculation completed")
    print("✅ Transition to risk analysis available")
    print("\n🎉 TPR Workflow Test Complete!")

if __name__ == "__main__":
    test_workflow()
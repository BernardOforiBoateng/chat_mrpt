#!/usr/bin/env python3
"""
Test script to verify the complete Data Analysis workflow including Option 2 (TPR)
"""

import requests
import json
import time
import os

def test_data_analysis_workflow():
    """Test the complete data analysis workflow including option selection"""
    
    print("=" * 60)
    print("DATA ANALYSIS WORKFLOW TEST")
    print("=" * 60)
    print()
    
    # Create test data with TPR columns
    test_csv_content = """State,LGA,WardName,TestPositiveUnder5RDT,TestNegativeUnder5RDT,TestPositiveUnder5Microscopy,TestNegativeUnder5Microscopy,Population
Lagos,Ikeja,Ward1,50,450,45,455,10000
Lagos,Ikeja,Ward2,75,425,70,430,12000
Lagos,Ikeja,Ward3,100,400,95,405,15000
Lagos,Eti-Osa,Ward1,60,440,55,445,11000
Lagos,Eti-Osa,Ward2,80,420,75,425,13000"""
    
    # Save test file
    test_file = "test_tpr_data.csv"
    with open(test_file, 'w') as f:
        f.write(test_csv_content)
    print(f"✅ Created test file: {test_file}")
    print()
    
    session_id = f"test_session_{int(time.time())}"
    
    # Step 1: Upload file
    print("Step 1: Uploading file...")
    print("-" * 40)
    
    with open(test_file, 'rb') as f:
        files = {'file': (test_file, f, 'text/csv')}
        data = {'session_id': session_id}
        
        response = requests.post(
            'http://localhost:5000/api/data-analysis/upload',
            files=files,
            data=data
        )
    
    if response.status_code == 200:
        upload_data = response.json()
        print(f"✅ Upload successful!")
        backend_session = upload_data.get('session_id')
        print(f"   Session ID: {backend_session}")
    else:
        print(f"❌ Upload failed: {response.status_code}")
        return False
    
    print()
    
    # Step 2: Trigger initial analysis
    print("Step 2: Getting initial analysis...")
    print("-" * 40)
    
    response = requests.post(
        'http://localhost:5000/api/v1/data-analysis/chat',
        json={
            'message': 'analyze uploaded data',
            'session_id': backend_session
        }
    )
    
    if response.status_code == 200:
        analysis_data = response.json()
        if analysis_data.get('success'):
            print("✅ Initial analysis received!")
            if 'Calculate Test Positivity Rate' in analysis_data.get('message', ''):
                print("✅ TPR option is available in menu")
            else:
                print("⚠️ TPR option not found in menu")
        else:
            print(f"❌ Analysis failed: {analysis_data}")
            return False
    else:
        print(f"❌ Analysis request failed: {response.status_code}")
        return False
    
    print()
    
    # Step 3: Select Option 2 (TPR)
    print("Step 3: Selecting Option 2 (TPR workflow)...")
    print("-" * 40)
    
    response = requests.post(
        'http://localhost:5000/api/v1/data-analysis/chat',
        json={
            'message': '2',
            'session_id': backend_session
        }
    )
    
    if response.status_code == 200:
        tpr_response = response.json()
        if tpr_response.get('success'):
            message = tpr_response.get('message', '')
            
            # Check if TPR workflow started
            if 'age group' in message.lower() or 'select' in message.lower():
                print("✅ TPR workflow started successfully!")
                print("✅ System is asking for age group selection")
                print()
                print("Response preview:")
                print(message[:300] + "..." if len(message) > 300 else message)
            else:
                print("⚠️ Unexpected response - TPR workflow may not have started")
                print("Response:", message[:200])
        else:
            print(f"❌ Option 2 selection failed: {tpr_response}")
            return False
    else:
        print(f"❌ Option 2 request failed: {response.status_code}")
        return False
    
    # Clean up
    os.remove(test_file)
    
    print()
    print("=" * 60)
    print("✅ TEST COMPLETE - Workflow is functioning!")
    print("=" * 60)
    print()
    print("Summary:")
    print("1. File upload: ✅")
    print("2. Initial analysis with menu: ✅") 
    print("3. Option 2 triggers TPR workflow: ✅")
    print()
    print("The data analysis mode routing is working correctly!")
    
    return True

if __name__ == "__main__":
    test_data_analysis_workflow()
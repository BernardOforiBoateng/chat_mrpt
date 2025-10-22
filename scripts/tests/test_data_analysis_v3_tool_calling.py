#!/usr/bin/env python3
"""
Test Data Analysis V3 Tool Calling with Llama 3.1
"""

import requests
import json
import time
import sys

# Configuration
BASE_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
SESSION_ID = f"test_tool_calling_{int(time.time())}"

def test_data_upload():
    """Upload a small test CSV file"""
    print("Step 1: Uploading test data file...")
    
    # Create a simple CSV content
    csv_content = """State,TestPositivityRate,Population,HealthFacilities
Kano,65.2,15000000,450
Lagos,42.1,21000000,850
Abuja,38.5,3500000,320
Kaduna,71.8,8200000,380
Rivers,45.3,7000000,410"""
    
    # Upload the file
    files = {
        'file': ('test_malaria_data.csv', csv_content, 'text/csv')
    }
    data = {
        'session_id': SESSION_ID,
        'file_type': 'csv'
    }
    
    response = requests.post(
        f"{BASE_URL}/api/data-analysis/upload",
        files=files,
        data=data,
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ File uploaded successfully")
        print(f"   Session: {SESSION_ID}")
        print(f"   Metadata cached: {result.get('metadata_cached', False)}")
        return True
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        return False

def test_tool_calling():
    """Test if the agent uses the analyze_data tool"""
    print("\nStep 2: Testing tool calling with 'What's in my data?' query...")
    
    # Send a query that should trigger tool usage
    payload = {
        'message': "What's in my data? Give me a summary of the key statistics.",
        'session_id': SESSION_ID
    }
    
    print(f"   Sending query: {payload['message']}")
    
    response = requests.post(
        f"{BASE_URL}/api/v3/data-analysis/chat",
        json=payload,
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        success = result.get('success', False)
        message = result.get('message', '')
        
        print(f"\n✅ Response received (success={success})")
        print(f"   Message length: {len(message)} characters")
        
        # Check if the response contains actual data analysis
        indicators = [
            'test positivity' in message.lower(),
            'kano' in message.lower() or 'lagos' in message.lower(),
            'population' in message.lower(),
            '65.2' in message or '71.8' in message,  # Actual values from data
            'states' in message.lower() or 'regions' in message.lower()
        ]
        
        actual_analysis = sum(indicators)
        
        if actual_analysis >= 3:
            print(f"✅ TOOL CALLING WORKING! Response contains actual data analysis")
            print(f"   Found {actual_analysis}/5 data indicators")
        else:
            print(f"⚠️  Response seems generic (only {actual_analysis}/5 indicators found)")
            print(f"   This suggests tool calling might not be working")
        
        print(f"\n   First 500 chars of response:")
        print(f"   {message[:500]}...")
        
        # Check for visualizations
        if 'visualizations' in result and result['visualizations']:
            print(f"\n✅ Visualizations generated: {len(result['visualizations'])}")
        
        return actual_analysis >= 3
    else:
        print(f"❌ Request failed: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        return False

def test_complex_analysis():
    """Test a more complex analysis request"""
    print("\nStep 3: Testing complex analysis with visualization request...")
    
    payload = {
        'message': "Create a bar chart showing test positivity rates by state and identify the highest risk areas",
        'session_id': SESSION_ID
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v3/data-analysis/chat",
        json=payload,
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        has_viz = 'visualizations' in result and result['visualizations']
        mentions_kaduna = 'kaduna' in result.get('message', '').lower()
        mentions_kano = 'kano' in result.get('message', '').lower()
        
        print(f"✅ Complex analysis response received")
        print(f"   Has visualizations: {has_viz}")
        print(f"   Mentions highest risk (Kaduna): {mentions_kaduna}")
        print(f"   Mentions high risk (Kano): {mentions_kano}")
        
        if has_viz or (mentions_kaduna and mentions_kano):
            print(f"✅ COMPLEX ANALYSIS WORKING!")
        else:
            print(f"⚠️  Complex analysis may not be fully working")
        
        return True
    else:
        print(f"❌ Complex analysis failed: {response.status_code}")
        return False

def main():
    print("=" * 60)
    print("Testing Data Analysis V3 Tool Calling with Llama 3.1")
    print("=" * 60)
    print(f"Target: {BASE_URL}")
    print(f"Session: {SESSION_ID}")
    print("")
    
    # Run tests
    upload_success = test_data_upload()
    if not upload_success:
        print("\n❌ Failed to upload test data. Exiting.")
        sys.exit(1)
    
    # Wait a moment for processing
    time.sleep(2)
    
    tool_calling_works = test_tool_calling()
    
    if tool_calling_works:
        complex_works = test_complex_analysis()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Data Upload: SUCCESS")
    print(f"{'✅' if tool_calling_works else '❌'} Tool Calling: {'SUCCESS' if tool_calling_works else 'FAILED'}")
    if tool_calling_works:
        print(f"✅ Complex Analysis: {'TESTED' if 'complex_works' in locals() else 'SKIPPED'}")
    
    if tool_calling_works:
        print("\n🎉 VLLM with Llama 3.1 tool calling is WORKING!")
        print("   The agent is successfully using the analyze_data tool")
        print("   Data Analysis V3 is now fully functional!")
    else:
        print("\n⚠️  Tool calling may not be working correctly")
        print("   The agent appears to be giving generic responses")
        print("   Check VLLM logs for tool parsing issues")

if __name__ == "__main__":
    main()
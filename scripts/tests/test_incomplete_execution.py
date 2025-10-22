#!/usr/bin/env python3
"""
Test to reproduce the incomplete tool execution issue.
The agent returns only 2 facilities when asked for top 10.
"""

import requests
import json
import time
import sys

# Test direct to staging instance
BASE_URL = "http://3.21.167.170:8080"

def test_incomplete_execution():
    """Test that specifically asks for top 10 and checks the response."""
    
    print("🧪 Testing Tool Execution Completeness")
    print("=" * 60)
    
    session_id = f"test_incomplete_{int(time.time())}"
    
    # First, upload the data file
    print("📤 Uploading test data...")
    
    # Read the cleaned TPR data
    import pandas as pd
    df = pd.read_csv('www/adamawa_tpr_cleaned.csv')
    print(f"   Data shape: {df.shape}")
    print(f"   First few columns: {list(df.columns[:5])}")
    
    # Upload the file
    files = {
        'file': ('adamawa_tpr_cleaned.csv', open('www/adamawa_tpr_cleaned.csv', 'rb'))
    }
    data = {'session_id': session_id}
    
    upload_response = requests.post(
        f"{BASE_URL}/api/data-analysis/upload",
        files=files,
        data=data,
        timeout=30
    )
    
    if upload_response.status_code != 200:
        print(f"   ❌ Upload failed: {upload_response.status_code}")
        return False
    
    print("   ✅ Data uploaded successfully")
    time.sleep(2)
    
    # Now test the specific query
    print("\n📝 Asking for top 10 facilities...")
    
    query = "Show me the top 10 facilities by total testing volume. List all 10 with their exact names and test counts."
    
    response = requests.post(
        f"{BASE_URL}/api/v1/data-analysis/chat",
        json={
            "message": query,
            "session_id": session_id
        },
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        message = result.get("message", "")
        
        print("\n📊 Response Analysis:")
        print("-" * 40)
        
        # Count how many facilities are mentioned
        import re
        
        # Look for patterns like "1. Name:" or "• Name" or just numbered lists
        facility_patterns = [
            r'\d+\.\s+([^:]+):\s*(\d+[,\d]*)',  # "1. Name: 123,456"
            r'•\s+([^:]+):\s*(\d+[,\d]*)',      # "• Name: 123,456"
            r'(\w+[\w\s]+(?:Health|Clinic|Hospital|Centre|Center))',  # Any health facility name
        ]
        
        facilities_found = []
        for pattern in facility_patterns:
            matches = re.findall(pattern, message)
            if matches:
                facilities_found.extend(matches)
        
        print(f"Facilities mentioned: {len(facilities_found)}")
        
        if len(facilities_found) < 10:
            print(f"   ⚠️  ISSUE: Only {len(facilities_found)} facilities returned (expected 10)")
            print("\n   First 500 chars of response:")
            print(f"   {message[:500]}...")
            
            # Check if there's an indication of truncation
            if "..." in message[-50:] or "etc" in message[-50:]:
                print("\n   📌 Response appears truncated!")
        else:
            print(f"   ✅ All 10 facilities returned")
        
        # Also check for error messages
        if "error" in message.lower() or "trouble" in message.lower():
            print("\n   ⚠️  Error indication found in response")
        
        return len(facilities_found) >= 10
        
    else:
        print(f"   ❌ Request failed: {response.status_code}")
        return False

def main():
    # Check service health
    print("🏥 Checking service health...")
    try:
        response = requests.get(f"{BASE_URL}/ping", timeout=5)
        if response.status_code == 200:
            print("✅ Service is healthy")
        else:
            print(f"⚠️  Service returned {response.status_code}")
    except Exception as e:
        print(f"❌ Service unreachable: {e}")
        sys.exit(1)
    
    print("")
    
    # Run the test
    success = test_incomplete_execution()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Test passed - Tool execution is complete")
    else:
        print("❌ Test failed - Tool execution is incomplete")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
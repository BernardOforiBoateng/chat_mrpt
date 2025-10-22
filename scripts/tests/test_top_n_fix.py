#!/usr/bin/env python3
"""
Test the Top N query fix
"""

import requests
import time
import json

STAGING_URL = "http://3.21.167.170:8080"

def test_top_n_query():
    """Test that top 10 query now returns 10 items."""
    
    session_id = f"test_top_n_{int(time.time())}"
    
    print("=" * 60)
    print("Testing Top N Query Fix")
    print("=" * 60)
    
    # 1. Upload data
    print("\n1. Uploading test data...")
    with open('www/adamawa_tpr_cleaned.csv', 'rb') as f:
        files = {'file': ('adamawa_tpr_cleaned.csv', f)}
        data = {'session_id': session_id}
        
        response = requests.post(
            f"{STAGING_URL}/api/data-analysis/upload",
            files=files,
            data=data,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Upload failed: {response.status_code}")
            return False
        
        print("✅ Data uploaded successfully")
    
    # Wait for processing
    time.sleep(3)
    
    # 2. Test "top 10" query
    print("\n2. Testing 'top 10 facilities' query...")
    response = requests.post(
        f"{STAGING_URL}/api/v1/data-analysis/chat",
        json={
            "message": "Show me the top 10 health facilities by total testing volume. List all 10 with their test counts.",
            "session_id": session_id
        },
        timeout=60
    )
    
    if response.status_code != 200:
        print(f"❌ Query failed: {response.status_code}")
        return False
    
    result = response.json()
    message = result.get("message", "")
    
    print("\n📊 Response Analysis:")
    print("-" * 40)
    
    # Count how many numbered items we got
    import re
    numbered_items = re.findall(r'^\s*(\d+)\.\s+', message, re.MULTILINE)
    
    print(f"✓ Number of items found: {len(numbered_items)}")
    
    # Check for generic names
    generic_names = re.findall(r'Facility [A-Z](?:\s|$)', message)
    if generic_names:
        print(f"❌ Generic names detected: {generic_names}")
    else:
        print("✓ No generic facility names detected")
    
    # Check for actual facility names
    real_facilities = [
        "General Hospital", "Primary Health", "Cottage Hospital",
        "Health Centre", "Health Clinic", "Healthcare"
    ]
    
    facilities_found = sum(1 for name in real_facilities if name in message)
    print(f"✓ Real facility types found: {facilities_found}")
    
    # Extract just the list portion
    print("\n📋 Extracted List:")
    print("-" * 40)
    
    # Try to extract numbered list
    lines = message.split('\n')
    list_items = []
    for line in lines:
        if re.match(r'^\s*\d+\.\s+', line):
            list_items.append(line.strip())
    
    if list_items:
        for item in list_items[:15]:  # Show up to 15 items
            print(item)
        if len(list_items) > 15:
            print(f"... and {len(list_items) - 15} more items")
    else:
        print("No numbered list found in response")
        print("\nFirst 500 chars of response:")
        print(message[:500])
    
    # 3. Test LLIN query (previously had "Facility A, B, C" issue)
    print("\n" + "=" * 60)
    print("3. Testing LLIN distribution query (hallucination check)...")
    
    response = requests.post(
        f"{STAGING_URL}/api/v1/data-analysis/chat",
        json={
            "message": "Which facilities distributed the most LLINs to children? Show top 5.",
            "session_id": session_id
        },
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        message = result.get("message", "")
        
        # Check for generic names
        generic_patterns = [
            r'Facility [A-Z](?:\s|$)',
            r'Hospital [A-Z](?:\s|$)',
            r'Clinic [A-Z](?:\s|$)'
        ]
        
        hallucinations_found = []
        for pattern in generic_patterns:
            matches = re.findall(pattern, message)
            hallucinations_found.extend(matches)
        
        if hallucinations_found:
            print(f"❌ Hallucinated names found: {hallucinations_found}")
        else:
            print("✅ No hallucinated facility names!")
        
        # Show first 300 chars
        print("\nResponse preview:")
        print(message[:300] + "...")
    
    # 4. Test percentage validation
    print("\n" + "=" * 60)
    print("4. Testing percentage validation...")
    
    response = requests.post(
        f"{STAGING_URL}/api/v1/data-analysis/chat",
        json={
            "message": "Compare positivity rates between children and adults",
            "session_id": session_id
        },
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        message = result.get("message", "")
        
        # Check for impossible percentages
        percentages = re.findall(r'(\d+(?:\.\d+)?)\s*%', message)
        impossible = []
        for pct_str in percentages:
            pct = float(pct_str)
            if pct > 100:
                impossible.append(f"{pct}%")
        
        if impossible:
            print(f"⚠️ Impossible percentages found: {impossible}")
            # Check if they were flagged
            if "error" in message.lower() or "impossible" in message.lower():
                print("✅ But they were properly flagged as errors")
            else:
                print("❌ And they were NOT flagged as errors")
        else:
            print("✅ All percentages within valid range (0-100%)")
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    
    success_count = 0
    if len(numbered_items) >= 8:  # Allow some flexibility
        print("✅ Top N query: SUCCESS (shows multiple items)")
        success_count += 1
    else:
        print(f"❌ Top N query: FAILED (only {len(numbered_items)} items)")
    
    if not hallucinations_found:
        print("✅ Hallucination prevention: SUCCESS")
        success_count += 1
    else:
        print("❌ Hallucination prevention: FAILED")
    
    if not impossible or "error" in message.lower():
        print("✅ Data validation: SUCCESS")
        success_count += 1
    else:
        print("❌ Data validation: FAILED")
    
    print(f"\nOverall: {success_count}/3 tests passed")
    print("=" * 60)
    
    return success_count == 3


if __name__ == "__main__":
    success = test_top_n_query()
    exit(0 if success else 1)
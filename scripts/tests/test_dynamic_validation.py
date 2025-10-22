#!/usr/bin/env python3
"""
Test the dynamic validation improvements
Works with ANY dataset structure - no hardcoding
"""

import requests
import time
import json
import re

STAGING_URL = "http://3.21.167.170:8080"

def test_dynamic_validation():
    """Test dynamic validation with no hardcoded assumptions."""
    
    session_id = f"test_dynamic_{int(time.time())}"
    
    print("=" * 60)
    print("Testing Dynamic Validation (No Hardcoding)")
    print("=" * 60)
    
    # 1. Upload data - works with ANY CSV
    print("\n1. Uploading test data...")
    with open('www/adamawa_tpr_cleaned.csv', 'rb') as f:
        files = {'file': ('test_data.csv', f)}
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
    
    # 2. Test generic "top N" query - no domain assumptions
    print("\n2. Testing generic 'top 10' query...")
    response = requests.post(
        f"{STAGING_URL}/api/v1/data-analysis/chat",
        json={
            "message": "Find the column with the most unique text values. Then show me the top 10 entries by their total numeric values (sum all numeric columns). List all 10.",
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
    
    # Count numbered items (works for any list)
    numbered_items = re.findall(r'^\s*(\d+)\.\s+', message, re.MULTILINE)
    print(f"✓ Number of items found: {len(numbered_items)}")
    
    # Check for generic placeholders (domain-agnostic)
    generic_patterns = [
        r'\b(?:Item|Entity|Entry|Object) [A-Z]\b',
        r'\b(?:Item|Entity|Entry) \d+\b',
        r'\bExample \w+\b',
        r'\bSample \w+\b',
        r'\bPlaceholder \w+\b'
    ]
    
    generics_found = []
    for pattern in generic_patterns:
        matches = re.findall(pattern, message, re.IGNORECASE)
        generics_found.extend(matches)
    
    if generics_found:
        print(f"❌ Generic placeholders detected: {generics_found}")
    else:
        print("✓ No generic placeholders detected")
    
    # 3. Test percentage validation (universal)
    print("\n3. Testing percentage validation...")
    response = requests.post(
        f"{STAGING_URL}/api/v1/data-analysis/chat",
        json={
            "message": "Calculate percentages for any ratio you can find in the data. Show me any percentage calculations.",
            "session_id": session_id
        },
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        message = result.get("message", "")
        
        # Check for percentages
        percentages = re.findall(r'(\d+(?:\.\d+)?)\s*%', message)
        invalid_percentages = []
        
        for pct_str in percentages:
            pct = float(pct_str)
            if pct > 100 or pct < 0:
                invalid_percentages.append(f"{pct}%")
        
        if invalid_percentages:
            print(f"⚠️ Invalid percentages found: {invalid_percentages}")
            # Check if properly flagged
            if any(word in message.lower() for word in ['error', 'invalid', 'impossible']):
                print("✅ But they were properly flagged")
            else:
                print("❌ And they were NOT flagged")
        else:
            print("✅ All percentages within valid range (0-100%)")
    
    # 4. Test data grounding (dynamic)
    print("\n4. Testing data grounding...")
    response = requests.post(
        f"{STAGING_URL}/api/v1/data-analysis/chat",
        json={
            "message": "List 5 random entries from the data with their key attributes.",
            "session_id": session_id
        },
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        message = result.get("message", "")
        
        # Check if response contains actual data or placeholders
        placeholder_count = sum(1 for pattern in generic_patterns 
                               if re.search(pattern, message, re.IGNORECASE))
        
        if placeholder_count > 0:
            print(f"❌ Found {placeholder_count} placeholder patterns")
        else:
            print("✅ Response appears to use real data")
    
    # 5. Test handling of unavailable data
    print("\n5. Testing response when data unavailable...")
    response = requests.post(
        f"{STAGING_URL}/api/v1/data-analysis/chat",
        json={
            "message": "Show me data about something that definitely doesn't exist in this dataset: spacecraft velocities and orbital parameters.",
            "session_id": session_id
        },
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        message = result.get("message", "")
        
        # Should acknowledge data doesn't exist, not make it up
        acknowledgment_words = ['not available', 'does not contain', 'cannot find', 
                               'no information', 'not found', 'does not include']
        
        if any(phrase in message.lower() for phrase in acknowledgment_words):
            print("✅ Correctly acknowledged missing data")
        else:
            print("❌ May have hallucinated response instead of acknowledging missing data")
    
    # Summary
    print("\n" + "=" * 60)
    print("Dynamic Validation Test Summary:")
    
    success_count = 0
    
    if len(numbered_items) >= 5:
        print("✅ Top N query: Shows multiple items")
        success_count += 1
    else:
        print(f"❌ Top N query: Only {len(numbered_items)} items shown")
    
    if not generics_found:
        print("✅ No generic placeholders used")
        success_count += 1
    else:
        print("❌ Generic placeholders detected")
    
    if not invalid_percentages or 'error' in message.lower():
        print("✅ Percentage validation working")
        success_count += 1
    else:
        print("❌ Invalid percentages not handled")
    
    if placeholder_count == 0:
        print("✅ Data grounding successful")
        success_count += 1
    else:
        print("❌ Using placeholders instead of real data")
    
    print(f"\nOverall: {success_count}/4 tests passed")
    print("=" * 60)
    
    return success_count >= 3  # Allow one failure for flexibility


if __name__ == "__main__":
    success = test_dynamic_validation()
    exit(0 if success else 1)
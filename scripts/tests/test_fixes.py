#!/usr/bin/env python3
"""
Test if our fixes resolved the issues
"""

import requests
import time
import re

STAGING_URL = "http://3.21.167.170:8080"

def test_fixes():
    session_id = f"test_fixes_{int(time.time())}"
    
    print("=" * 60)
    print("TESTING FIXES FOR TOP N AND HALLUCINATION")
    print("=" * 60)
    
    # Upload data
    print("\n1. Uploading data...")
    with open('www/adamawa_tpr_cleaned.csv', 'rb') as f:
        files = {'file': ('test.csv', f)}
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
            
        print("✅ Data uploaded")
    
    time.sleep(3)
    
    # Test 1: Top 10 query
    print("\n2. Testing 'Top 10' query...")
    response = requests.post(
        f"{STAGING_URL}/api/v1/data-analysis/chat",
        json={
            "message": "Show me the top 10 health facilities by total testing volume. List all 10.",
            "session_id": session_id
        },
        timeout=60
    )
    
    success_count = 0
    
    if response.status_code == 200:
        result = response.json()
        message = result.get("message", "")
        
        # Count numbered items
        numbered_items = re.findall(r'^\s*\d+\.', message, re.MULTILINE)
        
        print(f"   Found {len(numbered_items)} numbered items")
        
        if len(numbered_items) >= 10:
            print("   ✅ TOP 10 FIXED! Shows all 10 items")
            success_count += 1
        elif len(numbered_items) >= 8:
            print(f"   ⚠️ PARTIAL FIX: Shows {len(numbered_items)} items (close to 10)")
            success_count += 0.5
        else:
            print(f"   ❌ STILL BROKEN: Only shows {len(numbered_items)} items")
        
        # Check for hallucination
        if "Facility A" in message or "Facility B" in message:
            print("   ❌ HALLUCINATION: Still using 'Facility A, B, C'")
        else:
            print("   ✅ NO HALLUCINATION: Using real facility names")
            success_count += 1
        
        # Show sample of response
        print("\n   Response preview:")
        lines = message.split('\n')
        for line in lines[:15]:
            if re.match(r'^\s*\d+\.', line):
                print(f"   {line}")
    
    # Test 2: Explicit code test
    print("\n3. Testing explicit code execution...")
    response = requests.post(
        f"{STAGING_URL}/api/v1/data-analysis/chat",
        json={
            "message": "Run this exact code: for i, name in enumerate(df['healthfacility'].unique()[:10], 1): print(f'{i}. {name}')",
            "session_id": session_id
        },
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        message = result.get("message", "")
        
        numbered_items = re.findall(r'^\s*\d+\.', message, re.MULTILINE)
        
        if len(numbered_items) >= 10:
            print("   ✅ EXPLICIT CODE: Shows all 10 items")
            success_count += 1
        else:
            print(f"   ❌ EXPLICIT CODE: Only shows {len(numbered_items)} items")
    
    # Test 3: Check if columns are all visible
    print("\n4. Testing column visibility...")
    response = requests.post(
        f"{STAGING_URL}/api/v1/data-analysis/chat",
        json={
            "message": "How many columns are in the dataset?",
            "session_id": session_id
        },
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        message = result.get("message", "")
        
        if "22" in message:
            print("   ✅ COLUMNS: Correctly reports 22 columns")
            success_count += 1
        else:
            print("   ❌ COLUMNS: Incorrect column count")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    total_tests = 4
    print(f"\nPassed: {success_count}/{total_tests} tests")
    
    if success_count >= 3:
        print("\n🎉 SUCCESS! Major issues are fixed!")
    elif success_count >= 2:
        print("\n⚠️ PARTIAL SUCCESS: Some issues fixed, some remain")
    else:
        print("\n❌ FIXES NOT WORKING: Issues persist")
    
    return success_count >= 3

if __name__ == "__main__":
    success = test_fixes()
    exit(0 if success else 1)
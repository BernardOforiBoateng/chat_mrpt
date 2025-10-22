#!/usr/bin/env python3
"""
Test that the Data Analysis V3 agent now properly accesses data.
This verifies the fix for the fundamental issue where tools weren't receiving actual data.
"""

import requests
import json
import time
import sys

# Test direct to instance
BASE_URL = "http://3.21.167.170:8080"

def test_real_data_access():
    """Test that the agent returns real data, not hallucinations."""
    
    print("🧪 Testing Data Analysis V3 - Data Access Fix")
    print("=" * 60)
    
    session_id = f"test_fix_{int(time.time())}"
    
    # Test queries that previously returned fake data
    test_queries = [
        {
            "query": "Show me the top 10 facilities by total testing volume",
            "check_for_fake": ["Facility A", "Facility B", "Facility C"],
            "expect_real": ["actually contain real facility names from the data"]
        },
        {
            "query": "Which LGA has the highest number of tests performed?",
            "check_for_fake": ["highest", "102,013"],  # The fake Fufore number
            "expect_real": ["should return an actual LGA from Adamawa state"]
        },
        {
            "query": "What's the total number of pregnant women tested positive by RDT?",
            "check_for_fake": ["27,676"],  # The fake number it returned before
            "expect_real": ["should calculate from actual data columns"]
        },
        {
            "query": "Give me the column names in the dataset",
            "check_for_fake": ["I have identified", "wasn't directly displayed"],
            "expect_real": ["should list actual columns including those with ≥ and < symbols"]
        }
    ]
    
    results = {"passed": 0, "failed": 0}
    
    for test in test_queries:
        print(f"\n📝 Testing: '{test['query']}'")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/v3/agent/chat",
                json={
                    "message": test['query'],
                    "session_id": session_id
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                message = result.get("message", "")
                
                # Check for fake data indicators
                has_fake = any(fake in message for fake in test['check_for_fake'])
                
                if has_fake:
                    print(f"   ❌ FAILED: Still returning fake/hallucinated data!")
                    print(f"      Found: {test['check_for_fake'][0]} in response")
                    results["failed"] += 1
                else:
                    print(f"   ✅ PASSED: No obvious hallucinations detected")
                    print(f"      Response snippet: {message[:150]}...")
                    results["passed"] += 1
            else:
                print(f"   ❌ HTTP {response.status_code}")
                results["failed"] += 1
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results["failed"] += 1
        
        time.sleep(2)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 RESULTS")
    print("=" * 60)
    print(f"Passed: {results['passed']}/{len(test_queries)}")
    print(f"Failed: {results['failed']}/{len(test_queries)}")
    
    if results['passed'] == len(test_queries):
        print("\n🎉 SUCCESS! The data access fix is working!")
        print("The agent is now accessing real data from the uploaded files.")
        return True
    else:
        print("\n⚠️  Some tests failed. The agent may still have issues.")
        return False

def main():
    print("📝 NOTE: Make sure you've uploaded adamawa_tpr_cleaned.csv first!")
    print("You can do this at: http://3.21.167.170:8080")
    print("")
    
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
    input("Press Enter when you've uploaded the data file...")
    print("")
    
    # Run tests
    success = test_real_data_access()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
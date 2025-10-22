#!/usr/bin/env python3
"""
Test Data Analysis V3 agent with real Adamawa TPR data.
Tests that the encoding fix properly handles columns with special characters (≥, <).
"""

import requests
import json
import time
import sys
import os

# Configuration - test directly against staging instance
BASE_URL = "http://3.21.167.170:8080"  # Staging instance 1
DATA_FILE = "/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/adamawa_tpr_cleaned.csv"

# Real questions based on actual Adamawa TPR data structure
TEST_QUESTIONS = [
    # 1. Questions that directly reference columns with special characters
    {
        "query": "Show me the total number of people tested by RDT for age ≥5 years",
        "tests_encoding": True,
        "expected_behavior": "Should access 'Persons presenting with fever & tested by RDT ≥5yrs' column"
    },
    {
        "query": "What's the total testing volume for children <5 years across all facilities?",
        "tests_encoding": True,
        "expected_behavior": "Should access '<5yrs' columns without error"
    },
    {
        "query": "Calculate the positivity rate for pregnant women tested by RDT",
        "tests_encoding": False,
        "expected_behavior": "Should calculate ratio of positive/tested for PW"
    },
    
    # 2. Facility-level analysis questions
    {
        "query": "Which health facilities in Yola South have the highest testing volume?",
        "tests_encoding": False,
        "expected_behavior": "Should filter by LGA and rank facilities"
    },
    {
        "query": "Show me the top 10 facilities by total malaria positive cases",
        "tests_encoding": True,
        "expected_behavior": "Should sum positive columns across age groups"
    },
    
    # 3. Temporal analysis questions
    {
        "query": "What are the monthly trends in malaria cases from January to June 2024?",
        "tests_encoding": False,
        "expected_behavior": "Should use periodcode column for time series"
    },
    {
        "query": "Which months had the highest test positivity rates?",
        "tests_encoding": False,
        "expected_behavior": "Should calculate TPR by month"
    },
    
    # 4. Geographic analysis questions
    {
        "query": "Compare malaria burden between different LGAs in Adamawa",
        "tests_encoding": False,
        "expected_behavior": "Should group by LGA and aggregate"
    },
    {
        "query": "Which wards have the highest number of positive cases?",
        "tests_encoding": False,
        "expected_behavior": "Should group by WardName"
    },
    
    # 5. Demographic analysis with special characters
    {
        "query": "Compare testing rates between children under 5 and adults over 5 years",
        "tests_encoding": True,
        "expected_behavior": "Should compare <5yrs vs ≥5yrs columns"
    },
    {
        "query": "What percentage of tested pregnant women were positive for malaria?",
        "tests_encoding": False,
        "expected_behavior": "Should calculate PW positivity rate"
    },
    
    # 6. LLIN coverage questions
    {
        "query": "How many pregnant women received LLIN across all facilities?",
        "tests_encoding": False,
        "expected_behavior": "Should sum 'PW who received LLIN' column"
    },
    {
        "query": "What's the LLIN coverage for children under 5 years?",
        "tests_encoding": True,
        "expected_behavior": "Should access 'Children <5 yrs who received LLIN'"
    },
    
    # 7. Complex analytical questions
    {
        "query": "Create a summary of key malaria indicators by facility level (Primary vs Secondary)",
        "tests_encoding": False,
        "expected_behavior": "Should group by FacilityLevel"
    },
    {
        "query": "Identify facilities with unusually high positivity rates compared to the state average",
        "tests_encoding": True,
        "expected_behavior": "Should calculate facility TPR and compare to mean"
    }
]

def upload_data_file(session_id):
    """Upload the Adamawa TPR data file."""
    print(f"📤 Uploading Adamawa TPR data...")
    
    try:
        with open(DATA_FILE, 'rb') as f:
            files = {'file': ('adamawa_tpr_cleaned.csv', f, 'text/csv')}
            response = requests.post(
                f"{BASE_URL}/upload",
                files=files,
                data={'session_id': session_id},
                timeout=30
            )
            
        if response.status_code == 200:
            print("✅ Data uploaded successfully")
            return True
        else:
            print(f"❌ Upload failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

def test_agent_questions(session_id):
    """Test the agent with various questions."""
    
    print("\n🧪 Testing Data Analysis V3 Agent with Adamawa TPR Data")
    print("=" * 60)
    
    results = {
        "total": len(TEST_QUESTIONS),
        "passed": 0,
        "failed": 0,
        "hallucinations": 0
    }
    
    # Hallucination indicators
    hallucination_patterns = [
        "Facility A", "Facility B", "Facility C",  # Fake facility names
        "82.3%", "73.5%", "91.2%",  # Suspiciously specific fake percentages
        "I'll create", "example data", "hypothetical",
        "sample facilities", "let me generate"
    ]
    
    for i, test in enumerate(TEST_QUESTIONS, 1):
        print(f"\n📝 Test {i}/{len(TEST_QUESTIONS)}: {test['query'][:60]}...")
        
        if test['tests_encoding']:
            print("   ⚠️  This tests encoding handling for special characters")
        
        try:
            # Send query to agent
            response = requests.post(
                f"{BASE_URL}/api/v3/agent/chat",
                json={
                    "message": test['query'],
                    "session_id": session_id
                },
                timeout=45
            )
            
            if response.status_code == 200:
                result = response.json()
                message = result.get("message", "")
                
                # Check for success
                if result.get("success"):
                    # Check for hallucinations
                    has_hallucination = any(
                        pattern.lower() in message.lower() 
                        for pattern in hallucination_patterns
                    )
                    
                    if has_hallucination:
                        print(f"   ❌ FAILED: Agent hallucinated!")
                        print(f"      Response snippet: {message[:150]}...")
                        results["failed"] += 1
                        results["hallucinations"] += 1
                    else:
                        print(f"   ✅ PASSED: Got valid response")
                        print(f"      Response snippet: {message[:150]}...")
                        results["passed"] += 1
                else:
                    print(f"   ❌ FAILED: {result.get('error', 'Unknown error')}")
                    results["failed"] += 1
            else:
                print(f"   ❌ HTTP {response.status_code}: {response.text[:100]}")
                results["failed"] += 1
                
        except requests.exceptions.Timeout:
            print(f"   ⏱️  Request timed out")
            results["failed"] += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results["failed"] += 1
        
        # Small delay between requests
        time.sleep(2)
    
    return results

def print_results(results):
    """Print test results summary."""
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {results['total']}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"🤖 Hallucinations: {results['hallucinations']}")
    
    success_rate = (results['passed'] / results['total']) * 100 if results['total'] > 0 else 0
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    if results['hallucinations'] > 0:
        print("\n⚠️  WARNING: Agent hallucinated fake data!")
        print("This indicates the encoding fix may not be working properly.")
    
    if success_rate >= 80:
        print("\n🎉 ENCODING FIX IS WORKING!")
        print("The agent successfully handles columns with special characters.")
    elif success_rate >= 50:
        print("\n⚠️  PARTIAL SUCCESS")
        print("Some encoding issues may still exist.")
    else:
        print("\n❌ ENCODING FIX NEEDS MORE WORK")
        print("The agent is still struggling with encoded column names.")
    
    return success_rate >= 80

def main():
    """Main test execution."""
    
    # Check if data file exists
    if not os.path.exists(DATA_FILE):
        print(f"❌ Data file not found: {DATA_FILE}")
        sys.exit(1)
    
    # Generate session ID
    session_id = f"test_adamawa_{int(time.time())}"
    print(f"📝 Session ID: {session_id}")
    
    # First check service health
    print("\n🏥 Checking service health...")
    try:
        response = requests.get(f"{BASE_URL}/ping", timeout=5)
        if response.status_code == 200:
            print("✅ Service is healthy")
        else:
            print(f"⚠️  Service returned {response.status_code}")
    except Exception as e:
        print(f"❌ Service unreachable: {e}")
        print("\nPlease ensure staging server is running.")
        sys.exit(1)
    
    # Upload data
    if not upload_data_file(session_id):
        print("❌ Failed to upload data file")
        sys.exit(1)
    
    # Wait for processing
    print("⏳ Waiting for data processing...")
    time.sleep(3)
    
    # Run tests
    results = test_agent_questions(session_id)
    
    # Print summary
    success = print_results(results)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
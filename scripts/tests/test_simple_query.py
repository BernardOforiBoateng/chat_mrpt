#!/usr/bin/env python3
"""
Test simple queries to understand what's happening with the agent.
"""

import requests
import json
import time

# Test direct to staging instance
BASE_URL = "http://3.21.167.170:8080"

def test_simple_queries():
    """Test progressively complex queries to isolate the issue."""
    
    print("🧪 Testing Simple Data Analysis V3 Queries")
    print("=" * 60)
    
    session_id = f"test_simple_{int(time.time())}"
    
    # First, upload the data file
    print("📤 Uploading test data...")
    
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
        return
    
    print("   ✅ Data uploaded successfully")
    time.sleep(2)
    
    # Test queries from simple to complex
    test_queries = [
        {
            "name": "Column names",
            "query": "What are the column names in the dataset?",
            "expect": ["columns", "names"]
        },
        {
            "name": "Data shape",
            "query": "What is the shape of the data? How many rows and columns?",
            "expect": ["rows", "columns", "shape"]
        },
        {
            "name": "First 3 rows",
            "query": "Show me the first 3 rows of the data",
            "expect": ["HealthFacility", "WardName", "LGA"]
        },
        {
            "name": "Simple sum",
            "query": "What is the sum of the column 'Persons presenting with fever & tested by RDT <5yrs'?",
            "expect": ["sum", "total"]
        },
        {
            "name": "Facility list",
            "query": "List 5 health facility names from the data",
            "expect": ["Health", "Clinic", "Hospital", "Centre"]
        },
        {
            "name": "Top facilities",
            "query": "Show me the top 5 facilities by total testing volume",
            "expect": ["top", "facilities", "test"]
        }
    ]
    
    for test in test_queries:
        print(f"\n📝 Test: {test['name']}")
        print(f"   Query: '{test['query']}'")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/data-analysis/chat",
                json={
                    "message": test['query'],
                    "session_id": session_id
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                message = result.get("message", "")
                
                # Check if expected terms are in response
                found_expected = any(exp.lower() in message.lower() for exp in test['expect'])
                
                if found_expected:
                    print(f"   ✅ Response contains expected terms")
                    print(f"   Preview: {message[:200]}...")
                else:
                    print(f"   ⚠️  Response missing expected terms")
                    print(f"   Response: {message[:300]}...")
                
                # Check for error indicators
                if any(err in message.lower() for err in ['error', 'trouble', 'issue', 'problem', 'difficulty']):
                    print(f"   ⚠️  Error indicator found in response")
                    
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(3)  # Wait between queries

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
        return
    
    print("")
    
    # Run the tests
    test_simple_queries()

if __name__ == "__main__":
    main()
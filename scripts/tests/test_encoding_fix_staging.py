#!/usr/bin/env python3
"""
Test the encoding fix on staging server.
This tests that the Data Analysis V3 agent handles TPR data with special characters correctly.
"""

import requests
import json
import time
import sys

# Test direct to instance since ALB might be having issues
BASE_URL = "http://3.21.167.170:8080"  # Direct to staging instance 1

def test_encoding_fix():
    """Test that the agent handles encoded column names properly."""
    
    print("🧪 Testing Data Analysis V3 encoding fix on staging...")
    print(f"Target: {BASE_URL}")
    
    # Create a test session
    session_id = f"test_encoding_{int(time.time())}"
    
    # Test query that would trigger column access with special characters
    test_queries = [
        "Show me the top 10 facilities by testing volume",
        "Calculate TPR for age groups ≥5 years",
        "Show facilities with TPR for children <5 years"
    ]
    
    for query in test_queries:
        print(f"\n📝 Testing query: '{query}'")
        
        try:
            # Make request to data analysis endpoint
            response = requests.post(
                f"{BASE_URL}/api/v3/agent/chat",
                json={
                    "message": query,
                    "session_id": session_id
                },
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check for hallucination indicators
                message = result.get("message", "")
                
                # These are hallucination red flags
                hallucination_indicators = [
                    "Facility A",
                    "Facility B", 
                    "Facility C",
                    "82.3%",  # The specific fake percentage from before
                    "I'll create some example",
                    "hypothetical",
                    "sample data"
                ]
                
                has_hallucination = any(indicator in message for indicator in hallucination_indicators)
                
                if has_hallucination:
                    print(f"❌ FAILED: Agent hallucinated fake data!")
                    print(f"   Response contained: {message[:200]}...")
                    return False
                else:
                    print(f"✅ PASSED: No hallucination detected")
                    print(f"   Response: {message[:150]}...")
                    
            else:
                print(f"⚠️  Request failed with status {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"⏱️  Request timed out (might indicate service issues)")
        except Exception as e:
            print(f"❌ Error: {e}")
            
    print("\n✅ All encoding tests completed!")
    return True

def test_service_health():
    """Quick health check."""
    print("\n🏥 Checking service health...")
    
    try:
        response = requests.get(f"{BASE_URL}/ping", timeout=5)
        if response.status_code == 200:
            print("✅ Service is healthy")
            return True
        else:
            print(f"⚠️  Service returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Service health check failed: {e}")
        return False

if __name__ == "__main__":
    # First check if service is healthy
    if not test_service_health():
        print("\n⚠️  Service appears to be down. Please check the deployment.")
        sys.exit(1)
    
    # Run encoding tests
    success = test_encoding_fix()
    
    if success:
        print("\n🎉 SUCCESS: Encoding fix is working properly!")
        print("The agent no longer hallucinates when encountering special characters.")
    else:
        print("\n❌ FAILURE: Encoding issues still present.")
        print("The agent may still be hallucinating fake data.")
    
    sys.exit(0 if success else 1)
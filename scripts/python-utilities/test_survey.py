#!/usr/bin/env python3
"""
Quick test script for survey functionality
"""

import json
import requests
import sys

BASE_URL = "http://127.0.0.1:5000"

def test_survey_page():
    """Test that survey page loads"""
    print("Testing survey page...")
    response = requests.get(f"{BASE_URL}/survey/")
    assert response.status_code == 200, f"Survey page failed: {response.status_code}"
    assert "ChatMRPT Cognitive Assessment" in response.text
    print("✅ Survey page loads successfully")

def test_survey_status():
    """Test survey status endpoint"""
    print("\nTesting survey status...")
    response = requests.get(f"{BASE_URL}/survey/api/status/test_session_123")
    assert response.status_code == 200, f"Survey status failed: {response.status_code}"
    data = response.json()
    assert "success" in data
    print(f"✅ Survey status endpoint works: {data}")

def test_start_survey():
    """Test starting a survey session"""
    print("\nTesting survey session start...")
    payload = {
        "chatmrpt_session_id": "test_session_123",
        "trigger_type": "arena_comparison",
        "context": {
            "models": ["Model A", "Model B", "Model C"]
        }
    }
    response = requests.post(f"{BASE_URL}/survey/api/start", json=payload)
    assert response.status_code == 200, f"Survey start failed: {response.status_code}"
    data = response.json()
    assert "session_id" in data
    assert "questions" in data
    print(f"✅ Survey started: {data['session_id']}")
    print(f"   Questions received: {len(data['questions'])}")
    return data['session_id']

def test_submit_response(session_id):
    """Test submitting a survey response"""
    print("\nTesting response submission...")
    payload = {
        "session_id": session_id,
        "question_id": "arena_pref_1",
        "response": "Model A",
        "time_spent": 30
    }
    response = requests.post(f"{BASE_URL}/survey/api/submit", json=payload)
    assert response.status_code == 200, f"Response submit failed: {response.status_code}"
    data = response.json()
    assert data["success"] == True
    print(f"✅ Response submitted successfully")

def main():
    """Run all tests"""
    print("=" * 50)
    print("SURVEY MODULE TEST SUITE")
    print("=" * 50)

    try:
        # Check if server is running
        try:
            response = requests.get(f"{BASE_URL}/ping")
            if response.status_code != 200:
                print("❌ Server not responding. Please start the Flask server first.")
                print("   Run: python run.py")
                sys.exit(1)
        except requests.ConnectionError:
            print("❌ Cannot connect to server. Please start the Flask server first.")
            print("   Run: python run.py")
            sys.exit(1)

        # Run tests
        test_survey_page()
        test_survey_status()
        session_id = test_start_survey()
        test_submit_response(session_id)

        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED!")
        print("=" * 50)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
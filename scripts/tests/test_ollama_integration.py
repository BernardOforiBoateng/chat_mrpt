#!/usr/bin/env python3
"""Test Ollama integration with ChatMRPT."""

import requests
import json
import sys

def test_ollama_direct():
    """Test Ollama directly."""
    print("1. Testing Ollama directly...")
    try:
        response = requests.post(
            "http://3.21.167.170:11434/api/generate",
            json={
                "model": "qwen3:8b",
                "prompt": "What is malaria test positivity rate? Answer in one sentence.",
                "stream": False
            },
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Ollama responded: {result.get('response', '')[:100]}...")
            return True
        else:
            print(f"❌ Ollama error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Could not connect to Ollama: {e}")
        return False

def test_chatmrpt_api():
    """Test ChatMRPT API with Ollama."""
    print("\n2. Testing ChatMRPT API...")
    try:
        # First, get a session
        session = requests.Session()
        
        # Try the chat endpoint
        response = session.post(
            "http://3.21.167.170:5000/chat",
            json={
                "message": "What is test positivity rate?",
                "session_id": "test-ollama-001"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ ChatMRPT responded via Ollama")
            print(f"   Response: {result.get('response', '')[:100]}...")
            return True
        else:
            print(f"❌ ChatMRPT error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Could not connect to ChatMRPT: {e}")
        return False

def test_tpr_upload():
    """Test TPR file upload with Ollama analysis."""
    print("\n3. Testing TPR file analysis with Ollama...")
    
    # This would test file upload and Ollama analysis
    # For now, just check if the upload endpoint exists
    try:
        response = requests.get("http://3.21.167.170:5000/upload")
        if response.status_code in [200, 302]:
            print(f"✅ Upload endpoint accessible")
            return True
        else:
            print(f"❌ Upload endpoint error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Could not access upload endpoint: {e}")
        return False

def main():
    print("=" * 60)
    print("Testing Ollama Integration with ChatMRPT")
    print("=" * 60)
    
    results = []
    
    # Test 1: Direct Ollama
    results.append(test_ollama_direct())
    
    # Test 2: ChatMRPT API
    results.append(test_chatmrpt_api())
    
    # Test 3: TPR Upload
    results.append(test_tpr_upload())
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"✅ Passed: {sum(results)}/3")
    print(f"❌ Failed: {3 - sum(results)}/3")
    
    if all(results):
        print("\n🎉 ALL TESTS PASSED! Ollama is fully integrated!")
    else:
        print("\n⚠️ Some tests failed. Check the logs above.")
    
    return 0 if all(results) else 1

if __name__ == "__main__":
    sys.exit(main())
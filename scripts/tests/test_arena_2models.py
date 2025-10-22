#!/usr/bin/env python3
"""
Test Arena system with 2 real models (TinyLlama and Qwen2.5)
"""

import requests
import json
import time

# Test against production (formerly staging)
BASE_URL = "https://d225ar6c86586s.cloudfront.net"

def test_arena_chat():
    """Test Arena mode with a simple chat message"""
    print("\n=== Testing Arena with 2 Different Models ===\n")
    
    # Test message
    message = "What are the main factors that contribute to malaria transmission?"
    
    print(f"Sending message: {message}")
    print("-" * 50)
    
    # Send Arena request
    response = requests.post(
        f"{BASE_URL}/send_message",
        json={
            "message": message,
            "use_arena": True,  # Enable Arena mode
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        },
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        
        # Debug: print the actual response structure
        print(f"Response keys: {result.keys()}")
        print(f"Success: {result.get('success')}")
        print(f"Full response: {json.dumps(result, indent=2)[:1000]}...")
        
        if result.get('success'):
            
            # Check if we got Arena format
            if 'arena_responses' in result:
                print("=== Model A Response ===")
                print(result['arena_responses']['response_a'][:500] + "...")
                print("\n=== Model B Response ===")
                print(result['arena_responses']['response_b'][:500] + "...")
                
                print("\n=== Metadata ===")
                print(f"Battle ID: {result['arena_responses'].get('battle_id', 'N/A')}")
                print(f"View Index: {result['arena_responses'].get('view_index', 'N/A')}")
                print(f"Processing Time: {result.get('processing_time', 'N/A')}ms")
                
                # Check if responses are different
                resp_a = result['arena_responses']['response_a']
                resp_b = result['arena_responses']['response_b']
                
                if resp_a != resp_b:
                    print("\n✓ SUCCESS: Models gave different responses!")
                    print(f"Response A length: {len(resp_a)} chars")
                    print(f"Response B length: {len(resp_b)} chars")
                else:
                    print("\n⚠ WARNING: Both models gave identical responses")
            else:
                print("Regular response (not Arena format):")
                print(result.get('message', 'No message')[:500])
        else:
            print(f"✗ Request failed: {result.get('message', 'Unknown error')}")
    else:
        print(f"✗ HTTP Error {response.status_code}: {response.text[:200]}")
    
    return response.status_code == 200

def test_direct_vllm():
    """Test direct access to both vLLM models"""
    print("\n=== Testing Direct vLLM Access ===\n")
    
    models = [
        ("TinyLlama", "http://172.31.45.157:8000", "/home/ec2-user/models/tinyllama-1.1b"),
        ("Qwen2.5", "http://172.31.45.157:8001", "/home/ec2-user/models/qwen2.5-1.5b")
    ]
    
    prompt = "What causes malaria?"
    
    for name, url, path in models:
        print(f"Testing {name} at {url}...")
        try:
            # First SSH tunnel might be needed
            response = requests.post(
                f"{url}/v1/completions",
                json={
                    "model": path,
                    "prompt": prompt,
                    "max_tokens": 100
                },
                timeout=10
            )
            
            if response.status_code == 200:
                text = response.json()['choices'][0]['text']
                print(f"✓ {name} responded: {text[:100]}...")
            else:
                print(f"✗ {name} error: {response.status_code}")
        except Exception as e:
            print(f"✗ {name} connection error: {e}")
    

if __name__ == "__main__":
    print("=" * 60)
    print("Arena System Test - 2 Real Models")
    print("=" * 60)
    
    # Test Arena chat
    success = test_arena_chat()
    
    if success:
        print("\n" + "=" * 60)
        print("✓ Arena test completed successfully!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("✗ Arena test failed")
        print("=" * 60)
#!/usr/bin/env python3
"""Test Arena with Ollama backend - 2 different models"""

import requests
import json
import time

BASE_URL = "https://d225ar6c86586s.cloudfront.net"

print("=" * 60)
print("🎮 ARENA TEST WITH OLLAMA")
print("=" * 60)

# Test message
message = "What are the best ways to prevent malaria?"

print(f"\n📝 Question: {message}")
print("-" * 60)

# Send Arena request
print("\n⏳ Sending Arena request...")
response = requests.post(
    f"{BASE_URL}/send_message",
    json={
        "message": message,
        "use_arena": True
    },
    timeout=60
)

print(f"📊 Status Code: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    
    # Display responses
    if 'response_a' in result and 'response_b' in result:
        print("\n" + "=" * 60)
        print("🤖 MODEL A (TinyLlama) Response:")
        print("-" * 60)
        print(result['response_a'][:300] + "..." if len(result['response_a']) > 300 else result['response_a'])
        
        print("\n" + "=" * 60)
        print("🤖 MODEL B (Qwen2.5) Response:")
        print("-" * 60)
        print(result['response_b'][:300] + "..." if len(result['response_b']) > 300 else result['response_b'])
        
        # Check if responses are different
        if result['response_a'] != result['response_b']:
            print("\n" + "=" * 60)
            print("✅ SUCCESS: Different responses from 2 models!")
            print(f"   Model A length: {len(result['response_a'])} chars")
            print(f"   Model B length: {len(result['response_b'])} chars")
            
            # Show latencies
            print(f"\n⚡ Performance:")
            print(f"   Model A latency: {result.get('latency_a', 'N/A')}ms")
            print(f"   Model B latency: {result.get('latency_b', 'N/A')}ms")
        else:
            print("\n⚠️  Both models gave identical responses")
    else:
        print(f"\n❌ Unexpected response format:")
        print(json.dumps(result, indent=2)[:500])
else:
    print(f"\n❌ Error: {response.text[:200]}")

print("\n" + "=" * 60)
print("🎯 Ollama Arena Test Complete!")
print("=" * 60)
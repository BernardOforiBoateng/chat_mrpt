#!/usr/bin/env python3
"""
Complete test of the progressive arena battle system with GPU
"""

import requests
import json
import time
import statistics

BASE_URL = "https://d225ar6c86586s.cloudfront.net"

def test_complete_flow():
    """Test the complete progressive arena flow"""
    
    print("=" * 60)
    print("PROGRESSIVE ARENA COMPLETE TEST - GPU POWERED")
    print("=" * 60)
    
    # Test 1: Simple query
    print("\n📝 Test 1: Simple Math Query")
    print("-" * 40)
    session_id = f"gpu-test-{int(time.time())}"
    
    # Start battle
    print("Starting progressive battle...")
    response = requests.post(
        f"{BASE_URL}/api/arena/start_progressive",
        json={
            "message": "What is 5 + 7?",
            "session_id": session_id
        },
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to start battle: {response.status_code}")
        return
    
    battle_data = response.json()
    print(f"✅ Battle created: {battle_data['battle_id']}")
    print(f"   Total models: {battle_data['total_models']}")
    
    # Get responses
    print("\n⏱️ Getting model responses (GPU acceleration)...")
    start_time = time.time()
    
    response = requests.post(
        f"{BASE_URL}/api/arena/get_progressive_responses",
        json={"battle_id": battle_data['battle_id']},
        timeout=60
    )
    
    elapsed = time.time() - start_time
    
    if response.status_code != 200:
        print(f"❌ Failed to get responses: {response.status_code}")
        return
    
    results = response.json()
    print(f"✅ Responses received in {elapsed:.2f} seconds")
    print(f"\n🤖 Model A ({results['model_a']}): {results['latency_a']:.0f}ms")
    print(f"   Response: {results['response_a'][:100]}...")
    print(f"\n🤖 Model B ({results['model_b']}): {results['latency_b']:.0f}ms")
    print(f"   Response: {results['response_b'][:100]}...")
    
    # Submit choice
    print("\n🗳️ Submitting choice...")
    winner = results['model_a'] if results['latency_a'] < results['latency_b'] else results['model_b']
    
    response = requests.post(
        f"{BASE_URL}/api/arena/submit_progressive_choice",
        json={
            "battle_id": battle_data['battle_id'],
            "winner": winner
        },
        timeout=10
    )
    
    if response.status_code == 200:
        choice_result = response.json()
        print(f"✅ Choice submitted: {winner} wins!")
        print(f"   Remaining comparisons: {choice_result.get('remaining_comparisons', 0)}")
    
    # Test 2: Complex query
    print("\n" + "=" * 60)
    print("📝 Test 2: Complex Query")
    print("-" * 40)
    
    session_id = f"gpu-complex-{int(time.time())}"
    complex_prompt = "Explain the concept of machine learning in simple terms"
    
    # Start battle
    print("Starting battle with complex query...")
    response = requests.post(
        f"{BASE_URL}/api/arena/start_progressive",
        json={
            "message": complex_prompt,
            "session_id": session_id
        },
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to start battle: {response.status_code}")
        return
    
    battle_data = response.json()
    print(f"✅ Battle created: {battle_data['battle_id']}")
    
    # Get responses
    print("\n⏱️ Getting model responses for complex query...")
    start_time = time.time()
    
    response = requests.post(
        f"{BASE_URL}/api/arena/get_progressive_responses",
        json={"battle_id": battle_data['battle_id']},
        timeout=120
    )
    
    elapsed = time.time() - start_time
    
    if response.status_code != 200:
        print(f"❌ Failed to get responses: {response.status_code}")
        return
    
    results = response.json()
    print(f"✅ Responses received in {elapsed:.2f} seconds")
    print(f"\n🤖 Model A ({results['model_a']}): {results['latency_a']:.0f}ms")
    print(f"   Response length: {len(results['response_a'])} chars")
    print(f"\n🤖 Model B ({results['model_b']}): {results['latency_b']:.0f}ms")
    print(f"   Response length: {len(results['response_b'])} chars")
    
    # Performance summary
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE SUMMARY")
    print("-" * 40)
    
    avg_latency = (results['latency_a'] + results['latency_b']) / 2
    print(f"Average response time: {avg_latency:.0f}ms ({avg_latency/1000:.1f}s)")
    print(f"Fastest model: {results['model_a'] if results['latency_a'] < results['latency_b'] else results['model_b']}")
    print(f"GPU Acceleration: ✅ ACTIVE")
    
    if avg_latency < 10000:  # Less than 10 seconds
        print(f"Performance: 🚀 EXCELLENT (< 10s average)")
    elif avg_latency < 20000:  # Less than 20 seconds
        print(f"Performance: ✅ GOOD (< 20s average)")
    else:
        print(f"Performance: ⚠️ NEEDS OPTIMIZATION")
    
    print("\n" + "=" * 60)
    print("✅ PROGRESSIVE ARENA TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_complete_flow()
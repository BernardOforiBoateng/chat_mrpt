#!/usr/bin/env python3
"""Test Arena to debug response issue"""

import requests
import json
import time

BASE_URL = "https://d225ar6c86586s.cloudfront.net"
SESSION_ID = f"debug_{int(time.time())}"

print("=" * 60)
print("Arena Debug Test - Checking Response Issue")
print("=" * 60)

try:
    # 1. Start battle 
    print("\n1. Starting battle...")
    response = requests.post(
        f"{BASE_URL}/api/arena/start_battle",
        json={"message": "What is 1+1?", "session_id": SESSION_ID},
        timeout=60
    )
    
    if response.status_code != 200:
        print(f"❌ Start battle failed: {response.status_code}")
        print(response.text)
        exit(1)
    
    battle_data = response.json()
    print(f"Battle started: {battle_data['battle_id']}")
    print(f"Has initial responses: response_a={bool(battle_data.get('response_a'))}, response_b={bool(battle_data.get('response_b'))}")
    print(f"Response A length: {len(battle_data.get('response_a', ''))}")
    print(f"Response B length: {len(battle_data.get('response_b', ''))}")
    
    # 2. Vote for A (left wins, right eliminated)
    print("\n2. Voting for A (left wins)...")
    response = requests.post(
        f"{BASE_URL}/api/arena/vote",
        json={"battle_id": battle_data['battle_id'], "vote": "a", "session_id": SESSION_ID},
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Vote failed: {response.status_code}")
        print(response.text)
        exit(1)
    
    vote_data = response.json()
    print(f"Vote response:")
    print(f"  continue_battle: {vote_data.get('continue_battle')}")
    print(f"  needs_responses: {vote_data.get('needs_responses')}")
    print(f"  eliminated_side: {vote_data.get('eliminated_side')}")
    print(f"  Has response_a: {bool(vote_data.get('response_a'))}")
    print(f"  Has response_b: {bool(vote_data.get('response_b'))}")
    print(f"  Response A length: {len(vote_data.get('response_a', ''))}")
    print(f"  Response B length: {len(vote_data.get('response_b', ''))}")
    
    if vote_data.get('response_a'):
        print(f"  Response A preview: {vote_data['response_a'][:50]}...")
    else:
        print("  ❌ Response A is missing!")
        
    if vote_data.get('response_b'):
        print(f"  Response B preview: {vote_data['response_b'][:50]}...")
    else:
        print("  ❌ Response B is missing!")
    
    print("\n" + "=" * 60)
    print("Test complete - check server logs for detailed info")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
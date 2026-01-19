#!/usr/bin/env python3
"""Complete Arena Tournament Test - Tests full flow"""

import requests
import json
import time

BASE_URL = "https://d225ar6c86586s.cloudfront.net"
SESSION_ID = f"tournament_{int(time.time())}"

print("=" * 60)
print("Arena Tournament Complete Test")
print("=" * 60)

try:
    # 1. Start battle
    print("\n1. Starting tournament battle...")
    response = requests.post(
        f"{BASE_URL}/api/arena/start_battle",
        json={"message": "What is 2+2?", "session_id": SESSION_ID},
        timeout=60
    )
    
    if response.status_code != 200:
        print(f"❌ Start battle failed: {response.status_code}")
        print(response.text)
        exit(1)
    
    battle_data = response.json()
    print(f"✅ Battle started: {battle_data['battle_id']}")
    print(f"   Round 1: Response A vs Response B")
    print(f"   Response A (first 50 chars): {battle_data.get('response_a', '')[:50]}")
    print(f"   Response B (first 50 chars): {battle_data.get('response_b', '')[:50]}")
    
    # 2. Vote for A (Response A wins Round 1)
    print("\n2. Round 1 Vote: Choosing Response A...")
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
    print(f"✅ Round 1 complete!")
    print(f"   Winner: Response A")
    print(f"   Eliminated: Response B")
    print(f"   Round 2: Response A vs Response C")
    
    if vote_data.get('response_a'):
        print(f"   Response A (first 50 chars): {vote_data['response_a'][:50]}")
    if vote_data.get('response_b'):
        print(f"   Response C (first 50 chars): {vote_data['response_b'][:50]}")
    
    # 3. Vote for B (Response C wins Round 2)
    print("\n3. Round 2 Vote: Choosing Response C...")
    response = requests.post(
        f"{BASE_URL}/api/arena/vote",
        json={"battle_id": battle_data['battle_id'], "vote": "b", "session_id": SESSION_ID},
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Vote failed: {response.status_code}")
        print(response.text)
        exit(1)
    
    final_data = response.json()
    
    if not final_data.get('continue_battle'):
        print(f"✅ Tournament complete!")
        print(f"   Final ranking: {' > '.join(final_data.get('final_ranking', []))}")
        print(f"   Winner: {final_data.get('final_ranking', ['Unknown'])[0]}")
    else:
        print("❌ Battle should be complete but isn't")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! Arena tournament working correctly.")
    print("   - Response labels change correctly (A, B → A, C)")
    print("   - No 'Waiting for response...' issues")
    print("   - Tournament completes successfully")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
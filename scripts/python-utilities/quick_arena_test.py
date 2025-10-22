#!/usr/bin/env python3
"""Quick arena test"""

import requests
import json
import time

BASE_URL = "https://d225ar6c86586s.cloudfront.net"

print("Testing Arena System...")
print("=" * 50)

# 1. Check status
print("\n1. Arena Status:")
resp = requests.get(f"{BASE_URL}/api/arena/status")
if resp.status_code == 200:
    data = resp.json()
    print(f"   Available: {data['available']}")
    print(f"   Models: {data['active_models']}")
else:
    print(f"   ERROR: Status {resp.status_code}")

# 2. Start battle
print("\n2. Starting Battle:")
resp = requests.post(f"{BASE_URL}/api/arena/start_battle", 
                     json={"message": "What is the capital of France?"})
if resp.status_code == 200:
    battle = resp.json()
    battle_id = battle['battle_id']
    print(f"   Battle ID: {battle_id}")
    
    # 3. Get responses
    print("\n3. Getting Responses (waiting 3 seconds):")
    time.sleep(3)
    
    resp = requests.post(f"{BASE_URL}/api/arena/get_responses",
                         json={"battle_id": battle_id, 
                               "message": "What is the capital of France?"})
    if resp.status_code == 200:
        data = resp.json()
        resp_a = data.get('response_a', '')
        resp_b = data.get('response_b', '')
        
        print(f"   Response A ({len(resp_a)} chars): {resp_a[:100]}")
        print(f"   Response B ({len(resp_b)} chars): {resp_b[:100]}")
        
        # 4. Vote if both responded
        if resp_a and resp_b:
            print("\n4. Voting:")
            resp = requests.post(f"{BASE_URL}/api/arena/vote",
                               json={"battle_id": battle_id, "preference": "tie"})
            if resp.status_code == 200:
                print("   ✓ Vote recorded!")

print("\n" + "=" * 50)
print("Test Complete!")

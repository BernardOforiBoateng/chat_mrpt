#!/usr/bin/env python3
"""
Debug script for Arena voting issue
Tests the complete flow and shows detailed error information
"""

import requests
import json
import time

# Test against CloudFront URL
BASE_URL = "https://d225ar6c86586s.cloudfront.net"
SESSION_ID = f"test_debug_{int(time.time())}"

print("=" * 60)
print("Arena Vote Debugging Test")
print("=" * 60)
print(f"Session ID: {SESSION_ID}\n")

# Step 1: Start Arena battle
print("1. Starting Arena battle...")
response = requests.post(
    f"{BASE_URL}/send_message_streaming",
    json={
        "message": "What is Python?",
        "session_id": SESSION_ID,
        "mode": "arena"
    },
    stream=True,
    verify=False
)

battle_id = None
model_a = None
model_b = None

# Parse streaming response
for line in response.iter_lines():
    if line:
        line_str = line.decode('utf-8')
        if line_str.startswith('data: '):
            try:
                data = json.loads(line_str[6:])
                if data.get('arena_mode') and data.get('battle_id'):
                    battle_id = data.get('battle_id')
                    model_a = data.get('model_a')
                    model_b = data.get('model_b')
                    print(f"   ✓ Battle ID: {battle_id}")
                    print(f"   ✓ Models: {model_a} vs {model_b}")
                    break
            except json.JSONDecodeError:
                pass

if not battle_id:
    print("   ✗ Failed to start Arena battle")
    exit(1)

print("\n2. Waiting 2 seconds before voting...")
time.sleep(2)

# Step 2: Submit vote
print("\n3. Submitting vote 'a'...")
vote_payload = {
    "battle_id": battle_id,
    "vote": "a",
    "session_id": SESSION_ID
}
print(f"   Payload: {json.dumps(vote_payload, indent=2)}")

vote_response = requests.post(
    f"{BASE_URL}/api/arena/vote",
    json=vote_payload,
    verify=False
)

print(f"\n4. Vote Response:")
print(f"   Status Code: {vote_response.status_code}")
print(f"   Headers: {dict(vote_response.headers)}")
print(f"   Response Body: {vote_response.text[:500]}")

if vote_response.status_code == 200:
    print("\n   ✓ Vote submitted successfully!")
    vote_data = vote_response.json()
    if vote_data.get('continue_battle'):
        print(f"   Next round: {vote_data.get('model_a')} vs {vote_data.get('model_b')}")
    else:
        print(f"   Tournament complete: {vote_data.get('final_ranking')}")
else:
    print(f"\n   ✗ Vote failed with status {vote_response.status_code}")
    print(f"   Error: {vote_response.text}")

print("\n" + "=" * 60)
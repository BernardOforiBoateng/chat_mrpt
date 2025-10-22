#!/usr/bin/env python3
"""Simple Arena test"""

import requests
import json

BASE_URL = "https://d225ar6c86586s.cloudfront.net"

print("Testing Arena...")
response = requests.post(
    f"{BASE_URL}/send_message",
    json={
        "message": "What causes malaria?",
        "use_arena": True
    },
    timeout=45
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"Arena mode: {result.get('arena_mode')}")
    print(f"Response A: {result.get('response_a', 'N/A')[:100]}...")
    print(f"Response B: {result.get('response_b', 'N/A')[:100]}...")
    
    # Check if different
    if result.get('response_a') != result.get('response_b'):
        print("\n✓ SUCCESS: Different responses from 2 models!")
    else:
        print("\n⚠ Same response or error")
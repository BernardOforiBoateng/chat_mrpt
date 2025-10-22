#!/usr/bin/env python3
"""
Test script for Arena Tournament Mode
Tests the complete flow of the tournament-style Arena
"""

import requests
import json
import time
from typing import Dict, Any

# Test against CloudFront URL
BASE_URL = "https://d225ar6c86586s.cloudfront.net"
SESSION_ID = f"test_arena_{int(time.time())}"

def test_arena_mode():
    """Test the Arena tournament mode"""
    print("=" * 50)
    print("Testing Arena Tournament Mode")
    print("=" * 50)
    print(f"Session ID: {SESSION_ID}")
    print()
    
    # Step 1: Send a message in Arena mode
    print("Step 1: Starting Arena battle...")
    response = requests.post(
        f"{BASE_URL}/send_message_streaming",
        json={
            "message": "What is machine learning?",
            "session_id": SESSION_ID,
            "mode": "arena"
        },
        stream=True,
        verify=False  # Ignore SSL for testing
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
                    if data.get('arena_mode'):
                        battle_id = data.get('battle_id')
                        model_a = data.get('model_a')
                        model_b = data.get('model_b')
                        print(f"✓ Arena battle started: {battle_id}")
                        print(f"  Round 1: {model_a} vs {model_b}")
                        if data.get('response_a'):
                            print(f"  - {model_a} responded")
                        if data.get('response_b'):
                            print(f"  - {model_b} responded")
                except json.JSONDecodeError:
                    pass
    
    if not battle_id:
        print("✗ Failed to start Arena battle")
        return False
    
    print()
    
    # Step 2: Submit first vote (A wins)
    print("Step 2: Voting for model A...")
    vote_response = requests.post(
        f"{BASE_URL}/api/arena/vote",
        json={
            "battle_id": battle_id,
            "vote": "a",
            "session_id": SESSION_ID
        },
        verify=False
    )
    
    if vote_response.status_code == 200:
        vote_data = vote_response.json()
        print(f"✓ Vote submitted successfully")
        
        if vote_data.get('continue_battle'):
            print(f"  Round 2 starting...")
            print(f"  Next matchup: {vote_data.get('model_a')} vs {vote_data.get('model_b')}")
            print(f"  Eliminated: {vote_data.get('eliminated_models')}")
            
            # Step 3: Submit second vote (B wins)
            print()
            print("Step 3: Voting for model B...")
            vote2_response = requests.post(
                f"{BASE_URL}/api/arena/vote",
                json={
                    "battle_id": battle_id,
                    "vote": "b",
                    "session_id": SESSION_ID
                },
                verify=False
            )
            
            if vote2_response.status_code == 200:
                vote2_data = vote2_response.json()
                print(f"✓ Vote submitted successfully")
                
                if not vote2_data.get('continue_battle'):
                    print(f"✓ Tournament complete!")
                    print(f"  Final ranking: {' > '.join(vote2_data.get('final_ranking', []))}")
                    return True
                else:
                    print("✗ Tournament should be complete but isn't")
                    return False
            else:
                print(f"✗ Failed to submit second vote: {vote2_response.status_code}")
                return False
        else:
            print("✗ Tournament ended too early")
            return False
    else:
        print(f"✗ Failed to submit vote: {vote_response.status_code}")
        print(f"  Response: {vote_response.text}")
        return False

if __name__ == "__main__":
    try:
        success = test_arena_mode()
        print()
        print("=" * 50)
        if success:
            print("✓ Arena Tournament Mode is working correctly!")
        else:
            print("✗ Arena Tournament Mode has issues")
        print("=" * 50)
    except Exception as e:
        print(f"Error: {e}")
        print("✗ Test failed with exception")
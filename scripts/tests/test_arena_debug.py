#!/usr/bin/env python3
"""
Debug script for testing progressive arena battle system
"""

import requests
import json
import time
import sys

# Use CloudFront URL
BASE_URL = "https://d225ar6c86586s.cloudfront.net"

def test_progressive_arena():
    """Test the progressive arena battle flow"""
    
    # Step 1: Start a progressive battle
    print("1. Starting progressive battle...")
    session_id = f"test-debug-{int(time.time())}"
    
    response = requests.post(
        f"{BASE_URL}/api/arena/start_progressive",
        json={
            "message": "What is 2 + 2?",
            "session_id": session_id
        },
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"Error starting battle: {response.status_code}")
        print(response.text)
        return
    
    result = response.json()
    print(f"Battle started: {json.dumps(result, indent=2)}")
    battle_id = result.get('battle_id')
    
    # Step 2: Get progressive responses
    print("\n2. Getting progressive responses...")
    print("This may take 30-60 seconds as models generate responses...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/arena/get_progressive_responses",
            json={"battle_id": battle_id},
            timeout=120  # 2 minute timeout
        )
        
        if response.status_code != 200:
            print(f"Error getting responses: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response text: {response.text[:500]}")
            return
        
        result = response.json()
        print(f"\nResponses received: {json.dumps(result, indent=2)}")
        
        # Step 3: Submit a choice
        if result.get('status') == 'ready' and result.get('current_models'):
            print("\n3. Submitting choice...")
            models = result['current_models']
            winner = models[0]  # Choose first model as winner
            
            response = requests.post(
                f"{BASE_URL}/api/arena/submit_progressive_choice",
                json={
                    "battle_id": battle_id,
                    "winner": winner
                },
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"Error submitting choice: {response.status_code}")
                print(response.text)
                return
            
            result = response.json()
            print(f"Choice submitted: {json.dumps(result, indent=2)}")
            
    except requests.exceptions.Timeout:
        print("Request timed out after 2 minutes")
        print("This likely means the models are not responding")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_progressive_arena()
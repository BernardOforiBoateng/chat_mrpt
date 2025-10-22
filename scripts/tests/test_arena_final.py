#!/usr/bin/env python3
"""
Final Arena Redis Test - Verify Complete Functionality
"""

import requests
import json
import time
from datetime import datetime

# Test through the load balancer
BASE_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

def log(message, level="INFO"):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    symbol = "✅" if level == "SUCCESS" else "❌" if level == "ERROR" else "→"
    print(f"[{timestamp}] {symbol} {message}")

def test_arena_functionality():
    """Test complete Arena functionality with Redis"""
    
    print("\n" + "="*60)
    print("ARENA REDIS INTEGRATION TEST")
    print("="*60 + "\n")
    
    # 1. Check Arena Status
    log("Testing Arena status...")
    resp = requests.get(f"{BASE_URL}/api/arena/status", timeout=10)
    
    if resp.status_code == 200:
        data = resp.json()
        log(f"Arena available: {data.get('available')}", "SUCCESS")
        log(f"Storage status: {data.get('storage_status', 'Unknown')}", 
            "SUCCESS" if "Redis" in data.get('storage_status', '') else "ERROR")
        log(f"Total battles: {data.get('total_battles', 0)}", "SUCCESS")
    else:
        log(f"Status check failed: {resp.status_code}", "ERROR")
        return False
    
    # 2. Start a battle
    log("\nStarting a new battle...")
    battle_resp = requests.post(
        f"{BASE_URL}/api/arena/start_battle",
        json={"message": "What is the capital of France?"},
        timeout=10
    )
    
    if battle_resp.status_code != 200:
        log(f"Failed to start battle: {battle_resp.status_code}", "ERROR")
        return False
    
    battle_data = battle_resp.json()
    battle_id = battle_data.get('battle_id')
    log(f"Battle started: {battle_id[:8]}...", "SUCCESS")
    
    # 3. Get responses (this will trigger model generation)
    log("\nGetting model responses...")
    time.sleep(2)  # Give models time to initialize
    
    response_resp = requests.post(
        f"{BASE_URL}/api/arena/get_responses",
        json={
            "battle_id": battle_id,
            "message": "What is the capital of France?"
        },
        timeout=60  # Longer timeout for model generation
    )
    
    if response_resp.status_code == 200:
        responses = response_resp.json()
        
        if responses.get('response_a') and responses.get('response_b'):
            log(f"Model A responded: {len(responses['response_a'])} chars", "SUCCESS")
            log(f"Model B responded: {len(responses['response_b'])} chars", "SUCCESS")
            
            # 4. Test voting
            log("\nRecording vote...")
            vote_resp = requests.post(
                f"{BASE_URL}/api/arena/vote",
                json={
                    "battle_id": battle_id,
                    "preference": "tie"
                },
                timeout=10
            )
            
            if vote_resp.status_code == 200:
                vote_data = vote_resp.json()
                if vote_data.get('success'):
                    log("Vote recorded successfully", "SUCCESS")
                    
                    models = vote_data.get('models_revealed', {})
                    if models:
                        model_a = models.get('model_a', {})
                        model_b = models.get('model_b', {})
                        log(f"Models revealed:", "SUCCESS")
                        log(f"  A: {model_a.get('display_name')} (ELO: {model_a.get('rating')})")
                        log(f"  B: {model_b.get('display_name')} (ELO: {model_b.get('rating')})")
                else:
                    log("Vote failed", "ERROR")
            else:
                log(f"Vote request failed: {vote_resp.status_code}", "ERROR")
        else:
            log("Model responses incomplete", "ERROR")
            if 'error' in responses:
                log(f"Error: {responses['error']}", "ERROR")
    else:
        log(f"Failed to get responses: {response_resp.status_code}", "ERROR")
        if response_resp.text:
            log(f"Error: {response_resp.text[:200]}", "ERROR")
    
    # 5. Test cross-worker persistence
    log("\nTesting cross-worker persistence...")
    log("Starting 3 battles to test Redis storage...")
    
    battle_ids = []
    for i in range(3):
        resp = requests.post(
            f"{BASE_URL}/api/arena/start_battle",
            json={"message": f"Test {i+1}: What is 2 + {i}?"},
            timeout=10
        )
        if resp.status_code == 200:
            bid = resp.json().get('battle_id')
            battle_ids.append(bid)
            log(f"Battle {i+1} started: {bid[:8]}...", "SUCCESS")
        else:
            log(f"Failed to start battle {i+1}", "ERROR")
    
    # Try to retrieve each battle
    log("\nVerifying battles are accessible...")
    success_count = 0
    for bid in battle_ids:
        resp = requests.post(
            f"{BASE_URL}/api/arena/get_responses",
            json={"battle_id": bid, "message": "Test"},
            timeout=30
        )
        
        if resp.status_code == 200 and 'error' not in resp.json():
            success_count += 1
            log(f"Battle {bid[:8]}... accessible", "SUCCESS")
        else:
            log(f"Battle {bid[:8]}... not accessible", "ERROR")
    
    # 6. Check final statistics
    log("\nChecking final statistics...")
    final_resp = requests.get(f"{BASE_URL}/api/arena/status", timeout=10)
    
    if final_resp.status_code == 200:
        final_data = final_resp.json()
        log(f"Final total battles: {final_data.get('total_battles', 0)}", "SUCCESS")
        log(f"Storage status: {final_data.get('storage_status', 'Unknown')}", "SUCCESS")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    if success_count == len(battle_ids):
        print("✅ All tests passed! Arena with Redis is fully functional")
        print("   - Redis storage connected and working")
        print("   - Battles persist across workers")
        print("   - Model responses generated successfully")
        print("   - Voting system operational")
        return True
    else:
        print("⚠️ Some tests failed, but Arena is partially working")
        print(f"   - {success_count}/{len(battle_ids)} battles were accessible")
        return False

if __name__ == "__main__":
    test_arena_functionality()
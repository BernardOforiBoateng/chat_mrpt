#!/usr/bin/env python3
"""
Test Arena System with Redis Storage
Verifies that battle sessions persist across multiple workers
"""

import requests
import json
import time
import random
from datetime import datetime

BASE_URL = "https://d225ar6c86586s.cloudfront.net"
# BASE_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"  # Alternative

class ArenaRedisTest:
    def __init__(self):
        self.base_url = BASE_URL
        self.test_results = []
        self.battle_ids = []
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        symbol = "✓" if level == "SUCCESS" else "✗" if level == "ERROR" else "→"
        print(f"[{timestamp}] {symbol} {message}")
        
    def test_arena_status(self):
        """Test that arena is available and using Redis"""
        self.log("Testing Arena status...")
        
        try:
            resp = requests.get(f"{self.base_url}/api/arena/status", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                self.log(f"Arena available: {data.get('available', False)}", "SUCCESS")
                
                # Check for Redis storage indicator
                storage_status = data.get('storage_status', 'Unknown')
                if 'Redis' in storage_status:
                    self.log(f"Storage: {storage_status}", "SUCCESS")
                else:
                    self.log(f"Storage: {storage_status} (not using Redis)", "ERROR")
                
                return data.get('available', False)
            else:
                self.log(f"Status endpoint returned {resp.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Failed to check status: {e}", "ERROR")
            return False
    
    def test_cross_worker_persistence(self):
        """Test that battles persist across different workers"""
        self.log("\nTesting cross-worker persistence...")
        
        # Start multiple battles to increase chance of hitting different workers
        battle_ids = []
        
        for i in range(3):
            self.log(f"Starting battle {i+1}/3...")
            
            # Start battle
            resp = requests.post(
                f"{self.base_url}/api/arena/start_battle",
                json={"message": f"Test question {i+1}: What is {random.randint(1,10)} + {random.randint(1,10)}?"},
                timeout=10
            )
            
            if resp.status_code == 200:
                battle_id = resp.json().get('battle_id')
                battle_ids.append(battle_id)
                self.log(f"Started battle: {battle_id[:8]}...", "SUCCESS")
            else:
                self.log(f"Failed to start battle: {resp.status_code}", "ERROR")
        
        # Now try to retrieve each battle multiple times
        # This should work even if requests go to different workers
        self.log("\nVerifying battles are accessible from any worker...")
        
        success_count = 0
        for battle_id in battle_ids:
            # Try to get responses 3 times (likely hitting different workers)
            for attempt in range(3):
                time.sleep(1)
                
                resp = requests.post(
                    f"{self.base_url}/api/arena/get_responses",
                    json={
                        "battle_id": battle_id,
                        "message": "Test message"
                    },
                    timeout=30
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    
                    # Check if battle was found (not "Battle session not found" error)
                    if 'error' not in data:
                        success_count += 1
                        self.log(f"Battle {battle_id[:8]}... accessible (attempt {attempt+1})", "SUCCESS")
                        break
                    else:
                        self.log(f"Battle {battle_id[:8]}... not found: {data.get('error')}", "ERROR")
                else:
                    self.log(f"Failed to get responses: {resp.status_code}", "ERROR")
        
        return success_count == len(battle_ids)
    
    def test_model_responses(self):
        """Test that models actually respond"""
        self.log("\nTesting model responses...")
        
        # Start a battle
        resp = requests.post(
            f"{self.base_url}/api/arena/start_battle",
            json={"message": "What is the capital of France?"},
            timeout=10
        )
        
        if resp.status_code != 200:
            self.log("Failed to start battle", "ERROR")
            return False
        
        battle_id = resp.json().get('battle_id')
        self.log(f"Battle started: {battle_id[:8]}...", "SUCCESS")
        
        # Wait a moment for models to process
        time.sleep(5)
        
        # Get responses
        resp = requests.post(
            f"{self.base_url}/api/arena/get_responses",
            json={
                "battle_id": battle_id,
                "message": "What is the capital of France?"
            },
            timeout=60
        )
        
        if resp.status_code == 200:
            data = resp.json()
            
            response_a = data.get('response_a', '')
            response_b = data.get('response_b', '')
            
            if response_a and response_b and 'Error' not in response_a and 'Error' not in response_b:
                self.log(f"Model A responded: {len(response_a)} chars", "SUCCESS")
                self.log(f"Model B responded: {len(response_b)} chars", "SUCCESS")
                
                # Test voting
                resp = requests.post(
                    f"{self.base_url}/api/arena/vote",
                    json={
                        "battle_id": battle_id,
                        "preference": "tie"
                    },
                    timeout=10
                )
                
                if resp.status_code == 200:
                    vote_data = resp.json()
                    if vote_data.get('success'):
                        self.log("Voting successful", "SUCCESS")
                        
                        models = vote_data.get('models_revealed', {})
                        if models:
                            model_a = models.get('model_a', {})
                            model_b = models.get('model_b', {})
                            self.log(f"Models revealed: {model_a.get('display_name')} vs {model_b.get('display_name')}", "SUCCESS")
                        
                        return True
                    
            else:
                self.log(f"Model responses incomplete or errored", "ERROR")
                if response_a:
                    self.log(f"Response A: {response_a[:100]}")
                if response_b:
                    self.log(f"Response B: {response_b[:100]}")
                    
        return False
    
    def test_concurrent_battles(self):
        """Test multiple concurrent battles"""
        self.log("\nTesting concurrent battles...")
        
        import concurrent.futures
        
        def start_and_check_battle(index):
            try:
                # Start battle
                resp = requests.post(
                    f"{self.base_url}/api/arena/start_battle",
                    json={"message": f"Concurrent test {index}: Hello"},
                    timeout=10
                )
                
                if resp.status_code == 200:
                    battle_id = resp.json().get('battle_id')
                    
                    # Immediately try to retrieve it
                    time.sleep(0.5)
                    resp2 = requests.post(
                        f"{self.base_url}/api/arena/get_responses",
                        json={"battle_id": battle_id, "message": "Hello"},
                        timeout=30
                    )
                    
                    if resp2.status_code == 200 and 'error' not in resp2.json():
                        return True
                        
            except Exception as e:
                print(f"Concurrent test {index} failed: {e}")
                
            return False
        
        # Run 5 concurrent battle tests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(start_and_check_battle, i) for i in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        success_count = sum(results)
        self.log(f"Concurrent battles successful: {success_count}/5", 
                "SUCCESS" if success_count == 5 else "ERROR")
        
        return success_count == 5
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("\n" + "="*60)
        print("ARENA REDIS STORAGE TEST SUITE")
        print(f"Target: {self.base_url}")
        print("="*60 + "\n")
        
        test_results = {
            'status': False,
            'cross_worker': False,
            'model_responses': False,
            'concurrent': False
        }
        
        # Test 1: Check arena status
        test_results['status'] = self.test_arena_status()
        
        if not test_results['status']:
            self.log("Arena not available, stopping tests", "ERROR")
            return test_results
        
        # Test 2: Cross-worker persistence
        test_results['cross_worker'] = self.test_cross_worker_persistence()
        
        # Test 3: Model responses
        test_results['model_responses'] = self.test_model_responses()
        
        # Test 4: Concurrent battles
        test_results['concurrent'] = self.test_concurrent_battles()
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = sum(test_results.values())
        total = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nTests Passed: {passed}/{total}")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED - Redis storage working perfectly!")
        elif passed >= total * 0.75:
            print("\n✅ MOSTLY WORKING - Redis storage functional with minor issues")
        elif passed >= total * 0.5:
            print("\n⚠️ PARTIAL SUCCESS - Some Redis functionality working")
        else:
            print("\n❌ CRITICAL ISSUES - Redis storage not working properly")
        
        return test_results


if __name__ == "__main__":
    tester = ArenaRedisTest()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    passed = sum(results.values())
    if passed == len(results):
        exit(0)  # All tests passed
    elif passed > 0:
        exit(1)  # Partial success
    else:
        exit(2)  # Complete failure
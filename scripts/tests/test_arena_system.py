#!/usr/bin/env python3
"""
Arena System Test Script
Tests the complete arena functionality after deployment
"""

import requests
import json
import time
from typing import Dict, Any
from datetime import datetime

# Configuration
BASE_URLS = {
    'cloudfront': 'https://d225ar6c86586s.cloudfront.net',
    'alb': 'http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com',
    'local': 'http://127.0.0.1:5000'
}

# Test queries
TEST_QUERIES = [
    "What is the capital of France?",
    "Explain quantum computing in simple terms",
    "Write a Python function to calculate factorial",
    "What are the symptoms of malaria?",
    "How does machine learning work?"
]

class ArenaTestSuite:
    def __init__(self, base_url='cloudfront'):
        self.base_url = BASE_URLS.get(base_url, BASE_URLS['cloudfront'])
        self.results = []
        self.battle_ids = []
        
    def log(self, message, level='INFO'):
        """Log test progress"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        symbol = '✓' if level == 'SUCCESS' else '✗' if level == 'ERROR' else '→'
        print(f"[{timestamp}] {symbol} {message}")
        
    def test_arena_status(self) -> bool:
        """Test arena status endpoint"""
        self.log("Testing arena status endpoint...")
        
        try:
            response = requests.get(f"{self.base_url}/api/arena/status", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"Arena available: {data.get('available', False)}", 'SUCCESS')
                self.log(f"Active models: {data.get('active_models', 0)}")
                self.log(f"Total battles: {data.get('total_battles', 0)}")
                
                # Display leaderboard
                leaderboard = data.get('leaderboard', [])
                if leaderboard:
                    self.log("Top models:")
                    for model in leaderboard[:3]:
                        print(f"    - {model}")
                
                return data.get('available', False)
            else:
                self.log(f"Status endpoint returned {response.status_code}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"Failed to check status: {e}", 'ERROR')
            return False
    
    def test_start_battle(self, message: str) -> Dict[str, Any]:
        """Test starting a battle"""
        self.log(f"Starting battle with message: '{message[:50]}...'")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/arena/start_battle",
                json={'message': message},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                battle_id = data.get('battle_id')
                self.battle_ids.append(battle_id)
                self.log(f"Battle started: {battle_id}", 'SUCCESS')
                return data
            else:
                self.log(f"Failed to start battle: {response.status_code}", 'ERROR')
                return {}
                
        except Exception as e:
            self.log(f"Error starting battle: {e}", 'ERROR')
            return {}
    
    def test_get_responses(self, battle_id: str, message: str) -> Dict[str, Any]:
        """Test getting model responses"""
        self.log(f"Getting responses for battle {battle_id}")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/arena/get_responses",
                json={
                    'battle_id': battle_id,
                    'message': message
                },
                timeout=60  # Allow more time for model generation
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check responses
                response_a = data.get('response_a', '')
                response_b = data.get('response_b', '')
                
                self.log(f"Response A: {len(response_a)} chars, Latency: {data.get('latency_a', 0):.0f}ms")
                self.log(f"Response B: {len(response_b)} chars, Latency: {data.get('latency_b', 0):.0f}ms")
                
                # Display snippets
                if response_a:
                    print(f"    Model A: {response_a[:100]}...")
                if response_b:
                    print(f"    Model B: {response_b[:100]}...")
                
                if response_a and response_b:
                    self.log("Both models responded", 'SUCCESS')
                    return data
                else:
                    self.log("Missing model responses", 'ERROR')
                    return data
                    
            else:
                self.log(f"Failed to get responses: {response.status_code}", 'ERROR')
                return {}
                
        except Exception as e:
            self.log(f"Error getting responses: {e}", 'ERROR')
            return {}
    
    def test_voting(self, battle_id: str, preference: str = 'tie') -> bool:
        """Test voting functionality"""
        self.log(f"Testing vote submission: {preference}")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/arena/vote",
                json={
                    'battle_id': battle_id,
                    'preference': preference
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if models were revealed
                models = data.get('models_revealed', {})
                if models:
                    model_a = models.get('model_a', {})
                    model_b = models.get('model_b', {})
                    
                    self.log("Models revealed:", 'SUCCESS')
                    print(f"    Model A: {model_a.get('display_name')} (ELO: {model_a.get('rating', 0):.0f})")
                    print(f"    Model B: {model_b.get('display_name')} (ELO: {model_b.get('rating', 0):.0f})")
                    
                return True
            else:
                self.log(f"Failed to vote: {response.status_code}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"Error voting: {e}", 'ERROR')
            return False
    
    def test_leaderboard(self) -> bool:
        """Test leaderboard endpoint"""
        self.log("Testing leaderboard endpoint...")
        
        try:
            response = requests.get(f"{self.base_url}/api/arena/leaderboard", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                leaderboard = data.get('leaderboard', [])
                
                self.log(f"Leaderboard has {len(leaderboard)} models", 'SUCCESS')
                
                # Display leaderboard
                print("\n    === Model Leaderboard ===")
                for model in leaderboard:
                    print(f"    {model['rank']}. {model['display_name']}: "
                          f"ELO {model['elo_rating']}, "
                          f"Battles: {model['battles_fought']}, "
                          f"Win Rate: {model['win_rate']}%")
                
                return True
            else:
                self.log(f"Failed to get leaderboard: {response.status_code}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"Error getting leaderboard: {e}", 'ERROR')
            return False
    
    def test_statistics(self) -> bool:
        """Test statistics endpoint"""
        self.log("Testing statistics endpoint...")
        
        try:
            response = requests.get(f"{self.base_url}/api/arena/statistics", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                self.log("Statistics retrieved:", 'SUCCESS')
                print(f"    Total battles: {data.get('total_battles', 0)}")
                print(f"    Completed battles: {data.get('completed_battles', 0)}")
                print(f"    Completion rate: {data.get('completion_rate', 0):.1f}%")
                
                # Show preference distribution
                prefs = data.get('preference_distribution', {})
                if prefs:
                    print("    Preference distribution:")
                    for pref, count in prefs.items():
                        print(f"      - {pref}: {count}")
                
                return True
            else:
                self.log(f"Failed to get statistics: {response.status_code}", 'ERROR')
                return False
                
        except Exception as e:
            self.log(f"Error getting statistics: {e}", 'ERROR')
            return False
    
    def run_full_test(self):
        """Run complete test suite"""
        print("\n" + "="*60)
        print("ARENA SYSTEM TEST SUITE")
        print(f"Target: {self.base_url}")
        print("="*60 + "\n")
        
        test_results = {
            'status': False,
            'battles': [],
            'leaderboard': False,
            'statistics': False
        }
        
        # Test 1: Check arena status
        test_results['status'] = self.test_arena_status()
        
        if not test_results['status']:
            self.log("Arena not available, stopping tests", 'ERROR')
            return test_results
        
        print("\n" + "-"*40 + "\n")
        
        # Test 2: Run multiple battles
        for i, query in enumerate(TEST_QUERIES[:3], 1):
            print(f"\n--- Battle {i}/{len(TEST_QUERIES[:3])} ---")
            
            # Start battle
            battle_data = self.test_start_battle(query)
            
            if battle_data and 'battle_id' in battle_data:
                battle_id = battle_data['battle_id']
                
                # Get responses
                time.sleep(2)  # Small delay
                response_data = self.test_get_responses(battle_id, query)
                
                # Vote
                if response_data:
                    time.sleep(1)
                    preferences = ['left', 'right', 'tie']
                    pref = preferences[i % len(preferences)]
                    vote_success = self.test_voting(battle_id, pref)
                    
                    test_results['battles'].append({
                        'query': query,
                        'battle_id': battle_id,
                        'responses_received': bool(response_data),
                        'vote_success': vote_success
                    })
            
            print("")
            time.sleep(2)  # Delay between battles
        
        print("\n" + "-"*40 + "\n")
        
        # Test 3: Check leaderboard
        test_results['leaderboard'] = self.test_leaderboard()
        
        print("\n" + "-"*40 + "\n")
        
        # Test 4: Get statistics
        test_results['statistics'] = self.test_statistics()
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        success_count = 0
        total_count = 0
        
        # Count successes
        if test_results['status']:
            success_count += 1
        total_count += 1
        
        for battle in test_results['battles']:
            if battle['responses_received']:
                success_count += 1
            total_count += 1
            
            if battle['vote_success']:
                success_count += 1
            total_count += 1
        
        if test_results['leaderboard']:
            success_count += 1
        total_count += 1
        
        if test_results['statistics']:
            success_count += 1
        total_count += 1
        
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        print(f"\nTests Passed: {success_count}/{total_count} ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("\n✅ ARENA SYSTEM IS FUNCTIONAL")
        elif success_rate >= 50:
            print("\n⚠️  ARENA SYSTEM PARTIALLY WORKING")
        else:
            print("\n❌ ARENA SYSTEM HAS CRITICAL ISSUES")
        
        return test_results


def main():
    """Main test execution"""
    import sys
    
    # Check command line arguments
    target = 'cloudfront'
    if len(sys.argv) > 1:
        if sys.argv[1] in BASE_URLS:
            target = sys.argv[1]
        else:
            print(f"Unknown target: {sys.argv[1]}")
            print(f"Available targets: {', '.join(BASE_URLS.keys())}")
            sys.exit(1)
    
    # Run tests
    tester = ArenaTestSuite(target)
    results = tester.run_full_test()
    
    # Exit with appropriate code
    success_count = sum([
        results['status'],
        results['leaderboard'],
        results['statistics'],
        sum(1 for b in results['battles'] if b['responses_received']),
        sum(1 for b in results['battles'] if b.get('vote_success', False))
    ])
    
    if success_count == 0:
        sys.exit(2)  # Complete failure
    elif success_count < len(results['battles']) * 2 + 3:
        sys.exit(1)  # Partial failure
    else:
        sys.exit(0)  # Success


if __name__ == '__main__':
    main()
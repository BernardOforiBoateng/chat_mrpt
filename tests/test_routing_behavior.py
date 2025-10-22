#!/usr/bin/env python3
"""
Test routing behavior on AWS - from easy to hard requests
Following CLAUDE.md testing guidelines
"""
import requests
import json
import time
from typing import Dict, Any, List
import sys

# Test configuration
BASE_URLS = [
    "https://d225ar6c86586s.cloudfront.net",  # CloudFront
    "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"  # ALB
]

class RoutingTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session_id = f"test-routing-{int(time.time())}"
        self.results = []
        
    def send_message(self, message: str) -> Dict[str, Any]:
        """Send a message and get the response"""
        try:
            response = self.session.post(
                f"{self.base_url}/send_message",
                json={
                    "message": message,
                    "session_id": self.session_id
                },
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def check_response_type(self, response: Dict[str, Any]) -> str:
        """Determine what type of response we got"""
        if response.get("error"):
            return "error"
        elif response.get("needs_clarification"):
            return "clarification"
        elif response.get("arena_mode"):
            return "arena"
        elif response.get("tools_used"):
            return "tools"
        elif response.get("response"):
            # Check content for clues
            resp_text = response.get("response", "").lower()
            if "i need more information" in resp_text:
                return "clarification_embedded"
            elif any(word in resp_text for word in ["hello", "hi", "greetings", "welcome"]):
                return "greeting"
            else:
                return "conversational"
        else:
            return "unknown"
    
    def run_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test case"""
        print(f"\n{'='*60}")
        print(f"Test: {test_case['name']}")
        print(f"Message: '{test_case['message']}'")
        print(f"Expected: {test_case['expected']}")
        
        start_time = time.time()
        response = self.send_message(test_case['message'])
        duration = time.time() - start_time
        
        response_type = self.check_response_type(response)
        success = response_type in test_case['expected']
        
        result = {
            "name": test_case['name'],
            "message": test_case['message'],
            "expected": test_case['expected'],
            "actual": response_type,
            "success": success,
            "duration": duration,
            "response_preview": str(response.get("response", ""))[:100] if response.get("response") else response.get("message", "")
        }
        
        print(f"Actual: {response_type}")
        print(f"Success: {'✅' if success else '❌'}")
        print(f"Duration: {duration:.2f}s")
        if not success:
            print(f"Response preview: {result['response_preview']}")
        
        self.results.append(result)
        return result
    
    def run_all_tests(self, test_cases: List[Dict[str, Any]]):
        """Run all test cases"""
        print(f"\n{'#'*60}")
        print(f"# Testing Routing Behavior on {self.base_url}")
        print(f"{'#'*60}")
        
        for test_case in test_cases:
            self.run_test(test_case)
            time.sleep(1)  # Avoid rate limiting
        
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r['success'])
        failed = total - passed
        
        print(f"\n{'='*60}")
        print(f"SUMMARY: {passed}/{total} tests passed")
        print(f"{'='*60}")
        
        if failed > 0:
            print("\nFailed tests:")
            for result in self.results:
                if not result['success']:
                    print(f"  ❌ {result['name']}: Expected {result['expected']}, got {result['actual']}")
                    print(f"     Message: '{result['message']}'")
                    print(f"     Response: {result['response_preview']}")
        
        print(f"\n{'='*60}")
        return passed == total


# Define test cases - from easy to hard
TEST_CASES = [
    # Level 1: Simple greetings (should NOT trigger clarification)
    {
        "name": "Simple greeting - hey",
        "message": "hey",
        "expected": ["greeting", "conversational", "arena"],
        "difficulty": "easy"
    },
    {
        "name": "Simple greeting - hello",
        "message": "hello",
        "expected": ["greeting", "conversational", "arena"],
        "difficulty": "easy"
    },
    {
        "name": "Simple greeting - hi",
        "message": "hi",
        "expected": ["greeting", "conversational", "arena"],
        "difficulty": "easy"
    },
    
    # Level 2: Small talk (should be conversational)
    {
        "name": "Small talk - thanks",
        "message": "thanks",
        "expected": ["conversational", "arena"],
        "difficulty": "easy"
    },
    {
        "name": "Small talk - how are you",
        "message": "how are you",
        "expected": ["conversational", "arena"],
        "difficulty": "easy"
    },
    {
        "name": "Small talk - goodbye",
        "message": "goodbye",
        "expected": ["conversational", "arena"],
        "difficulty": "easy"
    },
    
    # Level 3: General knowledge questions (should be conversational/arena)
    {
        "name": "General knowledge - what is malaria",
        "message": "what is malaria",
        "expected": ["conversational", "arena"],
        "difficulty": "medium"
    },
    {
        "name": "General knowledge - explain TPR",
        "message": "explain TPR",
        "expected": ["conversational", "arena"],
        "difficulty": "medium"
    },
    {
        "name": "General knowledge - how does PCA work",
        "message": "how does PCA work",
        "expected": ["conversational", "arena"],
        "difficulty": "medium"
    },
    
    # Level 4: Ambiguous but short (should default to conversation)
    {
        "name": "Short ambiguous - ok",
        "message": "ok",
        "expected": ["conversational", "arena"],
        "difficulty": "medium"
    },
    {
        "name": "Short ambiguous - sure",
        "message": "sure",
        "expected": ["conversational", "arena"],
        "difficulty": "medium"
    },
    {
        "name": "Short ambiguous - yes",
        "message": "yes",
        "expected": ["conversational", "arena"],
        "difficulty": "medium"
    },
    
    # Level 5: Genuinely ambiguous (might trigger clarification)
    {
        "name": "Ambiguous - analyze",
        "message": "analyze",
        "expected": ["conversational", "arena", "clarification"],  # Without data, should be conversational
        "difficulty": "hard"
    },
    {
        "name": "Ambiguous - help me with analysis",
        "message": "help me with analysis",
        "expected": ["conversational", "arena", "clarification"],
        "difficulty": "hard"
    },
    
    # Level 6: Clear data requests (would need tools if data was uploaded)
    {
        "name": "Data request without data - plot distribution",
        "message": "plot distribution of rainfall",
        "expected": ["conversational", "arena"],  # Without data, should explain it needs data
        "difficulty": "hard"
    },
    {
        "name": "Data request without data - check quality",
        "message": "check data quality",
        "expected": ["conversational", "arena"],  # Without data, should explain it needs data
        "difficulty": "hard"
    }
]

def main():
    """Run tests on all endpoints"""
    all_passed = True
    
    for base_url in BASE_URLS:
        print(f"\n{'#'*60}")
        print(f"# Testing: {base_url}")
        print(f"{'#'*60}")
        
        try:
            tester = RoutingTester(base_url)
            passed = tester.run_all_tests(TEST_CASES)
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"Error testing {base_url}: {e}")
            all_passed = False
    
    # Final summary
    print(f"\n{'#'*60}")
    print(f"# FINAL RESULTS")
    print(f"{'#'*60}")
    if all_passed:
        print("✅ ALL TESTS PASSED ON ALL ENDPOINTS!")
    else:
        print("❌ SOME TESTS FAILED - Review routing logic")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
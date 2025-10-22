#!/usr/bin/env python3
"""
Quick Conversation Verification Test for ChatMRPT
Rapid verification of conversational capabilities
"""

import requests
import json
import time
import uuid
from datetime import datetime

BASE_URL = "https://d225ar6c86586s.cloudfront.net"
API_ENDPOINT = f"{BASE_URL}/send_message"

class QuickConversationVerifier:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.results = {}

    def send_message(self, message: str, timeout: int = 15) -> dict:
        """Send message with quick timeout"""
        try:
            response = requests.post(
                API_ENDPOINT,
                json={"message": message, "session_id": self.session_id},
                headers={"Content-Type": "application/json"},
                timeout=timeout,
                stream=True
            )

            if response.status_code == 200:
                # Parse SSE response
                content = ""
                arena_info = {}
                suggestions = []

                for line in response.iter_lines():
                    if line:
                        decoded = line.decode('utf-8')
                        if decoded.startswith('data: '):
                            data_str = decoded[6:]
                            if data_str.strip() not in ['[DONE]', '']:
                                try:
                                    data = json.loads(data_str)
                                    # Extract key info
                                    if 'arena_mode' in data:
                                        arena_info['arena_mode'] = data['arena_mode']
                                    if 'model_a' in data:
                                        arena_info['model_a'] = data['model_a']
                                    if 'model_b' in data:
                                        arena_info['model_b'] = data['model_b']
                                    if 'suggestions' in data:
                                        suggestions = data.get('suggestions', [])
                                    if 'delta' in data:
                                        content += data['delta']
                                    if 'response' in data:
                                        content += data['response']
                                except:
                                    pass

                return {
                    "success": True,
                    "content": content,
                    "arena": arena_info,
                    "suggestions": suggestions
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except requests.Timeout:
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_tests(self):
        """Run quick verification tests"""
        print("\n🚀 QUICK CONVERSATION VERIFICATION")
        print("="*50)
        print(f"Session: {self.session_id[:8]}...")
        print(f"Endpoint: {BASE_URL}")
        print("="*50)

        # Test 1: Identity
        print("\n1️⃣ Testing Identity...")
        r1 = self.send_message("Hello, who are you?")
        if r1['success']:
            content = r1['content'].lower()
            is_chatmrpt = "chatmrpt" in content or "malaria" in content
            has_arena = bool(r1['arena'])
            print(f"   ✅ Response received")
            print(f"   Identity: {'ChatMRPT' if is_chatmrpt else 'Unknown'}")
            print(f"   Arena: {r1['arena'].get('arena_mode', False)}")
            if r1['arena'].get('model_a'):
                print(f"   Models: {r1['arena'].get('model_a')} vs {r1['arena'].get('model_b')}")
            self.results['identity'] = is_chatmrpt
            self.results['arena_active'] = has_arena
        else:
            print(f"   ❌ Failed: {r1['error']}")
            self.results['identity'] = False

        time.sleep(2)

        # Test 2: Context
        print("\n2️⃣ Testing Context Persistence...")
        self.send_message("I'm working with data from Lagos state")
        time.sleep(2)
        r2 = self.send_message("What challenges exist in this area?")
        if r2['success']:
            content = r2['content'].lower()
            maintains_context = "lagos" in content or "nigeria" in content or "state" in content
            print(f"   ✅ Response received")
            print(f"   Context maintained: {maintains_context}")
            self.results['context'] = maintains_context
        else:
            print(f"   ❌ Failed: {r2['error']}")
            self.results['context'] = False

        time.sleep(2)

        # Test 3: Suggestions
        print("\n3️⃣ Testing Proactive Features...")
        r3 = self.send_message("I have malaria data to analyze")
        if r3['success']:
            has_suggestions = len(r3['suggestions']) > 0
            content = r3['content'].lower()
            is_proactive = any(p in content for p in ["you can", "you could", "recommend", "suggest"])
            print(f"   ✅ Response received")
            print(f"   Suggestions in SSE: {has_suggestions}")
            if r3['suggestions']:
                print(f"   Suggestions: {r3['suggestions'][:2]}")
            print(f"   Proactive language: {is_proactive}")
            self.results['suggestions'] = has_suggestions
            self.results['proactive'] = is_proactive
        else:
            print(f"   ❌ Failed: {r3['error']}")
            self.results['suggestions'] = False

        time.sleep(2)

        # Test 4: Workflow
        print("\n4️⃣ Testing Workflow Handling...")
        r4a = self.send_message("I want to calculate TPR")
        time.sleep(2)
        r4b = self.send_message("What does TPR mean?")
        if r4b['success']:
            content = r4b['content'].lower()
            answers_interruption = "tpr" in content and ("test" in content or "positivity" in content)
            has_reminder = any(w in content for w in ["continue", "resume", "back to"])
            print(f"   ✅ Response received")
            print(f"   Handles interruption: {answers_interruption}")
            print(f"   Workflow reminder: {has_reminder}")
            self.results['workflow'] = answers_interruption
        else:
            print(f"   ❌ Failed: {r4b['error']}")
            self.results['workflow'] = False

        # Calculate score
        self.calculate_score()

    def calculate_score(self):
        """Calculate overall score"""
        print("\n" + "="*50)
        print("📊 RESULTS SUMMARY")
        print("="*50)

        scores = {
            'Identity': (self.results.get('identity', False), 25),
            'Arena Mode': (self.results.get('arena_active', False), 15),
            'Context Persistence': (self.results.get('context', False), 25),
            'Proactive Features': (self.results.get('proactive', False) or self.results.get('suggestions', False), 20),
            'Workflow Handling': (self.results.get('workflow', False), 15)
        }

        total_score = 0
        for feature, (passed, weight) in scores.items():
            status = "✅" if passed else "❌"
            print(f"{status} {feature}: {'PASS' if passed else 'FAIL'}")
            if passed:
                total_score += weight

        print(f"\n🎯 ChatGPT-Likeness Score: {total_score}/100")

        if total_score >= 80:
            verdict = "⭐⭐⭐⭐⭐ Excellent - Very conversational!"
        elif total_score >= 65:
            verdict = "⭐⭐⭐⭐ Good - Mostly conversational"
        elif total_score >= 50:
            verdict = "⭐⭐⭐ Moderate - Basic conversation"
        elif total_score >= 35:
            verdict = "⭐⭐ Limited conversation"
        else:
            verdict = "⭐ Poor - Not conversational"

        print(f"Rating: {verdict}")

        # Save results
        with open('tests/quick_verification_results.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'session_id': self.session_id,
                'results': self.results,
                'score': total_score,
                'verdict': verdict
            }, f, indent=2)

        print(f"\n💾 Results saved to: tests/quick_verification_results.json")

        return total_score


def main():
    verifier = QuickConversationVerifier()
    verifier.run_tests()


if __name__ == "__main__":
    main()
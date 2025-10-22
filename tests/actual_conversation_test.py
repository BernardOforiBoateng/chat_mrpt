#!/usr/bin/env python3
"""
Actual Conversation Test - Capture real Arena responses
"""

import requests
import json
import time
from datetime import datetime

class ActualConversationTest:
    def __init__(self):
        self.url = "https://d225ar6c86586s.cloudfront.net/send_message"
        self.session_id = f"actual-test-{int(time.time())}"
        self.test_results = []

    def extract_response_content(self, stream_text):
        """Extract actual response content from SSE stream"""
        content = {
            'model_a_response': '',
            'model_b_response': '',
            'suggestions': [],
            'reminder': None,
            'arena_mode': False,
            'models': {}
        }

        lines = stream_text.split('\n')
        for line in lines:
            if line.startswith('data: '):
                data_str = line[6:]
                if data_str.strip() not in ['[DONE]', '']:
                    try:
                        data = json.loads(data_str)

                        # Track arena mode
                        if 'arena_mode' in data:
                            content['arena_mode'] = data['arena_mode']

                        # Track models
                        if 'model_a' in data:
                            content['models']['a'] = data['model_a']
                        if 'model_b' in data:
                            content['models']['b'] = data['model_b']

                        # Capture suggestions
                        if 'suggestions' in data and data['suggestions']:
                            content['suggestions'] = data['suggestions']

                        # Capture reminder
                        if 'reminder' in data:
                            content['reminder'] = data['reminder']

                        # Capture actual responses
                        if 'delta' in data and 'side' in data:
                            if data['side'] == 'a':
                                content['model_a_response'] += data['delta']
                            elif data['side'] == 'b':
                                content['model_b_response'] += data['delta']
                    except:
                        pass

        return content

    def send_and_capture(self, message, test_name, timeout=25):
        """Send message and capture full response"""
        print(f"\n📤 {test_name}: {message}")

        try:
            response = requests.post(
                self.url,
                json={"message": message, "session_id": self.session_id},
                headers={"Content-Type": "application/json"},
                timeout=timeout,
                stream=True
            )

            if response.status_code == 200:
                # Capture full stream
                full_stream = ""
                for line in response.iter_lines():
                    if line:
                        full_stream += line.decode('utf-8') + '\n'

                # Extract content
                content = self.extract_response_content(full_stream)

                # Analyze results
                result = {
                    'test': test_name,
                    'message': message,
                    'success': True,
                    'arena_mode': content['arena_mode'],
                    'models': content['models'],
                    'has_suggestions': len(content['suggestions']) > 0,
                    'suggestions': content['suggestions'],
                    'has_reminder': content['reminder'] is not None,
                    'reminder': content['reminder'],
                    'model_a_response': content['model_a_response'][:200],
                    'model_b_response': content['model_b_response'][:200]
                }

                self.test_results.append(result)

                # Print analysis
                print(f"   ✅ Response received")
                print(f"   Arena Mode: {content['arena_mode']}")
                if content['models']:
                    print(f"   Models: {content['models']}")
                if content['suggestions']:
                    print(f"   Suggestions: {content['suggestions'][:2]}")
                if content['reminder']:
                    print(f"   Reminder: {content['reminder'][:50]}...")

                # Check response quality
                if content['model_a_response']:
                    print(f"   Model A preview: {content['model_a_response'][:100]}...")
                if content['model_b_response']:
                    print(f"   Model B preview: {content['model_b_response'][:100]}...")

                return result

            else:
                print(f"   ❌ HTTP {response.status_code}")
                self.test_results.append({
                    'test': test_name,
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                })

        except requests.Timeout:
            print(f"   ⏱️ Timeout after {timeout}s")
            self.test_results.append({
                'test': test_name,
                'success': False,
                'error': "Timeout"
            })

        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}")
            self.test_results.append({
                'test': test_name,
                'success': False,
                'error': str(e)[:50]
            })

    def run_all_tests(self):
        """Run comprehensive conversation tests"""
        print("\n🔬 ACTUAL CONVERSATION TEST")
        print("="*60)
        print(f"Session: {self.session_id}")
        print("="*60)

        # Test 1: Identity
        self.send_and_capture(
            "Hello, who are you?",
            "Identity Test"
        )
        time.sleep(3)

        # Test 2: Context setup
        self.send_and_capture(
            "I'm working with malaria data from Kano state with 100 health facilities",
            "Context Setup"
        )
        time.sleep(3)

        # Test 3: Context recall
        self.send_and_capture(
            "What are the main challenges in this region?",
            "Context Recall"
        )
        time.sleep(3)

        # Test 4: Workflow start
        self.send_and_capture(
            "I want to calculate TPR",
            "Workflow Start"
        )
        time.sleep(3)

        # Test 5: Workflow interruption
        self.send_and_capture(
            "Actually, what does TPR mean?",
            "Workflow Interruption"
        )
        time.sleep(3)

        # Test 6: Suggestions request
        self.send_and_capture(
            "I have uploaded my data. What should I do next?",
            "Suggestions Test"
        )

        # Analyze results
        self.analyze_results()

    def analyze_results(self):
        """Analyze test results"""
        print("\n" + "="*60)
        print("📊 TEST ANALYSIS")
        print("="*60)

        # Count successes
        successful_tests = [r for r in self.test_results if r.get('success')]
        failed_tests = [r for r in self.test_results if not r.get('success')]

        print(f"\n✅ Successful: {len(successful_tests)}/{len(self.test_results)}")
        print(f"❌ Failed: {len(failed_tests)}/{len(self.test_results)}")

        # Check key features
        print("\n🔍 KEY FINDINGS:")

        # Arena activation
        arena_active = any(r.get('arena_mode') for r in successful_tests)
        print(f"{'✅' if arena_active else '❌'} Arena Mode: {'ACTIVE' if arena_active else 'NOT DETECTED'}")

        # Models used
        models_found = set()
        for r in successful_tests:
            if r.get('models'):
                models_found.update(r['models'].values())
        if models_found:
            print(f"✅ Models Active: {', '.join(models_found)}")

        # Suggestions
        has_suggestions = any(r.get('has_suggestions') for r in successful_tests)
        print(f"{'✅' if has_suggestions else '❌'} Proactive Suggestions: {'YES' if has_suggestions else 'NO'}")

        # Reminders
        has_reminders = any(r.get('has_reminder') for r in successful_tests)
        print(f"{'✅' if has_reminders else '⚠️'} Workflow Reminders: {'YES' if has_reminders else 'NO'}")

        # Check identity
        identity_test = [r for r in successful_tests if r['test'] == 'Identity Test']
        if identity_test and identity_test[0].get('model_a_response'):
            response = identity_test[0]['model_a_response'].lower()
            has_identity = 'chatmrpt' in response or 'malaria' in response
            print(f"{'✅' if has_identity else '❌'} ChatMRPT Identity: {'YES' if has_identity else 'NO'}")

        # Check context persistence
        context_tests = [r for r in successful_tests if 'Context' in r['test']]
        if len(context_tests) >= 2:
            recall_response = context_tests[-1].get('model_a_response', '').lower()
            maintains_context = 'kano' in recall_response or 'facilities' in recall_response
            print(f"{'✅' if maintains_context else '❌'} Context Persistence: {'YES' if maintains_context else 'NO'}")

        # Calculate score
        score = 0
        if arena_active: score += 20
        if models_found: score += 20
        if has_suggestions: score += 20
        if has_reminders: score += 10
        if identity_test and has_identity: score += 20
        if len(context_tests) >= 2 and maintains_context: score += 10

        print(f"\n🎯 CHATGPT-LIKENESS SCORE: {score}/100")

        if score >= 80:
            verdict = "⭐⭐⭐⭐⭐ Excellent - Very conversational!"
        elif score >= 60:
            verdict = "⭐⭐⭐⭐ Good - Mostly conversational"
        elif score >= 40:
            verdict = "⭐⭐⭐ Moderate - Basic conversation"
        elif score >= 20:
            verdict = "⭐⭐ Limited conversation"
        else:
            verdict = "⭐ Poor - Not conversational"

        print(f"Verdict: {verdict}")

        # Save results
        with open('tests/actual_conversation_results.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'session_id': self.session_id,
                'test_results': self.test_results,
                'score': score,
                'verdict': verdict,
                'key_findings': {
                    'arena_active': arena_active,
                    'models': list(models_found),
                    'has_suggestions': has_suggestions,
                    'has_reminders': has_reminders
                }
            }, f, indent=2)

        print(f"\n💾 Results saved to: tests/actual_conversation_results.json")

        return score


def main():
    tester = ActualConversationTest()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
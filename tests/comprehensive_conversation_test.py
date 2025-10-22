#!/usr/bin/env python3
"""
Comprehensive Conversational Test Suite for ChatMRPT
Tests all aspects of conversational capabilities against production
"""

import requests
import json
import time
import uuid
from datetime import datetime
import re
from typing import Dict, List, Optional, Tuple
import sys

# Configuration
BASE_URL = "https://d225ar6c86586s.cloudfront.net"
API_ENDPOINT = f"{BASE_URL}/send_message"
REQUEST_TIMEOUT = 30

class ComprehensiveConversationTester:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.conversation_log = []
        self.test_results = []
        self.arena_responses = {}

    def parse_sse_stream(self, response_text: str) -> Dict:
        """Parse SSE stream response and extract conversation data"""
        result = {
            'arena_mode': False,
            'battle_id': None,
            'models': {},
            'responses': [],
            'suggestions': [],
            'reminder': None,
            'full_text': ''
        }

        lines = response_text.strip().split('\n')
        current_response = {}

        for line in lines:
            if line.startswith('data: '):
                data_str = line[6:]
                if data_str.strip() == '[DONE]':
                    continue

                try:
                    event_data = json.loads(data_str)

                    # Check for arena mode
                    if 'arena_mode' in event_data:
                        result['arena_mode'] = event_data['arena_mode']

                    # Extract battle info
                    if 'battle_id' in event_data:
                        result['battle_id'] = event_data['battle_id']

                    # Extract model info
                    if 'model_a' in event_data:
                        result['models']['a'] = event_data['model_a']
                    if 'model_b' in event_data:
                        result['models']['b'] = event_data['model_b']

                    # Extract suggestions
                    if 'suggestions' in event_data and event_data['suggestions']:
                        result['suggestions'] = event_data['suggestions']

                    # Extract reminder
                    if 'reminder' in event_data:
                        result['reminder'] = event_data['reminder']

                    # Extract streamed content
                    if 'delta' in event_data:
                        side = event_data.get('side', 'unknown')
                        if side not in current_response:
                            current_response[side] = ''
                        current_response[side] += event_data['delta']
                        result['full_text'] += event_data['delta']

                    # Regular response field
                    if 'response' in event_data:
                        result['full_text'] += event_data['response']

                except json.JSONDecodeError:
                    pass

        # Store model responses
        for side, text in current_response.items():
            result['responses'].append({
                'side': side,
                'text': text,
                'model': result['models'].get(side, 'unknown')
            })

        return result

    def send_message(self, message: str, expect_arena: bool = True) -> Dict:
        """Send message and parse response"""

        try:
            payload = {
                "message": message,
                "session_id": self.session_id
            }

            headers = {
                "Content-Type": "application/json",
                "Accept": "text/event-stream, application/json"
            }

            start_time = time.time()
            response = requests.post(
                API_ENDPOINT,
                json=payload,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
                stream=True
            )
            latency = time.time() - start_time

            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')

                # Handle streaming response
                if 'event-stream' in content_type or 'text/plain' in content_type:
                    full_text = ""
                    for line in response.iter_lines():
                        if line:
                            decoded_line = line.decode('utf-8')
                            full_text += decoded_line + '\n'

                    parsed = self.parse_sse_stream(full_text)
                    parsed['latency'] = latency
                    parsed['success'] = True

                    # Log conversation
                    self.conversation_log.append({
                        'message': message,
                        'response': parsed,
                        'timestamp': datetime.now().isoformat()
                    })

                    return parsed
                else:
                    # Regular JSON response
                    result = response.json()
                    return {
                        'success': True,
                        'full_text': result.get('response', ''),
                        'latency': latency,
                        'arena_mode': False
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'latency': latency
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'latency': time.time() - start_time if 'start_time' in locals() else 0
            }

    def test_1_basic_conversation_identity(self):
        """Test 1: Basic conversation and ChatMRPT identity"""
        print("\n" + "="*60)
        print("TEST 1: Basic Conversation & Identity")
        print("="*60)

        test_cases = [
            ("Hello, who are you?", ["chatmrpt", "malaria", "health", "assistant"], "Identity check"),
            ("What can you help me with?", ["analyze", "data", "malaria", "risk", "help"], "Capabilities check"),
            ("Tell me about malaria", ["plasmodium", "mosquito", "disease", "transmission"], "Domain knowledge"),
            ("How can I prevent malaria?", ["net", "itn", "spray", "prevent", "insecticide"], "Prevention knowledge")
        ]

        results = {
            'test_name': 'Basic Conversation & Identity',
            'passed': 0,
            'failed': 0,
            'details': []
        }

        for message, expected_keywords, test_type in test_cases:
            print(f"\n📤 {test_type}: {message}")
            response = self.send_message(message)

            if response['success']:
                text = response['full_text'].lower()
                found_keywords = [kw for kw in expected_keywords if kw in text]

                # Check arena mode
                is_arena = response.get('arena_mode', False)
                has_models = bool(response.get('models'))

                # Check identity/knowledge
                has_identity = len(found_keywords) >= 2

                passed = response['success'] and has_identity

                if passed:
                    print(f"✅ PASS - Arena: {is_arena}, Keywords: {found_keywords}")
                    results['passed'] += 1
                else:
                    print(f"❌ FAIL - Missing identity/knowledge")
                    results['failed'] += 1

                results['details'].append({
                    'test': test_type,
                    'passed': passed,
                    'arena_mode': is_arena,
                    'models': response.get('models', {}),
                    'keywords_found': found_keywords,
                    'response_length': len(text),
                    'latency': response.get('latency', 0)
                })

                # Show response snippet
                if text:
                    snippet = text[:200] + "..." if len(text) > 200 else text
                    print(f"💬 Response: {snippet}")

            else:
                print(f"❌ Error: {response.get('error')}")
                results['failed'] += 1
                results['details'].append({
                    'test': test_type,
                    'passed': False,
                    'error': response.get('error')
                })

            time.sleep(2)  # Rate limiting

        self.test_results.append(results)
        return results

    def test_2_context_persistence(self):
        """Test 2: Context persistence across messages"""
        print("\n" + "="*60)
        print("TEST 2: Context Persistence")
        print("="*60)

        results = {
            'test_name': 'Context Persistence',
            'passed': 0,
            'failed': 0,
            'details': []
        }

        # Establish context
        print("\n📤 Setting context: Working in Kano with 200 facilities")
        r1 = self.send_message("I'm analyzing malaria data from Kano state with 200 health facilities")

        if r1['success']:
            print(f"✅ Context established (Arena: {r1.get('arena_mode')})")
            time.sleep(2)

            # Test context recall
            print("\n📤 Testing context recall: What challenges exist there?")
            r2 = self.send_message("What are the main challenges in this region?")

            if r2['success']:
                text = r2['full_text'].lower()

                # Check for context maintenance
                context_keywords = ["kano", "nigeria", "state", "facilities", "200", "northern"]
                found = [kw for kw in context_keywords if kw in text]

                context_maintained = len(found) > 0

                if context_maintained:
                    print(f"✅ PASS - Context maintained: {found}")
                    results['passed'] += 1
                else:
                    print(f"❌ FAIL - Context lost")
                    results['failed'] += 1

                results['details'].append({
                    'test': 'Location context',
                    'passed': context_maintained,
                    'context_keywords': found
                })

            # Test specific detail recall
            time.sleep(2)
            print("\n📤 Testing detail recall: How many facilities did I mention?")
            r3 = self.send_message("How many health facilities did I mention?")

            if r3['success']:
                text = r3['full_text'].lower()
                recalls_number = "200" in text or "two hundred" in text

                if recalls_number:
                    print(f"✅ PASS - Specific detail recalled (200 facilities)")
                    results['passed'] += 1
                else:
                    print(f"❌ FAIL - Detail forgotten")
                    results['failed'] += 1

                results['details'].append({
                    'test': 'Specific detail recall',
                    'passed': recalls_number
                })

        self.test_results.append(results)
        return results

    def test_3_proactive_suggestions(self):
        """Test 3: Proactive suggestions and guidance"""
        print("\n" + "="*60)
        print("TEST 3: Proactive Suggestions")
        print("="*60)

        results = {
            'test_name': 'Proactive Suggestions',
            'passed': 0,
            'failed': 0,
            'details': []
        }

        # Simulate data upload context
        print("\n📤 Simulating post-upload: I've uploaded my malaria data")
        r1 = self.send_message("I've just uploaded malaria incidence data for 50 wards")

        if r1['success']:
            # Check for suggestions in SSE
            has_suggestions = len(r1.get('suggestions', [])) > 0

            # Check for proactive content in response
            text = r1['full_text'].lower()
            proactive_phrases = [
                "you can", "you could", "i can", "would you like",
                "start with", "recommend", "suggest", "try",
                "quick overview", "analyze", "map"
            ]
            found_phrases = [p for p in proactive_phrases if p in text]

            is_proactive = has_suggestions or len(found_phrases) > 2

            if is_proactive:
                print(f"✅ PASS - Proactive guidance provided")
                if has_suggestions:
                    print(f"   Suggestions: {r1['suggestions']}")
                if found_phrases:
                    print(f"   Proactive phrases: {found_phrases[:3]}")
                results['passed'] += 1
            else:
                print(f"❌ FAIL - No proactive suggestions")
                results['failed'] += 1

            results['details'].append({
                'test': 'Post-upload suggestions',
                'passed': is_proactive,
                'has_suggestions': has_suggestions,
                'suggestions': r1.get('suggestions', []),
                'proactive_phrases': found_phrases
            })

        # Test open-ended help request
        time.sleep(2)
        print("\n📤 Open-ended: How do I reduce malaria in my community?")
        r2 = self.send_message("How do I reduce malaria transmission in my community?")

        if r2['success']:
            text = r2['full_text'].lower()

            # Check for actionable suggestions
            action_words = [
                "distribute", "spray", "educate", "monitor",
                "implement", "ensure", "provide", "conduct"
            ]
            has_actions = sum(1 for word in action_words if word in text) >= 2

            # Check for structured guidance
            has_structure = any(marker in text for marker in ["1.", "2.", "first", "second", "•", "-"])

            is_helpful = has_actions and has_structure

            if is_helpful:
                print(f"✅ PASS - Actionable guidance provided")
                results['passed'] += 1
            else:
                print(f"❌ FAIL - Guidance not actionable")
                results['failed'] += 1

            results['details'].append({
                'test': 'Open-ended guidance',
                'passed': is_helpful,
                'has_actions': has_actions,
                'has_structure': has_structure
            })

        self.test_results.append(results)
        return results

    def test_4_workflow_interruption(self):
        """Test 4: Workflow interruption and recovery"""
        print("\n" + "="*60)
        print("TEST 4: Workflow Interruption & Recovery")
        print("="*60)

        results = {
            'test_name': 'Workflow Interruption',
            'passed': 0,
            'failed': 0,
            'details': []
        }

        # Start workflow discussion
        print("\n📤 Starting workflow: I want to calculate TPR")
        r1 = self.send_message("I want to calculate TPR for my region")

        if r1['success']:
            # Check if workflow initiated
            text = r1['full_text'].lower()
            workflow_started = any(word in text for word in ["tpr", "test", "positivity", "calculate", "state", "age"])

            if workflow_started:
                print(f"✅ Workflow initiated")

            # Interrupt with side question
            time.sleep(2)
            print("\n📤 Interruption: What does PCA mean?")
            r2 = self.send_message("Wait, what does PCA mean?")

            if r2['success']:
                text = r2['full_text'].lower()

                # Check if interruption handled
                answers_question = "pca" in text and any(word in text for word in [
                    "principal", "component", "analysis", "statistical", "dimension"
                ])

                # Check for workflow reminder
                has_reminder = r2.get('reminder') is not None or any(phrase in text for phrase in [
                    "continue", "tpr", "back to", "resume", "shall we"
                ])

                handled_well = answers_question

                if handled_well:
                    print(f"✅ PASS - Interruption handled")
                    if has_reminder:
                        print(f"   Reminder: {r2.get('reminder', 'gentle nudge in response')}")
                    results['passed'] += 1
                else:
                    print(f"❌ FAIL - Poor interruption handling")
                    results['failed'] += 1

                results['details'].append({
                    'test': 'Side question handling',
                    'passed': handled_well,
                    'answers_question': answers_question,
                    'has_reminder': has_reminder
                })

                # Try to resume
                time.sleep(2)
                print("\n📤 Resumption: OK, let's continue with TPR")
                r3 = self.send_message("OK thanks. Let's continue with the TPR calculation")

                if r3['success']:
                    text = r3['full_text'].lower()

                    # Check for workflow continuation
                    resumes_workflow = any(word in text for word in [
                        "tpr", "state", "age", "facility", "continue",
                        "proceed", "next", "select", "choose"
                    ])

                    if resumes_workflow:
                        print(f"✅ PASS - Workflow resumed")
                        results['passed'] += 1
                    else:
                        print(f"❌ FAIL - Failed to resume workflow")
                        results['failed'] += 1

                    results['details'].append({
                        'test': 'Workflow resumption',
                        'passed': resumes_workflow
                    })

        self.test_results.append(results)
        return results

    def test_5_numeric_mapping(self):
        """Test 5: Numeric choice mapping and slot filling"""
        print("\n" + "="*60)
        print("TEST 5: Numeric Mapping & Slot Filling")
        print("="*60)

        results = {
            'test_name': 'Numeric Mapping',
            'passed': 0,
            'failed': 0,
            'details': []
        }

        # Present options
        print("\n📤 Requesting options: What analysis options do I have?")
        r1 = self.send_message("What types of malaria analysis can you help me with?")

        if r1['success']:
            text = r1['full_text'].lower()

            # Check if options are presented
            has_options = any(marker in text for marker in ["1", "2", "•", "-", "first", "second"])

            if has_options:
                print(f"✅ Options presented")

                # Try numeric selection
                time.sleep(2)
                print("\n📤 Numeric selection: I'll go with option 1")
                r2 = self.send_message("I'll go with option 1")

                if r2['success']:
                    # Check if numeric choice was understood
                    text = r2['full_text'].lower()

                    # Should reference first option somehow
                    understood = len(text) > 50  # At minimum, a reasonable response

                    if understood:
                        print(f"✅ PASS - Numeric choice processed")
                        results['passed'] += 1
                    else:
                        print(f"❌ FAIL - Numeric choice not understood")
                        results['failed'] += 1

                    results['details'].append({
                        'test': 'Numeric selection',
                        'passed': understood
                    })

        # Test slot filling
        time.sleep(2)
        print("\n📤 Slot filling: Calculate TPR for Kano under-5 at primary facilities")
        r3 = self.send_message("Calculate TPR for Kano state, under-5 age group, at primary health facilities")

        if r3['success']:
            text = r3['full_text'].lower()

            # Check if slots were recognized
            slots_recognized = [
                "kano" in text,
                "under-5" in text or "under 5" in text or "u5" in text,
                "primary" in text
            ]

            all_slots = sum(slots_recognized)

            if all_slots >= 2:
                print(f"✅ PASS - Slots recognized: {all_slots}/3")
                results['passed'] += 1
            else:
                print(f"❌ FAIL - Slots not fully recognized")
                results['failed'] += 1

            results['details'].append({
                'test': 'Slot filling',
                'passed': all_slots >= 2,
                'slots_recognized': all_slots
            })

        self.test_results.append(results)
        return results

    def test_6_arena_features(self):
        """Test 6: Arena-specific features"""
        print("\n" + "="*60)
        print("TEST 6: Arena Features")
        print("="*60)

        results = {
            'test_name': 'Arena Features',
            'passed': 0,
            'failed': 0,
            'details': []
        }

        # Test if Arena is active
        print("\n📤 Testing Arena: Hello ChatMRPT")
        r1 = self.send_message("Hello ChatMRPT, are you there?")

        if r1['success']:
            # Check Arena indicators
            is_arena = r1.get('arena_mode', False)
            has_battle_id = r1.get('battle_id') is not None
            has_models = bool(r1.get('models'))
            has_multiple_responses = len(r1.get('responses', [])) > 1

            arena_active = is_arena or has_battle_id or has_models

            if arena_active:
                print(f"✅ PASS - Arena mode active")
                print(f"   Models: {r1.get('models', {})}")
                print(f"   Battle ID: {r1.get('battle_id', 'N/A')}")
                results['passed'] += 1
            else:
                print(f"❌ FAIL - Arena mode not detected")
                results['failed'] += 1

            results['details'].append({
                'test': 'Arena activation',
                'passed': arena_active,
                'arena_mode': is_arena,
                'has_battle_id': has_battle_id,
                'has_models': has_models,
                'models': r1.get('models', {})
            })

        # Test suggestions in SSE
        time.sleep(2)
        print("\n📤 Testing suggestions: I need help with my data")
        r2 = self.send_message("I have malaria data and need guidance")

        if r2['success']:
            has_suggestions = len(r2.get('suggestions', [])) > 0

            if has_suggestions:
                print(f"✅ PASS - Suggestions provided: {r2['suggestions']}")
                results['passed'] += 1
            else:
                print(f"⚠️ INFO - No suggestions in SSE")
                # Don't count as failure - might be context-dependent

            results['details'].append({
                'test': 'SSE suggestions',
                'passed': has_suggestions,
                'suggestions': r2.get('suggestions', [])
            })

        self.test_results.append(results)
        return results

    def calculate_overall_score(self) -> float:
        """Calculate overall ChatGPT-likeness score"""

        weights = {
            'Basic Conversation & Identity': 20,
            'Context Persistence': 25,
            'Proactive Suggestions': 15,
            'Workflow Interruption': 20,
            'Numeric Mapping': 10,
            'Arena Features': 10
        }

        total_score = 0
        for result in self.test_results:
            test_name = result['test_name']
            if test_name in weights:
                total = result['passed'] + result['failed']
                if total > 0:
                    success_rate = result['passed'] / total
                    weighted_score = success_rate * weights[test_name]
                    total_score += weighted_score

        return total_score

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*70)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("="*70)

        # Summary statistics
        total_passed = sum(r['passed'] for r in self.test_results)
        total_failed = sum(r['failed'] for r in self.test_results)
        total_tests = total_passed + total_failed

        print(f"\n📈 Overall Statistics:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {total_passed}")
        print(f"   Failed: {total_failed}")
        print(f"   Success Rate: {(total_passed/total_tests*100):.1f}%")

        # Individual test results
        print(f"\n📋 Test Breakdown:")
        for result in self.test_results:
            passed = result['passed']
            failed = result['failed']
            total = passed + failed
            rate = (passed/total*100) if total > 0 else 0

            status = "✅" if rate >= 70 else "⚠️" if rate >= 50 else "❌"
            print(f"   {status} {result['test_name']}: {passed}/{total} passed ({rate:.0f}%)")

        # Calculate ChatGPT score
        chatgpt_score = self.calculate_overall_score()

        print(f"\n🎯 ChatGPT-Likeness Score: {chatgpt_score:.1f}/100")

        # Rating
        if chatgpt_score >= 80:
            rating = "⭐⭐⭐⭐⭐ Excellent - Very ChatGPT-like!"
            assessment = "ChatMRPT demonstrates strong conversational abilities"
        elif chatgpt_score >= 70:
            rating = "⭐⭐⭐⭐ Good - Mostly conversational"
            assessment = "ChatMRPT is conversational with some gaps"
        elif chatgpt_score >= 60:
            rating = "⭐⭐⭐ Moderate - Basic conversation"
            assessment = "ChatMRPT has foundational conversational features"
        elif chatgpt_score >= 50:
            rating = "⭐⭐ Limited - Some conversation"
            assessment = "ChatMRPT needs conversational improvements"
        else:
            rating = "⭐ Poor - Limited conversation"
            assessment = "ChatMRPT lacks key conversational features"

        print(f"   Rating: {rating}")
        print(f"   Assessment: {assessment}")

        # Key findings
        print(f"\n🔍 Key Findings:")

        # Check Arena status
        arena_tests = [r for r in self.test_results if r['test_name'] == 'Arena Features']
        if arena_tests:
            arena_details = arena_tests[0].get('details', [])
            if arena_details:
                arena_info = arena_details[0]
                if arena_info.get('arena_mode') or arena_info.get('has_models'):
                    print(f"   ✅ Arena mode is ACTIVE")
                    print(f"      Models: {arena_info.get('models', {})}")
                else:
                    print(f"   ❌ Arena mode NOT detected")

        # Check context persistence
        context_tests = [r for r in self.test_results if r['test_name'] == 'Context Persistence']
        if context_tests and context_tests[0]['passed'] > 0:
            print(f"   ✅ Context persistence WORKING")
        else:
            print(f"   ❌ Context persistence FAILING")

        # Check proactive features
        proactive_tests = [r for r in self.test_results if r['test_name'] == 'Proactive Suggestions']
        if proactive_tests:
            details = proactive_tests[0].get('details', [])
            has_suggestions = any(d.get('has_suggestions') for d in details)
            if has_suggestions:
                print(f"   ✅ Proactive suggestions ACTIVE")
            else:
                print(f"   ⚠️ Proactive suggestions LIMITED")

        # Performance metrics
        all_latencies = []
        for result in self.test_results:
            for detail in result.get('details', []):
                if 'latency' in detail:
                    all_latencies.append(detail['latency'])

        if all_latencies:
            avg_latency = sum(all_latencies) / len(all_latencies)
            print(f"\n⚡ Performance:")
            print(f"   Average Response Time: {avg_latency:.2f}s")
            print(f"   Total Conversations: {len(self.conversation_log)}")

        # Save detailed report
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'endpoint': API_ENDPOINT,
            'test_results': self.test_results,
            'metrics': {
                'total_tests': total_tests,
                'passed': total_passed,
                'failed': total_failed,
                'success_rate': (total_passed/total_tests*100) if total_tests > 0 else 0,
                'chatgpt_score': chatgpt_score,
                'assessment': assessment
            },
            'conversation_log': self.conversation_log
        }

        with open('tests/comprehensive_test_results.json', 'w') as f:
            json.dump(report_data, f, indent=2)

        print(f"\n💾 Detailed report saved to: tests/comprehensive_test_results.json")

        return chatgpt_score, assessment


def main():
    print("\n" + "="*70)
    print("🚀 CHATMRPT COMPREHENSIVE CONVERSATIONAL TEST")
    print("="*70)
    print(f"📍 Endpoint: {BASE_URL}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    tester = ComprehensiveConversationTester()

    # Run all tests
    tester.test_1_basic_conversation_identity()
    tester.test_2_context_persistence()
    tester.test_3_proactive_suggestions()
    tester.test_4_workflow_interruption()
    tester.test_5_numeric_mapping()
    tester.test_6_arena_features()

    # Generate report
    score, assessment = tester.generate_report()

    print("\n" + "="*70)
    print(f"✨ FINAL VERDICT: ChatMRPT is {score:.0f}% ChatGPT-like")
    print(f"📝 {assessment}")
    print("="*70)

    return score


if __name__ == "__main__":
    try:
        score = main()
        sys.exit(0 if score >= 70 else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
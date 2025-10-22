#!/usr/bin/env python3
"""
Test ChatMRPT Conversational Capabilities with SSE Support
Properly handles Server-Sent Events streaming responses
"""

import requests
import json
import time
import uuid
from datetime import datetime
import sys
import re

# Configuration
BASE_URL = "https://d225ar6c86586s.cloudfront.net"
API_ENDPOINT = f"{BASE_URL}/send_message"
REQUEST_TIMEOUT = 60

class SSEConversationalTester:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.conversation_log = []

    def parse_sse_response(self, response_text):
        """Parse Server-Sent Events response"""
        # SSE format: data: {json}\n\n
        lines = response_text.strip().split('\n')
        full_response = ""
        events = []

        for line in lines:
            if line.startswith('data: '):
                data_str = line[6:]  # Remove 'data: ' prefix
                if data_str.strip() == '[DONE]':
                    continue
                try:
                    event_data = json.loads(data_str)
                    events.append(event_data)
                    # Extract the actual message content
                    if 'content' in event_data:
                        full_response += event_data['content']
                    elif 'response' in event_data:
                        full_response += event_data['response']
                except json.JSONDecodeError:
                    # Sometimes data might be plain text
                    if data_str.strip():
                        full_response += data_str

        return full_response, events

    def send_message(self, message: str, max_retries: int = 2) -> dict:
        """Send message and handle SSE streaming response"""

        for attempt in range(max_retries):
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
                    stream=True  # Important for SSE
                )

                if response.status_code == 200:
                    # Check content type
                    content_type = response.headers.get('Content-Type', '')

                    if 'event-stream' in content_type:
                        # Handle SSE response
                        full_text = ""
                        for line in response.iter_lines():
                            if line:
                                decoded_line = line.decode('utf-8')
                                full_text += decoded_line + '\n'

                        parsed_response, events = self.parse_sse_response(full_text)
                        latency = time.time() - start_time

                        # Log conversation
                        self.conversation_log.append({
                            "message": message,
                            "response": parsed_response,
                            "latency": latency,
                            "timestamp": datetime.now().isoformat()
                        })

                        return {
                            "success": True,
                            "response": parsed_response,
                            "latency": latency,
                            "events": events
                        }
                    else:
                        # Regular JSON response
                        result = response.json()
                        latency = time.time() - start_time

                        self.conversation_log.append({
                            "message": message,
                            "response": result.get("response", ""),
                            "latency": latency
                        })

                        return {
                            "success": True,
                            "response": result.get("response", ""),
                            "latency": latency
                        }
                else:
                    if attempt < max_retries - 1:
                        print(f"      Retry {attempt + 1}/{max_retries} after status {response.status_code}")
                        time.sleep(2)
                        continue
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "response": response.text[:500]
                    }

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    print(f"      Retry {attempt + 1}/{max_retries} after timeout")
                    time.sleep(2)
                    continue
                return {
                    "success": False,
                    "error": f"Timeout after {REQUEST_TIMEOUT}s"
                }

            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"      Retry {attempt + 1}/{max_retries} after error")
                    time.sleep(2)
                    continue
                return {
                    "success": False,
                    "error": str(e)
                }

        return {"success": False, "error": "Max retries exceeded"}

    def run_tests(self):
        """Run comprehensive conversational tests"""
        print("\n" + "="*60)
        print("🚀 ChatMRPT Conversational Test with SSE Support")
        print("="*60)
        print(f"📍 Endpoint: {BASE_URL}")
        print(f"🔑 Session: {self.session_id}")

        test_results = {
            "basic_conversation": {"passed": 0, "failed": 0},
            "context_persistence": {"passed": 0, "failed": 0},
            "interruption": {"passed": 0, "failed": 0},
            "proactive": {"passed": 0, "failed": 0},
            "transitions": {"passed": 0, "failed": 0}
        }

        # Test 1: Basic Conversation
        print("\n📋 TEST 1: Basic Conversation")
        print("-"*40)

        test_messages = [
            ("Hello, who are you?", ["chatmrpt", "malaria", "assistant"]),
            ("What is malaria?", ["plasmodium", "mosquito", "disease"]),
            ("How can I prevent it?", ["net", "itn", "prevention", "spray"]),
            ("Thank you", ["welcome", "help", "glad"])
        ]

        for msg, keywords in test_messages:
            print(f"\n  📤 Sending: {msg}")
            response = self.send_message(msg)

            if response["success"]:
                resp_lower = response["response"].lower()
                found_keywords = [k for k in keywords if k in resp_lower]

                success = len(found_keywords) > 0 and len(response["response"]) > 20

                if success:
                    print(f"  ✅ PASS - Keywords: {found_keywords}, Time: {response['latency']:.1f}s")
                    test_results["basic_conversation"]["passed"] += 1
                else:
                    print(f"  ❌ FAIL - Missing keywords or short response")
                    test_results["basic_conversation"]["failed"] += 1

                # Show snippet
                snippet = response["response"][:150] + "..." if len(response["response"]) > 150 else response["response"]
                print(f"  💬 Response: {snippet}")
            else:
                print(f"  ❌ FAIL - {response['error']}")
                test_results["basic_conversation"]["failed"] += 1

            time.sleep(2)

        # Test 2: Context Persistence
        print("\n📋 TEST 2: Context Persistence")
        print("-"*40)

        print("\n  📤 Setting context: Working in Nigeria with 100 facilities")
        r1 = self.send_message("I'm working on a malaria project in Nigeria with 100 health facilities")

        if r1["success"]:
            print(f"  ✅ Context set ({r1['latency']:.1f}s)")
            time.sleep(2)

            print("\n  📤 Testing recall: What challenges exist there?")
            r2 = self.send_message("What are the main challenges in this region?")

            if r2["success"]:
                resp_lower = r2["response"].lower()
                maintains_context = any(word in resp_lower for word in ["nigeria", "african", "facilities", "100"])

                if maintains_context:
                    print(f"  ✅ PASS - Context maintained")
                    test_results["context_persistence"]["passed"] += 1
                else:
                    print(f"  ❌ FAIL - Lost context")
                    test_results["context_persistence"]["failed"] += 1

                snippet = r2["response"][:150] + "..." if len(r2["response"]) > 150 else r2["response"]
                print(f"  💬 Response: {snippet}")

        # Test 3: Interruption Handling
        print("\n📋 TEST 3: Interruption & Recovery")
        print("-"*40)

        print("\n  📤 Starting workflow: I want to analyze data")
        r1 = self.send_message("I want to analyze malaria risk in my region")
        time.sleep(2)

        print("\n  📤 Interrupting: What does TPR mean?")
        r2 = self.send_message("Wait, what does TPR mean?")

        if r2["success"]:
            resp_lower = r2["response"].lower()
            handles_interruption = "tpr" in resp_lower and ("test" in resp_lower or "positivity" in resp_lower or "rate" in resp_lower)

            if handles_interruption:
                print(f"  ✅ PASS - Handled interruption")
                test_results["interruption"]["passed"] += 1
            else:
                print(f"  ❌ FAIL - Poor interruption handling")
                test_results["interruption"]["failed"] += 1

            time.sleep(2)
            print("\n  📤 Resuming: Back to the analysis")
            r3 = self.send_message("Ok, so about analyzing my data?")

            if r3["success"]:
                resumes = any(word in r3["response"].lower() for word in ["analysis", "upload", "data", "csv"])

                if resumes:
                    print(f"  ✅ PASS - Resumed workflow")
                    test_results["interruption"]["passed"] += 1
                else:
                    print(f"  ❌ FAIL - Failed to resume")
                    test_results["interruption"]["failed"] += 1

        # Test 4: Proactive Assistance
        print("\n📋 TEST 4: Proactive Suggestions")
        print("-"*40)

        print("\n  📤 Open question: How do I start?")
        r = self.send_message("I want to reduce malaria in my community. How do I start?")

        if r["success"]:
            resp_lower = r["response"].lower()
            is_proactive = any(phrase in resp_lower for phrase in [
                "you can", "you could", "first", "start by",
                "recommend", "suggest", "consider"
            ])

            if is_proactive:
                print(f"  ✅ PASS - Proactive guidance provided")
                test_results["proactive"]["passed"] += 1
            else:
                print(f"  ❌ FAIL - No proactive suggestions")
                test_results["proactive"]["failed"] += 1

        # Test 5: Natural Transitions
        print("\n📋 TEST 5: Natural Topic Transitions")
        print("-"*40)

        transitions = [
            ("Tell me about mosquito biology", "mosquito"),
            ("How does this relate to climate?", "climate"),
            ("What about urban areas?", "urban")
        ]

        for msg, topic in transitions:
            print(f"\n  📤 Transition to {topic}: {msg}")
            r = self.send_message(msg)

            if r["success"] and len(r["response"]) > 30:
                print(f"  ✅ PASS - Smooth transition")
                test_results["transitions"]["passed"] += 1
            else:
                print(f"  ❌ FAIL - Poor transition")
                test_results["transitions"]["failed"] += 1

            time.sleep(2)

        return test_results

    def calculate_score(self, results):
        """Calculate ChatGPT-likeness score"""
        weights = {
            "basic_conversation": 20,
            "context_persistence": 25,
            "interruption": 20,
            "proactive": 15,
            "transitions": 20
        }

        total_score = 0
        for category, scores in results.items():
            if category in weights:
                total = scores["passed"] + scores["failed"]
                if total > 0:
                    success_rate = (scores["passed"] / total) * 100
                    weighted = (success_rate / 100) * weights[category]
                    total_score += weighted

        return total_score

    def generate_report(self, results):
        """Generate final report"""
        print("\n" + "="*60)
        print("📊 FINAL TEST REPORT")
        print("="*60)

        # Calculate totals
        total_passed = sum(r["passed"] for r in results.values())
        total_failed = sum(r["failed"] for r in results.values())
        total_tests = total_passed + total_failed

        print(f"\n📈 Overall Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {total_passed}")
        print(f"   Failed: {total_failed}")
        print(f"   Success Rate: {(total_passed/total_tests*100):.1f}%" if total_tests > 0 else "N/A")

        print(f"\n📋 Test Breakdown:")
        for category, scores in results.items():
            total = scores["passed"] + scores["failed"]
            status = "✅" if scores["passed"] > scores["failed"] else "❌"
            print(f"   {status} {category.replace('_', ' ').title()}: {scores['passed']}/{total} passed")

        # Calculate ChatGPT score
        chatgpt_score = self.calculate_score(results)

        print(f"\n🎯 ChatGPT-Likeness Score: {chatgpt_score:.1f}/100")

        if chatgpt_score >= 80:
            rating = "⭐⭐⭐⭐⭐ Excellent - Very ChatGPT-like!"
        elif chatgpt_score >= 70:
            rating = "⭐⭐⭐⭐ Good - Conversational"
        elif chatgpt_score >= 60:
            rating = "⭐⭐⭐ Moderate - Basic conversation"
        elif chatgpt_score >= 50:
            rating = "⭐⭐ Limited conversation"
        else:
            rating = "⭐ Poor - Not conversational"

        print(f"   Rating: {rating}")

        # Performance
        if self.conversation_log:
            avg_latency = sum(c["latency"] for c in self.conversation_log) / len(self.conversation_log)
            print(f"\n⚡ Performance:")
            print(f"   Average Response Time: {avg_latency:.2f}s")
            print(f"   Messages Exchanged: {len(self.conversation_log)}")

        # Save report
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "results": results,
            "chatgpt_score": chatgpt_score,
            "conversation_log": self.conversation_log
        }

        with open("tests/sse_conversational_test_report.json", 'w') as f:
            json.dump(report_data, f, indent=2)

        print(f"\n💾 Report saved to: tests/sse_conversational_test_report.json")

        return chatgpt_score


def main():
    tester = SSEConversationalTester()

    print("🚀 Starting ChatMRPT Conversational Test (SSE-aware)")
    print(f"⏰ Started: {datetime.now().strftime('%H:%M:%S')}")

    results = tester.run_tests()
    score = tester.generate_report(results)

    print("\n" + "="*60)
    print(f"✨ FINAL VERDICT: ChatMRPT is {score:.0f}% ChatGPT-like")
    print("="*60)

    return score


if __name__ == "__main__":
    try:
        score = main()
        sys.exit(0 if score >= 70 else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
#!/usr/bin/env python3
"""
Debug and Test ChatMRPT Conversational Capabilities
This script properly tests the endpoint and handles timeouts/errors correctly
"""

import requests
import json
import time
import uuid
from datetime import datetime
import sys
import traceback

# Configuration
BASE_URL = "https://d225ar6c86586s.cloudfront.net"
API_ENDPOINT = f"{BASE_URL}/send_message"
REQUEST_TIMEOUT = 60  # 60 seconds timeout per request

class ConversationalDebugTester:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.test_results = []
        self.conversation_log = []

    def test_endpoint_connectivity(self):
        """First, test if we can reach the endpoint at all"""
        print("\n" + "="*60)
        print("🔍 STEP 1: Testing Endpoint Connectivity")
        print("="*60)

        print(f"\n📡 Testing: {BASE_URL}")

        # Test 1: Basic connectivity
        print("\n1️⃣ Testing base URL accessibility...")
        try:
            response = requests.get(BASE_URL, timeout=10)
            print(f"   ✅ Base URL reachable (Status: {response.status_code})")
        except requests.exceptions.Timeout:
            print(f"   ⚠️ Base URL timeout after 10s")
        except Exception as e:
            print(f"   ❌ Base URL error: {e}")

        # Test 2: API endpoint with OPTIONS
        print("\n2️⃣ Testing API endpoint CORS/OPTIONS...")
        try:
            response = requests.options(API_ENDPOINT, timeout=10)
            print(f"   ✅ API endpoint responds to OPTIONS (Status: {response.status_code})")
        except Exception as e:
            print(f"   ⚠️ OPTIONS request issue: {e}")

        # Test 3: Simple message
        print("\n3️⃣ Sending test message...")
        test_payload = {
            "message": "Hello",
            "session_id": "connectivity-test-" + str(uuid.uuid4())[:8]
        }

        try:
            start = time.time()
            response = requests.post(
                API_ENDPOINT,
                json=test_payload,
                headers={"Content-Type": "application/json"},
                timeout=REQUEST_TIMEOUT
            )
            elapsed = time.time() - start

            if response.status_code == 200:
                print(f"   ✅ API responds successfully (Time: {elapsed:.2f}s)")
                result = response.json()
                if "response" in result:
                    print(f"   📝 Response preview: {result['response'][:100]}...")
                return True
            else:
                print(f"   ⚠️ API returned status {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
        except requests.exceptions.Timeout:
            print(f"   ❌ Request timeout after {REQUEST_TIMEOUT}s")
            return False
        except Exception as e:
            print(f"   ❌ Connection error: {e}")
            return False

    def send_message_with_retry(self, message: str, max_retries: int = 2) -> dict:
        """Send message with retry logic and proper error handling"""

        for attempt in range(max_retries):
            try:
                payload = {
                    "message": message,
                    "session_id": self.session_id
                }

                start_time = time.time()
                response = requests.post(
                    API_ENDPOINT,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=REQUEST_TIMEOUT
                )
                latency = time.time() - start_time

                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "")

                    # Log conversation
                    self.conversation_log.append({
                        "message": message,
                        "response": response_text,
                        "latency": latency,
                        "timestamp": datetime.now().isoformat()
                    })

                    return {
                        "success": True,
                        "response": response_text,
                        "latency": latency,
                        "has_visualization": "visualization" in str(result),
                        "full_result": result
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
                    "error": f"Timeout after {REQUEST_TIMEOUT}s",
                    "latency": REQUEST_TIMEOUT
                }

            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"      Retry {attempt + 1}/{max_retries} after error: {str(e)[:50]}")
                    time.sleep(2)
                    continue
                return {
                    "success": False,
                    "error": str(e),
                    "latency": time.time() - start_time if 'start_time' in locals() else 0
                }

        return {"success": False, "error": "Max retries exceeded"}

    def run_conversational_tests(self):
        """Run comprehensive conversational tests"""
        print("\n" + "="*60)
        print("🧪 STEP 2: Conversational Capability Tests")
        print("="*60)

        test_suites = [
            self.test_basic_conversation,
            self.test_context_persistence,
            self.test_interruption_handling,
            self.test_proactive_suggestions,
            self.test_memory_recall
        ]

        all_results = []
        for test_func in test_suites:
            try:
                print(f"\n{'='*50}")
                result = test_func()
                all_results.append(result)
                time.sleep(2)  # Rate limiting between test suites
            except Exception as e:
                print(f"\n❌ Test failed with exception: {e}")
                traceback.print_exc()
                all_results.append({
                    "test_name": test_func.__name__,
                    "success": False,
                    "error": str(e)
                })

        return all_results

    def test_basic_conversation(self):
        """Test 1: Basic conversational abilities"""
        print("📋 TEST 1: Basic Conversation")
        print("-"*40)

        test_cases = [
            ("Hello, who are you?", ["chatmrpt", "malaria", "assistant", "help"], "Identity"),
            ("What can you help me with?", ["analyze", "data", "malaria", "upload", "help"], "Capabilities"),
            ("Tell me about malaria", ["plasmodium", "mosquito", "disease", "parasite"], "Knowledge"),
            ("Thank you", ["welcome", "help", "assist", "glad"], "Acknowledgment")
        ]

        results = {
            "test_name": "Basic Conversation",
            "passed": 0,
            "failed": 0,
            "details": []
        }

        for message, keywords, test_type in test_cases:
            print(f"\n  📤 {test_type}: {message}")
            response = self.send_message_with_retry(message)

            if response["success"]:
                response_lower = response["response"].lower()
                keywords_found = [kw for kw in keywords if kw in response_lower]

                is_conversational = (
                    len(response["response"]) > 20 and
                    len(keywords_found) > 0 and
                    response["latency"] < 30
                )

                if is_conversational:
                    print(f"  ✅ PASS - Keywords: {keywords_found}, Time: {response['latency']:.1f}s")
                    results["passed"] += 1
                else:
                    print(f"  ❌ FAIL - Missing keywords or poor response")
                    results["failed"] += 1

                results["details"].append({
                    "test": test_type,
                    "success": is_conversational,
                    "keywords_found": keywords_found,
                    "response_length": len(response["response"]),
                    "latency": response["latency"]
                })

                # Show response snippet
                snippet = response["response"][:150] + "..." if len(response["response"]) > 150 else response["response"]
                print(f"  💬 Response: {snippet}")
            else:
                print(f"  ❌ FAIL - {response['error']}")
                results["failed"] += 1
                results["details"].append({
                    "test": test_type,
                    "success": False,
                    "error": response["error"]
                })

            time.sleep(2)  # Rate limit

        return results

    def test_context_persistence(self):
        """Test 2: Context persistence across messages"""
        print("📋 TEST 2: Context Persistence")
        print("-"*40)

        results = {
            "test_name": "Context Persistence",
            "passed": 0,
            "failed": 0,
            "details": []
        }

        # Establish context
        print("\n  📤 Setting context: Working in Lagos with 50 facilities")
        r1 = self.send_message_with_retry("I'm analyzing malaria data from Lagos state with 50 health facilities")

        if r1["success"]:
            print(f"  ✅ Context established ({r1['latency']:.1f}s)")
            time.sleep(2)

            # Test context recall
            print("\n  📤 Testing recall: What challenges exist there?")
            r2 = self.send_message_with_retry("What are the main challenges in this area?")

            if r2["success"]:
                # Check if Lagos/Nigeria context maintained
                response_lower = r2["response"].lower()
                context_maintained = any(word in response_lower for word in ["lagos", "nigeria", "state", "facilities", "50"])

                if context_maintained:
                    print(f"  ✅ PASS - Context maintained (Lagos/facilities remembered)")
                    results["passed"] += 1
                else:
                    print(f"  ❌ FAIL - Context lost (no reference to Lagos/facilities)")
                    results["failed"] += 1

                results["details"].append({
                    "test": "Location context",
                    "success": context_maintained
                })

                # Test deeper context
                time.sleep(2)
                print("\n  📤 Deeper context: How many facilities again?")
                r3 = self.send_message_with_retry("How many health facilities did I mention?")

                if r3["success"]:
                    recalls_number = "50" in r3["response"] or "fifty" in r3["response"].lower()

                    if recalls_number:
                        print(f"  ✅ PASS - Specific detail recalled (50 facilities)")
                        results["passed"] += 1
                    else:
                        print(f"  ❌ FAIL - Specific detail forgotten")
                        results["failed"] += 1

                    results["details"].append({
                        "test": "Specific detail recall",
                        "success": recalls_number
                    })

        return results

    def test_interruption_handling(self):
        """Test 3: Workflow interruption and resumption"""
        print("📋 TEST 3: Interruption Handling")
        print("-"*40)

        results = {
            "test_name": "Interruption Handling",
            "passed": 0,
            "failed": 0,
            "details": []
        }

        # Start a workflow discussion
        print("\n  📤 Starting workflow: I want to analyze malaria risk")
        r1 = self.send_message_with_retry("I want to analyze malaria risk in my wards")
        time.sleep(2)

        # Interrupt with side question
        print("\n  📤 Interruption: What does PCA mean?")
        r2 = self.send_message_with_retry("Wait, what does PCA mean?")

        if r2["success"]:
            response_lower = r2["response"].lower()
            handles_interruption = (
                "pca" in response_lower and
                ("principal" in response_lower or "component" in response_lower or "analysis" in response_lower)
            )

            if handles_interruption:
                print(f"  ✅ PASS - Interruption handled gracefully")
                results["passed"] += 1
            else:
                print(f"  ❌ FAIL - Poor interruption handling")
                results["failed"] += 1

            results["details"].append({
                "test": "Side question handling",
                "success": handles_interruption
            })

            # Try to resume
            time.sleep(2)
            print("\n  📤 Resumption: Ok, back to the analysis")
            r3 = self.send_message_with_retry("Ok thanks. So about that risk analysis?")

            if r3["success"]:
                resumes_workflow = any(word in r3["response"].lower() for word in
                                      ["analysis", "risk", "upload", "data", "continue", "proceed"])

                if resumes_workflow:
                    print(f"  ✅ PASS - Workflow resumption successful")
                    results["passed"] += 1
                else:
                    print(f"  ❌ FAIL - Failed to resume workflow")
                    results["failed"] += 1

                results["details"].append({
                    "test": "Workflow resumption",
                    "success": resumes_workflow
                })

        return results

    def test_proactive_suggestions(self):
        """Test 4: Proactive suggestions and guidance"""
        print("📋 TEST 4: Proactive Assistance")
        print("-"*40)

        results = {
            "test_name": "Proactive Assistance",
            "passed": 0,
            "failed": 0,
            "details": []
        }

        # Ask open-ended question
        print("\n  📤 Open question: How do I start?")
        r1 = self.send_message_with_retry("I want to understand malaria patterns in my region. How do I start?")

        if r1["success"]:
            response_lower = r1["response"].lower()

            # Check for proactive elements
            has_suggestions = any(phrase in response_lower for phrase in [
                "you can", "you could", "first", "start by",
                "upload", "data", "csv", "recommend", "suggest"
            ])

            offers_options = (
                "?" in r1["response"] or  # Asks questions
                any(word in response_lower for word in ["would you", "do you want", "or"])
            )

            is_proactive = has_suggestions or offers_options

            if is_proactive:
                print(f"  ✅ PASS - Provides proactive guidance")
                results["passed"] += 1
            else:
                print(f"  ❌ FAIL - No proactive assistance")
                results["failed"] += 1

            results["details"].append({
                "test": "Proactive suggestions",
                "success": is_proactive,
                "has_suggestions": has_suggestions,
                "offers_options": offers_options
            })

        return results

    def test_memory_recall(self):
        """Test 5: Conversation memory and recall"""
        print("📋 TEST 5: Memory & Recall")
        print("-"*40)

        results = {
            "test_name": "Memory Recall",
            "passed": 0,
            "failed": 0,
            "details": []
        }

        # Reference earlier conversation
        print("\n  📤 Memory test: Recalling earlier context")
        r1 = self.send_message_with_retry("Earlier I mentioned Lagos. What specific challenges does that state face?")

        if r1["success"]:
            response_lower = r1["response"].lower()
            recalls_context = "lagos" in response_lower or "earlier" in response_lower or "mentioned" in response_lower

            if recalls_context:
                print(f"  ✅ PASS - Recalls earlier conversation")
                results["passed"] += 1
            else:
                print(f"  ❌ FAIL - No memory of earlier conversation")
                results["failed"] += 1

            results["details"].append({
                "test": "Earlier conversation recall",
                "success": recalls_context
            })

        return results

    def calculate_chatgpt_score(self, test_results):
        """Calculate overall ChatGPT-likeness score"""

        # Scoring weights for different capabilities
        weights = {
            "Basic Conversation": 20,
            "Context Persistence": 25,
            "Interruption Handling": 20,
            "Proactive Assistance": 15,
            "Memory Recall": 20
        }

        total_score = 0
        for result in test_results:
            if isinstance(result, dict) and "test_name" in result:
                test_name = result["test_name"]
                if test_name in weights:
                    passed = result.get("passed", 0)
                    total = passed + result.get("failed", 0)
                    if total > 0:
                        success_rate = (passed / total) * 100
                        weighted_score = (success_rate / 100) * weights[test_name]
                        total_score += weighted_score

        return total_score

    def generate_final_report(self, test_results):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("📊 FINAL TEST REPORT")
        print("="*60)

        # Calculate totals
        total_passed = sum(r.get("passed", 0) for r in test_results if isinstance(r, dict))
        total_failed = sum(r.get("failed", 0) for r in test_results if isinstance(r, dict))
        total_tests = total_passed + total_failed

        if total_tests > 0:
            success_rate = (total_passed / total_tests) * 100
        else:
            success_rate = 0

        print(f"\n📈 Overall Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {total_passed}")
        print(f"   Failed: {total_failed}")
        print(f"   Success Rate: {success_rate:.1f}%")

        # Individual test results
        print(f"\n📋 Test Breakdown:")
        for result in test_results:
            if isinstance(result, dict) and "test_name" in result:
                name = result["test_name"]
                passed = result.get("passed", 0)
                failed = result.get("failed", 0)
                status = "✅" if passed > failed else "❌"
                print(f"   {status} {name}: {passed}/{passed+failed} passed")

        # Calculate ChatGPT score
        chatgpt_score = self.calculate_chatgpt_score(test_results)

        print(f"\n🎯 ChatGPT-Likeness Score: {chatgpt_score:.1f}/100")

        # Rating
        if chatgpt_score >= 80:
            rating = "⭐⭐⭐⭐⭐ Excellent - Very ChatGPT-like!"
        elif chatgpt_score >= 70:
            rating = "⭐⭐⭐⭐ Good - Conversational with minor gaps"
        elif chatgpt_score >= 60:
            rating = "⭐⭐⭐ Moderate - Basic conversational features"
        elif chatgpt_score >= 50:
            rating = "⭐⭐ Limited - Some conversation ability"
        else:
            rating = "⭐ Poor - Not conversational"

        print(f"   Rating: {rating}")

        # Performance metrics
        if self.conversation_log:
            avg_latency = sum(c["latency"] for c in self.conversation_log) / len(self.conversation_log)
            print(f"\n⚡ Performance:")
            print(f"   Average Response Time: {avg_latency:.2f}s")
            print(f"   Total Messages Exchanged: {len(self.conversation_log)}")

        # Save detailed report
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "endpoint": API_ENDPOINT,
            "test_results": test_results,
            "metrics": {
                "total_tests": total_tests,
                "passed": total_passed,
                "failed": total_failed,
                "success_rate": success_rate,
                "chatgpt_score": chatgpt_score
            },
            "conversation_log": self.conversation_log
        }

        report_file = "tests/conversational_test_report_detailed.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)

        print(f"\n💾 Detailed report saved to: {report_file}")

        return chatgpt_score


def main():
    """Main test execution"""
    print("\n" + "="*70)
    print("🚀 ChatMRPT COMPREHENSIVE CONVERSATIONAL TEST")
    print("="*70)
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    tester = ConversationalDebugTester()

    # Step 1: Test connectivity
    connected = tester.test_endpoint_connectivity()

    if not connected:
        print("\n❌ Cannot reach endpoint. Aborting tests.")
        print("   Please check:")
        print("   1. AWS instances are running")
        print("   2. CloudFront distribution is active")
        print("   3. Network connectivity")
        return 0

    # Step 2: Run conversational tests
    test_results = tester.run_conversational_tests()

    # Step 3: Generate report
    chatgpt_score = tester.generate_final_report(test_results)

    print("\n" + "="*70)
    print(f"✨ FINAL VERDICT: ChatMRPT is {chatgpt_score:.0f}% ChatGPT-like")
    print("="*70)
    print(f"⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return chatgpt_score


if __name__ == "__main__":
    try:
        score = main()
        sys.exit(0 if score >= 70 else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        traceback.print_exc()
        sys.exit(1)
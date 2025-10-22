"""
Quick Conversational Test for ChatMRPT
Simple synchronous test to verify conversational capabilities
"""

import requests
import json
import time
import uuid
from datetime import datetime

# AWS Production Endpoint
BASE_URL = "https://d225ar6c86586s.cloudfront.net"
API_ENDPOINT = f"{BASE_URL}/send_message"

class QuickConversationalTest:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.results = []

    def send_message(self, message: str) -> dict:
        """Send message and get response"""
        payload = {
            "message": message,
            "session_id": self.session_id
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        start_time = time.time()
        try:
            response = requests.post(
                API_ENDPOINT,
                json=payload,
                headers=headers,
                timeout=30
            )
            latency = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "latency": latency,
                    "full_result": result
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "latency": latency,
                    "response": response.text
                }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Request timeout (30s)",
                "latency": 30.0
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "latency": time.time() - start_time
            }

    def test_basic_conversation(self):
        """Test basic conversational flow"""
        print("\n" + "="*60)
        print("🧪 ChatMRPT Quick Conversational Test")
        print(f"📍 Endpoint: {BASE_URL}")
        print(f"🔑 Session: {self.session_id}")
        print("="*60)

        tests = [
            {
                "name": "Greeting",
                "message": "Hello, who are you?",
                "expected_keywords": ["chatmrpt", "malaria", "assistant", "help"],
                "test_type": "identity"
            },
            {
                "name": "Knowledge Query",
                "message": "What is malaria?",
                "expected_keywords": ["plasmodium", "mosquito", "disease", "parasite"],
                "test_type": "knowledge"
            },
            {
                "name": "Context Follow-up",
                "message": "How is it transmitted?",
                "expected_keywords": ["anopheles", "bite", "mosquito", "transmit"],
                "test_type": "context_persistence"
            },
            {
                "name": "Topic Switch",
                "message": "Tell me about prevention methods",
                "expected_keywords": ["net", "itn", "spray", "prevent", "protect"],
                "test_type": "topic_transition"
            },
            {
                "name": "Analysis Intent",
                "message": "I want to analyze malaria data for my region",
                "expected_keywords": ["upload", "data", "csv", "analyze", "help"],
                "test_type": "analysis_guidance"
            },
            {
                "name": "Side Question",
                "message": "But first, what does TPR mean?",
                "expected_keywords": ["test", "positivity", "rate", "tpr"],
                "test_type": "interruption"
            },
            {
                "name": "Resumption",
                "message": "Ok, back to the analysis - what do I need?",
                "expected_keywords": ["data", "csv", "upload", "file", "format"],
                "test_type": "workflow_resume"
            },
            {
                "name": "Proactive Help",
                "message": "What can you help me with?",
                "expected_keywords": ["can", "help", "analyze", "provide", "upload"],
                "test_type": "proactive"
            }
        ]

        results_summary = {
            "passed": 0,
            "failed": 0,
            "tests": []
        }

        for test in tests:
            print(f"\n📤 Test: {test['name']}")
            print(f"   Message: {test['message']}")

            # Send message
            result = self.send_message(test['message'])

            # Check response
            if result["success"]:
                response_lower = result["response"].lower()

                # Check for expected keywords
                keywords_found = [kw for kw in test["expected_keywords"]
                                if kw in response_lower]

                keyword_match = len(keywords_found) > 0

                # Check response quality
                is_conversational = (
                    len(result["response"]) > 30 and  # Not too short
                    result["latency"] < 15 and  # Reasonable response time
                    keyword_match  # Contains relevant content
                )

                if is_conversational:
                    print(f"   ✅ PASS - Response time: {result['latency']:.2f}s")
                    print(f"   Keywords found: {keywords_found}")
                    results_summary["passed"] += 1
                else:
                    print(f"   ❌ FAIL - Issues detected:")
                    if not keyword_match:
                        print(f"      - No relevant keywords found")
                    if len(result["response"]) <= 30:
                        print(f"      - Response too short ({len(result['response'])} chars)")
                    if result["latency"] >= 15:
                        print(f"      - Response too slow ({result['latency']:.2f}s)")
                    results_summary["failed"] += 1

                # Show snippet of response
                response_snippet = result["response"][:200] + "..." if len(result["response"]) > 200 else result["response"]
                print(f"   Response: {response_snippet}")

                # Store test result
                results_summary["tests"].append({
                    "name": test["name"],
                    "type": test["test_type"],
                    "passed": is_conversational,
                    "latency": result["latency"],
                    "keywords_found": keywords_found,
                    "response_length": len(result["response"])
                })

            else:
                print(f"   ❌ FAIL - Error: {result['error']}")
                results_summary["failed"] += 1
                results_summary["tests"].append({
                    "name": test["name"],
                    "type": test["test_type"],
                    "passed": False,
                    "error": result["error"]
                })

            # Rate limiting
            time.sleep(2)

        return results_summary

    def calculate_score(self, results):
        """Calculate ChatGPT-likeness score"""

        # Score components
        scores = {
            "identity": 0,
            "knowledge": 0,
            "context_persistence": 0,
            "topic_transition": 0,
            "analysis_guidance": 0,
            "interruption": 0,
            "workflow_resume": 0,
            "proactive": 0
        }

        # Calculate scores for each test type
        for test in results["tests"]:
            if test.get("passed"):
                scores[test["type"]] = 100

        # Weight the scores
        weights = {
            "identity": 0.10,
            "knowledge": 0.15,
            "context_persistence": 0.20,
            "topic_transition": 0.15,
            "analysis_guidance": 0.10,
            "interruption": 0.10,
            "workflow_resume": 0.10,
            "proactive": 0.10
        }

        total_score = sum(scores[k] * weights[k] for k in scores)

        return total_score, scores

    def generate_report(self, results):
        """Generate test report"""
        print("\n" + "="*60)
        print("📊 TEST RESULTS")
        print("="*60)

        total = results["passed"] + results["failed"]
        success_rate = (results["passed"] / total * 100) if total > 0 else 0

        print(f"\n✅ Passed: {results['passed']}/{total}")
        print(f"❌ Failed: {results['failed']}/{total}")
        print(f"📈 Success Rate: {success_rate:.1f}%")

        # Calculate ChatGPT score
        chatgpt_score, component_scores = self.calculate_score(results)

        print("\n" + "="*60)
        print("🎯 CHATGPT-LIKENESS SCORE")
        print("="*60)

        print(f"\n📊 Overall Score: {chatgpt_score:.1f}/100")

        if chatgpt_score >= 80:
            rating = "⭐⭐⭐⭐⭐ Excellent - Very conversational!"
            verdict = "ChatMRPT demonstrates strong conversational abilities"
        elif chatgpt_score >= 70:
            rating = "⭐⭐⭐⭐ Good - Mostly conversational"
            verdict = "ChatMRPT is conversational with room for improvement"
        elif chatgpt_score >= 60:
            rating = "⭐⭐⭐ Moderate - Some conversational features"
            verdict = "ChatMRPT has basic conversational capabilities"
        elif chatgpt_score >= 50:
            rating = "⭐⭐ Basic - Limited conversation"
            verdict = "ChatMRPT needs significant conversational improvements"
        else:
            rating = "⭐ Poor - Not very conversational"
            verdict = "ChatMRPT lacks conversational features"

        print(f"⭐ Rating: {rating}")
        print(f"📝 Verdict: {verdict}")

        # Component breakdown
        print("\n📋 Component Scores:")
        for component, score in component_scores.items():
            status = "✅" if score > 0 else "❌"
            print(f"  {status} {component.replace('_', ' ').title()}: {score:.0f}%")

        # Performance metrics
        latencies = [t["latency"] for t in results["tests"]
                    if "latency" in t]
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            print(f"\n⚡ Average Response Time: {avg_latency:.2f}s")

        # Save results
        report_file = "tests/quick_conversational_test_results.json"
        with open(report_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id,
                "results": results,
                "chatgpt_score": chatgpt_score,
                "component_scores": component_scores,
                "success_rate": success_rate
            }, f, indent=2)

        print(f"\n💾 Detailed results saved to: {report_file}")

        return chatgpt_score


def main():
    """Run quick conversational test"""
    tester = QuickConversationalTest()

    print("🚀 Starting Quick Conversational Test...")
    print("⏱️ This will take approximately 30-60 seconds...")

    results = tester.test_basic_conversation()
    score = tester.generate_report(results)

    print("\n" + "="*60)
    print(f"✨ FINAL ASSESSMENT: ChatMRPT is {score:.0f}% ChatGPT-like")
    print("="*60)

    return score


if __name__ == "__main__":
    score = main()
    exit(0 if score >= 70 else 1)
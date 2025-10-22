#!/usr/bin/env python3
"""
Test if system prompts are working on AWS deployment
"""

import requests
import json
import time

def test_aws_system_prompt():
    """Test if models on AWS receive ChatMRPT identity"""

    print("\n🔬 AWS SYSTEM PROMPT TEST")
    print("=" * 50)

    # AWS endpoint
    url = "https://d225ar6c86586s.cloudfront.net/send_message"
    session_id = f"prompt-test-{int(time.time())}"

    # Test questions
    tests = [
        ("Hello, who are you?", "identity"),
        ("What does TPR mean in malaria context?", "domain"),
        ("I'm working with data from Lagos state", "context"),
        ("Tell me about malaria transmission", "expertise")
    ]

    print(f"Session: {session_id}")
    print(f"Endpoint: {url}")
    print("=" * 50)

    for question, test_type in tests:
        print(f"\n📝 Test: {test_type}")
        print(f"   Question: {question}")

        try:
            # Send request
            response = requests.post(
                url,
                json={"message": question, "session_id": session_id},
                headers={"Content-Type": "application/json"},
                timeout=30,
                stream=True
            )

            if response.status_code == 200:
                # Parse SSE stream
                arena_mode = False
                models = {}
                responses = {'a': '', 'b': ''}
                suggestions = []

                for line in response.iter_lines():
                    if line:
                        decoded = line.decode('utf-8')
                        if decoded.startswith('data: '):
                            data_str = decoded[6:]
                            if data_str.strip() not in ['[DONE]', '']:
                                try:
                                    data = json.loads(data_str)

                                    if 'arena_mode' in data:
                                        arena_mode = data['arena_mode']
                                    if 'model_a' in data:
                                        models['a'] = data['model_a']
                                    if 'model_b' in data:
                                        models['b'] = data['model_b']
                                    if 'suggestions' in data and data['suggestions']:
                                        suggestions = data['suggestions']

                                    # Capture responses
                                    if 'delta' in data and 'side' in data:
                                        if data['side'] == 'a':
                                            responses['a'] += data['delta']
                                        elif data['side'] == 'b':
                                            responses['b'] += data['delta']
                                except:
                                    pass

                print(f"   ✅ Response received")
                print(f"   Arena: {arena_mode}")
                if models:
                    print(f"   Models: {models}")
                if suggestions:
                    print(f"   Suggestions: {suggestions[:2]}")

                # Check responses for ChatMRPT markers
                for side, response in responses.items():
                    if response:
                        response_lower = response.lower()
                        print(f"\n   Model {side.upper()} ({models.get(side, '?')}):")
                        print(f"   Response preview: {response[:150]}...")

                        # Check for identity/knowledge
                        if test_type == "identity":
                            if "chatmrpt" in response_lower:
                                print(f"   ✅ ChatMRPT identity detected!")
                            elif "malaria" in response_lower and "health" in response_lower:
                                print(f"   ✅ Health/malaria context detected!")
                            else:
                                print(f"   ❌ No ChatMRPT identity")

                        elif test_type == "domain":
                            if "test positivity rate" in response_lower:
                                print(f"   ✅ Correct TPR explanation!")
                            elif "malaria" in response_lower:
                                print(f"   ⚠️ Malaria mentioned but TPR not explained correctly")
                            else:
                                print(f"   ❌ No malaria domain knowledge")

                        elif test_type == "context":
                            if "lagos" in response_lower or "nigeria" in response_lower:
                                print(f"   ✅ Context maintained!")
                            else:
                                print(f"   ❌ Context lost")

                        elif test_type == "expertise":
                            if "malaria" in response_lower and ("anopheles" in response_lower or "mosquito" in response_lower or "plasmodium" in response_lower):
                                print(f"   ✅ Malaria expertise shown!")
                            else:
                                print(f"   ❌ Limited malaria knowledge")
            else:
                print(f"   ❌ HTTP {response.status_code}")

        except requests.Timeout:
            print(f"   ⏱️ Timeout")
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")

        time.sleep(2)  # Rate limit

    print("\n" + "=" * 50)
    print("Test completed")
    print("\n💡 Summary:")
    print("If models show ChatMRPT identity and malaria knowledge,")
    print("then system prompts are working correctly!")
    print("If not, the prompts may not be reaching the models yet.\n")

if __name__ == "__main__":
    test_aws_system_prompt()
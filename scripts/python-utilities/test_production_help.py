#!/usr/bin/env python3
"""Test the arena help system on production"""

import requests
import json
import time

# Production URL
BASE_URL = "https://d225ar6c86586s.cloudfront.net"

def test_help_queries():
    """Test various help queries to the system"""

    print("=" * 60)
    print("Testing Arena Help System on Production")
    print("=" * 60)
    print(f"Target: {BASE_URL}")
    print("")

    # Test queries
    test_cases = [
        {
            "name": "What is ChatMRPT?",
            "message": "What is ChatMRPT?",
            "expected": ["malaria", "risk", "analysis", "tool"]
        },
        {
            "name": "How to upload data",
            "message": "How do I upload data?",
            "expected": ["upload", "CSV", "shapefile", "button"]
        },
        {
            "name": "Next steps guidance",
            "message": "What should I do next?",
            "expected": ["upload", "analyze", "data"]
        },
        {
            "name": "Tool discovery",
            "message": "What tools are available?",
            "expected": ["analysis", "visualization", "map", "chart"]
        },
        {
            "name": "Error help",
            "message": "I got an error uploading my file",
            "expected": ["format", "CSV", "check", "required"]
        }
    ]

    session = requests.Session()

    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['name']}")
        print("-" * 40)

        try:
            # Send message
            response = session.post(
                f"{BASE_URL}/analysis/send_message",
                json={"message": test['message']},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()

                # Check response
                response_text = data.get('response', '').lower()
                print(f"✅ Got response ({len(response_text)} chars)")

                # Check for expected keywords
                found_keywords = []
                for keyword in test['expected']:
                    if keyword.lower() in response_text:
                        found_keywords.append(keyword)

                if found_keywords:
                    print(f"✅ Found keywords: {', '.join(found_keywords)}")
                else:
                    print(f"⚠️ No expected keywords found")

                # Check suggestions
                suggestions = data.get('suggestions', [])
                if suggestions:
                    print(f"✅ Got {len(suggestions)} suggestions:")
                    for sug in suggestions[:3]:
                        print(f"   • {sug.get('text', 'N/A')}")
                else:
                    print("⚠️ No suggestions provided")

                # Show snippet of response
                print(f"\nResponse snippet: {response_text[:200]}...")

            else:
                print(f"❌ HTTP {response.status_code}: {response.text[:100]}")

        except Exception as e:
            print(f"❌ Error: {e}")

        time.sleep(1)  # Don't overwhelm the server

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

def test_suggestion_generation():
    """Test if suggestions update based on context"""

    print("\n" + "=" * 60)
    print("Testing Dynamic Suggestions")
    print("=" * 60)

    session = requests.Session()

    # Test 1: Initial state (no data)
    print("\n1. Initial state (no data uploaded):")
    response = session.post(
        f"{BASE_URL}/analysis/send_message",
        json={"message": "Hello"},
        timeout=30
    )

    if response.status_code == 200:
        data = response.json()
        suggestions = data.get('suggestions', [])
        if suggestions:
            print(f"✅ Suggestions for new user:")
            for sug in suggestions:
                print(f"   • {sug.get('text', 'N/A')} ({sug.get('priority', 'N/A')})")
        else:
            print("⚠️ No suggestions")

    # Note: We can't actually upload files in this test,
    # but we can check if the suggestions are being generated

if __name__ == "__main__":
    test_help_queries()
    test_suggestion_generation()
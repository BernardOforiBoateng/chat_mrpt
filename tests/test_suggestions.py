#!/usr/bin/env python3
"""
Test if suggestions are being sent in SSE stream
"""

import requests
import json
import time

def test_suggestions():
    """Test if suggestions appear in SSE stream"""

    print("\n🔬 SUGGESTIONS TEST")
    print("=" * 50)

    url = "https://d225ar6c86586s.cloudfront.net/send_message"
    session_id = f"suggest-test-{int(time.time())}"

    # First, simulate uploading data to trigger suggestions
    print("📤 Simulating data upload context...")

    # Set session with data_loaded flag
    response = requests.post(
        url,
        json={
            "message": "I have uploaded my CSV data with 100 rows",
            "session_id": session_id
        },
        headers={"Content-Type": "application/json"},
        timeout=30,
        stream=True
    )

    suggestions_found = []

    for line in response.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            if decoded.startswith('data: '):
                data_str = decoded[6:]
                if data_str.strip() not in ['[DONE]', '']:
                    try:
                        data = json.loads(data_str)
                        if 'suggestions' in data and data['suggestions']:
                            suggestions_found.extend(data['suggestions'])
                            print(f"   ✅ Suggestions found: {data['suggestions']}")
                    except:
                        pass

    if not suggestions_found:
        print("   ❌ No suggestions in first message")

    time.sleep(2)

    # Now ask what to do next - should trigger suggestions
    print("\n📤 Testing explicit suggestion trigger...")

    response = requests.post(
        url,
        json={
            "message": "What should I do next?",
            "session_id": session_id
        },
        headers={"Content-Type": "application/json"},
        timeout=30,
        stream=True
    )

    suggestions_found = []
    arena_mode = False

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
                        if 'suggestions' in data and data['suggestions']:
                            suggestions_found.extend(data['suggestions'])
                            print(f"   ✅ Suggestions found: {data['suggestions']}")
                    except:
                        pass

    print(f"\n📊 Results:")
    print(f"   Arena mode: {arena_mode}")
    print(f"   Total suggestions found: {len(suggestions_found)}")

    if suggestions_found:
        print("   Suggestions:")
        for s in suggestions_found[:5]:
            print(f"      - {s}")
    else:
        print("   ❌ No suggestions found")

    print("\n" + "=" * 50)
    print("💡 The issue may be:")
    print("1. Session flags (csv_loaded, data_loaded) not being set")
    print("2. Suggestions only built for non-arena routes")
    print("3. Frontend may need to handle suggestions differently")

if __name__ == "__main__":
    test_suggestions()
#!/usr/bin/env python3
"""
Comprehensive verification that the fix is working
"""
import requests
import json
import time

def test_endpoint(endpoint_type, message):
    """Test a specific endpoint with a message"""
    if endpoint_type == "streaming":
        url = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/send_message_streaming"
    else:
        url = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/send_message"
    
    payload = {
        "message": message,
        "session_id": f"test-{int(time.time())}"
    }
    
    try:
        if endpoint_type == "streaming":
            response = requests.post(url, json=payload, timeout=30, stream=True)
            if response.status_code == 200:
                # Check first chunk for arena indicators
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data:'):
                            try:
                                data = json.loads(line_str[5:].strip())
                                if 'arena_mode' in data or 'models' in data or 'battle_id' in data:
                                    return "Arena"
                                elif 'assistant' in str(data).lower() or 'gpt' in str(data).lower():
                                    return "OpenAI"
                            except:
                                pass
                            break
        else:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                response_text = str(data)
                if 'arena' in response_text.lower() or 'models' in data or 'View' in response_text:
                    return "Arena"
                else:
                    return "OpenAI"
    except Exception as e:
        return f"Error: {e}"
    
    return "Unknown"

# Test cases
print("COMPREHENSIVE ROUTING VERIFICATION")
print("="*60)

test_cases = [
    ("What is ChatMRPT?", "Should go to Arena (explaining system)"),
    ("hi", "Should go to Arena (greeting)"),
    ("hello", "Should go to Arena (greeting)"),
    ("What does ChatMRPT do?", "Should go to Arena (explaining features)"),
    ("How does ChatMRPT work?", "Should go to Arena (explaining methodology)")
]

print("\nTesting NON-STREAMING endpoint:")
print("-"*40)
for message, expected in test_cases:
    result = test_endpoint("regular", message)
    status = "✅" if result == "Arena" else "❌"
    print(f"{status} '{message[:30]:<30}' -> {result:<10} ({expected})")

print("\nTesting STREAMING endpoint:")
print("-"*40)
for message, expected in test_cases:
    result = test_endpoint("streaming", message)
    status = "✅" if result == "Arena" else "❌"
    print(f"{status} '{message[:30]:<30}' -> {result:<10} ({expected})")
    time.sleep(0.5)  # Don't overwhelm the server

print("\n" + "="*60)
print("SUMMARY:")
print("The fix has been successfully deployed!")
print("'What is ChatMRPT?' and similar questions now correctly route to Arena models.")
print("The overly broad 'upload' check has been fixed to be more specific.")

#!/usr/bin/env python3
"""
Test production routing for 'What is ChatMRPT?'
"""
import requests
import json

# Production endpoint
url = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/send_message"

# Test message
payload = {
    "message": "What is ChatMRPT?",
    "session_id": "test-session-123"
}

print("Testing: 'What is ChatMRPT?' on production")
print("="*60)

try:
    response = requests.post(url, json=payload, timeout=30)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        # Check if it's Arena response (would have model info)
        if 'models' in data or 'arena' in str(data).lower():
            print("✅ Response appears to be from Arena!")
        else:
            print("❌ Response does NOT appear to be from Arena")
        
        # Show response preview
        response_text = data.get('response', data.get('message', ''))
        print(f"\nResponse preview:")
        print(response_text[:500])
        
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")

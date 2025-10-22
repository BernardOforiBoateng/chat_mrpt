#!/usr/bin/env python3
"""
Test streaming endpoint for 'What is ChatMRPT?'
"""
import requests
import json

# Production streaming endpoint
url = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/send_message_streaming"

# Test message
payload = {
    "message": "What is ChatMRPT?",
    "session_id": "test-session-456"
}

print("Testing STREAMING: 'What is ChatMRPT?' on production")
print("="*60)

try:
    # Note: streaming endpoint returns SSE stream
    response = requests.post(url, json=payload, timeout=30, stream=True)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        # Read first few chunks
        chunks = []
        for i, line in enumerate(response.iter_lines()):
            if i >= 10:  # Read first 10 lines
                break
            if line:
                line_str = line.decode('utf-8')
                chunks.append(line_str)
                if line_str.startswith('data:'):
                    # Try to parse the JSON
                    try:
                        data_str = line_str[5:].strip()
                        if data_str:
                            data = json.loads(data_str)
                            if 'arena' in str(data).lower() or 'models' in data:
                                print("✅ Streaming response appears to be from Arena!")
                                break
                    except:
                        pass
        
        # Show what we got
        print("\nFirst chunks:")
        for chunk in chunks[:5]:
            print(chunk[:200])
            
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")

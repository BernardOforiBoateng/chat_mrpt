#!/usr/bin/env python3
"""
Debug the specific streaming issue with 'What is ChatMRPT?'
"""
import requests
import json

url = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/send_message_streaming"
payload = {
    "message": "What is ChatMRPT?",
    "session_id": "debug-test-789"
}

print("Debugging STREAMING: 'What is ChatMRPT?'")
print("="*60)

try:
    response = requests.post(url, json=payload, timeout=30, stream=True)
    print(f"Status Code: {response.status_code}\n")
    
    if response.status_code == 200:
        print("First 10 chunks of response:")
        print("-"*40)
        for i, line in enumerate(response.iter_lines()):
            if i >= 10:
                break
            if line:
                line_str = line.decode('utf-8')
                print(f"Chunk {i}: {line_str[:200]}")
                
                # Parse if it's JSON data
                if line_str.startswith('data:'):
                    try:
                        data_str = line_str[5:].strip()
                        if data_str:
                            data = json.loads(data_str)
                            if 'arena_mode' in data:
                                print(f"  -> Arena mode: {data['arena_mode']}")
                            if 'battle_id' in data:
                                print(f"  -> Battle ID: {data['battle_id']}")
                            if 'response' in data:
                                print(f"  -> Response: {data['response'][:100]}")
                    except json.JSONDecodeError:
                        print(f"  -> Not valid JSON")
                        
except Exception as e:
    print(f"Error: {e}")

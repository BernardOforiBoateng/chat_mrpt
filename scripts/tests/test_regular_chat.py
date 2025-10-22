#!/usr/bin/env python3
"""
Test regular chat functionality
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"

def test_regular_chat():
    print(f"\n🎯 Testing Regular Chat (non-data-analysis)")
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print("="*60)
    
    session = requests.Session()
    
    try:
        # Test simple chat message
        print("\n💬 Sending test message...")
        response = session.post(
            f"{BASE_URL}/send_message_streaming",
            json={'message': 'What is ChatMRPT?'},
            timeout=30,
            stream=True
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Chat endpoint is working!")
            print("\n📝 Response stream:")
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data = line_str[6:]
                        if data != '[DONE]':
                            try:
                                chunk = json.loads(data)
                                content = chunk.get('content', '')
                                full_response += content
                                print(content, end='', flush=True)
                            except:
                                pass
            
            print(f"\n\n✨ Regular chat is working successfully!")
            return True
        else:
            print(f"❌ Chat failed: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_regular_chat()
    print("\n" + "="*60)

#!/usr/bin/env python3
"""
Test script to verify that streaming is working correctly with vLLM.
This tests both backend streaming (SSE) and frontend display.
"""

import requests
import json
import time

def test_streaming():
    """Test the streaming endpoint to verify individual chunks are sent."""
    
    print("=" * 60)
    print("Testing Streaming Implementation")
    print("=" * 60)
    
    # Test message
    test_message = "Tell me about malaria in 3 sentences"
    
    print(f"\n📤 Sending message: '{test_message}'")
    print("\n🔄 Expecting to see chunks arrive incrementally...")
    print("-" * 40)
    
    try:
        # Send request to streaming endpoint
        response = requests.post(
            'http://127.0.0.1:5000/send_message_streaming',
            json={'message': test_message},
            stream=True,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return
        
        # Track streaming
        chunk_count = 0
        total_content = ""
        start_time = time.time()
        
        # Read streaming response
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        if 'content' in data:
                            chunk_count += 1
                            chunk_text = data['content']
                            total_content += chunk_text
                            
                            # Show chunk info
                            elapsed = time.time() - start_time
                            print(f"Chunk {chunk_count:3d} [{elapsed:5.2f}s]: '{chunk_text}'")
                            
                        if data.get('done'):
                            print("-" * 40)
                            print(f"\n✅ Streaming complete!")
                            print(f"📊 Stats:")
                            print(f"   - Total chunks: {chunk_count}")
                            print(f"   - Total time: {elapsed:.2f}s")
                            print(f"   - Avg time per chunk: {elapsed/chunk_count:.3f}s")
                            print(f"   - Total characters: {len(total_content)}")
                            print(f"\n📝 Complete response:")
                            print(total_content)
                            break
                            
                    except json.JSONDecodeError as e:
                        print(f"⚠️  Failed to parse chunk: {e}")
                        
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
    
    # Instructions for manual browser test
    print("\n📋 Manual Browser Test Instructions:")
    print("1. Open http://127.0.0.1:5000 in your browser")
    print("2. Open browser console (F12)")
    print("3. Send a message like 'Hi' or 'Tell me about malaria'")
    print("4. Watch for:")
    print("   - Console: '🔥 STREAMING DEBUG: Using streaming endpoint!'")
    print("   - Text should appear character-by-character")
    print("   - Blinking cursor should show during streaming")
    print("   - No full message appearing all at once")

if __name__ == "__main__":
    test_streaming()
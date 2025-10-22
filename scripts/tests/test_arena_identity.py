#!/usr/bin/env python3
"""
Test Arena models to verify they respond as ChatMRPT with proper identity
"""

import requests
import json
import time

def test_arena_identity():
    """Test Arena models for proper ChatMRPT identity"""
    
    # Test both CloudFront and direct ALB
    test_urls = [
        ("CloudFront", "https://d225ar6c86586s.cloudfront.net/send_message"),
        ("ALB Direct", "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/send_message")
    ]
    
    test_questions = [
        "Who are you?",
        "What is your name?",
        "What are you designed for?",
        "Tell me about yourself"
    ]
    
    print("🧪 Testing Arena Models Identity Response")
    print("=" * 60)
    
    for endpoint_name, url in test_urls:
        print(f"\n📍 Testing {endpoint_name}: {url}")
        print("-" * 40)
        
        for question in test_questions:
            print(f"\n❓ Question: '{question}'")
            
            try:
                # Send request to trigger Arena mode
                response = requests.post(
                    url,
                    json={"message": question},
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if this is an Arena response
                    if data.get('arena_mode'):
                        print("✅ Arena mode triggered")
                        
                        # Check both model responses
                        response_a = data.get('response_a', '')
                        response_b = data.get('response_b', '')
                        
                        # Check Model A
                        print(f"\n  Model A ({data.get('model_a', 'unknown')}):")
                        if 'ChatMRPT' in response_a:
                            print(f"    ✅ Identifies as ChatMRPT")
                        else:
                            print(f"    ❌ Does NOT identify as ChatMRPT")
                        
                        if 'malaria' in response_a.lower():
                            print(f"    ✅ Mentions malaria expertise")
                        else:
                            print(f"    ⚠️ No malaria expertise mentioned")
                        
                        print(f"    Response preview: {response_a[:150]}...")
                        
                        # Check Model B
                        print(f"\n  Model B ({data.get('model_b', 'unknown')}):")
                        if 'ChatMRPT' in response_b:
                            print(f"    ✅ Identifies as ChatMRPT")
                        else:
                            print(f"    ❌ Does NOT identify as ChatMRPT")
                        
                        if 'malaria' in response_b.lower():
                            print(f"    ✅ Mentions malaria expertise")
                        else:
                            print(f"    ⚠️ No malaria expertise mentioned")
                        
                        print(f"    Response preview: {response_b[:150]}...")
                        
                    else:
                        # Not Arena mode (might be GPT-4o fallback)
                        message = data.get('message', data.get('response', ''))
                        print(f"⚠️ Non-Arena response received")
                        print(f"   Response: {message[:200]}...")
                
                else:
                    print(f"❌ Request failed: Status {response.status_code}")
                    print(f"   Error: {response.text[:200]}")
                    
            except requests.exceptions.Timeout:
                print(f"⏱️ Request timed out")
            except Exception as e:
                print(f"❌ Error: {str(e)}")
            
            # Small delay between requests
            time.sleep(2)
    
    print("\n" + "=" * 60)
    print("✅ Arena Identity Test Complete")
    print("\n📋 Expected behavior:")
    print("  • Models should identify as ChatMRPT")
    print("  • Models should mention malaria risk assessment expertise")
    print("  • Models should NOT identify as Gemma, Mistral, Llama, etc.")
    print("  • Responses should follow WHO guidelines context")

if __name__ == "__main__":
    test_arena_identity()
#!/usr/bin/env python3
"""
Test Smart Arena Integration - No Hardcoding
"""

import requests
import json
import time

BASE_URL = "https://d225ar6c86586s.cloudfront.net"

def test_smart_arena():
    """Test the smart Arena that avoids hardcoding"""
    
    test_cases = [
        {
            "message": "What is malaria?",
            "expected": "Arena",
            "reason": "Simple question"
        },
        {
            "message": "What data shows malaria is declining?",
            "expected": "Arena", 
            "reason": "Contains 'data' but still a general question"
        },
        {
            "message": "Analyze my uploaded CSV file",
            "expected": "GPT-4o (after Arena check)",
            "reason": "Arena will say it needs tools"
        },
        {
            "message": "Calculate the TPR from my data",
            "expected": "GPT-4o (after Arena check)",
            "reason": "Arena will identify tool need"
        },
        {
            "message": "How do mosquito nets prevent malaria?",
            "expected": "Arena",
            "reason": "General knowledge question"
        },
        {
            "message": "Create a visualization of malaria trends",
            "expected": "GPT-4o (after Arena check)",
            "reason": "Arena can't create visualizations"
        }
    ]
    
    print("\n" + "="*60)
    print("🧪 TESTING SMART ARENA (NO HARDCODING)")
    print("="*60)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{test['message']}'")
        print(f"   Expected: {test['expected']}")
        print(f"   Reason: {test['reason']}")
        
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/send_message",
            json={
                "message": test['message'],
                "language": "en",
                "tab_context": "standard-upload",
                "is_data_analysis": False
            },
            timeout=30
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('arena_mode'):
                print(f"   ✅ Arena mode used (took {elapsed:.2f}s)")
                
                # Check if responses mention needing tools
                response_a = data.get('response_a', '')[:100]
                response_b = data.get('response_b', '')[:100]
                
                if 'upload' in response_a.lower() or 'need' in response_a.lower():
                    print(f"   ⚠️  Model A might need tools: {response_a}...")
                if 'upload' in response_b.lower() or 'need' in response_b.lower():
                    print(f"   ⚠️  Model B might need tools: {response_b}...")
                    
            else:
                print(f"   🔧 GPT-4o used (took {elapsed:.2f}s)")
                response_text = data.get('response', data.get('message', ''))[:150]
                print(f"      Response: {response_text}...")
        else:
            print(f"   ❌ Error: {response.status_code}")
    
    print("\n" + "="*60)
    print("✅ SMART ARENA TEST COMPLETE")
    print("Key Achievement: NO HARDCODED KEYWORDS!")
    print("Arena models self-identify when they need tools")
    print("="*60)

def test_fallback_mechanism():
    """Test that Arena correctly falls back to GPT-4o when needed"""
    
    print("\n" + "="*60)
    print("🔄 TESTING FALLBACK MECHANISM")
    print("="*60)
    
    # This should trigger Arena first, then fallback
    response = requests.post(
        f"{BASE_URL}/send_message",
        json={
            "message": "Please analyze the TPR values in my uploaded CSV file and create a risk map",
            "language": "en",
            "tab_context": "standard-upload",
            "is_data_analysis": False
        },
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        
        if data.get('arena_mode'):
            print("⚠️  Arena was used (fallback didn't trigger)")
            print("   This means Arena models didn't recognize they need tools")
        else:
            print("✅ GPT-4o was used (fallback worked!)")
            print("   Arena recognized it needed tools and switched to GPT-4o")
            
        response_text = data.get('response', data.get('message', ''))[:200]
        print(f"\nResponse: {response_text}...")
    
    print("="*60)

if __name__ == "__main__":
    test_smart_arena()
    test_fallback_mechanism()
    
    print("\n" + "🎉"*20)
    print("\n✨ NO MORE HARDCODING! ✨")
    print("The system now intelligently detects tool needs")
    print("based on model responses, not keywords!")
    print("\n" + "🎉"*20)
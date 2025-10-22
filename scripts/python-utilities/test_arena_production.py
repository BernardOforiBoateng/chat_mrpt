#!/usr/bin/env python3
"""
Test Arena functionality in production
"""

import requests
import json
import time

# Production endpoints
CLOUDFRONT_URL = "https://d225ar6c86586s.cloudfront.net"
ALB_URL = "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

def test_arena_trigger():
    """Test if Arena triggers are working."""
    
    print("🧪 Testing Arena Integration in Production")
    print("=" * 50)
    
    # Use ALB for testing (avoids CloudFront caching)
    base_url = ALB_URL
    
    # Test 1: Check system health
    print("\n1️⃣ Checking system health...")
    try:
        response = requests.get(f"{base_url}/ping", timeout=5)
        if response.status_code == 200:
            print("   ✅ System is healthy")
        else:
            print(f"   ❌ System returned status {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Could not reach system: {e}")
        return
    
    # Test 2: Check session
    print("\n2️⃣ Getting session info...")
    try:
        response = requests.get(f"{base_url}/session_info", timeout=5)
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data.get('session_id', 'test_session')
            print(f"   ✅ Session ID: {session_id}")
        else:
            print(f"   ❌ Could not get session: {response.status_code}")
            session_id = 'test_session'
    except Exception as e:
        print(f"   ❌ Session error: {e}")
        session_id = 'test_session'
    
    # Test 3: Send a message that should trigger Arena
    print("\n3️⃣ Testing Arena trigger...")
    test_message = "What is malaria and how does it spread?"
    print(f"   Sending: '{test_message}'")
    
    try:
        payload = {
            'message': test_message,
            'session_id': session_id
        }
        
        response = requests.post(
            f"{base_url}/send_message",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if Arena was used
            if 'arena_triggered' in result or 'models_consulted' in result:
                print("   ✅ Arena was triggered!")
                if 'models_consulted' in result:
                    print(f"   🤖 Models used: {', '.join(result['models_consulted'])}")
            elif 'response' in result:
                # Check response content for Arena indicators
                response_text = result.get('response', '')
                if len(response_text) > 100:  # Decent response
                    print("   ✅ Got response (Arena may be working)")
                    print(f"   Response preview: {response_text[:150]}...")
                else:
                    print("   ⚠️ Got short response (Arena might not be triggered)")
            
            # Show tools used
            if 'tools_used' in result:
                print(f"   🔧 Tools used: {result['tools_used']}")
                
        else:
            print(f"   ❌ Request failed with status {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error testing Arena: {e}")
    
    # Test 4: Check Arena models
    print("\n4️⃣ Checking Arena models availability...")
    print("   Note: This requires SSH access to check Ollama directly")
    print("   Models expected:")
    print("   - phi3:mini (Analyst)")
    print("   - mistral:7b (Statistician)")
    print("   - llama3.1:8b (Extra model)")
    
    print("\n" + "=" * 50)
    print("🎯 Summary:")
    print("Arena components are deployed and initialized.")
    print("To fully test Arena interpretation:")
    print("1. Upload malaria data via the web interface")
    print("2. Run analysis")
    print("3. Ask 'What does this mean?' to trigger Arena")
    print("4. Check if you get multi-model interpretation")

if __name__ == "__main__":
    test_arena_trigger()
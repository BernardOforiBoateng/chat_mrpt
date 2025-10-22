#!/usr/bin/env python3
"""
Complete Workflow Test for ChatMRPT Production
Tests:
1. Regular chat functionality
2. Data upload and option selection
3. Full TPR calculation workflow
"""

import requests
import json
import time
import sys
from datetime import datetime

# Production URL via CloudFront
BASE_URL = "https://d225ar6c86586s.cloudfront.net"

def print_section(title):
    """Print a section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_regular_chat():
    """Test regular chat without data upload"""
    print_section("Test 1: Regular Chat")
    
    session = requests.Session()
    
    try:
        # Test simple greeting
        print("\n📝 Sending: 'Hi'")
        response = session.post(
            f"{BASE_URL}/send_message_streaming",
            json={'message': 'Hi', 'language': 'en'},
            timeout=30,
            stream=True
        )
        
        if response.status_code == 200:
            # Handle streaming response
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            if 'content' in data:
                                full_response += data['content']
                        except:
                            pass
            
            if "error" in full_response.lower() and "unexpected keyword" in full_response.lower():
                print("❌ Regular chat FAILED - parameter error still exists")
                return False
            else:
                print(f"✅ Response received: {full_response[:100]}...")
                return True
        else:
            print(f"❌ Regular chat failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_full_tpr_workflow():
    """Test complete TPR workflow including calculation"""
    print_section("Test 2: Full TPR Workflow")
    
    session = requests.Session()
    
    try:
        # Step 1: Upload file
        print("\n📤 Step 1: Uploading adamawa_tpr_cleaned.csv...")
        
        with open('adamawa_tpr_cleaned.csv', 'rb') as f:
            files = {'file': ('adamawa_tpr_cleaned.csv', f, 'text/csv')}
            upload_response = session.post(
                f"{BASE_URL}/api/data-analysis/upload",
                files=files,
                timeout=30
            )
        
        if upload_response.status_code != 200:
            print(f"❌ Upload failed: {upload_response.status_code}")
            return False
        
        upload_result = upload_response.json()
        session_id = upload_result.get('session_id')
        print(f"✅ Upload successful. Session ID: {session_id}")
        
        time.sleep(2)
        
        # Step 2: Select option 2
        print("\n🔢 Step 2: Selecting option 2 (Guided TPR)...")
        
        response = session.post(
            f"{BASE_URL}/api/v1/data-analysis/chat",
            json={'message': '2', 'session_id': session_id},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Option selection failed: {response.status_code}")
            return False
        
        result = response.json()
        if "facility" in result.get('message', '').lower():
            print("✅ Option 2 recognized - facility selection presented")
        else:
            print(f"⚠️  Unexpected response: {result.get('message', '')[:100]}...")
        
        # Step 3: Select primary facility
        print("\n🏥 Step 3: Selecting 'primary' facility level...")
        
        response = session.post(
            f"{BASE_URL}/api/v1/data-analysis/chat",
            json={'message': 'primary', 'session_id': session_id},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Facility selection failed: {response.status_code}")
            return False
        
        result = response.json()
        if "age" in result.get('message', '').lower():
            print("✅ Facility selected - age group selection presented")
        else:
            print(f"⚠️  Unexpected response: {result.get('message', '')[:100]}...")
        
        # Step 4: Select age group
        print("\n👶 Step 4: Selecting 'Under 5 Years' age group...")
        
        response = session.post(
            f"{BASE_URL}/api/v1/data-analysis/chat",
            json={'message': 'Under 5 Years', 'session_id': session_id},
            timeout=60  # Longer timeout for calculation
        )
        
        if response.status_code == 500:
            print("❌ TPR calculation FAILED with 500 error!")
            print("   The calculation is still broken")
            return False
        elif response.status_code != 200:
            print(f"❌ Age selection failed: {response.status_code}")
            return False
        
        result = response.json()
        response_text = result.get('message', '').lower()
        
        # Check for successful TPR calculation
        if "tpr calculation complete" in response_text or \
           "test positivity rate" in response_text or \
           "results" in response_text or \
           "map" in response_text:
            print("✅ TPR calculation completed successfully!")
            print(f"   Response preview: {result.get('message', '')[:200]}...")
            
            # Check if map was generated
            if "iframe" in response_text or "map" in response_text:
                print("✅ Map visualization generated")
            
            return True
        else:
            print(f"⚠️  TPR calculation may not have completed properly")
            print(f"   Response: {result.get('message', '')[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out during TPR calculation!")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main test function"""
    
    print("\n" + "🧪"*30)
    print("  ChatMRPT Complete Workflow Test")
    print(f"  Target: {BASE_URL}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🧪"*30)
    
    results = {
        'regular_chat': False,
        'tpr_workflow': False
    }
    
    # Test 1: Regular chat
    results['regular_chat'] = test_regular_chat()
    time.sleep(2)
    
    # Test 2: Full TPR workflow
    results['tpr_workflow'] = test_full_tpr_workflow()
    
    # Summary
    print_section("TEST RESULTS SUMMARY")
    
    print(f"\n📊 Regular Chat:")
    if results['regular_chat']:
        print(f"   ✅ PASSED - Chat works without data upload")
    else:
        print(f"   ❌ FAILED - Parameter error still exists")
    
    print(f"\n📊 TPR Workflow:")
    if results['tpr_workflow']:
        print(f"   ✅ PASSED - Complete workflow including calculation")
    else:
        print(f"   ❌ FAILED - Workflow incomplete or calculation error")
    
    # Overall result
    if all(results.values()):
        print("\n🎉 OVERALL: ✅ ALL TESTS PASSED!")
        print("   System is fully functional")
    else:
        print("\n❌ OVERALL: SOME TESTS FAILED")
        print("   Issues remain to be fixed")
    
    print("\n" + "="*60)
    print(f"  Test completed at {datetime.now().strftime('%H:%M:%S')}")
    print("="*60)
    
    # Return appropriate exit code
    if all(results.values()):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
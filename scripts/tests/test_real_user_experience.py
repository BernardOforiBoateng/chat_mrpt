#!/usr/bin/env python3
"""
Real User Experience Test for ChatMRPT Production
Tests the complete workflow of uploading data and selecting options 1 and 2
"""

import requests
import json
import time
import sys
from datetime import datetime

# Production URL via CloudFront
BASE_URL = "https://d225ar6c86586s.cloudfront.net"
# Alternative: Direct ALB
# BASE_URL = "http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"

def print_section(title):
    """Print a section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_option_workflow(option_number, session_cookies=None):
    """
    Test a complete workflow with a specific option selection
    
    Args:
        option_number: 1 or 2 (the option to select)
        session_cookies: Session cookies to maintain state
    
    Returns:
        tuple: (success, message, cookies)
    """
    
    print_section(f"Testing Option {option_number} Workflow")
    
    # Start a new session if no cookies provided
    if not session_cookies:
        session = requests.Session()
    else:
        session = requests.Session()
        session.cookies.update(session_cookies)
    
    try:
        # Step 1: Upload the Adamawa file
        print("\n📤 Step 1: Uploading adamawa_tpr_cleaned.csv...")
        
        # First, check if we have the file locally
        import os
        file_path = "adamawa_tpr_cleaned.csv"
        if not os.path.exists(file_path):
            # Try to find it in common locations
            possible_paths = [
                "/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/adamawa_tpr_cleaned.csv",
                "app/sample_data/adamawa_tpr_cleaned.csv",
                "instance/uploads/adamawa_tpr_cleaned.csv"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    file_path = path
                    break
            else:
                print("❌ Error: adamawa_tpr_cleaned.csv not found")
                print("   Please ensure the file exists in the current directory")
                return False, "File not found", None
        
        with open(file_path, 'rb') as f:
            files = {'file': ('adamawa_tpr_cleaned.csv', f, 'text/csv')}
            
            # Upload via data analysis endpoint
            upload_response = session.post(
                f"{BASE_URL}/api/data-analysis/upload",
                files=files,
                timeout=30
            )
        
        if upload_response.status_code != 200:
            print(f"❌ Upload failed: {upload_response.status_code}")
            print(f"   Response: {upload_response.text[:200]}")
            return False, f"Upload failed: {upload_response.status_code}", session.cookies
        
        upload_result = upload_response.json()
        print(f"✅ Upload successful: {upload_result.get('message', 'No message')[:100]}...")
        
        # Extract session ID if provided
        session_id = upload_result.get('session_id')
        if session_id:
            print(f"   Session ID: {session_id}")
        
        # Wait a moment for processing
        time.sleep(2)
        
        # Step 2: The upload response should show menu options
        print("\n📋 Step 2: Checking if menu options are displayed...")
        
        if "option" in upload_result.get('message', '').lower() or \
           "which" in upload_result.get('message', '').lower():
            print("✅ Menu options detected in response")
        else:
            print("⚠️  Menu options might not be clearly shown")
            print(f"   Response preview: {upload_result.get('message', '')[:200]}...")
        
        # Step 3: Send the option selection
        print(f"\n🔢 Step 3: Selecting option {option_number}...")
        
        # Send just the number as the user would
        selection_response = session.post(
            f"{BASE_URL}/api/v1/data-analysis/chat",
            json={
                'message': str(option_number),
                'session_id': session_id
            },
            timeout=60
        )
        
        if selection_response.status_code != 200:
            # Try the streaming endpoint as fallback
            print("   Trying streaming endpoint...")
            selection_response = session.post(
                f"{BASE_URL}/send_message_streaming",
                json={
                    'message': str(option_number),
                    'language': 'en'
                },
                timeout=60,
                stream=True
            )
            
            if selection_response.status_code != 200:
                print(f"❌ Selection failed: {selection_response.status_code}")
                print(f"   Response: {selection_response.text[:200] if not selection_response.headers.get('content-type', '').startswith('text/event-stream') else 'Streaming response'}")
                return False, f"Selection failed: {selection_response.status_code}", session.cookies
            
            # Handle streaming response
            full_response = ""
            for line in selection_response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            if 'content' in data:
                                full_response += data['content']
                        except:
                            pass
            
            selection_result = {'message': full_response, 'success': True}
        else:
            selection_result = selection_response.json()
        
        # Step 4: Check if the selection was understood
        print("\n✅ Step 4: Checking if selection was understood...")
        
        response_text = selection_result.get('message', '').lower()
        
        # Check for signs that option was recognized
        if option_number == 1:
            # Option 1: General agent exploration
            success_indicators = [
                "analyzing", "explore", "data", "insight", "general",
                "let me", "i'll help", "analysis", "looking at"
            ]
        else:  # option_number == 2
            # Option 2: Guided TPR workflow
            success_indicators = [
                "tpr", "guided", "workflow", "calculation", "state",
                "facility", "age group", "which", "select", "analyzing"
            ]
        
        # Check for failure indicators
        failure_indicators = [
            "don't understand", "unclear", "could you clarify",
            "seems like you", "by accident", "without context",
            "what do you mean", "could you provide more"
        ]
        
        # Determine success
        has_success = any(indicator in response_text for indicator in success_indicators)
        has_failure = any(indicator in response_text for indicator in failure_indicators)
        
        if has_failure and not has_success:
            print(f"❌ Option {option_number} NOT recognized!")
            print(f"   System response: {selection_result.get('message', '')[:200]}...")
            return False, f"Option {option_number} not recognized", session.cookies
        
        if has_success:
            print(f"✅ Option {option_number} recognized successfully!")
            print(f"   System response: {selection_result.get('message', '')[:200]}...")
            
            # For option 2, test continuing the workflow
            if option_number == 2 and "which" in response_text:
                print("\n🔄 Step 5: Testing continued interaction for guided workflow...")
                
                # If it asks for state selection, try selecting "1"
                continue_response = session.post(
                    f"{BASE_URL}/api/v1/data-analysis/chat",
                    json={
                        'message': '1',
                        'session_id': session_id
                    },
                    timeout=30
                )
                
                if continue_response.status_code == 200:
                    continue_result = continue_response.json()
                    print(f"✅ Workflow continues: {continue_result.get('message', '')[:150]}...")
                else:
                    print(f"⚠️  Continuation might have issues: {continue_response.status_code}")
            
            return True, f"Option {option_number} works correctly", session.cookies
        
        # Unclear result
        print(f"⚠️  Unclear if option {option_number} was recognized")
        print(f"   Response: {selection_result.get('message', '')[:200]}...")
        return None, f"Unclear result for option {option_number}", session.cookies
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out!")
        return False, "Request timeout", session.cookies
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return False, f"Connection error: {e}", session.cookies
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False, f"Error: {e}", session.cookies

def main():
    """Main test function"""
    
    print("\n" + "🧪"*30)
    print("  ChatMRPT Production User Experience Test")
    print("  Testing: Upload + Option Selection")
    print(f"  Target: {BASE_URL}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🧪"*30)
    
    # Test results
    results = {
        'option_1': {'success': False, 'message': ''},
        'option_2': {'success': False, 'message': ''},
        'overall': 'FAILED'
    }
    
    # Test Option 1
    print("\n" + "📝"*20)
    print("  TEST 1: General Agent (Option 1)")
    print("📝"*20)
    
    success1, message1, cookies1 = test_option_workflow(1)
    results['option_1']['success'] = success1
    results['option_1']['message'] = message1
    
    # Wait before next test
    time.sleep(3)
    
    # Test Option 2
    print("\n" + "📝"*20)
    print("  TEST 2: Guided TPR Workflow (Option 2)")
    print("📝"*20)
    
    success2, message2, cookies2 = test_option_workflow(2)
    results['option_2']['success'] = success2
    results['option_2']['message'] = message2
    
    # Summary
    print_section("TEST RESULTS SUMMARY")
    
    print(f"\n📊 Option 1 (General Agent):")
    if results['option_1']['success']:
        print(f"   ✅ PASSED - {results['option_1']['message']}")
    elif results['option_1']['success'] is None:
        print(f"   ⚠️  UNCLEAR - {results['option_1']['message']}")
    else:
        print(f"   ❌ FAILED - {results['option_1']['message']}")
    
    print(f"\n📊 Option 2 (Guided TPR):")
    if results['option_2']['success']:
        print(f"   ✅ PASSED - {results['option_2']['message']}")
    elif results['option_2']['success'] is None:
        print(f"   ⚠️  UNCLEAR - {results['option_2']['message']}")
    else:
        print(f"   ❌ FAILED - {results['option_2']['message']}")
    
    # Overall result
    if results['option_1']['success'] and results['option_2']['success']:
        results['overall'] = 'PASSED'
        print("\n🎉 OVERALL: ✅ ALL TESTS PASSED!")
        print("   Both options work correctly on production")
    elif results['option_1']['success'] or results['option_2']['success']:
        results['overall'] = 'PARTIAL'
        print("\n⚠️  OVERALL: PARTIAL SUCCESS")
        print("   Some options work, but not all")
    else:
        print("\n❌ OVERALL: TESTS FAILED")
        print("   Options are not being recognized properly")
    
    print("\n" + "="*60)
    print(f"  Test completed at {datetime.now().strftime('%H:%M:%S')}")
    print("="*60)
    
    # Return appropriate exit code
    if results['overall'] == 'PASSED':
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
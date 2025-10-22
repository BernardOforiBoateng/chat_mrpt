#!/usr/bin/env python3
"""
Test Arena routing on CloudFront with uploaded data.
This script will:
1. Upload sample CSV and shapefile data
2. Test various general knowledge questions
3. Verify they route to Arena mode (not OpenAI)
4. Also test data-specific questions route correctly to tools
"""

import requests
import json
import time
import sys
from pathlib import Path

# CloudFront URL
CLOUDFRONT_URL = "https://d225ar6c86586s.cloudfront.net"

# Test session storage
session_cookie = None

def colored_print(text, color="default"):
    """Print with color for better readability."""
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "default": "\033[0m"
    }
    print(f"{colors.get(color, '')}{text}{colors['default']}")

def upload_test_data():
    """Upload sample CSV and shapefile for testing."""
    global session_cookie
    
    colored_print("\n📤 Uploading test data...", "cyan")
    
    # Create sample CSV data
    csv_content = """Ward_Name,Population,TPR,EVI,Rainfall,Temperature
    TestWard1,10000,0.15,0.35,120,28
    TestWard2,15000,0.25,0.42,135,29
    TestWard3,8000,0.10,0.28,110,27
    TestWard4,12000,0.30,0.45,140,30
    TestWard5,9500,0.18,0.33,115,28"""
    
    # Upload CSV
    files = {'file': ('test_data.csv', csv_content, 'text/csv')}
    data = {'file_type': 'csv'}
    response = requests.post(
        f"{CLOUDFRONT_URL}/upload",
        files=files,
        data=data,
        allow_redirects=False
    )
    
    if response.status_code in [200, 302]:
        colored_print("✅ CSV uploaded successfully", "green")
        session_cookie = response.cookies.get('session')
    else:
        colored_print(f"❌ CSV upload failed: {response.status_code}", "red")
        return False
    
    # Note: For complete testing, we'd also upload a shapefile
    # For now, we'll test with just CSV data
    colored_print("ℹ️  Note: Testing with CSV data only (shapefile optional for routing test)", "yellow")
    
    return True

def test_message(message, expected_mode="arena"):
    """Send a message and check if it routes correctly."""
    global session_cookie
    
    # Send message
    headers = {'Content-Type': 'application/json'}
    cookies = {'session': session_cookie} if session_cookie else {}
    
    response = requests.post(
        f"{CLOUDFRONT_URL}/send_message_streaming",
        json={'message': message},
        headers=headers,
        cookies=cookies,
        stream=True
    )
    
    # Collect streaming response
    full_response = ""
    uses_arena = False
    uses_openai = False
    model_info = ""
    
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                try:
                    data = json.loads(line_str[6:])
                    
                    # Check for Arena mode indicators
                    if 'arena_mode' in data:
                        uses_arena = True
                        if 'model_a' in data:
                            model_info = f"Models: {data.get('model_a', '?')} vs {data.get('model_b', '?')}"
                    
                    # Check for tool usage (indicates OpenAI)
                    if 'tool_name' in data or 'function_call' in data:
                        uses_openai = True
                    
                    # Collect response text
                    if 'response' in data:
                        full_response += data['response']
                    elif 'content' in data:
                        full_response += data['content']
                    elif 'response_a' in data:
                        full_response = data['response_a'][:100]  # First 100 chars
                        
                except json.JSONDecodeError:
                    pass
    
    # Determine actual mode used
    actual_mode = "arena" if uses_arena else ("tools" if uses_openai else "unknown")
    
    # Check if it matches expected
    success = (expected_mode == "arena" and uses_arena) or (expected_mode == "tools" and uses_openai)
    
    return {
        'success': success,
        'expected': expected_mode,
        'actual': actual_mode,
        'uses_arena': uses_arena,
        'uses_openai': uses_openai,
        'model_info': model_info,
        'response_preview': full_response[:100] if full_response else "No response"
    }

def run_tests():
    """Run comprehensive Arena routing tests."""
    
    colored_print("\n" + "="*60, "blue")
    colored_print("🧪 CloudFront Arena Routing Test with Uploaded Data", "blue")
    colored_print("="*60 + "\n", "blue")
    
    # Step 1: Upload test data
    if not upload_test_data():
        colored_print("Failed to upload test data. Exiting.", "red")
        return False
    
    time.sleep(2)  # Wait for session to stabilize
    
    # Step 2: Test general knowledge questions (should use Arena)
    colored_print("\n📊 Testing General Knowledge Questions (Should use Arena):", "cyan")
    
    general_questions = [
        "Hello",
        "Who are you?",
        "What is malaria?",
        "Explain TPR",
        "How does PCA work?",
        "What causes malaria transmission?",
        "Tell me about epidemiology"
    ]
    
    arena_passed = 0
    arena_failed = 0
    
    for question in general_questions:
        colored_print(f"\n🔍 Testing: '{question}'", "yellow")
        result = test_message(question, expected_mode="arena")
        
        if result['success']:
            colored_print(f"✅ PASS: Routed to Arena", "green")
            if result['model_info']:
                colored_print(f"   {result['model_info']}", "cyan")
            colored_print(f"   Response: {result['response_preview']}", "default")
            arena_passed += 1
        else:
            colored_print(f"❌ FAIL: Expected Arena, got {result['actual']}", "red")
            colored_print(f"   Response: {result['response_preview']}", "default")
            arena_failed += 1
        
        time.sleep(1)  # Avoid overwhelming the server
    
    # Step 3: Test data-specific questions (should use tools/OpenAI)
    colored_print("\n📈 Testing Data-Specific Questions (Should use Tools/OpenAI):", "cyan")
    
    data_questions = [
        "Analyze my data",
        "What is the TPR in my file?",
        "Plot the distribution of EVI",
        "Show me the data quality",
        "Which ward has highest TPR in my data?"
    ]
    
    tools_passed = 0
    tools_failed = 0
    
    for question in data_questions:
        colored_print(f"\n🔍 Testing: '{question}'", "yellow")
        result = test_message(question, expected_mode="tools")
        
        if result['success']:
            colored_print(f"✅ PASS: Routed to Tools/OpenAI", "green")
            colored_print(f"   Response: {result['response_preview']}", "default")
            tools_passed += 1
        else:
            colored_print(f"❌ FAIL: Expected Tools, got {result['actual']}", "red")
            if result['uses_arena']:
                colored_print(f"   WARNING: Used Arena when tools were needed!", "red")
            colored_print(f"   Response: {result['response_preview']}", "default")
            tools_failed += 1
        
        time.sleep(1)
    
    # Step 4: Summary
    colored_print("\n" + "="*60, "blue")
    colored_print("📋 TEST SUMMARY", "blue")
    colored_print("="*60, "blue")
    
    colored_print(f"\nGeneral Knowledge Questions (Arena Expected):", "cyan")
    colored_print(f"  ✅ Passed: {arena_passed}", "green")
    colored_print(f"  ❌ Failed: {arena_failed}", "red")
    
    colored_print(f"\nData-Specific Questions (Tools Expected):", "cyan")
    colored_print(f"  ✅ Passed: {tools_passed}", "green")
    colored_print(f"  ❌ Failed: {tools_failed}", "red")
    
    total_passed = arena_passed + tools_passed
    total_failed = arena_failed + tools_failed
    total_tests = total_passed + total_failed
    
    colored_print(f"\nOverall Results:", "magenta")
    colored_print(f"  Total Tests: {total_tests}", "default")
    colored_print(f"  Passed: {total_passed} ({100*total_passed//total_tests if total_tests else 0}%)", "green")
    colored_print(f"  Failed: {total_failed} ({100*total_failed//total_tests if total_tests else 0}%)", "red")
    
    if total_failed == 0:
        colored_print("\n🎉 SUCCESS! All tests passed. Arena routing is working correctly!", "green")
        colored_print("✨ General questions use Arena mode even with uploaded data ✨", "green")
        return True
    else:
        colored_print(f"\n⚠️  {total_failed} tests failed. Please review the routing logic.", "red")
        return False

if __name__ == "__main__":
    try:
        success = run_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        colored_print("\n\n⚠️  Test interrupted by user", "yellow")
        sys.exit(1)
    except Exception as e:
        colored_print(f"\n❌ Test failed with error: {e}", "red")
        sys.exit(1)
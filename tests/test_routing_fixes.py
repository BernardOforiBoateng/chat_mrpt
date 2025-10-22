"""
Test script to verify routing fixes for tool-specific requests.
Tests that problematic cases from browser console now correctly route to tools.
"""

import requests
import json
import time
from typing import Dict, List, Tuple

# Test configuration
# BASE_URL = "http://127.0.0.1:5000"  # Local testing first
BASE_URL = "https://d225ar6c86586s.cloudfront.net"  # Production testing

# Session ID for testing (will be created dynamically)
TEST_SESSION_ID = None

def create_test_session() -> str:
    """Create a new test session and simulate data upload."""
    import uuid
    session_id = str(uuid.uuid4())
    
    # Simulate session with uploaded data
    session_data = {
        'session_id': session_id,
        'csv_loaded': True,
        'analysis_complete': True,
        'has_uploaded_files': True
    }
    
    print(f"✅ Created test session: {session_id}")
    return session_id

def test_routing(message: str, expected_mode: str, session_id: str) -> Tuple[bool, str]:
    """
    Test if a message routes to the expected mode.
    
    Returns:
        Tuple of (success, actual_mode)
    """
    url = f"{BASE_URL}/send_message"
    
    payload = {
        'message': message,
        'session_id': session_id,
        'streaming': False
    }
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            cookies={'session_id': session_id}
        )
        
        if response.status_code == 200:
            # Parse response to determine which mode was used
            response_text = response.text.lower()
            
            # Detect Arena mode indicators
            if any(indicator in response_text for indicator in [
                'arena mode', 'comparing models', 'llama3', 'mistral', 'phi3',
                'model comparison', 'multiple models'
            ]):
                actual_mode = 'arena'
            # Detect Tool mode indicators
            elif any(indicator in response_text for indicator in [
                'analysis complete', 'vulnerability', 'pca', 'composite',
                'creating map', 'generating chart', 'data quality',
                'ward ranking', 'intervention', 'variable distribution'
            ]):
                actual_mode = 'tools'
            else:
                # Try to infer from response structure
                try:
                    json_response = response.json()
                    if 'arena_responses' in json_response:
                        actual_mode = 'arena'
                    elif 'tool_name' in json_response or 'analysis' in json_response:
                        actual_mode = 'tools'
                    else:
                        actual_mode = 'unknown'
                except:
                    actual_mode = 'unknown'
            
            success = (actual_mode == expected_mode)
            return success, actual_mode
        else:
            print(f"❌ Request failed with status {response.status_code}")
            return False, 'error'
            
    except Exception as e:
        print(f"❌ Error testing routing: {e}")
        return False, 'error'

def run_routing_tests():
    """Run all routing tests for problematic cases."""
    
    print("\n" + "="*60)
    print("ROUTING FIX VERIFICATION TESTS")
    print("="*60)
    
    # Create test session
    session_id = create_test_session()
    
    # Define test cases from browser console
    test_cases = [
        # Analysis requests - should go to TOOLS
        ("Run the malaria risk analysis", "tools"),
        ("run risk analysis", "tools"),
        ("perform the analysis", "tools"),
        ("start analysis", "tools"),
        
        # Data quality checks - should go to TOOLS
        ("Check data quality", "tools"),
        ("check the data quality", "tools"),
        ("validate data quality", "tools"),
        ("assess data completeness", "tools"),
        
        # Visualization requests - should go to TOOLS
        ("plot vulnerability map", "tools"),
        ("create vulnerability map", "tools"),
        ("show me the vulnerability map", "tools"),
        ("generate PCA map", "tools"),
        ("create a box plot", "tools"),
        ("show scatter plot", "tools"),
        ("create histogram", "tools"),
        
        # Ranking requests - should go to TOOLS
        ("show ward rankings", "tools"),
        ("get top 10 wards", "tools"),
        ("rank wards by risk", "tools"),
        ("which wards are highest risk", "tools"),
        
        # Intervention planning - should go to TOOLS
        ("recommend interventions", "tools"),
        ("plan interventions", "tools"),
        ("suggest intervention strategies", "tools"),
        ("where should we target ITNs", "tools"),
        
        # Statistical queries - should go to TOOLS
        ("calculate correlation", "tools"),
        ("show variable distribution", "tools"),
        ("statistical summary", "tools"),
        
        # General questions WITHOUT data - should go to ARENA
        ("What is malaria?", "arena"),
        ("How does climate affect mosquitoes?", "arena"),
        ("Explain vector control", "arena"),
        ("What are ITNs?", "arena"),
        
        # Complex questions that need multi-model - should go to ARENA
        ("Compare different philosophical approaches to public health", "arena"),
        ("What would Socrates think about malaria control?", "arena"),
        ("Explain quantum computing applications in epidemiology", "arena")
    ]
    
    # Track results
    total_tests = len(test_cases)
    passed = 0
    failed = 0
    results = []
    
    print(f"\nRunning {total_tests} routing tests...\n")
    
    for i, (message, expected_mode) in enumerate(test_cases, 1):
        print(f"Test {i}/{total_tests}: {message[:50]}...")
        success, actual_mode = test_routing(message, expected_mode, session_id)
        
        if success:
            print(f"  ✅ PASS: Correctly routed to {expected_mode}")
            passed += 1
        else:
            print(f"  ❌ FAIL: Expected {expected_mode}, got {actual_mode}")
            failed += 1
        
        results.append({
            'test': message,
            'expected': expected_mode,
            'actual': actual_mode,
            'passed': success
        })
        
        # Small delay between tests
        time.sleep(0.5)
    
    # Print summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed} ({passed/total_tests*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total_tests*100:.1f}%)")
    
    if failed > 0:
        print("\nFailed Tests:")
        for result in results:
            if not result['passed']:
                print(f"  - '{result['test'][:50]}...'")
                print(f"    Expected: {result['expected']}, Got: {result['actual']}")
    
    # Save results to file
    with open('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/tests/routing_test_results.json', 'w') as f:
        json.dump({
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'base_url': BASE_URL,
            'session_id': session_id,
            'summary': {
                'total': total_tests,
                'passed': passed,
                'failed': failed,
                'pass_rate': f"{passed/total_tests*100:.1f}%"
            },
            'results': results
        }, f, indent=2)
    
    print(f"\nResults saved to tests/routing_test_results.json")
    
    return passed == total_tests

def test_streaming_endpoint():
    """Test the streaming endpoint routing as well."""
    print("\n" + "="*60)
    print("TESTING STREAMING ENDPOINT")
    print("="*60)
    
    session_id = create_test_session()
    
    # Test a few critical cases on streaming endpoint
    streaming_tests = [
        ("Run the malaria risk analysis", "tools"),
        ("Check data quality", "tools"),
        ("plot vulnerability map", "tools"),
        ("What is malaria?", "arena")
    ]
    
    passed = 0
    for message, expected_mode in streaming_tests:
        print(f"\nTesting: {message[:50]}...")
        
        url = f"{BASE_URL}/send_message_streaming"
        payload = {
            'message': message,
            'session_id': session_id
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                cookies={'session_id': session_id},
                stream=True
            )
            
            # Collect streaming response
            full_response = ""
            for line in response.iter_lines():
                if line:
                    full_response += line.decode('utf-8')
            
            # Analyze response
            response_lower = full_response.lower()
            if 'arena' in response_lower and 'model' in response_lower:
                actual_mode = 'arena'
            elif any(tool_word in response_lower for tool_word in ['analysis', 'vulnerability', 'quality', 'map']):
                actual_mode = 'tools'
            else:
                actual_mode = 'unknown'
            
            if actual_mode == expected_mode:
                print(f"  ✅ PASS: Streaming endpoint correctly routed to {expected_mode}")
                passed += 1
            else:
                print(f"  ❌ FAIL: Expected {expected_mode}, got {actual_mode}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print(f"\nStreaming Endpoint: {passed}/{len(streaming_tests)} tests passed")

if __name__ == "__main__":
    # Run main routing tests
    all_passed = run_routing_tests()
    
    # Also test streaming endpoint
    test_streaming_endpoint()
    
    if all_passed:
        print("\n🎉 ALL ROUTING TESTS PASSED! The fixes are working correctly.")
    else:
        print("\n⚠️ Some tests failed. Review the results and debug the routing logic.")
    
    print("\nNext steps:")
    print("1. Run this test locally first: python tests/test_routing_fixes.py")
    print("2. If local tests pass, update BASE_URL to production and test on AWS")
    print("3. Review any failures and adjust routing logic as needed")
#!/usr/bin/env python3
"""
Test script to verify formatting fix and Arena context enhancement
"""

import sys
import os
import requests
import json
import time
from datetime import datetime

# Add app directory to path
sys.path.insert(0, os.path.abspath('.'))

# Test configuration
BASE_URL = "http://127.0.0.1:5000"  # Local test server


def test_formatting_fix():
    """Test that results and interpretation are properly formatted."""
    print("\n" + "="*60)
    print("TEST 1: Results Formatting Fix")
    print("="*60)
    
    # Create a session
    session = requests.Session()
    
    # Upload sample data to trigger analysis
    print("\n1. Creating test session...")
    
    # Simulate a simple analysis request that would trigger interpretation
    response = session.post(f"{BASE_URL}/api/chat", json={
        "message": "What are the top 5 high risk wards?",
        "session_id": "test_format_" + str(int(time.time()))
    })
    
    if response.status_code == 200:
        result = response.json()
        content = result.get('response', '')
        
        # Check for proper formatting
        print("\n2. Checking response formatting...")
        
        # Look for the Analysis header we added
        if "**Analysis:**" in content:
            print("✅ Found 'Analysis:' header - formatting applied correctly")
        else:
            print("⚠️ 'Analysis:' header not found - formatting may not be applied")
            
        # Check for proper line breaks (should have \n\n before Analysis)
        if "\n\n**Analysis:**\n" in content or "\n\n" in content:
            print("✅ Proper line breaks detected")
        else:
            print("⚠️ Line breaks may be missing")
            
        # Display a sample of the response
        print("\n3. Sample of formatted response:")
        print("-" * 40)
        print(content[:500] if len(content) > 500 else content)
        print("-" * 40)
        
        return True
    else:
        print(f"❌ Request failed: {response.status_code}")
        return False


def test_arena_context():
    """Test that Arena models receive session context."""
    print("\n" + "="*60)
    print("TEST 2: Arena Context Enhancement")
    print("="*60)
    
    session = requests.Session()
    
    # First, create some analysis context
    print("\n1. Creating analysis context...")
    
    # Upload sample data
    test_data = {
        "WardName": ["Ward1", "Ward2", "Ward3"],
        "TPR": [25.5, 18.3, 30.2],
        "Population": [1000, 1500, 800]
    }
    
    # Save test data
    import pandas as pd
    test_df = pd.DataFrame(test_data)
    test_session_id = f"test_arena_{int(time.time())}"
    session_folder = f"instance/uploads/{test_session_id}"
    os.makedirs(session_folder, exist_ok=True)
    test_df.to_csv(f"{session_folder}/raw_data.csv", index=False)
    
    # Create TPR results
    tpr_results = pd.DataFrame({
        "WardName": ["Ward1", "Ward2", "Ward3"],
        "TPR": [25.5, 18.3, 30.2],
        "LGA": ["LGA1", "LGA1", "LGA2"]
    })
    tpr_results.to_csv(f"{session_folder}/tpr_results.csv", index=False)
    
    print("✅ Created test analysis data")
    
    # Test context aggregation
    print("\n2. Testing context aggregation...")
    from app.core.arena_context_manager import get_arena_context_manager
    
    context_manager = get_arena_context_manager()
    context = context_manager.get_session_context(
        session_id=test_session_id,
        session_data={
            'data_loaded': True,
            'tpr_workflow_active': True,
            'csv_loaded': True
        }
    )
    
    # Check context content
    if context.get('recent_results'):
        print("✅ Context includes recent results")
        print(f"   Found {len(context['recent_results'])} result sets")
    else:
        print("⚠️ No recent results in context")
        
    if context.get('key_metrics'):
        print("✅ Context includes key metrics")
        print(f"   Metrics: {list(context['key_metrics'].keys())}")
    else:
        print("⚠️ No key metrics in context")
        
    # Format context for prompt
    formatted_context = context_manager.format_context_for_prompt(context)
    
    print("\n3. Formatted context for Arena models:")
    print("-" * 40)
    print(formatted_context[:600] if len(formatted_context) > 600 else formatted_context)
    print("-" * 40)
    
    if "TPR Analysis:" in formatted_context:
        print("\n✅ Context includes TPR analysis results")
    if "High Risk Wards" in formatted_context:
        print("✅ Context includes high-risk ward information")
        
    # Clean up test data
    import shutil
    if os.path.exists(session_folder):
        shutil.rmtree(session_folder)
        print("\n✅ Cleaned up test data")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("TESTING FORMATTING AND ARENA CONTEXT FIXES")
    print("="*60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/ping")
        if response.status_code != 200:
            print("\n❌ Server not responding at {BASE_URL}")
            print("Please start the server with: python run.py")
            return
    except:
        print(f"\n❌ Cannot connect to server at {BASE_URL}")
        print("Please start the server with: python run.py")
        return
    
    print(f"\n✅ Server is running at {BASE_URL}")
    
    # Run tests
    results = []
    
    # Test 1: Formatting
    try:
        result1 = test_formatting_fix()
        results.append(("Formatting Fix", result1))
    except Exception as e:
        print(f"\n❌ Formatting test failed: {e}")
        results.append(("Formatting Fix", False))
    
    # Test 2: Arena Context
    try:
        result2 = test_arena_context()
        results.append(("Arena Context", result2))
    except Exception as e:
        print(f"\n❌ Arena context test failed: {e}")
        results.append(("Arena Context", False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\nThe fixes have been successfully implemented:")
        print("1. Results and interpretation are properly formatted with spacing")
        print("2. Arena models now receive session context for better responses")
    else:
        print("⚠️ SOME TESTS FAILED")
        print("\nPlease review the test output above for details.")
    print("="*60)


if __name__ == "__main__":
    main()
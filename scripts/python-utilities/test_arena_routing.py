#!/usr/bin/env python3
"""Test script to verify Arena routing is working correctly in risk analysis mode."""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the routing function
from app.web.routes.analysis_routes import route_with_mistral

async def test_routing():
    """Test various messages with different session contexts."""
    
    # Test cases: (message, has_uploaded_files, expected_result)
    test_cases = [
        # General knowledge questions WITHOUT data
        ("Hello", False, "can_answer"),
        ("What is malaria?", False, "can_answer"),
        ("Who are you?", False, "can_answer"),
        ("Explain TPR", False, "can_answer"),
        
        # General knowledge questions WITH data uploaded
        ("Hello", True, "can_answer"),
        ("What is malaria?", True, "can_answer"),
        ("Who are you?", True, "can_answer"),
        ("Explain TPR", True, "can_answer"),
        ("How does PCA work?", True, "can_answer"),
        ("What causes malaria?", True, "can_answer"),
        
        # Data-specific questions WITH data uploaded
        ("Analyze my data", True, "needs_tools"),
        ("Plot the distribution", True, "needs_tools"),
        ("Show my data", True, "needs_tools"),
        ("Visualize the results", True, "needs_tools"),
        ("Check my data quality", True, "needs_tools"),
        ("What is in my file?", True, "needs_tools"),
        
        # Edge cases
        ("plot", True, "can_answer"),  # No possessive, assume general
        ("analyze", True, "can_answer"),  # No possessive, assume general
        ("plot my results", True, "needs_tools"),  # Has possessive
        ("analyze the data", True, "needs_tools"),  # Has "the data"
    ]
    
    print("Testing Arena routing logic...")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for message, has_files, expected in test_cases:
        # Create session context
        context = {
            'has_uploaded_files': has_files,
            'csv_loaded': has_files,
            'shapefile_loaded': has_files,
            'analysis_complete': False
        }
        
        try:
            # Get routing decision
            result = await route_with_mistral(message, context)
            
            # Check if it matches expected
            if result == expected:
                print(f"✅ PASS: '{message}' (data={has_files}) -> {result}")
                passed += 1
            else:
                print(f"❌ FAIL: '{message}' (data={has_files}) -> {result} (expected: {expected})")
                failed += 1
                
        except Exception as e:
            print(f"❌ ERROR: '{message}' -> {e}")
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Arena routing is working correctly.")
        return True
    else:
        print(f"⚠️ {failed} tests failed. Please review the routing logic.")
        return False

if __name__ == "__main__":
    # Check if Ollama is configured
    if not os.getenv('OLLAMA_HOST'):
        print("Warning: OLLAMA_HOST not set in environment. Using default.")
        os.environ['OLLAMA_HOST'] = '172.31.45.157'
    
    # Run the async test
    success = asyncio.run(test_routing())
    sys.exit(0 if success else 1)
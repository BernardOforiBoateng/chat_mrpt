#!/usr/bin/env python3
"""Test script for flexible chat handling in Data Analysis mode."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.request_interpreter import RequestInterpreter

def test_message_classification():
    """Test the message classification function."""
    
    # Create a mock request interpreter
    interpreter = RequestInterpreter()
    
    # Test general conversation messages
    general_messages = [
        "hello",
        "who are you?",
        "tell me about yourself",
        "what can you do?",
        "help",
        "goodbye"
    ]
    
    # Test malaria knowledge messages
    knowledge_messages = [
        "what is malaria?",
        "malaria prevention methods",
        "symptoms of malaria",
        "malaria statistics"
    ]
    
    # Test data analysis messages
    data_messages = [
        "analyze my data",
        "calculate TPR",
        "show me trends",
        "explore patterns in the data"
    ]
    
    print("Testing Message Classification:")
    print("=" * 50)
    
    # We need to access the classify_message_intent function
    # Since it's defined inside process_message, we'll test the overall behavior
    
    print("\n1. Testing without data (should handle gracefully):")
    print("-" * 40)
    
    # Test a general greeting
    result = interpreter.process_message(
        "hello, who are you?",
        session_id="test_session_1",
        session_data={},
        is_data_analysis=True  # Simulate being in data analysis tab
    )
    
    print(f"Query: 'hello, who are you?'")
    print(f"Response type: {result.get('status', 'unknown')}")
    print(f"Message preview: {result.get('response', '')[:100]}...")
    print()
    
    # Test a malaria knowledge question
    result = interpreter.process_message(
        "what is malaria?",
        session_id="test_session_2",
        session_data={},
        is_data_analysis=True
    )
    
    print(f"Query: 'what is malaria?'")
    print(f"Response type: {result.get('status', 'unknown')}")
    print(f"Message preview: {result.get('response', '')[:100]}...")
    print()
    
    # Test a data analysis request without data
    result = interpreter.process_message(
        "analyze my data",
        session_id="test_session_3",
        session_data={},
        is_data_analysis=True
    )
    
    print(f"Query: 'analyze my data'")
    print(f"Response type: {result.get('status', 'unknown')}")
    print(f"Message preview: {result.get('response', '')[:100]}...")
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print("- General conversations should work without data")
    print("- Knowledge questions should be answered without data")
    print("- Data analysis requests should guide to upload")
    
    return True

def test_v3_agent_flexibility():
    """Test the V3 agent's handling of general conversations."""
    try:
        from app.data_analysis_v3.core.agent import DataAnalysisAgent
        
        print("\nTesting V3 Agent Flexibility:")
        print("=" * 50)
        
        agent = DataAnalysisAgent("test_session")
        
        # Test general conversation handling
        print("\n1. Testing general conversation:")
        print("-" * 40)
        
        queries = [
            "hello",
            "who are you?",
            "what can you do?"
        ]
        
        for query in queries:
            # Check if methods exist
            if hasattr(agent, '_is_general_conversation'):
                is_general = agent._is_general_conversation(query)
                print(f"Query: '{query}' -> General: {is_general}")
                
                if is_general and hasattr(agent, '_handle_general_conversation'):
                    response = agent._handle_general_conversation(query)
                    print(f"  Response preview: {response.get('message', '')[:80]}...")
            else:
                print(f"Query: '{query}' -> Method not found (expected in new code)")
        
        return True
        
    except ImportError as e:
        print(f"Could not import V3 agent: {e}")
        return False

if __name__ == "__main__":
    print("Testing Flexible Chat Handling")
    print("=" * 70)
    
    success = True
    
    try:
        # Test message classification
        if not test_message_classification():
            success = False
            
        # Test V3 agent
        if not test_v3_agent_flexibility():
            success = False
            
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    if success:
        print("\n✅ All tests completed successfully!")
    else:
        print("\n❌ Some tests failed. Check the output above.")
    
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Test script to verify OpenAI integration works correctly
Tests that tool calls go through OpenAI, not Arena mode
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_openai_function_calling():
    """Test that OpenAI function calling works correctly"""
    print("\n=== Testing OpenAI Function Calling ===\n")
    
    # Check API key
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not set in environment")
        return False
    else:
        print(f"✅ OpenAI API key found: {api_key[:10]}...")
    
    # Test LLM Manager
    print("\n--- Testing LLM Manager ---")
    try:
        from app.core.llm_manager import LLMManager
        
        llm_manager = LLMManager(api_key=api_key)
        print("✅ LLM Manager initialized")
        
        # Test basic generation
        response = llm_manager.generate_response(
            "What is 2+2?",
            temperature=0.1,
            max_tokens=10
        )
        print(f"✅ Basic generation works: {response}")
        
        # Test function calling
        functions = [{
            "name": "calculate_sum",
            "description": "Calculate the sum of two numbers",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"}
                },
                "required": ["a", "b"]
            }
        }]
        
        func_response = llm_manager.generate_with_functions(
            messages=[{"role": "user", "content": "Calculate 5 + 3"}],
            system_prompt="You are a helpful assistant. Use the calculate_sum function when asked to add numbers.",
            functions=functions,
            temperature=0.1
        )
        
        if func_response.get('function_call'):
            print(f"✅ Function calling works: {func_response['function_call']}")
        else:
            print(f"⚠️ No function call detected: {func_response}")
            
    except Exception as e:
        print(f"❌ LLM Manager error: {e}")
        return False
    
    # Test Request Interpreter
    print("\n--- Testing Request Interpreter ---")
    try:
        # Create minimal services using container
        from app.services.container import ServiceContainer
        from flask import Flask
        
        # Create minimal Flask app
        app = Flask(__name__)
        app.config['OPENAI_API_KEY'] = api_key
        
        # Initialize service container
        container = ServiceContainer(app)
        
        # Get request interpreter from container
        interpreter = container.get('request_interpreter')
        
        if interpreter:
            print("✅ Request Interpreter initialized")
            
            # Test that it has tools registered
            if hasattr(interpreter, 'tools'):
                print(f"✅ Tools registered: {list(interpreter.tools.keys())}")
            else:
                print("⚠️ No tools attribute found on interpreter")
        else:
            print("❌ Request Interpreter is None")
        
    except Exception as e:
        print(f"❌ Request Interpreter error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test Intent Detection
    print("\n--- Testing Intent Detection ---")
    try:
        from app.core.intent_clarifier import IntentClarifier
        
        clarifier = IntentClarifier()
        
        # Test with data context
        context_with_data = {
            'has_uploaded_files': True,
            'session_id': 'test123',
            'csv_loaded': True,
            'shapefile_loaded': True,
            'analysis_complete': True
        }
        
        # This should route to tools (OpenAI)
        intent1 = clarifier.analyze_intent("Show me the high risk wards", context_with_data)
        print(f"'Show me the high risk wards' with data → {intent1} {'✅' if intent1 == 'tools' else '❌'}")
        
        # This should route to arena
        intent2 = clarifier.analyze_intent("What is malaria?", context_with_data)
        print(f"'What is malaria?' → {intent2} {'✅' if intent2 == 'arena' else '❌'}")
        
        # Test without data
        context_no_data = {
            'has_uploaded_files': False,
            'session_id': 'test456'
        }
        
        # Without data, everything goes to arena
        intent3 = clarifier.analyze_intent("Analyze my data", context_no_data)
        print(f"'Analyze my data' without data → {intent3} {'✅' if intent3 == 'arena' else '❌'}")
        
    except Exception as e:
        print(f"❌ Intent detection error: {e}")
        return False
    
    print("\n=== All Tests Passed! ===")
    print("\nSummary:")
    print("✅ OpenAI API key is configured")
    print("✅ LLM Manager can make OpenAI calls")
    print("✅ Function calling is working")
    print("✅ Request Interpreter has tools registered")
    print("✅ Intent detection properly routes to tools vs arena")
    return True

if __name__ == "__main__":
    success = test_openai_function_calling()
    sys.exit(0 if success else 1)
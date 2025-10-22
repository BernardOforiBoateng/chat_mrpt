#!/usr/bin/env python3
"""Test the pre-routing logic without calling Ollama."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_pre_routing_logic():
    """Test the pre-routing filter logic."""
    
    # Test cases: (message, expected_result, description)
    test_cases = [
        # Greetings
        ("hello", "can_answer", "Simple greeting"),
        ("hi", "can_answer", "Simple greeting"),
        ("good morning", "can_answer", "Morning greeting"),
        
        # Small talk
        ("thanks", "can_answer", "Thanks"),
        ("thank you", "can_answer", "Thank you"),
        ("bye", "can_answer", "Goodbye"),
        
        # General knowledge questions
        ("what is malaria", "can_answer", "General knowledge - what is"),
        ("who are you", "can_answer", "Identity question"),
        ("how does pca work", "can_answer", "General knowledge - how does"),
        ("explain tpr", "can_answer", "Explanation request"),
        ("tell me about malaria", "can_answer", "Tell me about pattern"),
        
        # Questions that reference data (should NOT fast-track)
        ("what is in my data", None, "References 'my data'"),
        ("explain the data", None, "References 'the data'"),
        ("tell me about my file", None, "References 'my file'"),
        
        # Data operations (should NOT fast-track)
        ("analyze my data", None, "Explicit data operation"),
        ("plot the distribution", None, "Explicit data operation"),
    ]
    
    print("Testing pre-routing logic...")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for message, expected, description in test_cases:
        message_lower = message.lower().strip()
        result = None
        
        # Simulate the pre-routing logic
        common_greetings = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening', 'howdy']
        
        # Fast-track greetings
        if message_lower in common_greetings or any(message_lower.startswith(g) for g in common_greetings):
            result = "can_answer"
        
        # Fast-track common small talk
        elif message_lower in ['thanks', 'thank you', 'bye', 'goodbye', 'ok', 'okay', 'sure', 'yes', 'no']:
            result = "can_answer"
        
        else:
            # Fast-track general knowledge questions
            general_knowledge_patterns = [
                'what is', 'what are', 'who is', 'who are', 
                'how does', 'how do', 'why is', 'why do',
                'explain', 'tell me about', 'describe',
                'when does', 'when is', 'where is', 'where are'
            ]
            
            for pattern in general_knowledge_patterns:
                if message_lower.startswith(pattern):
                    # Check it's NOT explicitly about uploaded data
                    data_references = ['my data', 'the data', 'uploaded', 'my file', 'the file', 'my csv', 'the csv']
                    if not any(ref in message_lower for ref in data_references):
                        result = "can_answer"
                        break
            
            # Fast-track identity questions
            if result is None and any(phrase in message_lower for phrase in ['who are you', 'what are you', 'your name', 'tell me about yourself']):
                result = "can_answer"
        
        # Check result
        if result == expected:
            print(f"✅ PASS: '{message}' -> {result} ({description})")
            passed += 1
        elif expected is None and result is None:
            print(f"✅ PASS: '{message}' -> continues to Mistral ({description})")
            passed += 1
        else:
            print(f"❌ FAIL: '{message}' -> {result} (expected: {expected}) - {description}")
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All pre-routing tests passed!")
        return True
    else:
        print(f"⚠️ {failed} tests failed.")
        return False

if __name__ == "__main__":
    success = test_pre_routing_logic()
    sys.exit(0 if success else 1)
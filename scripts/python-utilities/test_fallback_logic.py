#!/usr/bin/env python3
"""
Test the fallback logic for 'What is ChatMRPT?'
"""

message = "What is ChatMRPT?"
message_lower = message.lower().strip()

# Simulate no data uploaded
session_context = {
    'has_uploaded_files': False,
    'csv_loaded': False,
    'analysis_complete': False
}

data_available = (session_context.get('has_uploaded_files', False) or
                session_context.get('csv_loaded', False) or
                session_context.get('analysis_complete', False))

print(f"Message: '{message}'")
print(f"Data available: {data_available}")
print("="*60)

# Check greetings
greeting_words = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'greetings']
if any(word == message_lower or message_lower.startswith(word + ' ') for word in greeting_words):
    print("RESULT: Greeting → 'can_answer' (Arena)")
else:
    # Check explanation words (lines 333-337)
    explanation_words = ['what is', 'what does', 'explain', 'how does', 'why is', 'tell me about']
    if any(phrase in message_lower for phrase in explanation_words):
        print(f"Found explanation phrase: '{[p for p in explanation_words if p in message_lower]}'")
        if not any(word in message_lower for word in ['my data', 'variable', 'column', 'dataset']):
            print("No data-specific words found")
            print("RESULT: Explanation → 'can_answer' (Arena)")
        else:
            print("Contains data-specific words")
            print("RESULT: Data explanation → 'needs_tools'")
    else:
        print("Not an explanation request")
        # Would continue through other checks...
        print("RESULT: Would continue to other checks...")

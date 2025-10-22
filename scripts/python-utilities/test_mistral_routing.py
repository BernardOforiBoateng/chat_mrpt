#!/usr/bin/env python
"""
Test script to verify Mistral routing logic for visualization requests.
"""

def test_routing_logic(message, context):
    """Test what routing decision would be made."""

    # Key phrases that MUST route to tools
    tool_triggers = [
        'plot', 'create', 'show', 'generate', 'map',
        'visualize', 'display', 'chart', 'histogram',
        'top', 'ranking', 'distribution', 'query'
    ]

    message_lower = message.lower()

    # Check for visualization/query triggers
    needs_tools = any(trigger in message_lower for trigger in tool_triggers)

    # Special cases that should go to Arena
    explanation_phrases = [
        'what is', 'why is', 'explain', 'how does',
        'what does', 'tell me about the methodology'
    ]

    is_explanation = any(phrase in message_lower for phrase in explanation_phrases)

    # If it's a pure explanation (no action verbs), it can go to Arena
    if is_explanation and not needs_tools:
        return 'can_answer'

    # All visualization and query requests need tools
    if needs_tools:
        return 'needs_tools'

    # Social interactions
    if message_lower in ['hi', 'hello', 'thanks', 'bye', 'thank you']:
        return 'can_answer'

    return 'needs_clarification'


# Test cases
test_cases = [
    # Should go to TOOLS
    ("plot vulnerability map", "needs_tools"),
    ("show me top 10 wards", "needs_tools"),
    ("plot the evi variable distribution", "needs_tools"),
    ("create a histogram", "needs_tools"),
    ("show me the distribution", "needs_tools"),
    ("generate a map", "needs_tools"),
    ("display rankings", "needs_tools"),

    # Should go to ARENA
    ("hi", "can_answer"),
    ("what is malaria", "can_answer"),
    ("explain the methodology", "can_answer"),
    ("why is this ward high risk", "can_answer"),

    # Mixed (should go to TOOLS because of action verb)
    ("explain and plot the results", "needs_tools"),
    ("tell me about my data", "can_answer"),  # Pure explanation
]

print("="*60)
print("MISTRAL ROUTING LOGIC TEST")
print("="*60)

context = {"has_data": True}

for message, expected in test_cases:
    result = test_routing_logic(message, context)
    status = "✅" if result == expected else "❌"
    print(f"{status} '{message}' → {result} (expected: {expected})")

print("\n" + "="*60)
print("Key Rules Applied:")
print("1. ALL visualization requests → needs_tools")
print("2. ALL query requests (top N, rankings) → needs_tools")
print("3. Pure explanations → can_answer")
print("4. Social interactions → can_answer")
print("="*60)
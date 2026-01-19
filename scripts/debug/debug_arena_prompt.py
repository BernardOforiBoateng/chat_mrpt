#!/usr/bin/env python3
"""
Debug script to check what prompt is actually sent to Arena models
"""

import sys
import os
sys.path.append('/home/ec2-user/ChatMRPT')

# Set up environment
os.environ['FLASK_ENV'] = 'production'
os.environ['OPENAI_API_KEY'] = 'dummy-key-for-testing'

from app.core.arena_system_prompt import get_arena_system_prompt
try:
    from app.core.arena_context_manager import get_arena_context_manager
except ImportError:
    print("Arena context manager not found")
    get_arena_context_manager = None

# Get base prompt
base_prompt = get_arena_system_prompt()

print("="*70)
print("ARENA PROMPT DEBUG")
print("="*70)

# Check base prompt
print(f"\n1. Base prompt length: {len(base_prompt)} characters")
print(f"2. Contains 'ChatMRPT Complete System Documentation': {'ChatMRPT Complete System Documentation' in base_prompt}")
print(f"3. Contains 'What is ChatMRPT?': {'What is ChatMRPT?' in base_prompt}")
print(f"4. Contains tool catalog: {'COMPLETE TOOL CATALOG' in base_prompt}")

# Check if it's the generic prompt or our enhanced one
if "You are a helpful AI assistant competing in an Arena Tournament" in base_prompt:
    print("\n⚠️ PROBLEM: Using GENERIC Arena prompt!")
else:
    print("\n✅ Using custom prompt")

# Show first part of prompt
print("\n5. First 2000 characters of prompt:")
print("-"*60)
print(base_prompt[:2000])

# Check for documentation sections
print("\n6. Documentation sections found:")
doc_sections = [
    "COMPLETE TOOL CATALOG",
    "USER INTERFACE COMPONENTS",
    "API ENDPOINTS & ROUTES",
    "WORKFLOWS & USER JOURNEYS",
    "SESSION & STATE MANAGEMENT",
    "ERROR HANDLING & RECOVERY",
    "QUICK REFERENCE"
]

for section in doc_sections:
    if section in base_prompt:
        print(f"  ✅ {section}")
    else:
        print(f"  ❌ {section}")

# Check context manager
if get_arena_context_manager:
    print("\n7. Arena context manager available")
    try:
        manager = get_arena_context_manager()
        context = manager.get_session_context(
            session_id='test',
            session_data={}
        )
        enhancement = manager.format_context_for_prompt(context)
        print(f"   Context enhancement: {len(enhancement)} chars")
    except Exception as e:
        print(f"   Error getting context: {e}")
else:
    print("\n7. Arena context manager NOT available")

# Final combined prompt
print(f"\n8. If context was added (0 chars here), total would be: {len(base_prompt)} chars")

# Check if this is too long for models
if len(base_prompt) > 32000:
    print("\n⚠️ WARNING: Prompt may be too long for some models (>32k chars)")
    print("   Some models might truncate or reject this prompt")

print("\n" + "="*70)
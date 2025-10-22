#!/usr/bin/env python3
"""
Test what different Arena models respond with for 'What is ChatMRPT?'
"""

import sys
import os

# Setup paths
sys.path.append('/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT')
os.environ['FLASK_ENV'] = 'production'

from app.core.arena_system_prompt import get_compact_arena_prompt

# Get the compact prompt that's used
prompt = get_compact_arena_prompt()

print("Testing with compact prompt (used for Ollama models)")
print(f"Prompt length: {len(prompt)} characters")
print("="*60)

# Simulate what models might respond with
test_response = """ChatMRPT is an AI-powered assistant designed to help public health professionals 
analyze malaria risk data and plan interventions. It combines WHO-verified knowledge with 
data-driven insights when user data is available. The tool provides epidemiological analysis 
and insights but does not offer medical diagnoses or treatment advice. It emphasizes the 
importance of consulting with local health authorities for planning and implementing 
malaria interventions."""

print("Expected response (like what you showed):")
print(test_response)
print("\n" + "="*60)

# Check against OLD indicators
old_tool_need_indicators = [
    "i need to see", "upload", "provide the", "i would need",
    "cannot analyze without", "don't have access", "no data available",
    "please share", "i require", "unable to access", "can't see your"
]

# Check against CURRENT indicators (already fixed)
current_tool_need_indicators = [
    "i need to see", "please upload", "provide the", "i would need",
    "cannot analyze without", "don't have access", "no data available",
    "please share", "i require", "unable to access", "can't see your",
    "upload your", "you need to upload", "first upload"
]

response_lower = test_response.lower()

# Check OLD
old_found = [ind for ind in old_tool_need_indicators if ind in response_lower]
print("\nWith OLD indicators (before fix):")
if old_found:
    print(f"  ❌ Would trigger fallback: Found '{old_found}'")
else:
    print(f"  ✅ Would stay in Arena")

# Check CURRENT
current_found = [ind for ind in current_tool_need_indicators if ind in response_lower]
print("\nWith CURRENT indicators (after fix):")
if current_found:
    print(f"  ❌ Would trigger fallback: Found '{current_found}'")
else:
    print(f"  ✅ Would stay in Arena")

print("\n" + "="*60)
print("CONCLUSION:")
if not old_found and not current_found:
    print("The response doesn't contain any problematic phrases.")
    print("Issue must be elsewhere - not in the tool_need_indicators check!")
elif old_found and not current_found:
    print("The fix resolved the issue - 'upload' no longer triggers falsely.")
else:
    print("There may still be an issue with the indicators.")

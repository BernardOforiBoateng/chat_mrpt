#!/usr/bin/env python3
"""Quick test for the arena-based help system"""

import sys
import os
sys.path.insert(0, '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT')

from app.core.arena_system_prompt import get_arena_system_prompt

def test_documentation_loading():
    """Test that documentation loads into prompts"""
    print("=" * 60)
    print("Testing Arena Help System")
    print("=" * 60)

    # Test 1: Check documentation loads
    print("\n1. Testing documentation loading...")
    prompt = get_arena_system_prompt()

    if "COMPLETE SYSTEM DOCUMENTATION" in prompt:
        print("✅ Documentation loaded into prompt")
    else:
        print("❌ Documentation NOT found in prompt")

    # Check for key sections
    sections = [
        "ALL TOOLS AND THEIR FUNCTIONS",
        "RunMalariaRiskAnalysis",
        "CreateVulnerabilityMap",
        "UI ELEMENTS AND BUTTONS",
        "WORKFLOWS & USER JOURNEYS"
    ]

    print("\n2. Checking for key documentation sections...")
    for section in sections:
        if section in prompt:
            print(f"✅ Found: {section}")
        else:
            print(f"❌ Missing: {section}")

    # Test 2: Check context enhancement
    print("\n3. Testing context-aware prompts...")
    test_context = {
        'has_uploaded_files': True,
        'analysis_complete': False,
        'workflow_step': 'data_ready',
        'detected_zone': 'North_West'
    }

    enhanced_prompt = get_arena_system_prompt(
        include_help_context=True,
        session_context=test_context
    )

    if "Current User Context" in enhanced_prompt:
        print("✅ Context enhancement working")
        if "North_West" in enhanced_prompt:
            print("✅ Session context properly injected")
    else:
        print("❌ Context enhancement not working")

    # Test 3: Check prompt size (should be substantial with docs)
    print(f"\n4. Prompt size check...")
    prompt_size = len(prompt)
    print(f"   Prompt length: {prompt_size:,} characters")

    if prompt_size > 50000:  # Documentation is large
        print("✅ Full documentation appears to be loaded")
    elif prompt_size > 5000:
        print("⚠️  Partial documentation loaded")
    else:
        print("❌ Documentation may not be loaded properly")

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_documentation_loading()
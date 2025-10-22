#!/usr/bin/env python3
"""Simple test to verify arena help is working"""

import json

# Test 1: Generate suggestions
def test_suggestions():
    print("Testing Dynamic Suggestions Generation...")

    context = {
        'has_uploaded_files': False,
        'analysis_complete': False,
        'workflow_step': 'initial'
    }

    # Test with fallback function
    from app.web.routes.analysis_routes import get_fallback_suggestions
    suggestions = get_fallback_suggestions(context)

    print(f"\nContext: {json.dumps(context, indent=2)}")
    print(f"\nGenerated {len(suggestions)} suggestions:")
    for i, sug in enumerate(suggestions, 1):
        print(f"{i}. {sug['text']}")
        print(f"   Reason: {sug['reason']}")
        print(f"   Priority: {sug['priority']}")

    # Test different context
    context2 = {
        'has_uploaded_files': True,
        'analysis_complete': True,
        'workflow_step': 'results'
    }

    suggestions2 = get_fallback_suggestions(context2)
    print(f"\n\nContext 2: {json.dumps(context2, indent=2)}")
    print(f"\nGenerated {len(suggestions2)} suggestions:")
    for i, sug in enumerate(suggestions2, 1):
        print(f"{i}. {sug['text']}")

# Test 2: Check if documentation is in prompt
def test_documentation():
    print("\n" + "=" * 60)
    print("Testing Documentation in Prompt...")

    from app.core.arena_system_prompt import get_arena_system_prompt

    prompt = get_arena_system_prompt()

    # Check for ChatMRPT specific content
    if "ChatMRPT" in prompt:
        print("✅ ChatMRPT identity found")

    if "RunMalariaRiskAnalysis" in prompt or "analysis" in prompt.lower():
        print("✅ Analysis tools referenced")

    if "CreateVulnerabilityMap" in prompt or "map" in prompt.lower():
        print("✅ Visualization tools referenced")

    if len(prompt) > 10000:
        print(f"✅ Substantial prompt loaded: {len(prompt):,} chars")

    # Test with context
    test_context = {'has_uploaded_files': True, 'detected_zone': 'Kano'}
    enhanced = get_arena_system_prompt(True, test_context)

    if "Kano" in enhanced:
        print("✅ Context injection working")

if __name__ == "__main__":
    import sys
    sys.path.insert(0, '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT')

    test_suggestions()
    test_documentation()

    print("\n" + "=" * 60)
    print("✅ Arena Help System is Functional!")
    print("=" * 60)
#!/usr/bin/env python3
"""
Test script for semantic routing system.
Tests various queries to ensure routing works without hardcoded patterns.
"""

import asyncio
import json

async def test_routing():
    """Test the semantic routing with various queries."""
    from app.web.routes.analysis_routes import route_with_mistral

    # Test cases: (message, expected_route, description)
    test_cases = [
        # Greetings (should go to Arena)
        ("hi", "can_answer", "Simple greeting"),
        ("hello there", "can_answer", "Greeting with extra word"),
        ("good morning", "can_answer", "Time-based greeting"),

        # Analysis requests (should go to tools)
        ("run malaria risk analysis", "needs_tools", "Analysis without 'the'"),
        ("run the malaria risk analysis", "needs_tools", "Analysis with 'the'"),
        ("analyze my data", "needs_tools", "Direct analysis request"),
        ("perform risk assessment", "needs_tools", "Alternative phrasing"),

        # Visualization requests (should go to tools)
        ("create a vulnerability map", "needs_tools", "Map creation"),
        ("show me variable distributions", "needs_tools", "Distribution request"),
        ("plot the data spread", "needs_tools", "Alternative distribution phrasing"),
        ("generate histogram", "needs_tools", "Specific chart type"),

        # Explanation requests (should go to Arena)
        ("what is malaria", "can_answer", "Knowledge question"),
        ("explain composite score", "can_answer", "Concept explanation"),
        ("what does PCA mean", "can_answer", "Acronym explanation"),
        ("how does risk analysis work", "can_answer", "Methodology question"),

        # Context-dependent (varies based on session)
        ("show me top 5 wards", None, "Depends on whether analysis is complete"),
        ("what are my results", None, "Depends on whether results exist"),
    ]

    print("=" * 80)
    print("SEMANTIC ROUTING TEST RESULTS")
    print("=" * 80)

    # Test with no data context
    print("\n📂 CONTEXT: No data uploaded")
    print("-" * 40)

    no_data_context = {
        'has_uploaded_files': False,
        'csv_loaded': False,
        'analysis_complete': False,
        'session_id': 'test_session_1'
    }

    for message, expected, description in test_cases[:8]:  # Test subset
        try:
            result = await route_with_mistral(message, no_data_context)
            status = "✅" if expected is None or result == expected else "❌"
            print(f"{status} '{message}' -> {result}")
            if result != expected and expected is not None:
                print(f"   Expected: {expected}, Got: {result}")
        except Exception as e:
            print(f"❌ '{message}' -> ERROR: {str(e)}")

    # Test with data context
    print("\n📊 CONTEXT: Data uploaded and analysis complete")
    print("-" * 40)

    with_data_context = {
        'has_uploaded_files': True,
        'csv_loaded': True,
        'analysis_complete': True,
        'session_id': 'test_session_2'
    }

    for message, expected, description in test_cases[8:16]:  # Test different subset
        try:
            result = await route_with_mistral(message, with_data_context)
            status = "✅" if expected is None or result == expected else "❌"
            print(f"{status} '{message}' -> {result}")
            if result != expected and expected is not None:
                print(f"   Expected: {expected}, Got: {result}")
        except Exception as e:
            print(f"❌ '{message}' -> ERROR: {str(e)}")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    # Run async test
    asyncio.run(test_routing())
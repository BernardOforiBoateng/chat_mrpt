"""
Simple test for fuzzy matching functions

Tests the extract_facility_level and extract_age_group methods directly
by reading and executing them in isolation.
"""

import sys
from pathlib import Path
import logging

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup minimal logging
logging.basicConfig(level=logging.WARNING)

# Import only what we need
from difflib import get_close_matches
from typing import Optional

def extract_facility_level(query: str) -> Optional[str]:
    """
    Extract facility level using 3-level fuzzy matching.
    Copied from tpr_workflow_handler.py for isolated testing.
    """
    query_clean = query.lower().strip()

    # Level 1: Exact keyword match
    exact_keywords = {
        'primary': 'primary', '1': 'primary', 'one': 'primary',
        'secondary': 'secondary', '2': 'secondary', 'two': 'secondary',
        'tertiary': 'tertiary', '3': 'tertiary', 'three': 'tertiary',
        'all': 'all', '4': 'all', 'four': 'all', 'every': 'all'
    }

    if query_clean in exact_keywords:
        return exact_keywords[query_clean]

    # Level 2: Fuzzy string matching for typos
    close_matches = get_close_matches(query_clean, exact_keywords.keys(), n=1, cutoff=0.75)
    if close_matches:
        matched_key = close_matches[0]
        result = exact_keywords[matched_key]
        return result

    # Level 3: Pattern/phrase matching for natural language
    patterns = {
        'primary': [
            'primary', 'basic', 'community', 'first level', 'phc',
            'health center', 'clinic', 'local', 'ward level'
        ],
        'secondary': [
            'secondary', 'district', 'general hospital', 'second level',
            'cottage hospital', 'comprehensive', 'lga'
        ],
        'tertiary': [
            'tertiary', 'specialist', 'teaching hospital', 'third level',
            'referral', 'federal medical', 'university hospital'
        ],
        'all': [
            'all', 'every', 'combined', 'everything', 'total',
            'across all', 'all levels', 'complete'
        ]
    }

    for level, keywords in patterns.items():
        for keyword in keywords:
            if keyword in query_clean:
                return level

    return None


def extract_age_group(query: str) -> Optional[str]:
    """
    Extract age group using 3-level fuzzy matching.
    Copied from tpr_workflow_handler.py for isolated testing.
    """
    query_clean = query.lower().strip()

    # Level 1: Exact keyword match
    exact_keywords = {
        'u5': 'u5', 'under5': 'u5', '1': 'u5', 'one': 'u5',
        'o5': 'o5', 'over5': 'o5', '2': 'o5', 'two': 'o5',
        'pw': 'pw', 'pregnant': 'pw', '3': 'pw', 'three': 'pw',
        'all': 'all_ages', '4': 'all_ages', 'four': 'all_ages'
    }

    if query_clean in exact_keywords:
        return exact_keywords[query_clean]

    # Level 2: Fuzzy string matching for typos
    close_matches = get_close_matches(query_clean, exact_keywords.keys(), n=1, cutoff=0.75)
    if close_matches:
        return exact_keywords[close_matches[0]]

    # Level 3: Pattern/phrase matching
    patterns = {
        'u5': ['under 5', 'under five', 'u5', 'under-5', 'children',
               'kids', 'infant', 'toddler', 'young', 'pediatric', 'child'],
        'o5': ['over 5', 'over five', 'o5', 'over-5', 'adult',
               'older', 'above 5', 'above five', 'grown'],
        'pw': ['pregnant', 'pregnancy', 'maternal', 'mother',
               'antenatal', 'expecting', 'gravid', 'prenatal', 'women'],
        'all_ages': ['all', 'every', 'combined', 'everything', 'total',
                     'all ages', 'everyone', 'complete', 'all groups']
    }

    for group, keywords in patterns.items():
        for keyword in keywords:
            if keyword in query_clean:
                return group

    return None


def run_tests():
    """Run all fuzzy matching tests"""

    print("=" * 70)
    print("TRACK A FUZZY KEYWORD MATCHING TESTS")
    print("=" * 70)

    # Facility Level Tests
    facility_tests = [
        # Level 1: Exact matches
        ("primary", "primary", "Exact keyword"),
        ("1", "primary", "Exact number"),
        ("secondary", "secondary", "Exact keyword"),
        ("tertiary", "tertiary", "Exact keyword"),
        ("all", "all", "Exact keyword"),

        # Level 2: Fuzzy matches (typos)
        ("prinary", "primary", "Typo tolerance"),
        ("seconary", "secondary", "Typo tolerance"),
        ("tertary", "tertiary", "Typo tolerance"),

        # Level 3: Pattern matches (natural language)
        ("I want primary facilities", "primary", "Natural language"),
        ("basic facilities", "primary", "Synonym mapping"),
        ("community health centers", "primary", "Phrase matching"),
        ("district hospitals", "secondary", "Phrase matching"),
        ("specialist centers", "tertiary", "Synonym mapping"),
        ("let's analyze all facilities", "all", "Natural language"),

        # No match
        ("show me the weather", None, "Unrelated input"),
    ]

    print("\n" + "-" * 70)
    print("FACILITY LEVEL EXTRACTION")
    print("-" * 70)

    passed = 0
    failed = 0

    for input_text, expected, description in facility_tests:
        result = extract_facility_level(input_text)
        status = "✓ PASS" if result == expected else "✗ FAIL"

        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"{status} | {description:20s} | '{input_text:35s}' → Expected: {str(expected):10s}, Got: {str(result):10s}")

    # Age Group Tests
    age_tests = [
        # Level 1: Exact matches
        ("u5", "u5", "Exact keyword"),
        ("1", "u5", "Exact number"),
        ("o5", "o5", "Exact keyword"),
        ("pw", "pw", "Exact keyword"),
        ("all", "all_ages", "Exact keyword"),

        # Level 2: Fuzzy matches (typos)
        ("pregant", "pw", "Typo tolerance"),

        # Level 3: Pattern matches (natural language)
        ("under five", "u5", "Natural language"),
        ("children under 5", "u5", "Phrase matching"),
        ("kids under five years", "u5", "Natural language"),
        ("pregnant women", "pw", "Natural phrase"),
        ("maternal health", "pw", "Synonym mapping"),
        ("all ages", "all_ages", "Natural phrase"),

        # No match
        ("show me the data", None, "Unrelated input"),
    ]

    print("\n" + "-" * 70)
    print("AGE GROUP EXTRACTION")
    print("-" * 70)

    for input_text, expected, description in age_tests:
        result = extract_age_group(input_text)
        status = "✓ PASS" if result == expected else "✗ FAIL"

        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"{status} | {description:20s} | '{input_text:35s}' → Expected: {str(expected):10s}, Got: {str(result):10s}")

    # Summary
    total = passed + failed
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed}/{total} tests passed")
    if failed == 0:
        print("✓ ALL TESTS PASSED!")
    else:
        print(f"✗ {failed} tests failed")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

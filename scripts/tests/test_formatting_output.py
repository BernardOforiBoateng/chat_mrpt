#!/usr/bin/env python3
"""
Test formatting output to verify proper line breaks and structure
"""

import sys
sys.path.insert(0, '.')

from app.data_analysis_v3.core.formatters import MessageFormatter

def test_formatting():
    """Test the formatting of TPR workflow messages"""
    
    print("="*60)
    print("TESTING FORMATTING OUTPUT")
    print("="*60)
    
    formatter = MessageFormatter("test_session")
    
    # Test 1: Age group selection formatting
    print("\n1. Testing Age Group Selection Formatting:")
    print("-"*40)
    
    analysis = {
        'state': 'Adamawa',
        'facility_level': 'primary',
        'age_groups': {
            'under_5': {
                'has_data': True,
                'name': 'Under 5 Years',
                'icon': '👶',
                'tests_available': 1500,
                'rdt_tests': 1000,
                'rdt_tpr': 25.5,
                'microscopy_tests': 500,
                'microscopy_tpr': 23.2,
                'positivity_rate': 24.8,
                'facilities_reporting': 45,
                'description': 'Highest risk group for severe malaria',
                'recommended': True
            },
            'over_5': {
                'has_data': True,
                'name': 'Over 5 Years',
                'icon': '👤',
                'tests_available': 2000,
                'rdt_tests': 1200,
                'rdt_tpr': 18.3,
                'microscopy_tests': 800,
                'microscopy_tpr': 16.5,
                'positivity_rate': 17.6,
                'facilities_reporting': 42,
                'description': 'General population excluding pregnant women'
            },
            'pregnant': {
                'has_data': True,
                'name': 'Pregnant Women',
                'icon': '🤰',
                'tests_available': 800,
                'rdt_tests': 600,
                'rdt_tpr': 22.1,
                'microscopy_tests': 200,
                'microscopy_tpr': 20.0,
                'positivity_rate': 21.5,
                'facilities_reporting': 38,
                'description': 'High-risk vulnerable group'
            }
        }
    }
    
    message = formatter.format_age_group_selection(analysis)
    print(message)
    
    # Verify formatting
    print("\n" + "-"*40)
    print("VERIFICATION:")
    print("-"*40)
    
    # Check 1: Only 3 age groups (no "All Age Groups Combined")
    if 'All Age Groups Combined' in message:
        print("❌ FAIL: 'All Age Groups Combined' should not be present")
    else:
        print("✅ PASS: No 'All Age Groups Combined' found")
    
    # Check 2: All 3 required groups present
    required_groups = ['Under 5 Years', 'Over 5 Years', 'Pregnant Women']
    for group in required_groups:
        if group in message:
            print(f"✅ PASS: '{group}' is present")
        else:
            print(f"❌ FAIL: '{group}' is missing")
    
    # Check 3: RDT and Microscopy stats present
    if 'RDT:' in message and 'Microscopy:' in message:
        print("✅ PASS: Both RDT and Microscopy stats are shown")
    else:
        print("❌ FAIL: Test type stats missing")
    
    # Check 4: Proper line breaks
    lines = message.split('\n')
    if len(lines) > 15:
        print(f"✅ PASS: Message has {len(lines)} lines (proper formatting)")
    else:
        print(f"❌ FAIL: Message only has {len(lines)} lines (crunched together)")
    
    # Check 5: No percentage over 100
    import re
    percentages = re.findall(r'(\d+\.?\d*)%', message)
    over_100 = [p for p in percentages if float(p) > 100]
    if over_100:
        print(f"❌ FAIL: Found percentages over 100%: {over_100}")
    else:
        print("✅ PASS: All percentages are <= 100%")
    
    # Test 2: Facility selection formatting
    print("\n" + "="*60)
    print("2. Testing Facility Selection Formatting:")
    print("-"*40)
    
    facility_analysis = {
        'state_name': 'Adamawa',
        'levels': {
            'primary': {
                'name': 'Primary Health Centers',
                'count': 245,
                'percentage': 65.3,
                'rdt_tests': 15000,
                'microscopy_tests': 5000,
                'description': 'Community-level facilities providing basic care',
                'recommended': True
            },
            'secondary': {
                'name': 'Secondary Health Facilities',
                'count': 98,
                'percentage': 26.1,
                'rdt_tests': 8000,
                'microscopy_tests': 4000,
                'description': 'District hospitals with enhanced services'
            },
            'tertiary': {
                'name': 'Tertiary Hospitals',
                'count': 12,
                'percentage': 3.2,
                'rdt_tests': 3000,
                'microscopy_tests': 2000,
                'description': 'Specialized referral hospitals'
            },
            'all': {
                'name': 'All Facility Levels',
                'count': 375,
                'percentage': 100.0,
                'rdt_tests': 26000,
                'microscopy_tests': 11000,
                'description': 'Combined analysis of all facilities'
            }
        }
    }
    
    facility_message = formatter.format_facility_selection_only(facility_analysis)
    print(facility_message)
    
    # Check facility formatting
    print("\n" + "-"*40)
    print("FACILITY VERIFICATION:")
    print("-"*40)
    
    if 'Primary Health Centers' in facility_message:
        print("✅ PASS: Primary facilities shown")
    if 'RDT tests:' in facility_message:
        print("✅ PASS: Test type breakdown shown")
    
    facility_lines = facility_message.split('\n')
    if len(facility_lines) > 10:
        print(f"✅ PASS: Facility message has {len(facility_lines)} lines")
    
    print("\n" + "="*60)
    print("TESTING COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_formatting()
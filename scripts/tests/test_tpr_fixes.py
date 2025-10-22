#!/usr/bin/env python3
"""
Test TPR Workflow Fixes
"""

import sys
import os
sys.path.insert(0, '.')

import pandas as pd
import logging
from app.data_analysis_v3.core.tpr_data_analyzer import TPRDataAnalyzer
from app.data_analysis_v3.core.formatters import MessageFormatter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create test data with all age groups
test_data = {
    'State': ['Adamawa'] * 10,
    'LGA': ['Yola North'] * 10,
    'WardName': [f'Ward_{i}' for i in range(10)],
    'HealthFacility': [f'Facility_{i}' for i in range(10)],
    'FacilityLevel': ['Primary'] * 8 + ['Secondary'] * 2,
    # Under 5 columns
    'Persons presenting with fever & tested by RDT <5yrs': [100, 150, 200, 120, 180, 90, 110, 130, 50, 60],
    'Persons tested positive for malaria by RDT <5yrs': [20, 30, 40, 25, 35, 18, 22, 26, 10, 12],
    'Persons presenting with fever and tested by Microscopy <5yrs': [80, 120, 160, 100, 140, 70, 90, 100, 40, 50],
    'Persons tested positive for malaria by Microscopy <5yrs': [16, 24, 32, 20, 28, 14, 18, 20, 8, 10],
    # Over 5 columns
    'Persons presenting with fever & tested by RDT ≥5yrs': [200, 250, 300, 220, 280, 190, 210, 230, 100, 120],
    'Persons tested positive for malaria by RDT ≥5yrs': [40, 50, 60, 44, 56, 38, 42, 46, 20, 24],
    'Persons presenting with fever and tested by Microscopy ≥5yrs': [150, 200, 250, 180, 220, 150, 170, 190, 80, 100],
    'Persons tested positive for malaria by Microscopy ≥5yrs': [30, 40, 50, 36, 44, 30, 34, 38, 16, 20],
    # Pregnant women columns
    'ANC Persons tested by RDT PW': [50, 60, 70, 55, 65, 45, 52, 58, 25, 30],
    'ANC Persons tested positive for malaria by RDT PW': [10, 12, 14, 11, 13, 9, 10, 11, 5, 6],
    'ANC Persons tested by Microscopy PW': [40, 50, 60, 45, 55, 35, 42, 48, 20, 25],
    'ANC Persons tested positive for malaria by Microscopy PW': [8, 10, 12, 9, 11, 7, 8, 9, 4, 5]
}

df = pd.DataFrame(test_data)

# Initialize analyzer
analyzer = TPRDataAnalyzer()
formatter = MessageFormatter("test_session")

print("\n" + "="*60)
print("Testing TPR Workflow Fixes")
print("="*60 + "\n")

# Test Age Group Analysis
age_analysis = analyzer.analyze_age_groups(df, 'Adamawa', 'primary')
age_groups = age_analysis.get('age_groups', {})

print(f"Age Groups Detected: {list(age_groups.keys())}")
print(f"Expected: ['under_5', 'over_5', 'pregnant']")
print(f"All Ages Removed: {'all_ages' not in age_groups}")

# Test formatting
age_msg = formatter.format_age_group_selection(age_analysis)
print("\n" + "="*40)
print("Formatted Message Preview:")
print("="*40)
print(age_msg[:500] + "...")

# Check for issues
if 'All Age Groups Combined' in age_msg:
    print("\n❌ ERROR: 'All Age Groups Combined' still in message!")
else:
    print("\n✅ SUCCESS: 'All Age Groups Combined' removed!")
    
if 'percentage_of_total' in age_msg:
    print("❌ ERROR: Percentage still shown!")
else:
    print("✅ SUCCESS: Percentages removed!")
    
if 'RDT:' in age_msg and 'Microscopy:' in age_msg:
    print("✅ SUCCESS: Test type stats included!")
else:
    print("❌ ERROR: Test type stats missing!")

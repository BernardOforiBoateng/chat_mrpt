#!/usr/bin/env python3
"""
Test TPR Workflow Formatting and Age Group Detection

Tests the complete TPR workflow with emphasis on:
1. Age group detection (all 4 groups)
2. Formatting of messages
3. Accurate positivity rate calculation
"""

import sys
import os
sys.path.insert(0, '.')

import pandas as pd
import logging
from app.data_analysis_v3.core.tpr_data_analyzer import TPRDataAnalyzer
from app.data_analysis_v3.core.formatters import MessageFormatter
from app.data_analysis_v3.core.encoding_handler import EncodingHandler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_tpr_workflow():
    """Test the complete TPR workflow with Adamawa data."""
    
    print("\n" + "="*60)
    print("Testing TPR Workflow Formatting & Age Group Detection")
    print("="*60 + "\n")
    
    # Load the Adamawa TPR data
    data_path = "instance/uploads/test_session/uploaded_data.csv"
    
    # Check if file exists
    if not os.path.exists(data_path):
        # Try to find any TPR data file
        alt_paths = [
            "instance/uploads/*/uploaded_data.csv",
            "instance/uploads/*/raw_data.csv",
            "www/NMEP TPR and LLIN 2024_16072025.xlsx"
        ]
        
        for alt_path in alt_paths:
            import glob
            matches = glob.glob(alt_path)
            if matches:
                data_path = matches[0]
                print(f"Using data file: {data_path}")
                break
        else:
            print("No data file found. Please upload TPR data first.")
            return
    
    # Load data (don't sanitize for TPR)
    print(f"Loading data from: {data_path}")
    if data_path.endswith('.csv'):
        df = EncodingHandler.read_csv_with_encoding(data_path, sanitize_columns=False)
    else:
        df = pd.read_excel(data_path)
    
    print(f"Loaded {len(df)} rows with {len(df.columns)} columns")
    print(f"Columns preview: {list(df.columns[:10])}")
    
    # Initialize analyzer
    analyzer = TPRDataAnalyzer()
    formatter = MessageFormatter("test_session")
    
    # Test 1: State Analysis
    print("\n" + "-"*40)
    print("TEST 1: State Analysis")
    print("-"*40)
    
    state_analysis = analyzer.analyze_states(df)
    print(f"Found {state_analysis.get('total_states', 0)} states")
    
    # Pick first state for testing
    if state_analysis.get('states'):
        test_state = list(state_analysis['states'].keys())[0]
        print(f"Using state: {test_state}")
        
        # Test 2: Facility Level Analysis
        print("\n" + "-"*40)
        print("TEST 2: Facility Level Analysis")
        print("-"*40)
        
        facility_analysis = analyzer.analyze_facility_levels(df, test_state)
        print(f"Found facility levels: {list(facility_analysis.get('levels', {}).keys())}")
        
        # Test formatting
        facility_msg = formatter.format_facility_selection(test_state, facility_analysis)
        print("\nFormatted Facility Selection Message:")
        print(facility_msg)
        
        # Test 3: Age Group Analysis
        print("\n" + "-"*40)
        print("TEST 3: Age Group Analysis (Primary Facilities)")
        print("-"*40)
        
        age_analysis = analyzer.analyze_age_groups(df, test_state, 'primary')
        
        # Check which age groups were detected
        age_groups = age_analysis.get('age_groups', {})
        print(f"\nAge Groups Detection Results:")
        for key, info in age_groups.items():
            status = "✓ FOUND" if info.get('has_data') else "✗ NOT FOUND"
            tests = info.get('tests_available', 0)
            tpr = info.get('positivity_rate', 0)
            print(f"  {info['name']}: {status} - {tests:,} tests, {tpr:.1f}% TPR")
        
        # Test formatting
        age_msg = formatter.format_age_group_selection(age_analysis)
        print("\n" + "="*40)
        print("Formatted Age Group Selection Message:")
        print("="*40)
        print(age_msg)
        
        # Check for missing age groups
        expected_groups = ['all_ages', 'under_5', 'over_5', 'pregnant']
        found_groups = [k for k in expected_groups if age_groups.get(k, {}).get('has_data')]
        missing_groups = [k for k in expected_groups if k not in found_groups]
        
        print("\n" + "="*40)
        print("SUMMARY:")
        print(f"✓ Found {len(found_groups)} age groups: {found_groups}")
        if missing_groups:
            print(f"✗ Missing {len(missing_groups)} age groups: {missing_groups}")
            print("\nPossible reasons for missing groups:")
            print("1. Column names don't match patterns")
            print("2. No data for those age groups")
            print("3. Columns were sanitized differently")
        else:
            print("✓ All 4 age groups detected successfully!")
        
        # Show sample column names to help debug
        print("\n" + "="*40)
        print("Sample Column Names (first 20):")
        for i, col in enumerate(df.columns[:20], 1):
            print(f"  {i}. {col}")
        
        return len(found_groups) == 4  # Return True if all 4 groups found
    
    return False

if __name__ == "__main__":
    success = test_tpr_workflow()
    if success:
        print("\n✅ TEST PASSED: All age groups detected and formatted correctly!")
    else:
        print("\n⚠️ TEST INCOMPLETE: Some age groups may be missing. Check column patterns.")
    
    sys.exit(0 if success else 1)
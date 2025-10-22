#!/usr/bin/env python3
"""
Integration Test: TPR prepare_for_risk action
This tests the full workflow of preparing TPR data for risk analysis
"""

import os
import sys
import pandas as pd
import geopandas as gpd
import json
import shutil
from pathlib import Path

# Add app to path
sys.path.insert(0, '.')

# Import TPR tool
from app.data_analysis_v3.tools.tpr_analysis_tool import analyze_tpr_data


def setup_test_session():
    """Setup a test session folder"""
    session_id = "test_tpr_integration"
    session_folder = f"instance/uploads/{session_id}"
    
    # Clean up if exists
    if os.path.exists(session_folder):
        shutil.rmtree(session_folder)
    
    # Create folder
    os.makedirs(session_folder, exist_ok=True)
    
    # Copy TPR file to session
    source_file = "www/tpr_data_by_state/ad_Adamawa_State_TPR_LLIN_2024.xlsx"
    dest_file = os.path.join(session_folder, "ad_Adamawa_State_TPR_LLIN_2024.xlsx")
    shutil.copy(source_file, dest_file)
    
    print(f"✅ Setup test session: {session_id}")
    print(f"   Copied TPR file to: {dest_file}")
    
    return session_id, session_folder


def test_analyze_action(session_id):
    """Test the analyze action"""
    print("\n" + "=" * 60)
    print("TEST 1: ANALYZE ACTION")
    print("=" * 60)
    
    # Create mock graph state
    graph_state = {
        'session_id': session_id
    }
    
    try:
        # Call the tool using invoke method
        result = analyze_tpr_data.invoke({
            "thought": "Testing analyze action",
            "action": "analyze",
            "options": "{}",
            "graph_state": graph_state
        })
        
        print("✅ Analyze action completed")
        print("\nResult preview:")
        print(result[:500] + "..." if len(result) > 500 else result)
        
        # Check if TPR was detected
        if "TPR Detection Confidence" in result:
            print("\n✅ TPR detection successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Analyze action failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_calculate_tpr_action(session_id):
    """Test the calculate_tpr action with options"""
    print("\n" + "=" * 60)
    print("TEST 2: CALCULATE TPR ACTION")
    print("=" * 60)
    
    # Test with different options
    test_cases = [
        {
            "name": "All ages, both methods",
            "options": json.dumps({"age_group": "all_ages", "test_method": "both"})
        },
        {
            "name": "Under 5, RDT only",
            "options": json.dumps({"age_group": "u5", "test_method": "rdt"})
        }
    ]
    
    graph_state = {'session_id': session_id}
    
    for test in test_cases:
        print(f"\n📊 Testing: {test['name']}")
        
        try:
            result = analyze_tpr_data.invoke({
                "thought": f"Testing {test['name']}",
                "action": "calculate_tpr",
                "options": test['options'],
                "graph_state": graph_state
            })
            
            if "TPR Calculation Complete" in result:
                print(f"✅ {test['name']} - Success")
                
                # Extract statistics
                if "Mean TPR:" in result:
                    lines = result.split('\n')
                    for line in lines:
                        if "Mean TPR:" in line or "Wards Analyzed:" in line:
                            print(f"   {line.strip()}")
            else:
                print(f"⚠️ {test['name']} - No results")
                
        except Exception as e:
            print(f"❌ {test['name']} failed: {e}")
            return False
    
    return True


def test_prepare_for_risk_action(session_id, session_folder):
    """Test the prepare_for_risk action"""
    print("\n" + "=" * 60)
    print("TEST 3: PREPARE FOR RISK ACTION")
    print("=" * 60)
    
    graph_state = {'session_id': session_id}
    
    try:
        print("🔄 Running prepare_for_risk action...")
        result = analyze_tpr_data.invoke({
            "thought": "Testing prepare for risk analysis",
            "action": "prepare_for_risk",
            "options": "{}",
            "graph_state": graph_state
        })
        
        print("✅ Action completed")
        
        # Check for success indicators
        if "TPR Data Prepared for Risk Analysis" in result:
            print("✅ Success message found")
            
            # Extract statistics from result
            lines = result.split('\n')
            for line in lines:
                if "Wards:" in line or "TPR Coverage:" in line or "Mean TPR:" in line:
                    print(f"   {line.strip()}")
        
        # Check if files were created
        print("\n📁 Checking output files...")
        
        raw_data_path = os.path.join(session_folder, "raw_data.csv")
        raw_shapefile_path = os.path.join(session_folder, "raw_shapefile.zip")
        risk_ready_flag = os.path.join(session_folder, ".risk_ready")
        
        files_check = {
            "raw_data.csv": os.path.exists(raw_data_path),
            "raw_shapefile.zip": os.path.exists(raw_shapefile_path),
            ".risk_ready flag": os.path.exists(risk_ready_flag)
        }
        
        all_files_exist = True
        for file_name, exists in files_check.items():
            status = "✅" if exists else "❌"
            print(f"   {status} {file_name}: {'Exists' if exists else 'Not found'}")
            all_files_exist = all_files_exist and exists
        
        # Analyze raw_data.csv if it exists
        if os.path.exists(raw_data_path):
            print("\n📊 Analyzing raw_data.csv...")
            df = pd.read_csv(raw_data_path)
            print(f"   Shape: {df.shape}")
            print(f"   Columns ({len(df.columns)}): {list(df.columns)[:10]}...")
            
            # Check critical columns
            critical_cols = ['WardCode', 'StateCode', 'LGACode', 'TPR', 'WardName']
            for col in critical_cols:
                if col in df.columns:
                    print(f"   ✅ {col} present")
                else:
                    print(f"   ❌ {col} missing")
            
            # Check TPR statistics
            if 'TPR' in df.columns:
                print(f"\n   TPR Statistics:")
                print(f"     Mean: {df['TPR'].mean():.2f}%")
                print(f"     Max: {df['TPR'].max():.2f}%")
                print(f"     Non-zero: {(df['TPR'] > 0).sum()}/{len(df)}")
        
        # Check shapefile
        if os.path.exists(raw_shapefile_path):
            print(f"\n📦 Shapefile package size: {os.path.getsize(raw_shapefile_path) / 1024:.1f} KB")
        
        return all_files_exist
        
    except Exception as e:
        print(f"❌ Prepare for risk action failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup_test_session(session_folder):
    """Clean up test session"""
    if os.path.exists(session_folder):
        shutil.rmtree(session_folder)
        print(f"\n🧹 Cleaned up test session folder")


if __name__ == "__main__":
    print("🚀 Starting TPR Integration Tests\n")
    
    # Setup
    session_id, session_folder = setup_test_session()
    
    # Run tests
    analyze_passed = test_analyze_action(session_id)
    calculate_passed = test_calculate_tpr_action(session_id)
    prepare_passed = test_prepare_for_risk_action(session_id, session_folder)
    
    # Summary
    print("\n" + "=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)
    print(f"Analyze Action: {'✅ PASSED' if analyze_passed else '❌ FAILED'}")
    print(f"Calculate TPR Action: {'✅ PASSED' if calculate_passed else '❌ FAILED'}")
    print(f"Prepare for Risk Action: {'✅ PASSED' if prepare_passed else '❌ FAILED'}")
    
    all_passed = analyze_passed and calculate_passed and prepare_passed
    
    print("\n" + ("✅ ALL INTEGRATION TESTS PASSED!" if all_passed else "❌ SOME TESTS FAILED"))
    
    # Cleanup (optional - comment out to inspect files)
    # cleanup_test_session(session_folder)
    
    sys.exit(0 if all_passed else 1)
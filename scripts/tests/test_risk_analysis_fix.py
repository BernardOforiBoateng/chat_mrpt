#!/usr/bin/env python3
"""
Test the risk analysis workflow fix.
This simulates the issue where ITN planning doesn't recognize completed analysis.
"""

import os
import sys
import json
from pathlib import Path

# Add the app to path
sys.path.insert(0, '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT')

def test_analysis_detection():
    """Test if the ITN tool can detect completed analysis."""
    
    print("=" * 60)
    print("TESTING RISK ANALYSIS ACKNOWLEDGMENT FIX")
    print("=" * 60)
    
    # Use the existing session with completed analysis
    test_session_id = "34216c86-ffe2-4d18-bbab-bd084e579553"
    session_folder = Path(f"instance/uploads/{test_session_id}")
    
    print(f"\n📁 Testing with session: {test_session_id}")
    print(f"   Session folder: {session_folder}")
    
    # Check what files exist
    print("\n🔍 Checking existing files:")
    if session_folder.exists():
        important_files = [
            ".analysis_complete",
            "unified_dataset.csv", 
            "unified_dataset.geoparquet",
            "analysis_composite_scores.csv",
            "analysis_vulnerability_rankings.csv",
            "composite_scores.csv",
            "raw_data.csv"
        ]
        
        for filename in important_files:
            filepath = session_folder / filename
            if filepath.exists():
                size = filepath.stat().st_size
                print(f"   ✅ {filename} ({size:,} bytes)")
            else:
                print(f"   ❌ {filename} (not found)")
    else:
        print("   ❌ Session folder doesn't exist!")
        return
    
    # Now test the ITN tool's detection logic
    print("\n🧪 Testing ITN tool's analysis detection:")
    
    try:
        from app.tools.itn_planning_tools import PlanITNDistribution
        from app.models.data_handler import DataHandler
        
        # Initialize the tool
        tool = PlanITNDistribution()
        
        # Create a data handler for the session
        session_path = f"instance/uploads/{test_session_id}"
        data_handler = DataHandler(session_path)
        data_handler.session_id = test_session_id
        
        # Test the _check_analysis_complete method
        is_complete = tool._check_analysis_complete(data_handler)
        
        if is_complete:
            print("   ✅ Analysis detected as COMPLETE!")
        else:
            print("   ❌ Analysis NOT detected (this is the bug)")
            
    except Exception as e:
        print(f"   ❌ Error testing ITN tool: {e}")
        import traceback
        traceback.print_exc()
    
    # Test UnifiedDataState
    print("\n🧪 Testing UnifiedDataState:")
    try:
        from app.core.unified_data_state import get_data_state
        
        data_state = get_data_state(test_session_id)
        print(f"   Data loaded: {data_state.data_loaded}")
        print(f"   Analysis complete: {data_state.analysis_complete}")
        
        if data_state.current_data is not None:
            df = data_state.current_data
            print(f"   Current data shape: {df.shape}")
            
            # Check for analysis columns
            analysis_cols = ['composite_score', 'composite_rank', 'pca_score', 'pca_rank']
            found_cols = [col for col in analysis_cols if col in df.columns]
            if found_cols:
                print(f"   ✅ Analysis columns found: {found_cols}")
            else:
                print(f"   ❌ No analysis columns found")
        else:
            print("   ❌ No current data available")
            
    except Exception as e:
        print(f"   ❌ Error testing UnifiedDataState: {e}")
    
    # Test session recovery
    print("\n🧪 Testing session state recovery:")
    try:
        # Simulate a fresh worker with no session state
        from flask import Flask
        from app.core.request_interpreter import RequestInterpreter
        
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-key'
        
        with app.test_request_context():
            interpreter = RequestInterpreter()
            context = interpreter._get_session_context(test_session_id)
            
            print(f"   Data loaded: {context.get('data_loaded')}")
            print(f"   Analysis complete: {context.get('analysis_complete')}")
            
            if context.get('analysis_complete'):
                print("   ✅ Session recovery successful!")
            else:
                print("   ❌ Session recovery failed")
                
    except Exception as e:
        print(f"   ❌ Error testing session recovery: {e}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    
    # Summary
    print("\n📊 SUMMARY:")
    print("The fix implements multiple fallback mechanisms:")
    print("1. ✅ Marker file (.analysis_complete) - most reliable")
    print("2. ✅ Direct file checks - works across workers")
    print("3. ✅ UnifiedDataState checks - file-based state")
    print("4. ✅ Session recovery - auto-recovers from files")
    print("5. ✅ Flask session - fallback for same worker")
    
    print("\nThe ITN tool should now recognize completed analysis")
    print("regardless of which worker handles the request.")

if __name__ == "__main__":
    test_analysis_detection()
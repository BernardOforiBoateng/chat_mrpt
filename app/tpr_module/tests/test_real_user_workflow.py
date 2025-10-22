"""
Real-world end-to-end test simulating actual user workflow through TPR module.

This test simulates:
1. User uploads NMEP Excel file
2. System detects it's TPR data
3. User goes through conversational flow
4. System generates outputs with proper structure
"""

import os
import sys
import json
import pandas as pd
import geopandas as gpd
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from app.tpr_module.core.tpr_conversation_manager import TPRConversationManager

# Path to actual NMEP data file
NMEP_FILE = "/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/NMEP Malaria Adamawa_Kwara_Osun_Test Postivity Rate_2022_2024.xlsx"


def simulate_user_workflow():
    """Simulate the complete user workflow from upload to output generation."""
    
    print("=" * 80)
    print("SIMULATING REAL USER WORKFLOW - TPR MODULE")
    print("=" * 80)
    
    # Initialize conversation manager (simulating what happens in the route)
    session_id = "test_user_session_001"
    conversation = TPRConversationManager()  # Use default initialization
    
    print("\n1. USER UPLOADS NMEP EXCEL FILE")
    print(f"   File: {os.path.basename(NMEP_FILE)}")
    
    # Process file upload - start conversation with file
    response = conversation.start_conversation(NMEP_FILE)
    print(f"\n   SYSTEM: {response.get('message', response.get('response', 'No message'))}")
    print(f"   Stage: {response.get('stage', 'Unknown')}")
    
    # Show detected states
    if 'data' in response and 'states' in response['data']:
        print(f"\n   Detected states: {', '.join(response['data']['states'])}")
    
    print("\n2. USER SELECTS STATE")
    user_input = "Adamawa State"
    print(f"   USER: {user_input}")
    
    response = conversation.process_user_input(user_input)
    print(f"   SYSTEM: {response.get('message', response.get('response', 'No message'))}")
    print(f"   Stage: {response.get('stage', 'Unknown')}")
    
    print("\n3. USER SELECTS FACILITY LEVEL")
    user_input = "all facilities"
    print(f"   USER: {user_input}")
    
    response = conversation.process_user_input(user_input)
    print(f"   SYSTEM: {response.get('message', response.get('response', 'No message'))}")
    print(f"   Stage: {response.get('stage', 'Unknown')}")
    
    print("\n4. USER SELECTS AGE GROUP")
    user_input = "under 5 children"
    print(f"   USER: {user_input}")
    
    response = conversation.process_user_input(user_input)
    print(f"   SYSTEM: {response.get('message', response.get('response', 'No message'))}")
    print(f"   Stage: {response.get('stage', 'Unknown')}")
    
    # If ready for output, generate the outputs
    if response.get('status') == 'ready_for_output':
        print("\n5. GENERATING OUTPUT FILES...")
        from app.tpr_module.output.output_generator import OutputGenerator
        
        # Get TPR results as dataframe
        tpr_df = conversation.calculator.export_results_to_dataframe()
        
        # Generate outputs
        output_generator = OutputGenerator(session_id)
        metadata = {
            'facility_level': conversation.selected_facility_level,
            'age_group': conversation.selected_age_group,
            'source_file': os.path.basename(NMEP_FILE)
        }
        
        output_paths = output_generator.generate_outputs(
            tpr_df,
            conversation.selected_state,
            metadata
        )
        
        # Store output paths in response for checking
        response['output_paths'] = output_paths
    
    # Check if outputs were generated
    if response.get('stage') == 'complete' or 'output_paths' in response:
        print("\n6. WORKFLOW COMPLETED - Checking output files...")
        
        # Look for generated files in the expected output directory
        import glob
        output_files = glob.glob(f"instance/uploads/{session_id}/*.csv") + \
                      glob.glob(f"instance/uploads/{session_id}/*.md") + \
                      glob.glob(f"instance/uploads/{session_id}/*.zip")
        
        if output_files:
            print(f"\n   Found {len(output_files)} output files:")
            for file in output_files:
                size = os.path.getsize(file) / 1024
                print(f"   ✓ {os.path.basename(file)} ({size:.1f} KB)")
                
                # Check main CSV structure if it exists
                if 'Main_Analysis' in file and file.endswith('.csv'):
                    df = pd.read_csv(file)
                    print(f"\n   MAIN CSV STRUCTURE ({os.path.basename(file)}):")
                    print(f"   Columns ({len(df.columns)}): {list(df.columns)}")
                    print(f"\n   Sample data:")
                    print(df[['WardName', 'TPR']].head(3) if 'WardName' in df.columns and 'TPR' in df.columns else df.head(3))
        else:
            print("\n   ⚠ No output files found in expected location")
        
        # Check if output_paths are in response
        if 'output_paths' in response:
            print("\n   Output paths from generator:")
            for file_type, path in response['output_paths'].items():
                if path and os.path.exists(path):
                    size = os.path.getsize(path) / 1024
                    print(f"   ✓ {file_type}: {os.path.basename(path)} ({size:.1f} KB)")
                    
                    # Check main CSV structure
                    if file_type == 'main_analysis':
                        df = pd.read_csv(path)
                        print(f"\n   MAIN CSV STRUCTURE:")
                        print(f"   Total columns: {len(df.columns)}")
                        print(f"   Column order: {list(df.columns)}")
                        print(f"\n   Sample data (first 3 rows):")
                        display_cols = ['WardName', 'TPR'] if all(c in df.columns for c in ['WardName', 'TPR']) else df.columns[:5]
                        print(df[display_cols].head(3).to_string(index=False))
            
    elif response.get('status') == 'success' and ('output_paths' in response or 'outputs' in response):
        print("\n5. OUTPUTS GENERATED")
        outputs = response['outputs']
        
        for file_type, path in outputs.items():
            if path and os.path.exists(path):
                size = os.path.getsize(path) / 1024
                print(f"   ✓ {file_type}: {os.path.basename(path)} ({size:.1f} KB)")
        
        # Examine main CSV structure
        main_csv = outputs.get('main_analysis')
        if main_csv and os.path.exists(main_csv):
            print("\n6. MAIN CSV STRUCTURE")
            df = pd.read_csv(main_csv)
            
            print(f"   Total rows: {len(df)}")
            print(f"   Total columns: {len(df.columns)}")
            
            print("\n   Column order:")
            for i, col in enumerate(df.columns, 1):
                print(f"   {i:2d}. {col}")
            
            print("\n   Sample data (first 5 rows):")
            print("   " + "-" * 100)
            
            # Show data in groups as requested
            print("\n   WARD NAME:")
            print(df[['WardName']].head().to_string(index=False))
            
            # Identifier columns
            id_cols = [c for c in ['WardCode', 'LGA', 'LGACode', 'State', 'StateCode', 'Urban', 'AMAPCODE'] 
                      if c in df.columns]
            if id_cols:
                print("\n   IDENTIFIERS:")
                print(df[id_cols].head().to_string(index=False))
            
            # TPR data
            tpr_cols = [c for c in ['TPR', 'TPR_Method', 'Facility_Count'] if c in df.columns]
            if tpr_cols:
                print("\n   TPR DATA:")
                print(df[tpr_cols].head().to_string(index=False))
            
            # Environmental variables
            env_cols = [c for c in df.columns if c in ['housing_quality', 'evi', 'ndwi', 'soil_wetness']]
            if env_cols:
                print("\n   ENVIRONMENTAL VARIABLES:")
                print(df[env_cols].head().to_string(index=False))
            
            # Data quality check
            print("\n7. DATA QUALITY CHECK")
            print(f"   ✓ Ward names cleaned: {'ad ' not in df['WardName'].iloc[0]}")
            print(f"   ✓ TPR values present: {df['TPR'].notna().sum()} out of {len(df)}")
            print(f"   ✓ Environmental variables included: {len(env_cols)} variables")
            
            # Check for specific issues
            if df['WardCode'].isna().all():
                print("   ⚠ WardCode is empty (expected if shapefile doesn't match)")
            
    else:
        print(f"\n   ERROR: Workflow did not complete. Stage: {response.get('stage')}")
        if 'error' in response:
            print(f"   Error: {response['error']}")
    
    print("\n" + "=" * 80)
    print("END OF WORKFLOW SIMULATION")
    print("=" * 80)
    
    # Return the conversation state for verification
    # Get final state
    final_state = {
        'session_id': getattr(conversation.state_manager, 'session_id', 'test_session'),
        'selected_state': conversation.selected_state,
        'facility_level': conversation.selected_facility_level,
        'age_group': conversation.selected_age_group,
        'workflow_stage': response.get('stage', 'unknown')
    }
    return final_state


def check_nmep_file_structure():
    """Quick check of NMEP file structure for debugging."""
    print("\n" + "=" * 80)
    print("NMEP FILE STRUCTURE CHECK")
    print("=" * 80)
    
    if not os.path.exists(NMEP_FILE):
        print(f"ERROR: NMEP file not found at {NMEP_FILE}")
        return
    
    # Read first few rows
    df = pd.read_excel(NMEP_FILE, sheet_name='raw', nrows=5)
    print(f"\nColumns in NMEP file: {len(df.columns)}")
    print("\nFirst 5 column names:")
    for i, col in enumerate(df.columns[:5], 1):
        print(f"  {i}. {col}")
    
    # Check for ward column
    ward_cols = [col for col in df.columns if 'ward' in col.lower()]
    print(f"\nWard-related columns found: {ward_cols}")
    
    if 'Ward' in df.columns:
        print("\nSample ward values:")
        print(df['Ward'].head())


if __name__ == "__main__":
    # First check NMEP file
    check_nmep_file_structure()
    
    # Then run the workflow simulation
    print("\n\n")
    final_state = simulate_user_workflow()
    
    # Print final state summary
    print("\n\nFINAL STATE SUMMARY:")
    print(f"Session ID: {final_state.get('session_id')}")
    print(f"Selected State: {final_state.get('selected_state')}")
    print(f"Facility Level: {final_state.get('facility_level')}")
    print(f"Age Group: {final_state.get('age_group')}")
    print(f"Workflow Stage: {final_state.get('workflow_stage')}")
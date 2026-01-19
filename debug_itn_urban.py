#!/usr/bin/env python3
"""
Debug ITN urban percentage issue
"""

import sys
import os
import json
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# Set environment
os.environ['FLASK_APP'] = 'run.py'
sys.path.insert(0, '/home/ec2-user/ChatMRPT')

def debug_urban_issue(session_id):
    """Debug why urban percentage is not passed through"""
    
    from app import create_app
    app = create_app()
    
    with app.app_context():
        from app.data import DataHandler
        
        session_folder = f'instance/uploads/{session_id}'
        print(f"Session: {session_id}")
        
        # Initialize data handler
        data_handler = DataHandler(session_folder)
        data_handler._attempt_data_reload()
        
        # Check unified dataset
        if hasattr(data_handler, 'unified_dataset') and data_handler.unified_dataset is not None:
            print(f"\n✅ Unified dataset loaded: {len(data_handler.unified_dataset)} rows")
            print(f"Columns: {list(data_handler.unified_dataset.columns)}")
            
            # Check for urban columns
            urban_cols = [col for col in data_handler.unified_dataset.columns if 'urban' in col.lower()]
            print(f"\nUrban-related columns: {urban_cols}")
            
            if 'urbanPercentage' in data_handler.unified_dataset.columns:
                non_null = data_handler.unified_dataset['urbanPercentage'].notna().sum()
                print(f"urbanPercentage: {non_null}/{len(data_handler.unified_dataset)} non-null values")
                print(f"Sample values: {data_handler.unified_dataset['urbanPercentage'].head(5).values}")
            
            if 'urban_percentage' in data_handler.unified_dataset.columns:
                non_null = data_handler.unified_dataset['urban_percentage'].notna().sum()
                print(f"urban_percentage: {non_null}/{len(data_handler.unified_dataset)} non-null values")
                print(f"Sample values: {data_handler.unified_dataset['urban_percentage'].head(5).values}")
        else:
            print("❌ No unified dataset")
        
        # Check CSV data
        if hasattr(data_handler, 'csv_data') and data_handler.csv_data is not None:
            print(f"\n✅ CSV data loaded: {len(data_handler.csv_data)} rows")
            print(f"Columns: {list(data_handler.csv_data.columns)[:20]}...")
            
            # Check for urban columns
            urban_cols = [col for col in data_handler.csv_data.columns if 'urban' in col.lower()]
            print(f"Urban-related columns: {urban_cols}")
        
        # Now test ITN pipeline logic directly
        print("\n=== Testing ITN Pipeline Logic ===")
        
        from app.analysis.itn_pipeline import calculate_itn_distribution, detect_state, load_population_data
        
        # Detect state
        state = detect_state(data_handler)
        print(f"State: {state}")
        
        # Load population data
        pop_data = load_population_data(state)
        if pop_data:
            print(f"Population data: {len(pop_data)} wards")
        
        # Check what happens in the pipeline
        method = 'composite'
        
        if hasattr(data_handler, 'unified_dataset') and data_handler.unified_dataset is not None:
            print("\n🔍 Using unified dataset path...")
            
            rank_col = 'composite_rank'
            score_col = 'composite_score'
            category_col = 'composite_category'
            
            # Extract rankings with all necessary data
            required_cols = ['WardName', score_col, rank_col, category_col]
            
            # Check if urbanPercentage exists
            if 'urbanPercentage' in data_handler.unified_dataset.columns:
                print("✅ Adding urbanPercentage to required columns")
                required_cols.append('urbanPercentage')
            elif 'urban_percentage' in data_handler.unified_dataset.columns:
                print("✅ Adding urban_percentage to required columns")
                required_cols.append('urban_percentage')
            else:
                print("❌ No urban column found in unified dataset!")
            
            print(f"Required columns: {required_cols}")
            
            # Check if all columns exist
            missing = [col for col in required_cols if col not in data_handler.unified_dataset.columns]
            if missing:
                print(f"⚠️ Missing columns: {missing}")
            
            # Extract the data
            rankings = data_handler.unified_dataset[required_cols].copy()
            print(f"\nExtracted rankings shape: {rankings.shape}")
            print(f"Extracted columns: {list(rankings.columns)}")
            
            # After renaming
            rankings = rankings.rename(columns={
                score_col: 'score',
                rank_col: 'overall_rank',
                category_col: 'vulnerability_category'
            })
            print(f"After rename columns: {list(rankings.columns)}")
        
        return True

if __name__ == "__main__":
    session_id = '4e21ce78-66e6-4ef4-b13e-23e994846de8'
    debug_urban_issue(session_id)
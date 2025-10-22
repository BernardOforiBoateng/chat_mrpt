#\!/usr/bin/env python3
"""Debug script to check column names in unified dataset"""

import os
import sys
import pandas as pd

def check_session_data(session_id):
    """Check what columns are in the unified dataset"""
    print(f"\nChecking session: {session_id}")
    print("=" * 60)
    
    # Check if files exist
    session_folder = os.path.join('instance/uploads', session_id)
    if not os.path.exists(session_folder):
        print(f"Session folder does not exist: {session_folder}")
        return
        
    print(f"Session folder exists: {session_folder}")
    
    # List CSV files
    csv_files = [f for f in os.listdir(session_folder) if f.endswith('.csv')]
    print(f"\nCSV files in session folder:")
    for f in csv_files:
        print(f"  - {f}")
    
    # Check vulnerability rankings
    rankings_path = os.path.join(session_folder, 'analysis_vulnerability_rankings.csv')
    if os.path.exists(rankings_path):
        print(f"\nVulnerability rankings exist")
        try:
            df = pd.read_csv(rankings_path)
            print(f"Rankings shape: {df.shape}")
            print(f"Rankings columns: {list(df.columns)}")
            
            # Check for key columns
            print("\nChecking for key columns:")
            check_cols = ['composite_score', 'median_score', 'composite_rank', 'overall_rank', 'WardName']
            for col in check_cols:
                if col in df.columns:
                    print(f"  {col} EXISTS")
                else:
                    print(f"  {col} MISSING")
                    
        except Exception as e:
            print(f"Error reading rankings: {e}")

if __name__ == "__main__":
    # Test with a specific session ID from command line
    test_session = "59b18890-638c-4c1e-862b-82a900cea3e9"
    
    if len(sys.argv) > 1:
        test_session = sys.argv[1]
        
    check_session_data(test_session)
EOF < /dev/null

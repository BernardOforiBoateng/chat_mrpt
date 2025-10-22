#!/usr/bin/env python3
"""Final test of ITN distribution to verify data flow."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from app.models.data_handler import DataHandler
from app.tools.itn_planning_tools import PlanITNDistribution

def test_itn_final():
    """Test ITN distribution with proper data loading."""
    
    session_id = "59b18890-638c-4c1e-862b-82a900cea3e9"
    
    print("Final ITN Distribution Test - Data Flow Verification")
    print("=" * 60)
    
    # Load the data handler
    data_handler = DataHandler(session_id)
    
    # Manually load the key files
    print("\n1. Loading data files...")
    
    # Load vulnerability rankings (this should be used for ITN)
    rankings_path = f"instance/uploads/{session_id}/analysis_vulnerability_rankings.csv"
    data_handler.vulnerability_rankings = pd.read_csv(rankings_path)
    print(f"   ✓ Vulnerability rankings: {len(data_handler.vulnerability_rankings)} wards")
    print(f"   Sample wards: {list(data_handler.vulnerability_rankings['WardName'].head())}")
    
    # Check if unified dataset exists but DON'T load it to force using rankings
    unified_path = f"instance/uploads/{session_id}/unified_dataset.csv"
    if os.path.exists(unified_path):
        print(f"   ℹ️  Unified dataset exists but not loading it to test rankings path")
    
    # Use the ITN tool directly
    print("\n2. Running ITN distribution planning...")
    tool = PlanITNDistribution(
        total_nets=10000,
        avg_household_size=5.0,
        urban_threshold=30.0,
        method='composite'
    )
    
    result = tool.execute(session_id)
    
    print(f"\n3. Result:")
    print(f"   Success: {result.success}")
    print(f"   Message: {result.message[:200]}...")
    
    if result.success and result.data:
        stats = result.data.get('stats', {})
        print(f"\n   Stats:")
        print(f"   - Allocated: {stats.get('allocated', 0):,} nets")
        print(f"   - Coverage: {stats.get('coverage_percent', 0)}%")
        print(f"   - Prioritized wards: {stats.get('prioritized_wards', 0)}")

if __name__ == "__main__":
    test_itn_final()
"""
Test the enhanced interpretation for logistics queries.
This will test both pre-ITN and post-ITN query interpretations.
"""

import sys
import os
import pandas as pd
from pathlib import Path

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test session with Adamawa data
SESSION_ID = "9000f9df-451d-4dd9-a4d1-2040becdf902"

def test_sql_queries():
    """Test SQL query interpretation with the enhanced system."""

    # Initialize the conversational data access
    from app.services.conversational_data_access import ConversationalDataAccess
    from app.core.llm_manager import get_llm_manager

    # Get LLM manager
    llm_manager = get_llm_manager()

    # Create conversational data access
    conv_access = ConversationalDataAccess(SESSION_ID, llm_manager)

    print("=" * 80)
    print("TESTING ENHANCED INTERPRETATION")
    print("=" * 80)

    # Test 1: Top risk wards query (logistics interpretation)
    print("\n1. Testing: 'Where should I go first?'")
    print("-" * 40)
    result1 = conv_access.process_sql_query(
        "SELECT WardName, composite_score, composite_rank FROM df ORDER BY composite_score DESC LIMIT 5"
    )
    if result1['success']:
        print(result1['output'])
    else:
        print(f"Error: {result1['error']}")

    # Test 2: Ward ranking explanation
    print("\n2. Testing: 'Why is a specific ward ranked high?'")
    print("-" * 40)
    result2 = conv_access.process_sql_query(
        "SELECT * FROM df WHERE WardName LIKE '%Demsa%' LIMIT 1"
    )
    if result2['success']:
        print(result2['output'])
    else:
        print(f"Error: {result2['error']}")

    # Test 3: Check if ITN table is available
    print("\n3. Testing ITN table availability")
    print("-" * 40)
    result3 = conv_access.process_sql_query(
        "SELECT COUNT(*) as ward_count FROM itn_df"
    )
    print(f"ITN table available: {result3['success']}")
    if result3['success']:
        print(result3['output'])

    # Test 4: If ITN available, test ITN query
    if result3['success']:
        print("\n4. Testing: 'Which wards get the most nets?'")
        print("-" * 40)
        result4 = conv_access.process_sql_query(
            "SELECT WardName, Nets_Allocated, Coverage_Percent, composite_score FROM itn_df ORDER BY Nets_Allocated DESC LIMIT 5"
        )
        if result4['success']:
            print(result4['output'])
        else:
            print(f"Error: {result4['error']}")

def test_itn_planning():
    """First run ITN planning to generate the CSV."""
    from app.tools.itn_planning_tools import PlanITNDistribution

    print("\n" + "=" * 80)
    print("RUNNING ITN PLANNING FIRST")
    print("=" * 80)

    # Create ITN planning tool
    itn_tool = PlanITNDistribution(
        total_nets=50000,
        avg_household_size=5.0,
        urban_threshold=30.0,
        method='composite'
    )

    # Execute ITN planning
    result = itn_tool.execute(SESSION_ID)

    if result.success:
        print("✅ ITN Planning completed successfully")
        print(f"Message: {result.message[:500]}...")

        # Check if CSV was created
        csv_path = Path(f"instance/uploads/{SESSION_ID}/itn_distribution_results.csv")
        if csv_path.exists():
            print(f"✅ CSV file created: {csv_path}")
            df = pd.read_csv(csv_path)
            print(f"   Shape: {df.shape}")
            print(f"   Columns: {df.columns.tolist()}")
        else:
            print("❌ CSV file not found")
    else:
        print(f"❌ ITN Planning failed: {result.message}")

    return result.success

if __name__ == "__main__":
    # First check if unified dataset exists
    unified_path = Path(f"instance/uploads/{SESSION_ID}/unified_dataset.csv")
    if not unified_path.exists():
        print(f"❌ No unified dataset found for session {SESSION_ID}")
        sys.exit(1)

    print(f"✅ Found unified dataset: {unified_path}")

    # Run ITN planning first
    itn_success = test_itn_planning()

    # Then test SQL queries
    print("\n" + "=" * 80)
    test_sql_queries()

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
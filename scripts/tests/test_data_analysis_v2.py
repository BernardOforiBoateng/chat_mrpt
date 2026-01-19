#!/usr/bin/env python
"""Test Data Analysis V2 orchestrator"""

import asyncio
import sys
from pathlib import Path

# Add ChatMRPT to path
sys.path.insert(0, '/home/ec2-user/ChatMRPT')

from app.agents.data_analysis import DataAnalysisOrchestrator
import pandas as pd

async def test():
    print("Creating test data...")
    # Create dummy test file
    df = pd.DataFrame({
        "State": ["Kano", "Lagos", "Abuja", "Kaduna"],
        "Cases": [1234, 5678, 910, 1112],
        "Tests": [10000, 20000, 5000, 8000],
        "TPR": [12.34, 28.39, 18.20, 13.90]
    })
    
    test_dir = Path("/home/ec2-user/ChatMRPT/instance/uploads/test")
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_dir / "test_data.csv"
    df.to_csv(test_file, index=False)
    print(f"Test file created: {test_file}")
    
    print("\nInitializing orchestrator...")
    orch = DataAnalysisOrchestrator()
    
    print("\nRunning analysis...")
    result = await orch.analyze(
        test_file,
        "Show me a summary of this data",
        "test123"
    )
    
    print("\n=== RESULTS ===")
    print(f"Success: {result.get('success')}")
    print(f"Message length: {len(result.get('message', ''))}")
    
    if result.get('message'):
        print(f"\nMessage:\n{result.get('message', '')[:500]}")
        if len(result.get('message', '')) > 500:
            print("... (truncated)")
    else:
        print("No message returned")
    
    print(f"\nAgents used: {result.get('agents_used', [])}")
    print(f"Reasoning steps: {len(result.get('reasoning', []))}")
    
    if result.get('error'):
        print(f"\nError: {result.get('error')}")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(test())
    if not result.get('success') or not result.get('message') or result.get('message') == "Analysis completed but no specific results were generated.":
        print("\n❌ TEST FAILED - No actual results generated")
        sys.exit(1)
    else:
        print("\n✅ TEST PASSED")
        sys.exit(0)
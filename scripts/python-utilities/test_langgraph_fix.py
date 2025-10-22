#!/usr/bin/env python3
"""
Test script to verify LangGraph agent fixes
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up environment
os.environ['FLASK_ENV'] = 'development'

async def test_langgraph_agent():
    """Test that LangGraph agent now uses tools properly"""

    try:
        # Import after environment setup
        from app.data_analysis_v3.core.agent import DataAnalysisAgent

        # Create a test session ID
        test_session_id = "test_langgraph_fix"

        # Initialize the agent
        print("🔧 Initializing DataAnalysisAgent...")
        agent = DataAnalysisAgent(test_session_id)

        # Test 1: Check Option 1 Handler
        print("\n📝 Test 1: Option 1 Handler")
        result = await agent.analyze("1")
        print(f"  Success: {result.get('success')}")
        print(f"  Has response message: {bool(result.get('message'))}")
        if result.get('message'):
            print(f"  Message preview: {result.get('message', '')[:150]}")

        # Test 2: Check tool binding
        print("\n📝 Test 2: Tool Binding Check")
        print(f"  Tools available: {len(agent.tools)}")
        print(f"  Tool names: {[tool.name for tool in agent.tools]}")
        print(f"  Model has tools bound: {hasattr(agent, 'llm_with_tools')}")

        # Test 3: Simulate data analysis request
        print("\n📝 Test 3: Simulate Data Analysis Request")

        # Create sample data file
        import pandas as pd
        data_dir = f"instance/uploads/{test_session_id}"
        os.makedirs(data_dir, exist_ok=True)

        # Create test data
        test_data = pd.DataFrame({
            'State': ['Adamawa'] * 5,
            'LGA': ['LGA1', 'LGA2', 'LGA3', 'LGA4', 'LGA5'],
            'Positive': [10, 20, 15, 25, 30],
            'Tested': [100, 150, 120, 200, 180]
        })
        test_file = os.path.join(data_dir, 'test_data.csv')
        test_data.to_csv(test_file, index=False)
        print(f"  Created test data: {test_file}")

        # Reload agent to pick up data
        agent._check_and_add_tpr_tool()

        # Test analysis request
        analysis_result = await agent.analyze("Show me the shape of the data")
        print(f"  Analysis success: {analysis_result.get('success')}")
        print(f"  Has message: {bool(analysis_result.get('message'))}")

        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)
        if os.path.exists(data_dir) and not os.listdir(data_dir):
            os.rmdir(data_dir)

        print("\n✅ All tests completed!")
        return True

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing LangGraph Agent Fixes")
    print("=" * 60)

    # Run the async test
    success = asyncio.run(test_langgraph_agent())

    if success:
        print("\n🎉 Tests passed! LangGraph agent fixes appear to be working.")
        print("\nNext steps:")
        print("1. Test in browser with real data upload")
        print("2. Select Option 1 and ask analysis questions")
        print("3. Check browser console for tool calls")
        print("4. Deploy to production if working")
    else:
        print("\n⚠️ Tests failed. Please check the implementation.")
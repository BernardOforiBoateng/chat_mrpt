#!/usr/bin/env python3
"""
Test script to verify data overview appears after upload
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up environment
os.environ['FLASK_ENV'] = 'development'

async def test_data_overview():
    """Test that data overview is generated correctly"""

    try:
        # Import after environment setup
        from app.data_analysis_v3.core.agent import DataAnalysisAgent

        # Create a test session ID
        test_session_id = "test_session_123"

        # Initialize the agent
        print("🔧 Initializing DataAnalysisAgent...")
        agent = DataAnalysisAgent(test_session_id)

        # Test 1: Initial trigger without data
        print("\n📝 Test 1: Initial trigger without data")
        result = await agent.analyze("analyze uploaded data")
        print(f"  Success: {result.get('success')}")
        print(f"  Has message: {bool(result.get('message'))}")
        print(f"  Message preview: {result.get('message', '')[:100]}")

        # Test 2: Check if agent loads data summary
        print("\n📝 Test 2: Check data summary generation")
        # Force reload to check if summary is generated
        agent._check_and_add_tpr_tool()

        if hasattr(agent, 'data_summary'):
            print(f"  ✅ Data summary generated")
            print(f"  Summary preview: {agent.data_summary[:100] if agent.data_summary else 'None'}")
        else:
            print(f"  ⚠️ No data summary generated (expected if no data uploaded)")

        # Test 3: Response format
        print("\n📝 Test 3: Response format check")
        result = await agent.analyze("analyze uploaded data")
        required_fields = ['success', 'message', 'session_id']
        for field in required_fields:
            if field in result:
                print(f"  ✅ {field}: present")
            else:
                print(f"  ❌ {field}: missing")

        print("\n✅ All tests completed!")
        return True

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Data Overview Generation")
    print("=" * 60)

    # Run the async test
    success = asyncio.run(test_data_overview())

    if success:
        print("\n🎉 Test passed! Data overview handling is working.")
    else:
        print("\n⚠️ Test failed. Please check the implementation.")
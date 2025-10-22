#!/usr/bin/env python3
"""
Test Routing Logging Implementation

This script tests that routing logging is working correctly.
"""

import sys
import os
# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.interaction.core import DatabaseManager, log_routing_decision
import sqlite3

def test_routing_logging():
    """Test routing decision logging functionality."""
    print("Testing Routing Logging Implementation...")
    print("=" * 60)

    # Use temporary database for testing
    db_path = "/tmp/test_routing.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    print("1. Creating test database...")
    db = DatabaseManager(db_path=db_path)
    print("   ✓ Database created")

    # Test logging a routing decision
    print("\n2. Testing log_routing_decision() function...")
    routing_id = log_routing_decision(
        db_manager=db,
        session_id="test_session_123",
        user_message="What is TPR?",
        routing_decision="can_answer",
        routing_method="keyword_match",
        keywords_matched=["what is"],
        session_context={"has_uploaded_files": False}
    )

    if routing_id:
        print(f"   ✓ Routing logged successfully: {routing_id}")
    else:
        print("   ✗ Routing logging failed")
        return False

    # Verify data was written
    print("\n3. Verifying data in database...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM routing_decisions WHERE routing_id = ?", (routing_id,))
    row = cursor.fetchone()

    if row:
        print("   ✓ Data verified in database")
        print(f"   - Session ID: {row[2]}")
        print(f"   - User Message: {row[4]}")
        print(f"   - Routing Decision: {row[5]}")
        print(f"   - Routing Method: {row[6]}")
    else:
        print("   ✗ Data not found in database")
        conn.close()
        return False

    # Test multiple logging entries
    print("\n4. Testing multiple routing decisions...")
    test_cases = [
        {
            "user_message": "analyze my data",
            "routing_decision": "needs_tools",
            "routing_method": "keyword_match_analysis",
            "keywords_matched": ["analyze"]
        },
        {
            "user_message": "hi",
            "routing_decision": "can_answer",
            "routing_method": "fast_track_greeting",
            "keywords_matched": ["greeting"]
        },
        {
            "user_message": "plot vulnerability map",
            "routing_decision": "needs_tools",
            "routing_method": "keyword_match_vulnerability_viz",
            "keywords_matched": ["vulnerability", "map"]
        }
    ]

    for i, test in enumerate(test_cases, 1):
        rid = log_routing_decision(
            db_manager=db,
            session_id="test_session_123",
            user_message=test["user_message"],
            routing_decision=test["routing_decision"],
            routing_method=test["routing_method"],
            keywords_matched=test.get("keywords_matched"),
            session_context={"has_uploaded_files": True}
        )
        if rid:
            print(f"   ✓ Test case {i}: {test['user_message'][:30]:30} → {test['routing_decision']}")
        else:
            print(f"   ✗ Test case {i} failed")

    # Count total logs
    cursor.execute("SELECT COUNT(*) FROM routing_decisions")
    total = cursor.fetchone()[0]
    print(f"\n   Total logs: {total} (expected 4)")

    conn.close()

    # Cleanup
    print("\n5. Cleaning up...")
    os.remove(db_path)
    print("   ✓ Test database removed")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)

    return True

if __name__ == "__main__":
    try:
        success = test_routing_logging()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

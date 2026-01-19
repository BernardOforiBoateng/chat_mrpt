#!/usr/bin/env python3
"""
Routing Logs Monitoring Script

This script checks the routing_decisions table and displays statistics
about routing behavior.
"""

import sqlite3
from datetime import datetime, timedelta
import os

def main():
    db_path = "instance/interactions.db"

    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if routing_decisions table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='routing_decisions'")
    if not cursor.fetchone():
        print("✗ routing_decisions table NOT found in database")
        print("  Run the application once to create the table")
        conn.close()
        return

    print("✓ routing_decisions table exists\n")

    # Check routing logs from last 24 hours
    yesterday = datetime.now() - timedelta(days=1)
    cursor.execute("""
        SELECT
            routing_decision,
            routing_method,
            COUNT(*) as count
        FROM routing_decisions
        WHERE timestamp > ?
        GROUP BY routing_decision, routing_method
        ORDER BY count DESC
    """, (yesterday,))

    print("Routing Statistics (Last 24 Hours):")
    print("=" * 70)
    results = cursor.fetchall()
    if results:
        for row in results:
            decision, method, count = row
            print(f"{decision:20} {method:30} {count:5} logs")
    else:
        print("No routing logs in the last 24 hours")

    # Check total logs
    cursor.execute("SELECT COUNT(*) FROM routing_decisions")
    total = cursor.fetchone()[0]
    print(f"\nTotal routing logs: {total}")

    # Show most recent routing decisions
    print("\n" + "=" * 70)
    print("Most Recent Routing Decisions (Last 10):")
    print("=" * 70)
    cursor.execute("""
        SELECT
            datetime(timestamp) as time,
            substr(user_message, 1, 40) as message,
            routing_decision,
            routing_method
        FROM routing_decisions
        ORDER BY timestamp DESC
        LIMIT 10
    """)

    for row in cursor.fetchall():
        time, message, decision, method = row
        print(f"{time} | {message:40} | {decision:15} | {method}")

    # Show Ollama routing statistics
    cursor.execute("""
        SELECT COUNT(*) FROM routing_decisions
        WHERE routing_method = 'ollama_decision'
    """)
    ollama_count = cursor.fetchone()[0]

    if ollama_count > 0:
        print(f"\n" + "=" * 70)
        print(f"Ollama-routed messages: {ollama_count}")
        print("=" * 70)

        cursor.execute("""
            SELECT
                routing_decision,
                COUNT(*) as count
            FROM routing_decisions
            WHERE routing_method = 'ollama_decision'
            GROUP BY routing_decision
        """)

        for row in cursor.fetchall():
            decision, count = row
            print(f"  {decision}: {count}")

    conn.close()

if __name__ == "__main__":
    main()

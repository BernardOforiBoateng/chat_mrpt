#!/usr/bin/env python3
"""
Routing Data Export Script

Exports routing decisions data to CSV for analysis.
"""

import sqlite3
import pandas as pd
from datetime import datetime
import os

def main():
    db_path = "instance/interactions.db"
    output_path = f"routing_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)

    # Export all routing decisions with context
    query = """
    SELECT
        r.routing_id,
        r.message_id,
        r.session_id,
        r.timestamp,
        r.user_message,
        r.routing_decision,
        r.routing_method,
        r.keywords_matched,
        r.confidence,
        r.ollama_reasoning,
        r.session_context,
        m.content as assistant_response,
        m.intent as detected_intent
    FROM routing_decisions r
    LEFT JOIN messages m ON r.message_id = m.message_id AND m.sender = 'assistant'
    ORDER BY r.timestamp
    """

    print(f"Exporting routing data from {db_path}...")
    df = pd.read_sql_query(query, conn)
    conn.close()

    df.to_csv(output_path, index=False)
    print(f"✓ Exported {len(df)} routing decisions to {output_path}")

    # Print summary statistics
    print("\nSummary Statistics:")
    print("=" * 60)
    print(f"Total routing decisions: {len(df)}")
    print(f"\nRouting decisions breakdown:")
    print(df['routing_decision'].value_counts())
    print(f"\nRouting methods breakdown:")
    print(df['routing_method'].value_counts())

    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        print(f"\nDate range: {df['timestamp'].min()} to {df['timestamp'].max()}")

if __name__ == "__main__":
    main()

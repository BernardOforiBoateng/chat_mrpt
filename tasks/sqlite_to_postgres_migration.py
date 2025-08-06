#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script for ChatMRPT
This script migrates data from SQLite to PostgreSQL while preserving data integrity
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import sys
import os
from datetime import datetime

# Database connections
SQLITE_DB = '/home/ec2-user/ChatMRPT/instance/interactions.db'
POSTGRES_CONFIG = {
    'host': 'chatmrpt-staging-db.c3yi24k2gtqu.us-east-2.rds.amazonaws.com',
    'port': 5432,
    'database': 'postgres',
    'user': 'chatmrptadmin',
    'password': '1IyPCV5J71jY2nOu1FogVOViC'
}

def create_postgres_schema(pg_conn):
    """Create the schema in PostgreSQL"""
    cursor = pg_conn.cursor()
    
    # Create interactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interaction (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255),
            session_id VARCHAR(255),
            message TEXT,
            response TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            message_type VARCHAR(50),
            context TEXT,
            analysis_complete BOOLEAN DEFAULT FALSE,
            file_uploaded BOOLEAN DEFAULT FALSE,
            error_occurred BOOLEAN DEFAULT FALSE,
            error_message TEXT,
            processing_time FLOAT,
            tokens_used INTEGER,
            model_used VARCHAR(100),
            tool_calls TEXT,
            feedback_rating INTEGER,
            feedback_text TEXT
        );
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON interaction(session_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON interaction(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON interaction(timestamp);")
    
    pg_conn.commit()
    print("PostgreSQL schema created successfully")

def get_sqlite_tables(sqlite_conn):
    """Get all tables from SQLite database"""
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    return [row[0] for row in cursor.fetchall()]

def get_table_schema(sqlite_conn, table_name):
    """Get schema information for a table"""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    return cursor.fetchall()

def migrate_interactions_table(sqlite_conn, pg_conn):
    """Migrate the interactions table"""
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    # Get all data from SQLite
    sqlite_cursor.execute("SELECT * FROM interaction")
    columns = [description[0] for description in sqlite_cursor.description]
    rows = sqlite_cursor.fetchall()
    
    print(f"Found {len(rows)} rows to migrate from interaction table")
    
    if rows:
        # Prepare insert query
        insert_query = f"""
            INSERT INTO interaction ({', '.join(columns)}) 
            VALUES %s
            ON CONFLICT (id) DO NOTHING
        """
        
        # Batch insert
        batch_size = 1000
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i+batch_size]
            execute_values(pg_cursor, insert_query, batch)
            print(f"Migrated {min(i+batch_size, len(rows))}/{len(rows)} rows")
        
        pg_conn.commit()
        print("Interaction table migration completed")

def verify_migration(sqlite_conn, pg_conn):
    """Verify that migration was successful"""
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    # Count rows in SQLite
    sqlite_cursor.execute("SELECT COUNT(*) FROM interaction")
    sqlite_count = sqlite_cursor.fetchone()[0]
    
    # Count rows in PostgreSQL
    pg_cursor.execute("SELECT COUNT(*) FROM interaction")
    pg_count = pg_cursor.fetchone()[0]
    
    print(f"\nVerification:")
    print(f"SQLite rows: {sqlite_count}")
    print(f"PostgreSQL rows: {pg_count}")
    
    if sqlite_count == pg_count:
        print("✓ Migration successful - row counts match")
        return True
    else:
        print("✗ Migration failed - row counts don't match")
        return False

def main():
    """Main migration function"""
    print("Starting SQLite to PostgreSQL migration...")
    print(f"Timestamp: {datetime.now()}")
    
    try:
        # Connect to databases
        sqlite_conn = sqlite3.connect(SQLITE_DB)
        pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
        
        print(f"Connected to SQLite: {SQLITE_DB}")
        print(f"Connected to PostgreSQL: {POSTGRES_CONFIG['host']}")
        
        # Create schema
        create_postgres_schema(pg_conn)
        
        # Get tables
        tables = get_sqlite_tables(sqlite_conn)
        print(f"\nFound tables: {tables}")
        
        # Migrate interactions table
        if 'interaction' in tables:
            migrate_interactions_table(sqlite_conn, pg_conn)
        
        # Verify migration
        if verify_migration(sqlite_conn, pg_conn):
            print("\n✓ Migration completed successfully!")
        else:
            print("\n✗ Migration completed with errors")
            
    except Exception as e:
        print(f"\nError during migration: {e}")
        sys.exit(1)
    finally:
        sqlite_conn.close()
        pg_conn.close()
        print("\nDatabase connections closed")

if __name__ == "__main__":
    main()
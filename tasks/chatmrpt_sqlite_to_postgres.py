#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script for ChatMRPT
Migrates the actual ChatMRPT database schema
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import json
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
    """Create all tables in PostgreSQL"""
    cursor = pg_conn.cursor()
    
    # Create sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            user_id TEXT,
            interaction_mode TEXT,
            analysis_type TEXT,
            total_messages INTEGER,
            analysis_completed BOOLEAN
        );
    """)
    
    # Create messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            message_id TEXT PRIMARY KEY,
            session_id TEXT,
            timestamp TIMESTAMP,
            sender TEXT,
            content TEXT,
            intent TEXT,
            entities TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        );
    """)
    
    # Create file_uploads table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_uploads (
            upload_id TEXT PRIMARY KEY,
            session_id TEXT,
            timestamp TIMESTAMP,
            filename TEXT,
            file_type TEXT,
            file_path TEXT,
            file_size INTEGER,
            processing_status TEXT,
            metadata TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        );
    """)
    
    # Create analysis_events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_events (
            event_id TEXT PRIMARY KEY,
            session_id TEXT,
            timestamp TIMESTAMP,
            event_type TEXT,
            event_data TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        );
    """)
    
    # Create errors table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS errors (
            error_id TEXT PRIMARY KEY,
            session_id TEXT,
            timestamp TIMESTAMP,
            error_type TEXT,
            error_message TEXT,
            stack_trace TEXT,
            context TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        );
    """)
    
    # Create other tables
    tables = [
        """CREATE TABLE IF NOT EXISTS analysis_steps (
            step_id TEXT PRIMARY KEY,
            session_id TEXT,
            timestamp TIMESTAMP,
            step_name TEXT,
            step_type TEXT,
            input_data TEXT,
            output_data TEXT,
            duration REAL,
            success BOOLEAN,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        );""",
        
        """CREATE TABLE IF NOT EXISTS llm_interactions (
            interaction_id TEXT PRIMARY KEY,
            session_id TEXT,
            timestamp TIMESTAMP,
            prompt TEXT,
            response TEXT,
            model TEXT,
            tokens_used INTEGER,
            cost REAL,
            duration REAL,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        );""",
        
        """CREATE TABLE IF NOT EXISTS ward_rankings (
            ranking_id TEXT PRIMARY KEY,
            session_id TEXT,
            timestamp TIMESTAMP,
            ward_name TEXT,
            rank INTEGER,
            score REAL,
            algorithm TEXT,
            variables_used TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        );"""
    ]
    
    for table_sql in tables:
        cursor.execute(table_sql)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);")
    
    pg_conn.commit()
    print("✓ PostgreSQL schema created successfully")

def migrate_table(sqlite_conn, pg_conn, table_name):
    """Migrate a single table from SQLite to PostgreSQL"""
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    try:
        # Get data from SQLite
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        columns = [description[0] for description in sqlite_cursor.description]
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print(f"  - {table_name}: No data to migrate")
            return
        
        print(f"  - {table_name}: Migrating {len(rows)} rows...", end='')
        
        # Create insert query
        placeholders = ','.join(['%s'] * len(columns))
        insert_query = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
        
        # Batch insert
        batch_size = 500
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i+batch_size]
            for row in batch:
                pg_cursor.execute(insert_query, row)
        
        pg_conn.commit()
        print(f" ✓ Done")
        
    except Exception as e:
        print(f" ✗ Error: {e}")
        pg_conn.rollback()

def verify_migration(sqlite_conn, pg_conn):
    """Verify migration results"""
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    print("\n📊 Migration Verification:")
    print("-" * 40)
    
    # Get list of tables
    sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in sqlite_cursor.fetchall()]
    
    total_sqlite = 0
    total_pg = 0
    
    for table in tables:
        # Count SQLite rows
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        sqlite_count = sqlite_cursor.fetchone()[0]
        total_sqlite += sqlite_count
        
        # Count PostgreSQL rows
        try:
            pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            pg_count = pg_cursor.fetchone()[0]
            total_pg += pg_count
            
            status = "✓" if sqlite_count == pg_count else "✗"
            print(f"{status} {table}: SQLite={sqlite_count}, PostgreSQL={pg_count}")
        except:
            print(f"✗ {table}: Not migrated")
    
    print("-" * 40)
    print(f"Total: SQLite={total_sqlite}, PostgreSQL={total_pg}")
    
    return total_sqlite == total_pg

def main():
    """Main migration function"""
    print("🚀 ChatMRPT SQLite to PostgreSQL Migration")
    print(f"📅 Started: {datetime.now()}\n")
    
    try:
        # Connect to databases
        sqlite_conn = sqlite3.connect(SQLITE_DB)
        pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
        
        print(f"✓ Connected to SQLite: {SQLITE_DB}")
        print(f"✓ Connected to PostgreSQL: {POSTGRES_CONFIG['host']}\n")
        
        # Create schema
        print("📋 Creating PostgreSQL schema...")
        create_postgres_schema(pg_conn)
        
        # Get tables to migrate
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"\n📦 Migrating {len(tables)} tables:")
        
        # Migrate tables in order (respecting foreign keys)
        ordered_tables = ['sessions', 'messages', 'file_uploads', 'analysis_events', 
                         'errors', 'analysis_steps', 'llm_interactions', 'ward_rankings']
        
        # Add any remaining tables
        for table in tables:
            if table not in ordered_tables:
                ordered_tables.append(table)
        
        for table in ordered_tables:
            if table in tables:
                migrate_table(sqlite_conn, pg_conn, table)
        
        # Verify migration
        if verify_migration(sqlite_conn, pg_conn):
            print("\n✅ Migration completed successfully!")
        else:
            print("\n⚠️  Migration completed with discrepancies")
            
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        return 1
    finally:
        sqlite_conn.close()
        pg_conn.close()
        print(f"\n📅 Completed: {datetime.now()}")

if __name__ == "__main__":
    main()
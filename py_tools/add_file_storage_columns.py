#!/usr/bin/env python3
"""
Migration script to add file storage columns to existing database.
This script safely adds the new BYTEA columns for storing files in the database.

Usage:
    python add_file_storage_columns.py

This script will:
1. Check if columns already exist
2. Add missing columns if needed
3. Preserve all existing data
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/paper_portal")

# Create engine
if "neon.tech" in DATABASE_URL or "neondb" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "sslmode": "require",
            "connect_timeout": 10,
        },
        pool_pre_ping=True,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 10}
    )

def column_exists(conn, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    # Use SQL query to check if column exists (more reliable)
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = :table_name AND column_name = :column_name
    """), {"table_name": table_name, "column_name": column_name})
    return result.fetchone() is not None

def add_column_if_not_exists(conn, table_name: str, column_name: str, column_type: str):
    """Add a column to a table if it doesn't exist"""
    if not column_exists(conn, table_name, column_name):
        print(f"  Adding column {table_name}.{column_name}...")
        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
        print(f"  ✅ Added {table_name}.{column_name}")
    else:
        print(f"  ✓ Column {table_name}.{column_name} already exists")

def main():
    print("=" * 70)
    print("Database Migration: Adding File Storage Columns")
    print("=" * 70)
    print()
    
    try:
        with engine.begin() as conn:
            # Check if tables exist using SQL
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            
            if 'users' not in tables:
                print("⚠️  Warning: 'users' table not found. Run the app first to create tables.")
                return
            
            if 'papers' not in tables:
                print("⚠️  Warning: 'papers' table not found. Run the app first to create tables.")
                return
            
            print("Checking and adding columns...")
            print()
            
            # Add columns to users table
            print("📋 Users table:")
            add_column_if_not_exists(conn, 'users', 'photo_data', 'BYTEA')
            add_column_if_not_exists(conn, 'users', 'id_card_data', 'BYTEA')
            print()
            
            # Add columns to papers table
            print("📋 Papers table:")
            add_column_if_not_exists(conn, 'papers', 'file_data', 'BYTEA')
            
            # Make file_path nullable if it's not already (for backward compatibility)
            try:
                # Check if file_path is NOT NULL
                result = conn.execute(text("""
                    SELECT is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'papers' AND column_name = 'file_path'
                """))
                row = result.fetchone()
                if row and row[0] == 'NO':
                    print("  Making file_path nullable for backward compatibility...")
                    conn.execute(text("ALTER TABLE papers ALTER COLUMN file_path DROP NOT NULL"))
                    print("  ✅ Made file_path nullable")
            except Exception as e:
                print(f"  ⚠️  Could not modify file_path: {e}")
            
            print()
            print("=" * 70)
            print("✅ Migration completed successfully!")
            print("=" * 70)
            print()
            print("The database is now ready to store files in the database.")
            print("New uploads will be stored in the BYTEA columns.")
            print()
            
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


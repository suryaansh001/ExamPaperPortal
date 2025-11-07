#!/usr/bin/env python3
"""
Migration Script: SQLite to PostgreSQL
Migrates data from local SQLite database to PostgreSQL (Render)
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# SQLite database (source)
SQLITE_URL = "sqlite:///paper_portal.db"

# PostgreSQL database (destination) - from environment variable
POSTGRES_URL = os.getenv("DATABASE_URL")

if not POSTGRES_URL:
    print("❌ ERROR: DATABASE_URL not found in environment")
    print("Please set DATABASE_URL to your Render PostgreSQL connection string")
    sys.exit(1)

print("🔄 Starting migration from SQLite to PostgreSQL...")
print(f"Source: {SQLITE_URL}")
print(f"Destination: {POSTGRES_URL.split('@')[1] if '@' in POSTGRES_URL else '***'}\n")

# Create engines
sqlite_engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
postgres_engine = create_engine(POSTGRES_URL)

sqlite_session = sessionmaker(bind=sqlite_engine)()
postgres_session = sessionmaker(bind=postgres_engine)()

try:
    # Test connections
    print("📡 Testing connections...")
    sqlite_engine.connect()
    postgres_engine.connect()
    print("✅ Both databases connected\n")
    
    # Get all tables from SQLite
    print("📋 Reading tables from SQLite...")
    tables_query = text("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
    """)
    tables = sqlite_session.execute(tables_query).fetchall()
    table_names = [table[0] for table in tables]
    print(f"Found {len(table_names)} tables: {', '.join(table_names)}\n")
    
    # Migrate each table
    for table_name in table_names:
        print(f"🔄 Migrating table: {table_name}")
        
        # Get all data from SQLite
        select_query = text(f"SELECT * FROM {table_name}")
        rows = sqlite_session.execute(select_query).fetchall()
        
        if not rows:
            print(f"   ⚠️  Table {table_name} is empty, skipping...\n")
            continue
        
        # Get column names
        columns_query = text(f"PRAGMA table_info({table_name})")
        columns_info = sqlite_session.execute(columns_query).fetchall()
        column_names = [col[1] for col in columns_info]
        
        print(f"   Found {len(rows)} rows")
        
        # Insert into PostgreSQL
        inserted = 0
        for row in rows:
            try:
                # Build INSERT query
                values = dict(zip(column_names, row))
                placeholders = ', '.join([f':{col}' for col in column_names])
                columns = ', '.join(column_names)
                
                insert_query = text(f"""
                    INSERT INTO {table_name} ({columns})
                    VALUES ({placeholders})
                    ON CONFLICT DO NOTHING
                """)
                
                postgres_session.execute(insert_query, values)
                inserted += 1
            except Exception as e:
                print(f"   ⚠️  Error inserting row: {e}")
                continue
        
        postgres_session.commit()
        print(f"   ✅ Migrated {inserted}/{len(rows)} rows\n")
    
    print("✅ Migration completed successfully!")
    print("\n📊 Summary:")
    for table_name in table_names:
        count_query = text(f"SELECT COUNT(*) FROM {table_name}")
        count = postgres_session.execute(count_query).scalar()
        print(f"   {table_name}: {count} rows")
    
except Exception as e:
    print(f"\n❌ Migration failed: {e}")
    postgres_session.rollback()
    sys.exit(1)
finally:
    sqlite_session.close()
    postgres_session.close()



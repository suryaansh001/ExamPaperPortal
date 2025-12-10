#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup script for Railway PostgreSQL Database
This script connects to Railway PostgreSQL and creates all necessary tables.
"""

import os
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Railway PostgreSQL connection string
RAILWAY_DATABASE_URL = "postgresql://postgres:yvFPUoOUFxjaiLqtimFIZRDgcqavpCeU@yamabiko.proxy.rlwy.net:21623/railway"

# Set environment variable BEFORE importing main.py (which reads DATABASE_URL)
os.environ["DATABASE_URL"] = RAILWAY_DATABASE_URL
print(f"Using Railway PostgreSQL connection string")

print("=" * 70)
print("Railway PostgreSQL Database Setup")
print("=" * 70)
db_host = RAILWAY_DATABASE_URL.split('@')[1] if '@' in RAILWAY_DATABASE_URL else 'Railway PostgreSQL'
print(f"Connecting to: {db_host}")
print()

try:
    # Import models from main.py FIRST (will use Railway DATABASE_URL from environment)
    print("Importing database models...")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Import Base, models, and engine from main.py
    from main import Base, User, Course, Paper, engine
    
    print("Models imported successfully")
    print()
    
    # Test connection using engine from main.py
    print("Testing database connection...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print("Connected successfully!")
        print(f"   PostgreSQL Version: {version.split(',')[0]}")
    print()
    
    print("Models imported successfully")
    print()
    
    # Create all tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")
    print()
    
    # Verify tables were created
    print("Verifying tables...")
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    expected_tables = ['users', 'courses', 'papers']
    print(f"   Found {len(tables)} table(s):")
    for table in sorted(tables):
        status = "[OK]" if table in expected_tables else "[WARN]"
        print(f"   {status} {table}")
    
    # Check if all expected tables exist
    missing_tables = [t for t in expected_tables if t not in tables]
    if missing_tables:
        print(f"\n[WARN] Missing tables: {', '.join(missing_tables)}")
    else:
        print("\n[OK] All expected tables are present!")
    print()
    
    # Show table structures
    print("Table Structures:")
    print()
    for table_name in expected_tables:
        if table_name in tables:
            columns = inspector.get_columns(table_name)
            print(f"   {table_name}:")
            for col in columns:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                print(f"      - {col['name']}: {col['type']} ({nullable})")
            print()
    
    # Get database size info
    print("Database Information:")
    with engine.connect() as conn:
        # Get database size
        result = conn.execute(text("""
            SELECT pg_size_pretty(pg_database_size(current_database())) AS size
        """))
        db_size = result.fetchone()[0]
        print(f"   Database Size: {db_size}")
        
        # Get table row counts
        for table_name in expected_tables:
            if table_name in tables:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.fetchone()[0]
                    print(f"   {table_name}: {count} row(s)")
                except Exception as e:
                    print(f"   {table_name}: Error counting rows - {e}")
    
    print()
    print("=" * 70)
    print("[SUCCESS] Database setup completed successfully!")
    print("=" * 70)
    print()
    print("Next Steps:")
    print("   1. Update your Railway backend service DATABASE_URL environment variable")
    print("   2. Set DATABASE_URL to: postgresql://postgres:yvFPUoOUFxjaiLqtimFIZRDgcqavpCeU@yamabiko.proxy.rlwy.net:21623/railway")
    print("   3. Redeploy your backend service")
    print("   4. Your backend will now use Railway PostgreSQL!")
    print()

except Exception as e:
    print()
    print("=" * 70)
    print("[ERROR] Error setting up database")
    print("=" * 70)
    print(f"Error: {str(e)}")
    print()
    print("Troubleshooting:")
    print("   1. Check if the connection string is correct")
    print("   2. Verify Railway PostgreSQL service is running")
    print("   3. Check network connectivity")
    print()
    sys.exit(1)


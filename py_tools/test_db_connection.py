#!/usr/bin/env python3
"""
Database Connection Test Script
Tests the connection to the PostgreSQL database using SQLAlchemy
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL not found in .env file")
    print("Please make sure your .env file contains:")
    print("DATABASE_URL='postgresql://username:password@host:port/database'")
    exit(1)

print(f"🔍 Testing connection to: {DATABASE_URL.replace(DATABASE_URL.split('@')[0], '***:***@')}")
print()

try:
    # Create engine
    engine = create_engine(DATABASE_URL)

    # Test connection
    with engine.connect() as conn:
        # Execute a simple query
        result = conn.execute(text("SELECT 1 as test"))
        row = result.fetchone()
        if row and row[0] == 1:
            print("✅ Database connection successful!")
            print("✅ Query execution successful!")
        else:
            print("❌ Query execution failed!")

    # Test if tables exist (optional)
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = result.fetchall()
            if tables:
                print(f"📋 Found {len(tables)} tables in database:")
                for table in tables[:5]:  # Show first 5
                    print(f"   - {table[0]}")
                if len(tables) > 5:
                    print(f"   ... and {len(tables) - 5} more")
            else:
                print("📋 No tables found in database (run setup.py to create them)")
    except Exception as e:
        print(f"⚠️  Could not check tables: {e}")

except Exception as e:
    print(f"❌ Database connection failed: {e}")
    print()
    print("💡 Troubleshooting tips:")
    print("   - Check if PostgreSQL is running")
    print("   - Verify DATABASE_URL in .env file")
    print("   - Check network connectivity (if using cloud DB)")
    print("   - Ensure SSL settings are correct (for Neon, etc.)")

print()
print("Test completed.")
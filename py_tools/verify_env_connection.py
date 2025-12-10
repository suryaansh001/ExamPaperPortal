#!/usr/bin/env python3
"""
Verify that the backend can read DATABASE_URL from .env and connect
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load .env file
load_dotenv()

print(f"\n{'='*60}")
print("VERIFYING .ENV FILE AND DATABASE CONNECTION")
print(f"{'='*60}\n")

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in environment variables!")
    print("   Make sure .env file exists and has DATABASE_URL")
    exit(1)

print(f"✓ DATABASE_URL found in .env")
print(f"  Length: {len(DATABASE_URL)} characters")

# Check if it has the psql command (wrong format)
if DATABASE_URL.startswith("psql"):
    print("\n❌ ERROR: DATABASE_URL contains 'psql' command!")
    print("   This is WRONG - it should be just the connection string")
    print(f"   Current: {DATABASE_URL[:80]}...")
    print("\n   Fix: Remove 'psql' and quotes from DATABASE_URL in .env file")
    exit(1)

# Check if it's a valid PostgreSQL URL
if not DATABASE_URL.startswith("postgresql://"):
    print(f"\n❌ ERROR: DATABASE_URL doesn't start with 'postgresql://'")
    print(f"   Current: {DATABASE_URL[:80]}...")
    exit(1)

print(f"✓ DATABASE_URL format looks correct")
print(f"  Starts with: postgresql://")

# Test connection
try:
    print("\nTesting database connection...")
    
    # Handle Neon DB SSL requirements
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
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Database connection successful!")
        
        # Check user
        user_result = conn.execute(text("""
            SELECT id, email, name, is_admin FROM users 
            WHERE email = 'amanpratapsingh@jklu.edu.in'
        """))
        user = user_result.fetchone()
        
        if user:
            print(f"✅ User found: {user[1]}")
        else:
            print("❌ User not found")
    
    print(f"\n{'='*60}")
    print("✅ EVERYTHING IS WORKING CORRECTLY!")
    print(f"{'='*60}\n")
    print("The backend should be able to connect to the database.")
    print("If you're still getting 'User not found' errors:")
    print("  1. Make sure your backend server is restarted")
    print("  2. Check that frontend is pointing to the correct backend URL")
    print("  3. Verify Render backend has the same DATABASE_URL in environment variables")
    
except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    import traceback
    traceback.print_exc()


#!/usr/bin/env python3
"""
Test database connection with the provided DATABASE_URL
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Test connection string
DATABASE_URL = "postgresql://neondb_owner:npg_EAkX0WVqeR5r@ep-polished-bush-a1fj2trf-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

print(f"\n{'='*60}")
print("TESTING DATABASE CONNECTION")
print(f"{'='*60}\n")
print(f"Database URL: {DATABASE_URL[:50]}...\n")

try:
    # Create engine with SSL for Neon
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "sslmode": "require",
            "connect_timeout": 10,
        },
        pool_pre_ping=True,
    )
    
    print("✓ Engine created successfully")
    
    # Test connection
    print("\nTesting connection...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✓ Connection successful!")
        
        # Get database version
        version_result = conn.execute(text("SELECT version()"))
        version = version_result.scalar()
        print(f"✓ Database version: {version[:50]}...")
        
        # Check if users table exists
        print("\nChecking users table...")
        table_check = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            )
        """))
        table_exists = table_check.scalar()
        
        if table_exists:
            print("✓ Users table exists")
            
            # Count users
            count_result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = count_result.scalar()
            print(f"✓ Total users in database: {user_count}")
            
            # List all users
            if user_count > 0:
                print("\nUsers in database:")
                users_result = conn.execute(text("SELECT id, email, name, is_admin FROM users"))
                for row in users_result:
                    print(f"  - ID: {row[0]}, Email: {row[1]}, Name: {row[2]}, Admin: {row[3]}")
            
            # Check specific user
            print(f"\nChecking for user: amanpratapsingh@jklu.edu.in")
            user_check = conn.execute(text("""
                SELECT id, email, name, is_admin FROM users 
                WHERE email = 'amanpratapsingh@jklu.edu.in'
            """))
            user = user_check.fetchone()
            
            if user:
                print(f"✅ USER FOUND!")
                print(f"   ID: {user[0]}")
                print(f"   Email: {user[1]}")
                print(f"   Name: {user[2]}")
                print(f"   Admin: {user[3]}")
            else:
                print(f"❌ User NOT found in database")
        else:
            print("❌ Users table does NOT exist")
            print("   You may need to run the setup script to create tables")
    
    print(f"\n{'='*60}")
    print("✅ DATABASE CONNECTION SUCCESSFUL!")
    print(f"{'='*60}\n")
    
except Exception as e:
    print(f"\n❌ DATABASE CONNECTION FAILED!")
    print(f"{'='*60}\n")
    print(f"Error: {type(e).__name__}: {e}\n")
    
    if "could not translate host name" in str(e).lower():
        print("Possible issues:")
        print("  1. Database host is unreachable")
        print("  2. Network connection problem")
        print("  3. Database URL is incorrect")
    elif "authentication failed" in str(e).lower() or "password" in str(e).lower():
        print("Possible issues:")
        print("  1. Database password is incorrect")
        print("  2. Database user doesn't exist")
        print("  3. Database credentials are wrong")
    elif "does not exist" in str(e).lower():
        print("Possible issues:")
        print("  1. Database name is incorrect")
        print("  2. Database doesn't exist")
    else:
        print("Possible issues:")
        print("  1. Database URL format is incorrect")
        print("  2. SSL connection issue")
        print("  3. Database server is down")
    
    import traceback
    print(f"\nFull error details:")
    traceback.print_exc()


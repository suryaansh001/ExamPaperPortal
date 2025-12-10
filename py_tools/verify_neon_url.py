#!/usr/bin/env python3
"""
Verify which Neon database URL is being used
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

print("="*70)
print("🔍 VERIFYING NEON DATABASE CONNECTION")
print("="*70)
print()

# Get URL from .env
env_url = os.getenv("DATABASE_URL", "")

print("1️⃣  .env File Configuration:")
print(f"   DATABASE_URL: {env_url[:80]}...")
print()

# Check which database
old_url_identifier = "ep-plain-mouse-a13pemef"
new_url_identifier = "ep-polished-bush-a1fj2trf"

if old_url_identifier in env_url:
    print("   ⚠️  OLD Neon database URL detected!")
    print("   URL contains: ep-plain-mouse-a13pemef")
elif new_url_identifier in env_url:
    print("   ✅ NEW Neon database URL detected!")
    print("   URL contains: ep-polished-bush-a1fj2trf")
else:
    print("   ⚠️  Unknown database URL")
print()

# Test backend import
print("2️⃣  Backend Configuration:")
try:
    from main import DATABASE_URL as backend_url, engine
    
    print(f"   Backend DATABASE_URL: {backend_url[:80]}...")
    print()
    
    if old_url_identifier in backend_url:
        print("   ⚠️  Backend using OLD Neon database!")
    elif new_url_identifier in backend_url:
        print("   ✅ Backend using NEW Neon database!")
    else:
        print("   ⚠️  Unknown database")
    print()
    
    # Test actual connection
    print("3️⃣  Testing Actual Connection:")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT current_database()"))
        db_name = result.scalar()
        print(f"   ✅ Connected to database: {db_name}")
        
        # Get connection info
        try:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"   ✅ PostgreSQL version: {version[:50]}...")
        except:
            pass
        
        # Check users
        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()
        print(f"   ✅ Users in database: {user_count}")
    
    print()
    print("="*70)
    
    if new_url_identifier in backend_url:
        print("✅ CONFIRMED: Backend is using NEW Neon database!")
        print("="*70)
        print()
        print("📊 Summary:")
        print(f"   • .env file: ✅ Has NEW URL")
        print(f"   • Backend: ✅ Using NEW URL")
        print(f"   • Connection: ✅ Working")
        print(f"   • Database: ✅ {db_name}")
        print(f"   • Users: ✅ {user_count} users")
        print()
        print("🎯 Your backend is connected to the NEW Neon database!")
    else:
        print("⚠️  WARNING: Backend might be using OLD database!")
        print("="*70)
        print()
        print("Please check your .env file and restart the backend.")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()


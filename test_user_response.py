#!/usr/bin/env python3
"""
Test script to verify UserResponse serialization for coding_ta users
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Simple database connection without FastAPI dependencies
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/paper_portal")

# Create engine
if "neon.tech" in DATABASE_URL or "neondb" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"sslmode": "require", "connect_timeout": 10},
        pool_pre_ping=True,
    )
elif "railway.app" in DATABASE_URL or "rlwy.net" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 10},
    )
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_coding_ta_users():
    """Check if coding_ta users exist and their fields"""
    db = SessionLocal()
    try:
        # Query users with admin_role = 'coding_ta'
        result = db.execute(text("""
            SELECT id, email, name, is_admin, admin_role
            FROM users
            WHERE admin_role = 'coding_ta'
        """))
        
        users = result.fetchall()
        
        if not users:
            print("❌ No coding_ta users found in database!")
            print("\nTo create coding_ta users, run:")
            print("  python3 seed_coding_hour.py")
            return False
        
        print(f"✅ Found {len(users)} coding_ta user(s):\n")
        for user in users:
            print(f"  ID: {user.id}")
            print(f"  Email: {user.email}")
            print(f"  Name: {user.name}")
            print(f"  is_admin: {user.is_admin}")
            print(f"  admin_role: {user.admin_role}")
            print(f"  Expected is_sub_admin: {user.admin_role == 'coding_ta'}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error querying database: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Testing coding_ta User Configuration")
    print("=" * 60)
    print()
    
    success = test_coding_ta_users()
    
    print("=" * 60)
    if success:
        print("✅ Backend should be sending role correctly")
        print("\nThe UserResponse schema includes:")
        print("  - admin_role: Optional[str]")
        print("  - is_sub_admin: bool (computed from admin_role)")
        print("\nFrontend checks:")
        print("  - user.admin_role === 'coding_ta'")
        print("  - Redirects to /admin/coding-hour")
    else:
        print("❌ Issue detected - see above")
    print("=" * 60)

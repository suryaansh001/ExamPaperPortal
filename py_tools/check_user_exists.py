#!/usr/bin/env python3
"""
Check if a user exists in the database
"""

import os
import sys
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in environment variables!")
    print("   Make sure .env file exists with DATABASE_URL")
    exit(1)

# Simple User model for checking
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String)
    name = Column(String)
    is_admin = Column(Boolean)
    email_verified = Column(Boolean)

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

SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def check_user(email: str):
    """Check if user exists"""
    print(f"\n{'='*60}")
    print("CHECKING USER IN DATABASE")
    print(f"{'='*60}\n")
    
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            print(f"✅ User found!")
            print(f"  Email: {user.email}")
            print(f"  Name: {user.name}")
            print(f"  Admin: {user.is_admin}")
            print(f"  Email Verified: {user.email_verified}")
            print(f"  User ID: {user.id}")
            return True
        else:
            print(f"❌ User NOT found in database")
            print(f"  Email: {email}")
            print(f"\n  Solution: User needs to register first")
            return False
            
    except Exception as e:
        print(f"❌ Error checking user: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    email = "amanparatapsingh@jklu.edu.in"
    check_user(email)
    
    print(f"\n{'='*60}")
    print("ALL USERS IN DATABASE:")
    print(f"{'='*60}\n")
    
    db = SessionLocal()
    try:
        all_users = db.query(User).all()
        if all_users:
            for user in all_users:
                print(f"  - {user.email} ({user.name}) - Admin: {user.is_admin}")
        else:
            print("  No users found in database")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()


#!/usr/bin/env python3
"""
Create a student user in the database
"""

import os
import sys
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from passlib.context import CryptContext
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in environment variables!")
    exit(1)

# Simple User model
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String)
    name = Column(String)
    password_hash = Column(String)
    is_admin = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    created_at = Column(String)  # Simplified for checking

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

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_student_user(email: str, name: str, password: str):
    """Create a student user"""
    print(f"\n{'='*60}")
    print("CREATING STUDENT USER")
    print(f"{'='*60}\n")
    
    try:
        # Check if user exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"⚠️  User {email} already exists!")
            print(f"   Name: {existing.name}")
            print(f"   Admin: {existing.is_admin}")
            return existing
        
        # Create new user
        hashed_password = pwd_context.hash(password)
        new_user = User(
            email=email,
            name=name,
            password_hash=hashed_password,
            is_admin=False,
            email_verified=True  # Auto-verify for manually created users
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"✅ Student user created successfully!")
        print(f"   Email: {new_user.email}")
        print(f"   Name: {new_user.name}")
        print(f"   User ID: {new_user.id}")
        print(f"   Password: {password}")
        print(f"\n   You can now login with this email and password!")
        
        return new_user
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) >= 4:
        email = sys.argv[1]
        name = sys.argv[2]
        password = sys.argv[3]
    else:
        print("Creating user: amanparatapsingh@jklu.edu.in")
        email = "amanparatapsingh@jklu.edu.in"
        name = "Aman Pratap Singh"
        password = "Asujam@67"
        print(f"Password: {password}\n")
    
    create_student_user(email, name, password)


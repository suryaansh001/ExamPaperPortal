#!/usr/bin/env python3
"""
Reset admin password in the database
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from dotenv import load_dotenv
from main import User

load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in environment variables!")
    exit(1)

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

def reset_admin_password(email: str, new_password: str):
    """Reset admin password"""
    print(f"\n{'='*60}")
    print("RESETTING ADMIN PASSWORD")
    print(f"{'='*60}\n")
    
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"❌ User {email} not found in database!")
            return False
        
        print(f"✓ User found: {user.name}")
        print(f"  Email: {user.email}")
        print(f"  Current is_admin: {user.is_admin}")
        
        # Reset password
        new_hash = pwd_context.hash(new_password)
        user.password_hash = new_hash
        user.is_admin = True  # Ensure admin status
        user.email_verified = True  # Ensure verified
        
        db.commit()
        db.refresh(user)
        
        print(f"\n✅ Password reset successfully!")
        print(f"  New password: {new_password}")
        print(f"  Admin status: {user.is_admin}")
        print(f"  Email verified: {user.email_verified}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    email = "examportaljklu@jklu.edu.in"
    password = "Aexamadmin@123"
    
    print(f"Resetting password for: {email}")
    print(f"New password: {password}\n")
    
    confirm = input("Continue? (y/n): ").strip().lower()
    if confirm == 'y':
        reset_admin_password(email, password)
    else:
        print("Cancelled.")


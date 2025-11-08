#!/usr/bin/env python3
"""
Script to add an admin user to the database with all super admin powers.
This script creates a user with is_admin=True, granting access to all admin endpoints.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import User model from main
from main import Base, User

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/paper_portal")

# Handle Neon DB SSL requirements
if "neon.tech" in DATABASE_URL or "neondb" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "sslmode": "require",
            "connect_timeout": 10,
        },
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=10,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={
            "connect_timeout": 10,
        }
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def add_admin_user(email: str, name: str, password: str):
    """
    Add an admin user to the database with all super admin powers.
    
    Args:
        email: Admin email address
        name: Admin full name
        password: Admin password (will be hashed)
    """
    db = SessionLocal()
    try:
        print(f"\n{'='*60}")
        print("ADDING ADMIN USER TO DATABASE")
        print(f"{'='*60}\n")
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        
        if existing_user:
            print(f"⚠️  User with email '{email}' already exists.")
            
            if existing_user.is_admin:
                print(f"   User is already an admin.")
                response = input("   Do you want to update the password? (y/n): ").strip().lower()
                if response == 'y':
                    hashed_password = pwd_context.hash(password)
                    existing_user.password_hash = hashed_password
                    existing_user.email_verified = True
                    existing_user.is_admin = True  # Ensure admin status
                    db.commit()
                    print(f"✓ Password updated for admin user: {email}")
                    print(f"  Name: {existing_user.name}")
                    print(f"  Admin Status: {existing_user.is_admin}")
                    print(f"  Email Verified: {existing_user.email_verified}")
                    return existing_user
                else:
                    print("   Operation cancelled.")
                    return None
            else:
                # User exists but is not admin - make them admin
                print(f"   User exists but is not an admin.")
                response = input("   Do you want to promote this user to admin? (y/n): ").strip().lower()
                if response == 'y':
                    hashed_password = pwd_context.hash(password)
                    existing_user.is_admin = True
                    existing_user.email_verified = True
                    existing_user.password_hash = hashed_password
                    existing_user.name = name  # Update name
                    db.commit()
                    db.refresh(existing_user)
                    print(f"✓ User promoted to admin: {email}")
                    print(f"  Name: {existing_user.name}")
                    print(f"  Admin Status: {existing_user.is_admin}")
                    print(f"  Email Verified: {existing_user.email_verified}")
                    return existing_user
                else:
                    print("   Operation cancelled.")
                    return None
        else:
            # Create new admin user
            print(f"Creating new admin user...")
            hashed_password = pwd_context.hash(password)
            
            # Fix sequence if needed (for PostgreSQL)
            try:
                # Get the current max ID
                result = db.execute(text("SELECT MAX(id) FROM users"))
                max_id = result.scalar() or 0
                
                # Reset sequence to be higher than max ID
                if max_id > 0:
                    db.execute(text(f"SELECT setval('users_id_seq', {max_id + 1}, false)"))
                    db.commit()
            except Exception as seq_error:
                # If sequence doesn't exist or other error, continue anyway
                print(f"  Note: Could not reset sequence (this is OK if using auto-increment): {seq_error}")
                db.rollback()
            
            admin_user = User(
                email=email,
                name=name,
                password_hash=hashed_password,
                is_admin=True,  # Super admin power
                email_verified=True,  # Admins are pre-verified
            )
            
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            
            print(f"\n{'='*60}")
            print("✓ ADMIN USER CREATED SUCCESSFULLY!")
            print(f"{'='*60}\n")
            print(f"Email:        {admin_user.email}")
            print(f"Name:         {admin_user.name}")
            print(f"Admin Status: {admin_user.is_admin} (Super Admin)")
            print(f"Email Verified: {admin_user.email_verified}")
            print(f"User ID:      {admin_user.id}")
            print(f"\nPassword:     {password}")
            print(f"\n{'='*60}")
            print("ADMIN PRIVILEGES GRANTED:")
            print(f"{'='*60}")
            print("✓ Access to /admin/dashboard")
            print("✓ Access to /admin/verification-requests")
            print("✓ Access to /admin/verify-user/{user_id}")
            print("✓ Can create, update, delete courses")
            print("✓ Can review, approve, reject papers")
            print("✓ Can edit and delete papers")
            print("✓ Can view all papers (including pending)")
            print("✓ Can access all admin-protected endpoints")
            print(f"{'='*60}\n")
            
            return admin_user
            
    except Exception as e:
        print(f"\n❌ Error creating admin user: {type(e).__name__}: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("ADMIN USER CREATION SCRIPT")
    print("="*60)
    
    # Try to get admin details from .env file first (lines 1-12 area)
    admin_email = os.getenv("ADMIN_EMAIL", "")
    admin_name = os.getenv("ADMIN_NAME", "Super Admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "")
    
    # Get admin details from command line, .env, or prompt
    if len(sys.argv) >= 4:
        email = sys.argv[1]
        name = sys.argv[2]
        password = sys.argv[3]
    elif admin_email and admin_password:
        print(f"\n✓ Found admin credentials in .env file")
        email = admin_email
        name = admin_name
        password = admin_password
        print(f"  Email: {email}")
        print(f"  Name: {name}")
        print(f"  Using password from .env file\n")
    else:
        print("\nEnter admin user details:")
        email = input("Email: ").strip()
        if not email:
            print("❌ Email is required!")
            sys.exit(1)
        
        name = input("Name: ").strip()
        if not name:
            print("❌ Name is required!")
            sys.exit(1)
        
        password = input("Password: ").strip()
        if not password:
            print("❌ Password is required!")
            sys.exit(1)
        
        if len(password) < 6:
            print("⚠️  Warning: Password is less than 6 characters. Consider using a stronger password.")
            confirm = input("Continue anyway? (y/n): ").strip().lower()
            if confirm != 'y':
                print("Operation cancelled.")
                sys.exit(0)
    
    # Add admin user
    result = add_admin_user(email, name, password)
    
    if result:
        print("\n✅ Admin user setup complete!")
        print("\nYou can now login using:")
        print(f"  Endpoint: POST /admin-login")
        print(f"  Email: {email}")
        print(f"  Password: {password}")
        print("\n⚠️  IMPORTANT: Keep these credentials secure!")
    else:
        print("\n❌ Failed to create admin user.")
        sys.exit(1)


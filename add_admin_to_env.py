#!/usr/bin/env python3
"""
Helper script to add admin credentials to .env file (lines 1-12 area)
"""

import os
from pathlib import Path

def add_admin_to_env(email: str, name: str, password: str):
    """Add admin credentials to .env file"""
    env_path = Path(".env")
    
    if not env_path.exists():
        print("❌ .env file not found!")
        return False
    
    # Read current .env content
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Check if admin credentials already exist
    has_admin_email = any(line.startswith("ADMIN_EMAIL=") for line in lines)
    has_admin_name = any(line.startswith("ADMIN_NAME=") for line in lines)
    has_admin_password = any(line.startswith("ADMIN_PASSWORD=") for line in lines)
    
    if has_admin_email or has_admin_name or has_admin_password:
        print("⚠️  Admin credentials already exist in .env file")
        response = input("Do you want to update them? (y/n): ").strip().lower()
        if response != 'y':
            print("Operation cancelled.")
            return False
        
        # Remove existing admin lines
        lines = [line for line in lines 
                if not (line.startswith("ADMIN_EMAIL=") or 
                       line.startswith("ADMIN_NAME=") or 
                       line.startswith("ADMIN_PASSWORD="))]
    
    # Add admin credentials at the beginning (lines 1-12 area)
    admin_lines = [
        f"ADMIN_EMAIL={email}\n",
        f"ADMIN_NAME={name}\n",
        f"ADMIN_PASSWORD={password}\n",
        "\n"  # Empty line for separation
    ]
    
    # Insert after any existing header comments or at the beginning
    insert_pos = 0
    for i, line in enumerate(lines):
        if line.strip() and not line.strip().startswith("#"):
            insert_pos = i
            break
    
    # Insert admin credentials
    lines[insert_pos:insert_pos] = admin_lines
    
    # Write back to .env
    with open(env_path, 'w') as f:
        f.writelines(lines)
    
    print(f"\n✓ Admin credentials added to .env file (around line {insert_pos + 1})")
    print(f"  ADMIN_EMAIL={email}")
    print(f"  ADMIN_NAME={name}")
    print(f"  ADMIN_PASSWORD={password}")
    print("\n⚠️  IMPORTANT: Keep .env file secure and never commit it to version control!")
    
    return True

if __name__ == "__main__":
    print("\n" + "="*60)
    print("ADD ADMIN CREDENTIALS TO .ENV FILE")
    print("="*60)
    
    email = input("\nAdmin Email: ").strip()
    if not email:
        print("❌ Email is required!")
        exit(1)
    
    name = input("Admin Name: ").strip()
    if not name:
        name = "Super Admin"
    
    password = input("Admin Password: ").strip()
    if not password:
        print("❌ Password is required!")
        exit(1)
    
    add_admin_to_env(email, name, password)


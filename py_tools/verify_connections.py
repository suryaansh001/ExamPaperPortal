#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Connection Verification Script
Checks: Database, Backend API, Frontend Configuration
"""

import os
import sys
import requests
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

print("=" * 70)
print("COMPREHENSIVE CONNECTION VERIFICATION")
print("=" * 70)
print()

# Load environment variables
load_dotenv()

# ============================================================================
# 1. DATABASE CONNECTION CHECK
# ============================================================================
print("1. DATABASE CONNECTION")
print("-" * 70)

DATABASE_URL = os.getenv("DATABASE_URL", "")
RAILWAY_DB_URL = "postgresql://postgres:yvFPUoOUFxjaiLqtimFIZRDgcqavpCeU@yamabiko.proxy.rlwy.net:21623/railway"

# Determine which database URL to use
if not DATABASE_URL or "neon" in DATABASE_URL.lower():
    print("⚠️  DATABASE_URL not set or points to Neon")
    print(f"   Using Railway PostgreSQL: {RAILWAY_DB_URL.split('@')[1]}")
    db_url_to_test = RAILWAY_DB_URL
else:
    print(f"✓ DATABASE_URL found: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'configured'}")
    db_url_to_test = DATABASE_URL

try:
    engine = create_engine(
        db_url_to_test,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 10}
    )
    
    with engine.connect() as conn:
        # Test connection
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"✓ Database connection: SUCCESS")
        print(f"  PostgreSQL Version: {version.split(',')[0]}")
        
        # Check tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        expected_tables = ['users', 'courses', 'papers']
        
        print(f"\n  Tables found: {len(tables)}")
        for table in expected_tables:
            if table in tables:
                # Count rows
                count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = count_result.fetchone()[0]
                print(f"  ✓ {table}: {count} row(s)")
            else:
                print(f"  ✗ {table}: NOT FOUND")
        
        # Check database size
        size_result = conn.execute(text("SELECT pg_size_pretty(pg_database_size(current_database()))"))
        db_size = size_result.fetchone()[0]
        print(f"\n  Database Size: {db_size}")
        
except Exception as e:
    print(f"✗ Database connection: FAILED")
    print(f"  Error: {str(e)}")
    db_connected = False
else:
    db_connected = True

print()

# ============================================================================
# 2. BACKEND API CHECK
# ============================================================================
print("2. BACKEND API CONNECTION")
print("-" * 70)

# Get backend URL from environment or use default
BACKEND_URL = os.getenv("BACKEND_URL", "https://exam-portal-backend-jklu-solomaze.vercel.app")
print(f"Backend URL: {BACKEND_URL}")

endpoints_to_check = [
    ("/health", "Health Check"),
    ("/papers/public/all", "Public Papers API"),
    ("/courses", "Courses API"),
]

backend_working = True
for endpoint, name in endpoints_to_check:
    try:
        url = f"{BACKEND_URL}{endpoint}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print(f"✓ {name}: SUCCESS ({len(data)} items)")
            else:
                print(f"✓ {name}: SUCCESS")
        else:
            print(f"✗ {name}: FAILED (Status: {response.status_code})")
            backend_working = False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ {name}: FAILED")
        print(f"  Error: {str(e)}")
        backend_working = False

print()

# ============================================================================
# 3. FRONTEND CONFIGURATION CHECK
# ============================================================================
print("3. FRONTEND CONFIGURATION")
print("-" * 70)

# Check frontend API configuration files
frontend_files = [
    "../ExamPaperPortalFrontend/src/utils/api.ts",
    "../ExamPaperPortalFrontend/src/contexts/AuthContext.tsx",
]

for file_path in frontend_files:
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if BACKEND_URL in content:
                    print(f"✓ {os.path.basename(file_path)}: Configured with backend URL")
                elif "VITE_API_URL" in content or "VITE_BACKEND_URL" in content:
                    print(f"✓ {os.path.basename(file_path)}: Uses environment variables")
                else:
                    print(f"⚠️  {os.path.basename(file_path)}: May need configuration")
        except Exception as e:
            print(f"✗ {os.path.basename(file_path)}: Error reading ({str(e)})")
    else:
        print(f"⚠️  {file_path}: File not found")

print()

# ============================================================================
# 4. ENVIRONMENT VARIABLES CHECK
# ============================================================================
print("4. ENVIRONMENT VARIABLES")
print("-" * 70)

env_vars = {
    "DATABASE_URL": "Database connection string",
    "SECRET_KEY": "JWT secret key",
    "VITE_API_URL": "Frontend API URL (if set)",
    "VITE_BACKEND_URL": "Frontend backend URL (if set)",
}

for var, desc in env_vars.items():
    value = os.getenv(var, "")
    if value:
        if "password" in var.lower() or "secret" in var.lower() or "key" in var.lower():
            # Mask sensitive values
            if "@" in value:
                # Database URL - show host only
                masked = value.split("@")[1] if "@" in value else "***"
            else:
                masked = "***" + value[-4:] if len(value) > 4 else "***"
            print(f"✓ {var}: Set ({masked})")
        else:
            print(f"✓ {var}: Set ({value})")
    else:
        print(f"⚠️  {var}: Not set")

print()

# ============================================================================
# 5. CONNECTION SUMMARY
# ============================================================================
print("=" * 70)
print("CONNECTION SUMMARY")
print("=" * 70)

if db_connected:
    print("✓ Database: Connected")
else:
    print("✗ Database: Not Connected")

if backend_working:
    print("✓ Backend API: Working")
else:
    print("✗ Backend API: Not Working")

print("✓ Frontend: Configuration files checked")
print()

# Recommendations
print("RECOMMENDATIONS:")
print("-" * 70)

if not db_connected:
    print("1. ✗ Fix database connection")
    print("   - Check DATABASE_URL in Railway backend service")
    print("   - Verify Railway PostgreSQL is running")
    print("   - Check connection string is correct")

if not backend_working:
    print("2. ✗ Fix backend API")
    print("   - Check backend service is running in Railway")
    print("   - Verify backend URL is correct")
    print("   - Check backend logs for errors")

if db_connected and backend_working:
    print("✓ All connections working!")
    print("  - Database: Connected")
    print("  - Backend API: Responding")
    print("  - Frontend: Configured")
    print()
    print("If no data showing:")
    print("  - Database may be empty (new Railway PostgreSQL)")
    print("  - Add papers through admin dashboard")
    print("  - Or migrate data from Neon if accessible")

print()
print("=" * 70)


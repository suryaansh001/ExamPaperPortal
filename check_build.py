#!/usr/bin/env python3
"""
Comprehensive Backend Build Check
Checks all files for build issues
"""

import os
import sys
import importlib.util
from pathlib import Path

print("="*70)
print("🔍 COMPREHENSIVE BACKEND BUILD CHECK")
print("="*70)
print()

errors = []
warnings = []

# Check 1: Python Syntax
print("1️⃣  Checking Python Syntax...")
try:
    with open('main.py', 'r', encoding='utf-8') as f:
        compile(f.read(), 'main.py', 'exec')
    print("   ✅ main.py syntax is valid")
except SyntaxError as e:
    print(f"   ❌ Syntax error in main.py: {e}")
    errors.append(f"Syntax error: {e}")
except UnicodeDecodeError as e:
    print(f"   ⚠️  Encoding issue (non-critical): {e}")
    warnings.append(f"Encoding issue: {e}")
print()

# Check 2: Required Files
print("2️⃣  Checking Required Files...")
required_files = [
    'main.py',
    'requirements.txt',
    'Procfile',
]
for file in required_files:
    if os.path.exists(file):
        print(f"   ✅ {file} exists")
    else:
        print(f"   ❌ {file} MISSING")
        errors.append(f"Missing file: {file}")
print()

# Check 3: Dependencies
print("3️⃣  Checking Dependencies...")
try:
    import fastapi
    print(f"   ✅ fastapi {fastapi.__version__}")
except ImportError:
    print("   ❌ fastapi not installed")
    errors.append("fastapi not installed")

try:
    import uvicorn
    print(f"   ✅ uvicorn {uvicorn.__version__}")
except ImportError:
    print("   ❌ uvicorn not installed")
    errors.append("uvicorn not installed")

try:
    import sqlalchemy
    print(f"   ✅ sqlalchemy {sqlalchemy.__version__}")
except ImportError:
    print("   ❌ sqlalchemy not installed")
    errors.append("sqlalchemy not installed")

try:
    import pydantic
    print(f"   ✅ pydantic {pydantic.__version__}")
except ImportError:
    print("   ❌ pydantic not installed")
    errors.append("pydantic not installed")
print()

# Check 4: Import Main Module
print("4️⃣  Testing Main Module Import...")
try:
    spec = importlib.util.spec_from_file_location("main", "main.py")
    if spec is None:
        raise ImportError("Could not load main.py")
    
    # Suppress print output during import
    import io
    import contextlib
    f = io.StringIO()
    with contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
        main_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_module)
    
    print("   ✅ main.py imports successfully")
    
    # Check key components
    if hasattr(main_module, 'app'):
        print("   ✅ FastAPI app created")
    else:
        print("   ❌ FastAPI app not found")
        errors.append("FastAPI app not found")
    
    if hasattr(main_module, 'Base'):
        print("   ✅ SQLAlchemy Base defined")
    else:
        print("   ❌ SQLAlchemy Base not found")
        errors.append("SQLAlchemy Base not found")
    
    if hasattr(main_module, 'User'):
        print("   ✅ User model defined")
    else:
        print("   ❌ User model not found")
        errors.append("User model not found")
        
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    errors.append(f"Import error: {e}")
    import traceback
    traceback.print_exc()
print()

# Check 5: Pydantic Schemas
print("5️⃣  Checking Pydantic Schemas...")
try:
    from main import (
        UserResponse, RegisterVerifyResponse, CourseResponse, PaperResponse,
        Token, LoginRequest, RegisterRequest
    )
    print("   ✅ All Pydantic schemas importable")
except Exception as e:
    print(f"   ❌ Schema import error: {e}")
    errors.append(f"Schema error: {e}")
print()

# Check 6: Database Models
print("6️⃣  Checking Database Models...")
try:
    from main import User, Course, Paper
    print("   ✅ User model defined")
    print("   ✅ Course model defined")
    print("   ✅ Paper model defined")
except Exception as e:
    print(f"   ❌ Model import error: {e}")
    errors.append(f"Model error: {e}")
print()

# Check 7: API Endpoints
print("7️⃣  Checking API Endpoints...")
try:
    from main import app
    routes = [route.path for route in app.routes]
    print(f"   ✅ {len(routes)} routes registered")
    
    # Check key endpoints
    key_endpoints = ['/login', '/register', '/papers', '/courses', '/me']
    for endpoint in key_endpoints:
        if any(endpoint in route for route in routes):
            print(f"   ✅ {endpoint} endpoint exists")
        else:
            print(f"   ⚠️  {endpoint} endpoint not found")
            warnings.append(f"Missing endpoint: {endpoint}")
except Exception as e:
    print(f"   ❌ Endpoint check error: {e}")
    errors.append(f"Endpoint error: {e}")
print()

# Check 8: Environment Variables
print("8️⃣  Checking Environment Configuration...")
from dotenv import load_dotenv
load_dotenv()

required_env = ['DATABASE_URL', 'SECRET_KEY']
for env_var in required_env:
    if os.getenv(env_var):
        print(f"   ✅ {env_var} is set")
    else:
        print(f"   ⚠️  {env_var} not set (may use default)")
        warnings.append(f"{env_var} not set")
print()

# Check 9: Deployment Files
print("9️⃣  Checking Deployment Files...")
deployment_files = {
    'Procfile': 'Render/Railway deployment',
    'Dockerfile': 'Docker deployment',
    'render.yaml': 'Render deployment config',
    'fly.toml': 'Fly.io deployment',
}
for file, purpose in deployment_files.items():
    if os.path.exists(file):
        print(f"   ✅ {file} exists ({purpose})")
    else:
        print(f"   ⚠️  {file} not found (optional for {purpose})")
print()

# Check 10: Forward References Fix
print("🔟 Checking Forward References...")
try:
    with open('main.py', 'r') as f:
        content = f.read()
        if 'from __future__ import annotations' in content:
            print("   ✅ Forward references enabled")
        else:
            print("   ⚠️  Forward references not enabled")
            warnings.append("Forward references not enabled")
        
        if 'user: "UserResponse"' in content or 'user: UserResponse' in content:
            print("   ✅ RegisterVerifyResponse uses UserResponse correctly")
        else:
            print("   ⚠️  RegisterVerifyResponse may have issues")
            warnings.append("RegisterVerifyResponse may have forward reference issues")
except Exception as e:
    print(f"   ⚠️  Could not check forward references: {e}")
print()

# Summary
print("="*70)
if errors:
    print("❌ BUILD CHECK FAILED")
    print("="*70)
    print("\nErrors found:")
    for i, error in enumerate(errors, 1):
        print(f"   {i}. {error}")
    print()
    if warnings:
        print("Warnings:")
        for i, warning in enumerate(warnings, 1):
            print(f"   {i}. {warning}")
    sys.exit(1)
else:
    print("✅ BUILD CHECK PASSED")
    print("="*70)
    if warnings:
        print("\nWarnings (non-critical):")
        for i, warning in enumerate(warnings, 1):
            print(f"   {i}. {warning}")
    else:
        print("\n✅ No errors or warnings found!")
    print("\n🚀 Backend is ready for deployment!")


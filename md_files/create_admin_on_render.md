# Quick Fix: Create Admin User on Render

## The Problem
The admin user exists in your **local database** but not in the **deployed Render database**. That's why login is failing.

## Solution: Create Admin User on Render

### Method 1: Using Render Shell (Fastest) ⚡

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Click on your Web Service** (the backend service)
3. **Click "Shell" tab** (in the left sidebar)
4. **Run this command**:

```bash
python add_admin_user.py examportaljklu@jklu.edu.in "Portal_exam" Aexamadmin@123
```

That's it! The admin user will be created.

### Method 2: Using API Endpoint (If service is running)

If your Render service is accessible, you can create the admin via API:

```bash
curl -X POST "https://your-app-name.onrender.com/create-admin" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "examportaljklu@jklu.edu.in",
    "name": "Portal_exam",
    "password": "Aexamadmin@123"
  }'
```

Replace `your-app-name` with your actual Render app name.

### Method 3: Direct Python Script (In Render Shell)

If the script doesn't work, run this directly in Render Shell:

```python
python
```

Then paste this:

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from main import User

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Connecting to database...")

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Admin details
email = "examportaljklu@jklu.edu.in"
name = "Portal_exam"
password = "Aexamadmin@123"

# Check if exists
existing = db.query(User).filter(User.email == email).first()
if existing:
    print(f"User {email} exists. Checking admin status...")
    if existing.is_admin:
        print(f"✓ User is already an admin!")
    else:
        existing.is_admin = True
        existing.email_verified = True
        existing.password_hash = pwd_context.hash(password)
        db.commit()
        print(f"✓ Promoted {email} to admin")
else:
    hashed = pwd_context.hash(password)
    admin = User(
        email=email,
        name=name,
        password_hash=hashed,
        is_admin=True,
        email_verified=True
    )
    db.add(admin)
    db.commit()
    print(f"✓ Admin user {email} created successfully!")
    print(f"  Name: {name}")
    print(f"  Password: {password}")

db.close()
print("Done!")
```

## Verify It Works

After creating the admin, test the login:

```bash
curl -X POST "https://your-app-name.onrender.com/admin-login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=examportaljklu@jklu.edu.in&password=Aexamadmin@123"
```

You should get an `access_token` in the response.

## Update Frontend to Point to Render

If your frontend is still pointing to `localhost:8000`, update it:

1. **Create `.env` file** in `ExamPaperPortalFrontend/`:

```env
VITE_API_URL=https://your-app-name.onrender.com
```

2. **Or set environment variable** when building:
   - Vercel/Netlify: Set `VITE_API_URL` in environment variables
   - Local dev: Create `.env` file

3. **Rebuild frontend**:
```bash
npm run build
```

## Quick Test

Test if your Render backend is accessible:

```bash
# Health check
curl https://your-app-name.onrender.com/health

# API docs
# Visit: https://your-app-name.onrender.com/docs
```

---

**Need Help?** Check Render logs: Dashboard → Your Service → Logs


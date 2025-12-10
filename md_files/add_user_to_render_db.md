# Add User to Render Database

## The Problem

The user `amanpratapsingh@jklu.edu.in` exists in your **local database** but NOT in the **Render database**. Since your frontend is pointing to Render backend, it queries the Render database, which doesn't have this user.

## Solution: Add User to Render Database

### Method 1: Use Render Shell (Recommended)

1. Go to **Render Dashboard** → Your Backend Service → **Shell** tab
2. Run this Python code:

```python
from main import User, get_password_hash
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os

# Get database from environment
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# User details
email = "amanpratapsingh@jklu.edu.in"
name = "amanpratapsingh"
password = "Asujam@67"

# Check if exists
existing = db.query(User).filter(User.email == email).first()
if existing:
    print(f"User {email} already exists")
else:
    # Create user
    hashed = get_password_hash(password)
    new_user = User(
        email=email,
        name=name,
        password_hash=hashed,
        is_admin=False,
        email_verified=True
    )
    db.add(new_user)
    db.commit()
    print(f"✅ User {email} created successfully!")

db.close()
```

### Method 2: Use API Endpoint (If service is running)

If your Render service is accessible, you can register the user via the API:

```bash
curl -X POST "https://exam-portal-backend-jklu-solomaze.onrender.com/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "amanpratapsingh@jklu.edu.in",
    "name": "amanpratapsingh",
    "password": "Asujam@67",
    "confirm_password": "Asujam@67"
  }'
```

Then verify the OTP (check server logs or email).

### Method 3: Use the Frontend Register Page

1. Go to your deployed frontend
2. Click "Sign up"
3. Register with:
   - Email: `amanpratapsingh@jklu.edu.in`
   - Name: `amanpratapsingh`
   - Password: `Asujam@67`
4. Complete OTP verification

## Why This Happens

- **Local Database**: Your development database (SQLite or local PostgreSQL)
- **Render Database**: Production database on Render (separate from local)
- **Frontend**: Points to Render backend → queries Render database

They are **separate databases**, so users need to exist in both (or just in Render for production).

## After Adding User

Once the user is added to Render database:
1. Try login again
2. It should work now!

---

**Quick Fix**: Use Method 1 (Render Shell) - it's the fastest way to add the user.


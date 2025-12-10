# Post-Deployment Setup for Render.com

## ✅ Deployment Successful!

Your backend has been successfully deployed to Render.com. Now you need to:

### 1. Verify Environment Variables on Render

Go to your Render dashboard → Your Web Service → Environment tab and ensure these are set:

**Required:**
```
DATABASE_URL=<Your Render PostgreSQL Internal URL>
SECRET_KEY=<Your secret key (same as local or generate new)>
PORT=10000
```

**Email Configuration (choose one):**
```
RESEND_API_KEY=<your-resend-key>
RESEND_FROM_EMAIL=<your-email>
```

OR

```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<your-email>
SMTP_PASS=<app-password>
SMTP_FROM_EMAIL=<your-email>
```

**Optional - Admin Credentials (for automated setup):**
```
ADMIN_EMAIL=examportaljklu@jklu.edu.in
ADMIN_NAME=Portal_exam
ADMIN_PASSWORD=Aexamadmin@123
```

### 2. Create Admin User on Deployed Database

The admin user we created locally exists only in your local database. You need to create it on the deployed Render database.

#### Option A: Using Render Shell (Recommended)

1. Go to Render Dashboard → Your Web Service
2. Click on "Shell" tab
3. Run the admin creation script:

```bash
cd /opt/render/project/src
python add_admin_user.py examportaljklu@jklu.edu.in "Portal_exam" Aexamadmin@123
```

#### Option B: Using API Endpoint (After first manual setup)

If you can access the API, you can use the `/create-admin` endpoint:

```bash
curl -X POST "https://your-app.onrender.com/create-admin" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "examportaljklu@jklu.edu.in",
    "name": "Portal_exam",
    "password": "Aexamadmin@123"
  }'
```

#### Option C: Using Python Script via Render Shell

1. Open Render Shell
2. Run Python interactively:

```python
python
```

Then paste this code:

```python
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from main import User, Base

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create admin user
email = "examportaljklu@jklu.edu.in"
name = "Portal_exam"
password = "Aexamadmin@123"

# Check if exists
existing = db.query(User).filter(User.email == email).first()
if existing:
    print(f"User {email} already exists")
    if not existing.is_admin:
        existing.is_admin = True
        existing.email_verified = True
        existing.password_hash = pwd_context.hash(password)
        db.commit()
        print(f"Promoted {email} to admin")
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
    print(f"Admin user {email} created successfully!")

db.close()
```

### 3. Test Admin Login

Once the admin user is created, test the login:

```bash
curl -X POST "https://your-app.onrender.com/admin-login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=examportaljklu@jklu.edu.in&password=Aexamadmin@123"
```

You should receive an access token in response.

### 4. Update Frontend API URL

Update your frontend to point to the Render URL:

```typescript
// In your frontend API configuration
const API_URL = "https://your-app.onrender.com";
```

### 5. Verify Database Tables

The tables should be created automatically on first startup. To verify:

1. Go to Render Dashboard → Your PostgreSQL Database
2. Click "Connect" → "psql" or use a database client
3. Run: `\dt` to list tables
4. You should see: `users`, `courses`, `papers`

### 6. Health Check

Test your deployed API:

```bash
# Health check
curl https://your-app.onrender.com/health

# API root
curl https://your-app.onrender.com/

# Docs
# Visit: https://your-app.onrender.com/docs
```

### 7. Important Notes

⚠️ **Render Free Tier:**
- Service spins down after 15 minutes of inactivity
- First request after spin-down takes 30-60 seconds (cold start)
- This is normal and expected on free tier

⚠️ **Database:**
- Use the **Internal Database URL** (not External) for your app
- External URL is only for local development/testing

⚠️ **Environment Variables:**
- Never commit `.env` file to Git
- Set all sensitive variables in Render dashboard
- The deployed app uses Render's environment variables, not `.env` file

### 8. Troubleshooting

**Service won't start:**
- Check Render logs: Dashboard → Your Service → Logs
- Verify all environment variables are set
- Check `requirements.txt` is correct

**Database connection errors:**
- Verify `DATABASE_URL` is set correctly
- Use Internal Database URL (starts with `postgresql://`)
- Ensure database is running (check Render dashboard)

**Admin user creation fails:**
- Check database connection
- Verify tables exist (`\dt` in psql)
- Check sequence issues (script handles this automatically)

### 9. Next Steps

1. ✅ Create admin user on deployed database
2. ✅ Test admin login
3. ✅ Update frontend API URL
4. ✅ Test full workflow (register → login → upload paper → review)
5. ✅ Monitor logs for any issues

---

**Deployment Date**: 2025-11-08  
**Status**: ✅ Deployed Successfully  
**Next Action**: Create admin user on deployed database


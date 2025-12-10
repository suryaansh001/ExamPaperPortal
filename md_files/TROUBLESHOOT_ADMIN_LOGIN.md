# Troubleshooting Admin Login (Admin Exists in Database)

## ✅ Confirmed: Admin User Exists

You have confirmed that `examportaljklu@jklu.edu.in` exists in the database with `is_admin: TRUE`.

## Possible Issues

### 1. Password Hash Mismatch

The password in the database might not match `Aexamadmin@123`. This can happen if:
- The user was created with a different password
- The password hash was generated differently

**Solution**: Reset the password or verify the correct password.

### 2. Frontend Still Pointing to Localhost

Check if your frontend is still using `http://localhost:8000` instead of Render URL.

**Check**:
1. Open browser DevTools (F12)
2. Go to Network tab
3. Try to login
4. See what URL the request goes to

Should be: `https://exam-portal-backend-jklu-solomaze.onrender.com/admin-login`
NOT: `http://localhost:8000/admin-login`

### 3. CORS or Connection Issues

The request might be blocked or not reaching the backend.

**Check**: Look at browser console for errors.

### 4. Wrong Database Connection

The backend might be connected to a different database than the one you're viewing.

**Check**: Verify `DATABASE_URL` in Render environment variables matches your database.

## Quick Tests

### Test 1: Direct API Call

Test the login endpoint directly:

```bash
curl -X POST "https://exam-portal-backend-jklu-solomaze.onrender.com/admin-login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=examportaljklu@jklu.edu.in&password=Aexamadmin@123"
```

**Expected**: Should return `{"access_token":"...","token_type":"bearer"}`

**If it fails**: The password might be wrong or there's a backend issue.

### Test 2: Check Frontend API URL

In browser console, run:
```javascript
console.log(import.meta.env.VITE_API_URL)
```

Should show: `https://exam-portal-backend-jklu-solomaze.onrender.com`

### Test 3: Reset Admin Password

If password is wrong, reset it using Render Shell:

```bash
python
```

Then:
```python
from main import User, get_password_hash
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

user = db.query(User).filter(User.email == "examportaljklu@jklu.edu.in").first()
if user:
    user.password_hash = get_password_hash("Aexamadmin@123")
    db.commit()
    print("Password reset successfully!")
else:
    print("User not found")

db.close()
```

## Most Likely Issue

Since the admin exists, the most common issues are:

1. **Password mismatch** - Try resetting password (Test 3 above)
2. **Frontend pointing to wrong URL** - Check Test 2
3. **Backend not running** - Check Render dashboard service status

## Next Steps

1. Run Test 1 (direct API call) to see if backend works
2. Check browser Network tab to see where frontend is sending requests
3. If password is wrong, use Test 3 to reset it


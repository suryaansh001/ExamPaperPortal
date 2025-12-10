# 🔧 Quick Fix: Admin Login Error

## Problem
You're seeing "Incorrect email or password" when trying to log in as admin.

## Root Cause
The admin user exists in your **local database** but **NOT** in the **deployed Render database**.

## ✅ Solution (Choose One)

### Option 1: Render Shell (Recommended - 2 minutes)

1. Go to: https://dashboard.render.com
2. Click your **Web Service** → **Shell** tab
3. Run:
   ```bash
   python add_admin_user.py examportaljklu@jklu.edu.in "Portal_exam" Aexamadmin@123
   ```
4. Done! Try logging in again.

### Option 2: API Call (If service is running)

Replace `your-app-name` with your Render app name:

```bash
curl -X POST "https://your-app-name.onrender.com/create-admin" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "examportaljklu@jklu.edu.in",
    "name": "Portal_exam",
    "password": "Aexamadmin@123"
  }'
```

### Option 3: Check Frontend API URL

Make sure your frontend is pointing to Render, not localhost:

1. Check browser console (F12) → Network tab
2. See what URL the login request goes to
3. If it's `localhost:8000`, update your frontend `.env`:

```env
VITE_API_URL=https://your-app-name.onrender.com
```

Then rebuild:
```bash
cd ExamPaperPortalFrontend
npm run build
```

## Test After Fix

```bash
curl -X POST "https://your-app-name.onrender.com/admin-login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=examportaljklu@jklu.edu.in&password=Aexamadmin@123"
```

Should return: `{"access_token":"...","token_type":"bearer"}`

## Still Not Working?

1. **Check Render Logs**: Dashboard → Service → Logs
2. **Verify Database URL**: Dashboard → Service → Environment → `DATABASE_URL`
3. **Check if service is running**: Dashboard → Service status should be "Live"

---

**Most Common Issue**: Admin user doesn't exist in deployed database → Use Option 1 above ✅


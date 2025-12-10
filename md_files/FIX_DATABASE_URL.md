# Fix DATABASE_URL in .env File

## ❌ Current (WRONG)

Your current `.env` file has:
```
DATABASE_URL=psql 'postgresql://neondb_owner:npg_EAkX0WVqeR5r@ep-polished-bush-a1fj2trf-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
```

**Problem**: It includes `psql` command and quotes, which is wrong!

## ✅ Correct Format

The `DATABASE_URL` should be **just the connection string**, without `psql` command or quotes:

```
DATABASE_URL=postgresql://neondb_owner:npg_EAkX0WVqeR5r@ep-polished-bush-a1fj2trf-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

## How to Fix

1. Open `ExamSystemBackend/.env` file
2. Find the line with `DATABASE_URL=`
3. Replace it with:

```
DATABASE_URL=postgresql://neondb_owner:npg_EAkX0WVqeR5r@ep-polished-bush-a1fj2trf-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

**Important changes:**
- ❌ Remove `psql` 
- ❌ Remove quotes `'`
- ❌ Remove `channel_binding=require` (not needed for SQLAlchemy)
- ✅ Keep `sslmode=require` (required for Neon)

## Complete .env File Should Look Like:

```
ADMIN_EMAIL=examportaljklu@jklu.edu.in
ADMIN_NAME=Portal_exam
ADMIN_PASSWORD=Aexamadmin@123

RESEND_API_KEY=re_YmLY9FhV_2QS3Ycecqu6GKfxxTbkSG7t5
HOST=smtp.resend.com
PORT=465
User=resend

SMTP_SERVER=smtp.resend.com
SMTP_PORT=587
SMTP_USER=resend
SMTP_PASS=re_your_resend_api_key_here
SMTP_FROM_EMAIL=onboarding@resend.dev

DATABASE_URL=postgresql://neondb_owner:npg_EAkX0WVqeR5r@ep-polished-bush-a1fj2trf-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require

SECRET_KEY=vs0P5-VBgTHEg-aPdhEV618__XTNdsOfm5cuDa6320w
```

## After Fixing

1. **Restart your backend server** (if running locally)
2. The database connection should work now
3. Try login again - it should find the user!

## For Render Deployment

On Render, set the same `DATABASE_URL` in:
- Render Dashboard → Your Backend Service → Environment tab
- Add: `DATABASE_URL` = `postgresql://neondb_owner:npg_EAkX0WVqeR5r@ep-polished-bush-a1fj2trf-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require`

---

**The key**: `DATABASE_URL` should be just the connection string, NOT a `psql` command!


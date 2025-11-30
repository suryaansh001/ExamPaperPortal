# Setting Up PostgreSQL Database on Railway

## ✅ Yes, Railway Supports PostgreSQL!

Railway provides managed PostgreSQL databases that you can easily connect to your backend service.

## Step-by-Step Guide

### Step 1: Create PostgreSQL Database in Railway

1. **Go to your Railway Dashboard**
   - Visit: https://railway.app/dashboard
   - Select your project (or create a new one)

2. **Add PostgreSQL Service**
   - Click **"+ New"** button
   - Select **"Database"** → **"Add PostgreSQL"**
   - Railway will automatically create a PostgreSQL database

3. **Wait for Database to Provision**
   - Railway will provision the database (takes ~30 seconds)
   - You'll see the database service appear in your project

### Step 2: Get Database Connection String

1. **Click on the PostgreSQL service** you just created

2. **Go to "Variables" tab**
   - You'll see `DATABASE_URL` automatically created
   - This is your connection string

3. **Copy the `DATABASE_URL`**
   - It will look like:
     ```
     postgresql://postgres:password@containers-us-west-xxx.railway.app:5432/railway
     ```
   - Railway automatically provides this environment variable

### Step 3: Connect Backend to Railway PostgreSQL

#### Option A: Automatic Connection (Recommended)

If your backend service and PostgreSQL are in the **same Railway project**:

1. **Go to your Backend Service** (the one running `main.py`)

2. **Go to "Variables" tab**

3. **Add/Update `DATABASE_URL`**
   - Railway automatically provides `DATABASE_URL` from the PostgreSQL service
   - You can reference it directly, OR
   - Copy the full connection string from PostgreSQL service

4. **If using reference** (same project):
   - Railway automatically injects `DATABASE_URL` from PostgreSQL service
   - Your backend will automatically use it!

#### Option B: Manual Connection

1. **Copy the full `DATABASE_URL`** from PostgreSQL service Variables tab

2. **Go to your Backend Service** → **Variables** tab

3. **Add/Update `DATABASE_URL`**:
   - **Key**: `DATABASE_URL`
   - **Value**: Paste the connection string from PostgreSQL service
   - Example:
     ```
     postgresql://postgres:password@containers-us-west-xxx.railway.app:5432/railway
     ```

4. **Save** and Railway will redeploy your backend

### Step 4: Update Your Code (if needed)

Your code already supports Railway PostgreSQL! The connection logic in `main.py` will work:

```python
# Your code already handles this:
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/paper_portal")

# Railway PostgreSQL doesn't require SSL like Neon, so it will use the standard connection
```

**Note**: Railway PostgreSQL doesn't require `sslmode=require` like Neon, so your code will automatically use the standard connection path.

### Step 5: Verify Connection

1. **Check Backend Logs**
   - Go to your Backend Service → **Deployments** → **View Logs**
   - Look for database connection messages
   - Should see: `✓ Database: PostgreSQL` (not Neon DB)

2. **Test API Endpoint**
   - Visit: `https://your-railway-backend.up.railway.app/health`
   - Should return success

3. **Check Database Tables**
   - Your tables will be automatically created on first startup
   - Tables: `users`, `courses`, `papers`

## Migrating Data from Neon to Railway PostgreSQL

If you want to migrate your existing data from Neon:

### Option 1: Using pg_dump (Recommended)

1. **Export from Neon**:
   ```bash
   pg_dump "your-neon-connection-string" > backup.sql
   ```

2. **Import to Railway**:
   ```bash
   psql "your-railway-database-url" < backup.sql
   ```

### Option 2: Using Railway CLI

1. **Install Railway CLI**:
   ```bash
   npm i -g @railway/cli
   railway login
   ```

2. **Connect to Railway PostgreSQL**:
   ```bash
   railway connect postgres
   ```

3. **Import data**:
   ```bash
   psql < backup.sql
   ```

### Option 3: Manual Migration Script

You can create a migration script to copy data:

```python
# migrate_to_railway.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Neon source
neon_url = "your-neon-connection-string"
neon_engine = create_engine(neon_url)

# Railway destination
railway_url = os.getenv("RAILWAY_DATABASE_URL")
railway_engine = create_engine(railway_url)

# Copy tables (example for users)
# ... migration logic ...
```

## Railway PostgreSQL vs Neon

| Feature | Railway PostgreSQL | Neon |
|---------|-------------------|------|
| **SSL Required** | No (optional) | Yes (required) |
| **Free Tier** | ✅ Yes (with limits) | ✅ Yes (with limits) |
| **Connection String** | Auto-provided | Manual setup |
| **Disk Space** | Depends on plan | 0.5GB free tier |
| **Auto-scaling** | ✅ Yes | ✅ Yes |
| **Backups** | ✅ Automatic | ✅ Automatic |

## Railway PostgreSQL Pricing

- **Free Tier**: Limited usage (good for development)
- **Hobby Plan**: $5/month - More resources
- **Pro Plan**: $20/month - Production ready

## Troubleshooting

### Issue: Database connection fails

**Solution**:
1. Check `DATABASE_URL` is set correctly in backend service
2. Ensure PostgreSQL service is running (green status)
3. Check backend logs for connection errors

### Issue: Tables not created

**Solution**:
1. Your code automatically creates tables on startup
2. Check backend logs for table creation messages
3. Verify `Base.metadata.create_all(bind=engine)` runs successfully

### Issue: SSL errors

**Solution**:
- Railway PostgreSQL doesn't require SSL by default
- Your code will automatically use non-SSL connection
- If you see SSL errors, check your connection string

## Benefits of Railway PostgreSQL

1. ✅ **Same Platform**: Backend and database in one place
2. ✅ **Auto-scaling**: Handles traffic automatically
3. ✅ **Easy Setup**: One-click database creation
4. ✅ **Automatic Backups**: Built-in backup system
5. ✅ **Environment Variables**: Auto-injected connection strings
6. ✅ **Monitoring**: Built-in database metrics

## Next Steps

1. ✅ Create PostgreSQL service in Railway
2. ✅ Connect backend to PostgreSQL (automatic if same project)
3. ✅ Verify connection in logs
4. ✅ (Optional) Migrate data from Neon
5. ✅ Update frontend if needed (usually not needed)

## Quick Checklist

- [ ] Created PostgreSQL service in Railway
- [ ] Verified `DATABASE_URL` is available in backend service
- [ ] Backend service redeployed
- [ ] Checked logs for successful connection
- [ ] Tested API endpoints
- [ ] (Optional) Migrated data from Neon

---

**Your backend code is already compatible with Railway PostgreSQL!** Just add the PostgreSQL service and Railway will handle the rest automatically.


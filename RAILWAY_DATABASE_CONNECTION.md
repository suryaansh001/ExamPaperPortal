# Connect Backend to Railway PostgreSQL Database

## ✅ Your Backend Code is Ready!

Your `main.py` already supports Railway PostgreSQL. It will automatically use the correct connection settings.

## Step-by-Step: Connect Backend to Railway PostgreSQL

### Step 1: Go to Railway Dashboard

1. Visit: https://railway.app/dashboard
2. Select your project
3. Click on your **Backend Service** (the one running `main.py`)

### Step 2: Set DATABASE_URL Environment Variable

1. In your Backend Service, click on **"Variables"** tab
2. Look for `DATABASE_URL` in the list
3. If it exists, click **"Edit"**
4. If it doesn't exist, click **"+ New Variable"**

### Step 3: Add Railway PostgreSQL Connection String

**Option A: Direct Value (Recommended for now)**

1. **Key**: `DATABASE_URL`
2. **Value**: 
   ```
   postgresql://postgres:yvFPUoOUFxjaiLqtimFIZRDgcqavpCeU@yamabiko.proxy.rlwy.net:21623/railway
   ```
3. Click **"Add"** or **"Save"**

**Option B: Service Reference (If PostgreSQL service is in same project)**

1. **Key**: `DATABASE_URL`
2. **Value**: `${{ Postgres.DATABASE_URL }}`
   - Replace `Postgres` with your actual PostgreSQL service name
3. Click **"Add"** or **"Save"**

### Step 4: Redeploy Backend

After setting the environment variable:

1. Railway will **automatically redeploy** your service, OR
2. Go to **"Deployments"** tab
3. Click **"Redeploy"** on the latest deployment

### Step 5: Verify Connection

1. **Check Backend Logs**:
   - Go to **"Deployments"** → Click on latest deployment → **"View Logs"**
   - Look for:
     ```
     ✓ Database: PostgreSQL
     ```
   - Should NOT see "Neon DB" anymore

2. **Test API Endpoint**:
   - Visit: `https://your-railway-backend.up.railway.app/health`
   - Should return: `{"status": "ok"}`

3. **Check Database Tables**:
   - Your tables (`users`, `courses`, `papers`) should already exist
   - They were created when we ran `create_railway_tables.py`

## How Your Backend Connects

Your `main.py` code automatically detects the database type:

```python
# Line 84-106 in main.py
if "neon.tech" in DATABASE_URL or "neondb" in DATABASE_URL:
    # Neon DB connection with SSL
    engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require", ...})
else:
    # Railway PostgreSQL (or other providers) - no SSL required
    engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 10, ...})
```

Since your Railway URL doesn't contain "neon.tech" or "neondb", it will use the **standard PostgreSQL connection** (no SSL required).

## Connection String Details

```
postgresql://postgres:yvFPUoOUFxjaiLqtimFIZRDgcqavpCeU@yamabiko.proxy.rlwy.net:21623/railway
```

- **Protocol**: `postgresql://`
- **User**: `postgres`
- **Password**: `yvFPUoOUFxjaiLqtimFIZRDgcqavpCeU`
- **Host**: `yamabiko.proxy.rlwy.net`
- **Port**: `21623`
- **Database**: `railway`

## Troubleshooting

### Issue: Backend still connecting to Neon

**Solution**:
1. Verify `DATABASE_URL` is set correctly in Railway Variables
2. Check the value doesn't contain the old Neon connection string
3. Redeploy the backend service
4. Check logs to confirm new connection

### Issue: Connection timeout

**Solution**:
1. Verify PostgreSQL service is running (green status in Railway)
2. Check connection string is correct
3. Verify network connectivity

### Issue: Tables not found

**Solution**:
- Tables should already exist (created by `create_railway_tables.py`)
- If not, they will be created automatically on first backend startup
- Check logs for table creation messages

### Issue: Authentication failed

**Solution**:
1. Verify password in connection string is correct
2. Check PostgreSQL service is accessible
3. Verify user `postgres` has proper permissions

## Verification Checklist

- [ ] `DATABASE_URL` set in Railway backend service Variables
- [ ] Value is the Railway PostgreSQL connection string
- [ ] Backend service redeployed
- [ ] Logs show "PostgreSQL" (not "Neon DB")
- [ ] `/health` endpoint returns success
- [ ] Can access database tables

## Next Steps After Connection

1. ✅ Backend will automatically use Railway PostgreSQL
2. ✅ All API endpoints will work with new database
3. ✅ Data will be stored in Railway PostgreSQL
4. ✅ No more disk full errors!

## Security Note

⚠️ **Keep your connection string secure!**
- Don't commit it to Git
- Don't share it publicly
- Railway Variables are encrypted and secure

---

**Your backend is ready to connect to Railway PostgreSQL!** Just set the `DATABASE_URL` environment variable and redeploy. 🚀


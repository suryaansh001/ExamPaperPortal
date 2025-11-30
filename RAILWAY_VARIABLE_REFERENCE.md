# Railway Service Variable Reference Guide

## Using `${{ Postgres.DATABASE_URL }}` in Railway

### What is this?

This is Railway's **service variable reference syntax**. It allows you to reference environment variables from one service (PostgreSQL) in another service (your backend).

### Syntax

```bash
${{ ServiceName.VARIABLE_NAME }}
```

### For PostgreSQL Connection

If your PostgreSQL service is named **"Postgres"** (or "PostgreSQL"):

```bash
${{ Postgres.DATABASE_URL }}
```

This will automatically inject the `DATABASE_URL` from your PostgreSQL service into your backend service.

## How to Set It Up

### Step 1: Check Your PostgreSQL Service Name

1. Go to Railway Dashboard
2. Look at your PostgreSQL service
3. Check the service name (usually "Postgres" or "PostgreSQL")

### Step 2: Add Variable Reference in Backend Service

1. Go to your **Backend Service** (the one running `main.py`)
2. Click on **"Variables"** tab
3. Click **"+ New Variable"**
4. Add:
   - **Key**: `DATABASE_URL`
   - **Value**: `${{ Postgres.DATABASE_URL }}`
     - Replace `Postgres` with your actual PostgreSQL service name if different
5. Click **"Add"**

### Step 3: Verify

After adding, Railway will:
- ✅ Automatically resolve the reference
- ✅ Inject the actual connection string
- ✅ Update when PostgreSQL connection changes

## Service Name Examples

The service name in Railway is case-sensitive and must match exactly:

| PostgreSQL Service Name | Variable Reference |
|------------------------|-------------------|
| `Postgres` | `${{ Postgres.DATABASE_URL }}` |
| `PostgreSQL` | `${{ PostgreSQL.DATABASE_URL }}` |
| `postgres` | `${{ postgres.DATABASE_URL }}` |
| `Database` | `${{ Database.DATABASE_URL }}` |
| `db` | `${{ db.DATABASE_URL }}` |

## How to Find Your Service Name

1. Go to Railway Dashboard
2. Click on your project
3. Look at the service list on the left
4. The name shown is what you use in the reference

## Complete Setup Example

### Scenario: Backend + PostgreSQL in Same Project

**Project Structure:**
```
My Project
├── Backend Service (Python)
└── Postgres (PostgreSQL Database)
```

**Backend Service Variables:**
```
DATABASE_URL = ${{ Postgres.DATABASE_URL }}
SECRET_KEY = your-secret-key
PORT = ${{ PORT }}
```

**Postgres Service Variables (Auto-generated):**
```
DATABASE_URL = postgresql://postgres:password@host:5432/railway
PGHOST = host
PGPORT = 5432
PGUSER = postgres
PGPASSWORD = password
PGDATABASE = railway
```

## Benefits

1. ✅ **Automatic Updates**: If PostgreSQL connection changes, backend automatically gets new URL
2. ✅ **No Manual Copying**: Don't need to copy/paste connection strings
3. ✅ **Secure**: Connection details stay in PostgreSQL service
4. ✅ **Easy Management**: One place to manage database credentials

## Alternative: Direct Value

If you prefer to set it directly (not recommended for production):

1. Go to PostgreSQL service → Variables tab
2. Copy the `DATABASE_URL` value
3. Go to Backend service → Variables tab
4. Add `DATABASE_URL` with the copied value

**But using `${{ Postgres.DATABASE_URL }}` is better** because:
- Updates automatically if database changes
- Less error-prone
- Railway best practice

## Troubleshooting

### Issue: Variable not resolving

**Check:**
1. Service name matches exactly (case-sensitive)
2. PostgreSQL service exists in same project
3. Variable name is correct (`DATABASE_URL`)

**Solution:**
- Double-check service name spelling
- Ensure both services are in the same Railway project

### Issue: Connection fails

**Check:**
1. PostgreSQL service is running (green status)
2. Variable reference is correct
3. Backend service has been redeployed after adding variable

**Solution:**
- Redeploy backend service after adding variable
- Check backend logs for connection errors

### Issue: Can't find service name

**Solution:**
- Service name is shown in Railway dashboard
- Usually "Postgres" or "PostgreSQL" by default
- You can rename services in Railway settings

## Railway Documentation

For more details, see Railway docs:
- [Service Variables](https://docs.railway.app/develop/variables)
- [Service References](https://docs.railway.app/develop/variables#service-variables)

## Quick Reference

```bash
# Reference PostgreSQL DATABASE_URL
${{ Postgres.DATABASE_URL }}

# Reference PostgreSQL PGHOST
${{ Postgres.PGHOST }}

# Reference PostgreSQL PGPASSWORD
${{ Postgres.PGPASSWORD }}

# Reference any variable from any service
${{ ServiceName.VARIABLE_NAME }}
```

---

**Summary**: Use `${{ Postgres.DATABASE_URL }}` in your backend service's `DATABASE_URL` variable to automatically connect to your Railway PostgreSQL database!


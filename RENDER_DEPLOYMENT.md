# Render.com Deployment Guide (Free Tier Available)

## Why Render?
- ✅ Free tier available for web services
- ✅ Free PostgreSQL database
- ✅ Automatic SSL certificates
- ✅ Easy GitHub integration
- ✅ No credit card required for free tier

## Step-by-Step Deployment

### 1. Create Render Account
1. Go to https://render.com
2. Sign up with GitHub (free)

### 2. Create PostgreSQL Database
1. Click "New" → "PostgreSQL"
2. Name: `paper-portal-db`
3. Plan: Free (or paid if needed)
4. Region: Choose closest to you
5. Click "Create Database"
6. Copy the "Internal Database URL" (for your app)
7. Copy the "External Database URL" (for local testing)

### 3. Create Web Service
1. Click "New" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name**: `paper-portal-backend`
   - **Region**: Same as database
   - **Branch**: `main` (or your default branch)
   - **Root Directory**: `ExamSystemBackend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free (or paid)

### 4. Set Environment Variables
In your Web Service → Environment tab, add:

**Required:**
```
DATABASE_URL=<Internal Database URL from step 2>
SECRET_KEY=<generate-random-key>
PORT=10000
```

**Email (choose one):**
```
RESEND_API_KEY=<your-resend-key>
RESEND_FROM_EMAIL=<your-email>
```

OR

```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
GMAIL_USER=<your-email>
GMAIL_PASS=<app-password>
```

### 5. Deploy
1. Click "Create Web Service"
2. Render will automatically:
   - Clone your repo
   - Install dependencies
   - Start your app
3. Wait for deployment (first deploy takes ~5-10 minutes)

### 6. Get Your URL
- Render provides: `https://your-app-name.onrender.com`
- Update frontend with this URL

## Render Free Tier Limits
- ✅ 750 hours/month (enough for 24/7)
- ✅ 512MB RAM
- ✅ Free SSL
- ⚠️ Spins down after 15 minutes of inactivity (wakes up on request)
- ⚠️ Cold starts can take 30-60 seconds

## Upgrade Options
- **Starter Plan ($7/month)**: No spin-down, better performance
- **Professional Plans**: For production workloads

## Troubleshooting

### Service Won't Start
- Check logs in Render dashboard
- Verify all environment variables are set
- Ensure `requirements.txt` is correct

### Database Connection Issues
- Use Internal Database URL (not External)
- Verify database is running
- Check connection string format

### Slow Cold Starts
- Normal on free tier (15 min inactivity)
- Upgrade to Starter plan to avoid spin-down

## Alternative: Fly.io (Also Free Tier)
See `FLY_DEPLOYMENT.md` for Fly.io deployment guide.


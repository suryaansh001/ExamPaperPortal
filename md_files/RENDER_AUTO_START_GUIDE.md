# Render Auto-Start & Keep-Alive Guide

## Problem
On Render's free tier, services automatically spin down after 15 minutes of inactivity. When a user visits the website, the backend needs to wake up, which takes 30-60 seconds (cold start).

## Solution Implemented

### 1. Backend Keep-Alive ✅
- **Location**: `main.py` - `keep_alive_task()`
- **Function**: Maintains active event loop to prevent idle detection
- **Frequency**: Heartbeat every 5 minutes
- **Note**: Self-pinging doesn't work well on Render, so we use event loop activity instead

### 2. Frontend Keep-Alive Service ✅
- **Location**: `src/utils/keepAlive.ts`
- **Function**: Pings backend every 5 minutes to keep it active
- **Auto-start**: Wakes up backend when app loads
- **Integration**: Automatically started in `App.tsx`

### 3. Wake-Up Endpoint ✅
- **Endpoint**: `GET /wake`
- **Purpose**: Simple endpoint to wake up the service
- **Usage**: Called by frontend when backend appears to be sleeping

### 4. Improved Error Handling ✅
- **Location**: `src/utils/api.ts`
- **Function**: Detects when backend is sleeping and attempts wake-up
- **User Experience**: Better handling of cold start delays

## How It Works

### When User Visits Website:
1. Frontend loads → Calls `wakeUpBackend()`
2. Backend receives request → Wakes up (if sleeping)
3. Frontend starts keep-alive service → Pings every 5 minutes
4. Backend stays active → No more spin-downs while users are active

### Keep-Alive Flow:
```
Frontend (every 5 min) → GET /health → Backend stays awake
```

### If Backend Sleeps:
```
User Request → Connection Error → Frontend calls /wake → Backend wakes up → Retry request
```

## Render Configuration

### Option 1: Use render.yaml (Recommended)
The `render.yaml` file is configured with:
- Health check path: `/health`
- Auto-deploy: Enabled
- Plan: Free (or upgrade to paid for always-on)

### Option 2: Manual Configuration
In Render Dashboard:
1. Go to your Web Service → Settings
2. Set **Health Check Path**: `/health`
3. Set **Health Check Interval**: 30 seconds
4. Enable **Auto-Deploy**

## Environment Variables

Add to Render Dashboard → Environment:
```env
BASE_URL=https://your-app.onrender.com  # Optional: for self-ping (not needed)
PORT=10000  # Automatically set by Render
```

## Testing

### Test Keep-Alive:
1. Visit your website
2. Open browser console
3. You should see: `✓ Backend keep-alive ping successful`
4. Check every 5 minutes - should see ping messages

### Test Wake-Up:
1. Wait 15+ minutes (let backend sleep)
2. Visit website
3. Check console - should see: `⏳ Backend is waking up...`
4. After 30-60 seconds: `✓ Backend woke up successfully`

## Limitations (Free Tier)

⚠️ **Render Free Tier:**
- Services spin down after 15 minutes of **no requests**
- First request after spin-down: 30-60 second delay (cold start)
- Keep-alive prevents spin-down **while users are active**
- If no users for 15+ minutes, service will still sleep

## Upgrade Options

For **always-on** service (no spin-down):
- Upgrade to Render **Starter Plan** ($7/month)
- Service stays active 24/7
- No cold start delays

## Troubleshooting

### Backend Still Sleeping?
1. Check Render logs: Dashboard → Logs
2. Verify `/health` endpoint works: `curl https://your-app.onrender.com/health`
3. Check frontend console for keep-alive messages
4. Verify `BASE_URL` is correct in frontend `.env`

### Keep-Alive Not Working?
1. Check browser console for errors
2. Verify `keepAlive.ts` is imported in `App.tsx`
3. Check network tab - should see requests to `/health` every 5 minutes

### Cold Start Too Slow?
- This is normal on free tier (30-60 seconds)
- Consider upgrading to paid plan for instant response
- Or use a service like UptimeRobot to ping `/health` every 10 minutes

## Summary

✅ **Backend**: Keep-alive task maintains active process
✅ **Frontend**: Auto-wakes backend on load + periodic pings
✅ **Error Handling**: Detects sleeping backend and wakes it up
✅ **User Experience**: Better handling of cold starts

The system now automatically wakes up the backend when users visit and keeps it active while they're using the site!


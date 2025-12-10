# Quick Fix: Email on Cloud Platforms (Render, Railway, etc.)

## Problem
Your cloud platform is blocking SMTP connections (Gmail, etc.). This is common on Render, Railway, and similar platforms.

## Solution: Use Resend SMTP (Recommended)

Resend SMTP works on cloud platforms and uses your existing Resend API key!

### Step 1: Get Your Resend API Key
You already have it! Check your `.env` file for `RESEND_API_KEY` (starts with `re_`)

### Step 2: Update Your `.env` File

Add or update these lines in your `.env` file:

```env
# Resend SMTP Configuration (works on cloud platforms)
SMTP_SERVER=smtp.resend.com
SMTP_PORT=587
SMTP_USER=resend
SMTP_PASS=re_your_resend_api_key_here
SMTP_FROM_EMAIL=onboarding@resend.dev
```

**Important**: 
- `SMTP_PASS` should be your **Resend API key** (same as `RESEND_API_KEY`)
- Example: If `RESEND_API_KEY=re_YmLY9FhV_2QS3Ycecqu6GKfxxTbkSG7t5`, then `SMTP_PASS=re_YmLY9FhV_2QS3Ycecqu6GKfxxTbkSG7t5`

### Step 3: Restart Your Server

After updating `.env`, restart your backend server.

### Step 4: Test

Try sending an OTP again. You should see:
```
✅ OTP sent via nodemailer-like service (SMTP)
✅ OTP email sent: user@example.com
```

## Alternative: Verify Domain with Resend (For Production)

If you want to use a custom "from" address (like `noreply@yourdomain.com`):

1. Go to https://resend.com/domains
2. Add your domain
3. Add the DNS records they provide
4. Wait for verification
5. Update `.env`:
   ```env
   RESEND_FROM_EMAIL=noreply@yourdomain.com
   SMTP_FROM_EMAIL=noreply@yourdomain.com
   ```

## Why This Works

- ✅ Resend SMTP works on cloud platforms (not blocked)
- ✅ Uses your existing API key (no new credentials)
- ✅ Better deliverability than Gmail
- ✅ No need for Gmail App Passwords

## Troubleshooting

If you still see errors:
1. Make sure `SMTP_PASS` is your full Resend API key (starts with `re_`)
2. Check that `SMTP_USER=resend` (exactly as shown)
3. Verify your Resend API key is valid at https://resend.com/api-keys
4. Restart your server after changing `.env`


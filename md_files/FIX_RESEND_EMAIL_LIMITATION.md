# Fix: Resend Only Sending to One Email

## The Problem

Resend's default `onboarding@resend.dev` email **only allows sending to your account email**. This is a Resend limitation, not a bug in your code.

## Solutions

### Solution 1: Use Resend SMTP (Recommended - Uses Your Existing API Key)

Resend provides SMTP access that works with any email address. Update your `.env` file:

```env
# Keep your Resend API key
RESEND_API_KEY=re_YmLY9FhV_2QS3Ycecqu6GKfxxTbkSG7t5

# Add Resend SMTP configuration (uses same API key)
SMTP_SERVER=smtp.resend.com
SMTP_PORT=587
SMTP_USER=resend
SMTP_PASS=re_YmLY9FhV_2QS3Ycecqu6GKfxxTbkSG7t5
SMTP_FROM_EMAIL=onboarding@resend.dev
```

**Note**: `SMTP_PASS` should be your **Resend API key** (same as `RESEND_API_KEY`)

### Solution 2: Use Gmail SMTP

If Resend SMTP doesn't work, use Gmail:

1. **Create Gmail App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Create app password for "Mail"
   - Copy the 16-character password

2. **Update `.env`**:
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-16-char-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
```

### Solution 3: Verify Domain with Resend (Best for Production)

1. Go to: https://resend.com/domains
2. Add your domain (e.g., `jklu.edu.in`)
3. Add DNS records they provide
4. Wait for verification
5. Update `.env`:
```env
RESEND_API_KEY=re_YmLY9FhV_2QS3Ycecqu6GKfxxTbkSG7t5
RESEND_FROM_EMAIL=noreply@jklu.edu.in
```

## How It Works

The code automatically:
1. **Tries Resend REST API first** (fast, but limited to account email)
2. **Falls back to SMTP** if Resend API fails (works with any email)

So even if Resend API fails, SMTP will handle it!

## Quick Fix (Recommended)

Add this to your `.env` file:

```env
SMTP_SERVER=smtp.resend.com
SMTP_PORT=587
SMTP_USER=resend
SMTP_PASS=re_YmLY9FhV_2QS3Ycecqu6GKfxxTbkSG7t5
SMTP_FROM_EMAIL=onboarding@resend.dev
```

Then **restart your backend server**.

## Test

After updating, test by:
1. Requesting OTP for any user email
2. Check server logs - should show "Email sent successfully via SMTP"
3. User should receive email

---

**The system already has fallback logic built in - you just need to configure SMTP!**



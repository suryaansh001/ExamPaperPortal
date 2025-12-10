# Email Configuration Guide

## Problem
Resend's default `onboarding@resend.dev` email only allows sending to your own email address. To send to other users, you need either:
1. **Verify a domain with Resend** (recommended for production)
2. **Use SMTP** (Gmail, Outlook, etc.) as a fallback

## Solution 1: Configure Gmail SMTP (Quick Fix)

### Step 1: Create Gmail App Password

1. Go to your Google Account: https://myaccount.google.com/
2. Navigate to **Security** → **2-Step Verification** (enable if not already)
3. Scroll down to **App passwords**
4. Create a new app password:
   - Select app: **Mail**
   - Select device: **Other (Custom name)**
   - Name it: **Paper Portal**
   - Click **Generate**
5. **Copy the 16-character password** (you'll need this)

### Step 2: Set Environment Variables

Add these to your `.env` file or deployment environment:

```bash
# Gmail SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=amanpratapsinghuy67032@gmail.com
SMTP_PASS=your-16-character-app-password-here
SMTP_FROM_EMAIL=amanpratapsinghuy67032@gmail.com

# Optional: Keep Resend for future use (after domain verification)
# RESEND_API_KEY=re_xxxxx
# RESEND_FROM_EMAIL=noreply@yourdomain.com
```

### Step 3: Restart Your Server

After setting the environment variables, restart your backend server.

## Solution 2: Verify Domain with Resend (Production)

### Step 1: Verify Your Domain

1. Go to https://resend.com/domains
2. Add your domain (e.g., `yourdomain.com`)
3. Add the DNS records they provide
4. Wait for verification (usually a few minutes)

### Step 2: Update Environment Variables

```bash
RESEND_API_KEY=re_xxxxx
RESEND_FROM_EMAIL=noreply@yourdomain.com
```

## Testing

After configuration, test the email service:

```bash
# Check email health
curl http://localhost:8000/health/email

# Or visit in browser
http://localhost:8000/health/email
```

## Troubleshooting

### Gmail SMTP Not Working?

1. **Check App Password**: Make sure you're using the 16-character app password, not your regular Gmail password
2. **Enable 2-Step Verification**: Required for app passwords
3. **Check Firewall**: Some cloud platforms (Render, Railway) block SMTP port 587
   - Solution: Use Resend with verified domain instead

### Resend Domain Verification Issues?

1. **DNS Propagation**: Can take up to 48 hours (usually much faster)
2. **Check DNS Records**: Make sure all required records are added correctly
3. **Verify Status**: Check domain status in Resend dashboard

## Alternative SMTP Providers

If Gmail doesn't work, you can use:

### Outlook/Hotmail
```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=your-email@outlook.com
SMTP_PASS=your-password
```

### SendGrid (Free tier available)
```bash
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASS=your-sendgrid-api-key
```

### Mailgun (Free tier available)
```bash
SMTP_SERVER=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=your-mailgun-username
SMTP_PASS=your-mailgun-password
```

## Quick Setup Script

For local development, create a `.env` file in `ExamSystemBackend/`:

```bash
# Copy this template
cp .env.example .env

# Edit .env and add your credentials
nano .env  # or use your preferred editor
```

## Notes

- **Security**: Never commit `.env` files to git
- **Production**: Use Resend with verified domain for best deliverability
- **Development**: Gmail SMTP works fine for testing
- **Rate Limits**: Gmail has daily sending limits (~500 emails/day for free accounts)


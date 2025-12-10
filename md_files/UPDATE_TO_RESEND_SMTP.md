# Update to Resend SMTP

Based on the Resend SMTP settings you're viewing, here's how to update your `.env` file:

## Current Configuration (Gmail SMTP):
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=amanpratapsinghuy67032@gmail.com
SMTP_PASS=your-gmail-app-password
SMTP_FROM_EMAIL=amanpratapsinghuy67032@gmail.com
```

## Updated Configuration (Resend SMTP):
```
SMTP_SERVER=smtp.resend.com
SMTP_PORT=587
SMTP_USER=resend
SMTP_PASS=re_your_resend_api_key_here
SMTP_FROM_EMAIL=onboarding@resend.dev
```

## Steps:

1. **Copy your Resend API Key** (you already have it: `re_...G7t5`)

2. **Update your `.env` file** - Replace the SMTP section with:
   ```bash
   SMTP_SERVER=smtp.resend.com
   SMTP_PORT=587
   SMTP_USER=resend
   SMTP_PASS=re_your_actual_api_key_here
   SMTP_FROM_EMAIL=onboarding@resend.dev
   ```

3. **Port Options** (from Resend settings):
   - `587` - Recommended (TLS/STARTTLS) ✅
   - `465` - SSL
   - `2465` or `2587` - Alternative TLS ports

4. **Restart your backend server**

## Benefits of Resend SMTP:

- ✅ Uses your existing Resend API key (no new credentials needed)
- ✅ Better deliverability than Gmail
- ✅ No Gmail App Password required
- ✅ Works seamlessly with Resend infrastructure
- ✅ Can still verify a domain later for custom "from" addresses

## After Update:

Run the check script to verify:
```bash
python ExamSystemBackend/check_env_vars.py
```

Then restart your server and test sending an OTP!


# Resend SMTP Configuration

Great news! You can use Resend's SMTP server with your existing Resend API key. This is simpler than setting up Gmail.

## Configuration

Add these to your `.env` file:

```bash
# Resend SMTP Configuration (uses your existing API key)
SMTP_SERVER=smtp.resend.com
SMTP_PORT=587
SMTP_USER=resend
SMTP_PASS=re_your_resend_api_key_here
SMTP_FROM_EMAIL=onboarding@resend.dev
```

## Important Notes:

1. **SMTP_PASS**: Use your Resend API key (the same one you have in `RESEND_API_KEY`)
2. **Port Options**:
   - `587` - Recommended (TLS/STARTTLS)
   - `465` - SSL
   - `2465` or `2587` - Alternative TLS ports
3. **SMTP_USER**: Always use `resend`
4. **SMTP_FROM_EMAIL**: Can use `onboarding@resend.dev` or verify a domain later

## Benefits:

- ✅ Uses your existing Resend API key
- ✅ No need for Gmail App Passwords
- ✅ Works with Resend's infrastructure
- ✅ Better deliverability than Gmail SMTP
- ✅ Can still verify a domain later for custom "from" addresses

## After Configuration:

1. Save your `.env` file
2. Restart your backend server
3. Test by sending an OTP
4. Check logs to confirm SMTP is working

The system will automatically use Resend SMTP when the REST API fails (like when sending to non-owner emails).


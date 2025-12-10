#!/usr/bin/env python3
"""
Quick test script to verify email configuration
Run this after updating .env to check if SMTP/Resend is configured correctly
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("Email Configuration Check")
print("=" * 60)

# Check Resend
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "").strip()
RESEND_CONFIGURED = bool(RESEND_API_KEY)

print(f"\n[Resend Configuration]")
print(f"   API Key: {'[OK] Set' if RESEND_API_KEY else '[X] Not set'}")
if RESEND_API_KEY:
    print(f"   Key (last 4): {'*' * 10}{RESEND_API_KEY[-4:] if len(RESEND_API_KEY) > 4 else '****'}")
print(f"   From Email: {RESEND_FROM_EMAIL if RESEND_FROM_EMAIL else 'Not set (default: onboarding@resend.dev)'}")

# Check SMTP
SMTP_SERVER = os.getenv("SMTP_SERVER", "").strip()
SMTP_PORT = os.getenv("SMTP_PORT", "").strip()
SMTP_USER = os.getenv("SMTP_USER", os.getenv("GMAIL_USER", "")).strip()
SMTP_PASS = os.getenv("SMTP_PASS", os.getenv("GMAIL_PASS", "")).strip()
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER).strip()

SMTP_CONFIGURED = bool(SMTP_USER and SMTP_PASS and SMTP_SERVER)

print(f"\n[SMTP Configuration]")
print(f"   Server: {SMTP_SERVER if SMTP_SERVER else 'Not set (default: smtp.gmail.com)'}")
print(f"   Port: {SMTP_PORT if SMTP_PORT else 'Not set (default: 587)'}")
print(f"   User: {'[OK] Set' if SMTP_USER else '[X] Not set'}")
if SMTP_USER:
    print(f"   Email: {SMTP_USER}")
print(f"   Password: {'[OK] Set' if SMTP_PASS else '[X] Not set'}")
if SMTP_PASS:
    print(f"   Password length: {len(SMTP_PASS)} characters")
    if len(SMTP_PASS) == 16:
        print(f"   [OK] Looks like a Gmail App Password (16 chars)")
    elif len(SMTP_PASS) < 8:
        print(f"   [WARNING] Password seems too short (should be 16 for Gmail App Password)")
print(f"   From Email: {SMTP_FROM_EMAIL if SMTP_FROM_EMAIL else 'Not set (uses SMTP_USER)'}")

# Overall status
EMAIL_CONFIGURED = RESEND_CONFIGURED or SMTP_CONFIGURED

print(f"\n{'=' * 60}")
print(f"Overall Status:")
if EMAIL_CONFIGURED:
    print(f"   [OK] Email service is CONFIGURED")
    if RESEND_CONFIGURED:
        print(f"   Primary: Resend API")
    if SMTP_CONFIGURED:
        print(f"   {'Primary' if not RESEND_CONFIGURED else 'Fallback'}: SMTP ({SMTP_SERVER})")
    print(f"\n   Next steps:")
    print(f"   1. Restart your backend server")
    print(f"   2. Test by sending an OTP (try login/register)")
    print(f"   3. Check server logs for email sending status")
    print(f"   4. Visit http://localhost:10000/health/email for detailed status (or use PORT env var if different)")
else:
    print(f"   [X] Email service is NOT CONFIGURED")
    print(f"\n   To configure:")
    print(f"   1. Set SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASS in .env")
    print(f"   2. Or set RESEND_API_KEY and RESEND_FROM_EMAIL")
    print(f"   3. See EMAIL_SETUP_GUIDE.md for detailed instructions")

print(f"\n{'=' * 60}\n")


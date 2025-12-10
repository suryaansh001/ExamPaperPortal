#!/usr/bin/env python3
"""
Check all environment variables related to email
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("All Email-Related Environment Variables")
print("=" * 60)

env_vars = [
    "RESEND_API_KEY",
    "RESEND_FROM_EMAIL",
    "SMTP_SERVER",
    "SMTP_PORT",
    "SMTP_USER",
    "SMTP_PASS",
    "SMTP_FROM_EMAIL",
    "GMAIL_USER",  # Legacy support
    "GMAIL_PASS",  # Legacy support
]

print("\nChecking environment variables:\n")
for var in env_vars:
    value = os.getenv(var, "")
    if value:
        if "PASS" in var or "KEY" in var:
            # Hide sensitive values
            display_value = f"{'*' * (len(value) - 4)}{value[-4:]}" if len(value) > 4 else "****"
            print(f"  {var:20} = {display_value} (length: {len(value)})")
        else:
            print(f"  {var:20} = {value}")
    else:
        print(f"  {var:20} = [NOT SET]")

print("\n" + "=" * 60)
print("Configuration Status:")
print("=" * 60)

# Check what's configured
has_resend = bool(os.getenv("RESEND_API_KEY", "").strip())
has_smtp_user = bool(os.getenv("SMTP_USER", os.getenv("GMAIL_USER", "")).strip())
has_smtp_pass = bool(os.getenv("SMTP_PASS", os.getenv("GMAIL_PASS", "")).strip())
has_smtp_server = bool(os.getenv("SMTP_SERVER", "").strip())

if has_resend:
    print("\n[OK] Resend API Key is set")
    print("     Note: onboarding@resend.dev only works for your own email")
    print("     To send to others, you need SMTP or a verified domain")

if has_smtp_user and has_smtp_pass:
    print("\n[OK] SMTP credentials are set")
    if has_smtp_server:
        print(f"     Server: {os.getenv('SMTP_SERVER')}")
    else:
        print("     Server: Will use default (smtp.gmail.com)")
    print("     This will work as fallback when Resend fails!")
else:
    print("\n[X] SMTP credentials are NOT set")
    print("     To fix: Add these to your .env file:")
    print("     SMTP_SERVER=smtp.gmail.com")
    print("     SMTP_PORT=587")
    print("     SMTP_USER=your-email@gmail.com")
    print("     SMTP_PASS=your-16-char-app-password")

print("\n" + "=" * 60)


#!/usr/bin/env python3
"""
Verify SMTP configuration and test connection
"""

import os
import smtplib
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

print("=" * 60)
print("SMTP Configuration Verification")
print("=" * 60)

SMTP_SERVER = os.getenv("SMTP_SERVER", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASS = os.getenv("SMTP_PASS", "").strip()
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER).strip()

print(f"\nCurrent Configuration:")
print(f"  Server: {SMTP_SERVER}")
print(f"  Port: {SMTP_PORT}")
print(f"  User: {SMTP_USER}")
print(f"  Password: {'*' * len(SMTP_PASS)} (length: {len(SMTP_PASS)})")
print(f"  From Email: {SMTP_FROM_EMAIL}")

# Check if it's Gmail
is_gmail = "gmail.com" in SMTP_SERVER.lower()
is_resend = "resend.com" in SMTP_SERVER.lower()

print(f"\n{'=' * 60}")
print("Analysis:")
print(f"{'=' * 60}")

if is_gmail:
    print("\n[Gmail SMTP Detected]")
    if len(SMTP_PASS) == 16:
        print("  [OK] Password length looks correct for Gmail App Password")
    else:
        print(f"  [WARNING] Password length is {len(SMTP_PASS)} characters")
        print("  Gmail App Passwords should be exactly 16 characters")
        print("  If this is your regular password, it won't work!")
        print("  Get App Password: https://myaccount.google.com/apppasswords")
    
    print("\n  To switch to Resend SMTP (recommended):")
    print("  Update your .env file:")
    print("    SMTP_SERVER=smtp.resend.com")
    print("    SMTP_PORT=587")
    print("    SMTP_USER=resend")
    print("    SMTP_PASS=re_your_resend_api_key")
    print("    SMTP_FROM_EMAIL=onboarding@resend.dev")

elif is_resend:
    print("\n[Resend SMTP Detected]")
    if SMTP_PASS.startswith("re_"):
        print("  [OK] Password looks like a Resend API key")
    else:
        print("  [WARNING] Password should be your Resend API key (starts with 're_')")
    if SMTP_USER.lower() == "resend":
        print("  [OK] Username is correct")
    else:
        print(f"  [WARNING] Username should be 'resend', not '{SMTP_USER}'")

print(f"\n{'=' * 60}")
print("Test Connection (optional):")
print(f"{'=' * 60}")
print("\nTo test if SMTP works, restart your server and try sending an OTP.")
print("Check the server logs to see if email sending succeeds.\n")


"""
Email Service - Nodemailer-like API for Python
Simple and clean email sending using SMTP

Usage (similar to nodemailer):
    from email_service import send_otp_email
    
    # Send OTP email
    send_otp_email("user@example.com", "123456")

Configuration (via environment variables):
    SMTP_SERVER=smtp.gmail.com
    SMTP_PORT=587
    SMTP_USER=your-email@gmail.com
    SMTP_PASS=your-app-password
    SMTP_FROM_EMAIL=your-email@gmail.com
    SMTP_SECURE=false  # 465 = true, 587 = false
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

# Email configuration from environment variables
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASS = os.getenv("SMTP_PASS", "").strip()
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER).strip()
SMTP_SECURE = os.getenv("SMTP_SECURE", "false").lower() == "true"  # 465 = true, 587 = false

# Create transporter (similar to nodemailer.createTransport)
def create_transporter():
    """Create and return SMTP transporter configuration"""
    return {
        "host": SMTP_SERVER,
        "port": SMTP_PORT,
        "secure": SMTP_SECURE,  # 465 = true, 587 = false
        "auth": {
            "user": SMTP_USER,
            "pass": SMTP_PASS,
        },
    }

def send_otp_email(to: str, otp: str) -> bool:
    """
    Send OTP email - Nodemailer-like function
    
    Args:
        to: Recipient email address
        otp: OTP code to send
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Validate configuration
        if not SMTP_USER or not SMTP_PASS or not SMTP_SERVER:
            print(f"⚠️  Email not configured. OTP for {to}: {otp}")
            print("   Configure SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASS in .env")
            return False
        
        # Create message
        message = MIMEMultipart()
        message["From"] = SMTP_FROM_EMAIL
        message["To"] = to
        message["Subject"] = "Your OTP Code"
        
        # Plain text version
        text_body = f"Your OTP is {otp}. It will expire in 10 minutes."
        message.attach(MIMEText(text_body, "plain"))
        
        # HTML version (optional - can be enhanced)
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #333; text-align: center;">Your OTP Code</h2>
                    <div style="text-align: center; margin: 30px 0;">
                        <div style="font-size: 32px; font-weight: bold; color: #007bff; letter-spacing: 5px; padding: 20px; background-color: #f8f9fa; border-radius: 5px; display: inline-block;">
                            {otp}
                        </div>
                    </div>
                    <p style="color: #666; text-align: center; font-size: 14px;">
                        This code will expire in 10 minutes.
                    </p>
                    <p style="color: #999; text-align: center; font-size: 12px; margin-top: 30px;">
                        If you didn't request this code, please ignore this email.
                    </p>
                </div>
            </body>
        </html>
        """
        message.attach(MIMEText(html_body, "html"))
        
        # Send email via SMTP
        if SMTP_SECURE:
            # Use SSL (port 465)
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=15)
        else:
            # Use STARTTLS (port 587)
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15)
            server.starttls()
        
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(message)
        server.quit()
        
        print(f"✅ OTP email sent: {to}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Email authentication error: {e}")
        print(f"   Check SMTP_USER and SMTP_PASS credentials")
        return False
    except (smtplib.SMTPException, OSError, ConnectionError) as e:
        error_msg = str(e)
        print(f"❌ Email send error: {error_msg}")
        print(f"   Server: {SMTP_SERVER}:{SMTP_PORT}")
        
        # Check if it's a network unreachable error (common on cloud platforms)
        if "Network is unreachable" in error_msg or "Errno 101" in error_msg:
            print(f"\n   ⚠️  SMTP is blocked on this platform (common on Render, Railway, etc.)")
            print(f"   Solutions:")
            print(f"   1. Use Resend SMTP (works on cloud platforms) - RECOMMENDED")
            print(f"      Add to .env:")
            print(f"      SMTP_SERVER=smtp.resend.com")
            print(f"      SMTP_PORT=587")
            print(f"      SMTP_USER=resend")
            print(f"      SMTP_PASS=your_resend_api_key_here")
            print(f"      SMTP_FROM_EMAIL=onboarding@resend.dev")
            print(f"      (Use your existing RESEND_API_KEY as SMTP_PASS)")
            print(f"")
            print(f"   2. Verify domain with Resend (for production)")
            print(f"      - Verify domain at https://resend.com/domains")
            print(f"      - Update RESEND_FROM_EMAIL to use your domain")
            print(f"")
            print(f"   3. Use SendGrid or Mailgun (work on cloud platforms)")
            print(f"")
        
        return False
    except Exception as e:
        print(f"❌ Email send error: {type(e).__name__}: {e}")
        return False



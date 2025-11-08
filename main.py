# main.py
from __future__ import annotations  # Enable forward references
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Query, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Text, Enum as SQLEnum, DateTime, text, Index
from sqlalchemy.orm import declarative_base, Session, sessionmaker, relationship, joinedload
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from enum import Enum
import shutil
import os
from pathlib import Path
from passlib.context import CryptContext
from jose import JWTError, jwt
from dotenv import load_dotenv
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Try to import Resend (recommended for production email sending)
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False

# Load environment variables
load_dotenv()

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/paper_portal")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Email Configuration - Support Resend (primary) and SMTP (fallback)
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev").strip()

# Generic SMTP Configuration (works with Gmail, SendGrid, Mailgun, Outlook, etc.)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", os.getenv("GMAIL_USER", "")).strip()  # Support both SMTP_USER and GMAIL_USER
SMTP_PASS = os.getenv("SMTP_PASS", os.getenv("GMAIL_PASS", "")).strip()  # Support both SMTP_PASS and GMAIL_PASS
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER).strip()  # From email address

# Validate email configuration on startup
RESEND_CONFIGURED = bool(RESEND_API_KEY and RESEND_AVAILABLE)
SMTP_CONFIGURED = bool(SMTP_USER and SMTP_PASS and SMTP_SERVER and not SMTP_USER.startswith("your-") and not SMTP_PASS.startswith("your-"))
EMAIL_CONFIGURED = RESEND_CONFIGURED or SMTP_CONFIGURED

if not EMAIL_CONFIGURED:
    print("\n⚠️  WARNING: Email not configured!")
    print("   Option 1 (Recommended): Set RESEND_API_KEY and RESEND_FROM_EMAIL")
    print("   Option 2: Set SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASS")
    print("   OTP emails will be printed to console only for now")
    print("\n")
elif RESEND_CONFIGURED:
    print("\n✓ Resend email service configured")
    print(f"   API Key: {'*' * 10}{RESEND_API_KEY[-4:] if len(RESEND_API_KEY) > 4 else '****'}")
    print(f"   From Email: {RESEND_FROM_EMAIL}")
    resend.api_key = RESEND_API_KEY
elif SMTP_CONFIGURED:
    print(f"\n✓ SMTP email service configured: {SMTP_SERVER}:{SMTP_PORT}")
    print(f"   From: {SMTP_FROM_EMAIL}")
    print("   Note: Some cloud platforms may block SMTP connections")
print("\n")

# Database setup with Neon DB support
# Neon requires SSL/TLS connections
if "neon.tech" in DATABASE_URL or "neondb" in DATABASE_URL:
    # Neon DB connection with SSL
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "sslmode": "require",
            "connect_timeout": 10,
        },
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=10,
    )
else:
    # Local PostgreSQL or other providers
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={
            "connect_timeout": 10,
        }
    )

# Validate DB connectivity; fall back to SQLite for local development if PostgreSQL is unavailable
try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
except Exception as e:
    if DATABASE_URL.startswith("postgresql://") and ("localhost" in DATABASE_URL or "127.0.0.1" in DATABASE_URL):
        print("WARNING: PostgreSQL at localhost:5432 is not reachable. Falling back to local SQLite database 'paper_portal.db' for development.")
        DATABASE_URL = "sqlite:///paper_portal.db"
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )
    else:
        raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Create uploads directory
UPLOAD_DIR_STR = os.getenv("UPLOAD_DIR", "uploads")
UPLOAD_DIR = Path(UPLOAD_DIR_STR)
UPLOAD_DIR.mkdir(exist_ok=True)

# In-memory OTP storage (use Redis for production)
otp_storage = {}
# In-memory registration data storage (use Redis for production)
registration_storage = {}

# Background task: Clean up expired OTPs and registration data
def cleanup_expired_data():
    """Clean up expired OTPs and registration data"""
    current_time = datetime.now(timezone.utc)
    
    # Clean expired OTPs
    expired_emails = [
        email for email, data in otp_storage.items()
        if current_time > data.get("expires_at", datetime.min.replace(tzinfo=timezone.utc))
    ]
    for email in expired_emails:
        del otp_storage[email]
    
    # Clean expired registration data
    expired_reg_emails = [
        email for email, data in registration_storage.items()
        if current_time > data.get("expires_at", datetime.min.replace(tzinfo=timezone.utc))
    ]
    for email in expired_reg_emails:
        del registration_storage[email]
    
    if expired_emails or expired_reg_emails:
        print(f"🧹 Cleaned up {len(expired_emails)} expired OTPs and {len(expired_reg_emails)} expired registration sessions")

# ========== Enums ==========
class PaperType(str, Enum):
    QUIZ = "quiz"
    MIDTERM = "midterm"
    ENDTERM = "endterm"
    ASSIGNMENT = "assignment"
    PROJECT = "project"
    OTHER = "other"

class SubmissionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

# ========== Database Models ==========
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    # Profile fields 
    age = Column(Integer, nullable=True)
    year = Column(String(20), nullable=True)
    university = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    roll_no = Column(String(100), nullable=True)
    student_id = Column(String(100), nullable=True)
    photo_path = Column(String(500), nullable=True)
    id_card_path = Column(String(500), nullable=True)
    id_verified = Column(Boolean, default=False)
    verified_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    papers = relationship("Paper", foreign_keys="Paper.uploaded_by", back_populates="uploader")

class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    papers = relationship("Paper", back_populates="course")

class Paper(Base):
    __tablename__ = "papers"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True)
    
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    paper_type = Column(SQLEnum(PaperType), nullable=False, index=True)
    year = Column(Integer, index=True)
    semester = Column(String(20), index=True)
    
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer)
    
    status = Column(SQLEnum(SubmissionStatus), default=SubmissionStatus.PENDING, index=True)
    reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at = Column(DateTime)
    rejection_reason = Column(Text)
    
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    course = relationship("Course", back_populates="papers", lazy="joined")
    uploader = relationship("User", foreign_keys=[uploaded_by], back_populates="papers", lazy="joined")
    reviewer = relationship("User", foreign_keys=[reviewed_by], lazy="select")
    
    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_paper_status_uploaded', 'status', 'uploaded_at'),
        Index('idx_paper_course_status', 'course_id', 'status'),
        Index('idx_paper_type_year', 'paper_type', 'year'),
    )

# Create tables
Base.metadata.create_all(bind=engine)

# ========== Pydantic Schemas ==========
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str
    confirm_password: str

class RegisterVerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    otp: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: str
    name: str
    is_admin: bool
    email_verified: bool
    # extended profile fields
    age: Optional[int] = None
    year: Optional[str] = None
    university: Optional[str] = None
    department: Optional[str] = None
    roll_no: Optional[str] = None
    student_id: Optional[str] = None
    photo_path: Optional[str] = None
    id_card_path: Optional[str] = None
    id_verified: bool
    created_at: datetime

class RegisterVerifyResponse(BaseModel):
    access_token: str
    token_type: str
    user: "UserResponse"

# OTP Schemas
class SendOTPRequest(BaseModel):
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class CourseCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None

class CourseUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None

class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    code: str
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

class PaperResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    course_id: int
    course_code: Optional[str]
    course_name: Optional[str]
    uploader_name: Optional[str]
    uploader_email: Optional[str]
    title: str
    description: Optional[str]
    paper_type: PaperType
    year: Optional[int]
    semester: Optional[str]
    file_name: str
    file_path: str
    file_size: Optional[int]
    status: SubmissionStatus
    uploaded_at: datetime
    reviewed_at: Optional[datetime]
    rejection_reason: Optional[str]

class PaperReview(BaseModel):
    status: SubmissionStatus
    rejection_reason: Optional[str] = None

class PaperUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    paper_type: Optional[PaperType] = None
    course_id: Optional[int] = None
    year: Optional[int] = None
    semester: Optional[str] = None

class DashboardStats(BaseModel):
    total_papers: int
    pending_papers: int
    approved_papers: int
    rejected_papers: int
    total_courses: int
    total_users: int

# ========== Auth Functions ==========
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ========== OTP Functions ==========
def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email: str, otp: str):
    """
    Send OTP to email using Resend (primary) or Gmail SMTP (fallback).
    Supports both testing (console output) and production (actual email sending).
    """
    try:
        # Always print to console for testing/debugging
        print(f"\n{'='*60}")
        print(f"OTP for {email}: {otp}")
        print(f"Expires in: 10 minutes")
        print(f"{'='*60}\n")
        
        # If email is not configured, just use console output
        if not EMAIL_CONFIGURED:
            print(f"ℹ️  Email credentials not configured. OTP shown above.")
            print(f"    Configure RESEND_API_KEY or GMAIL_USER/GMAIL_PASS in .env\n")
            return True
        
        # Email HTML template
        html_body = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Paper Portal - Email Verification</title>
                <style>
                    body {{
                        margin: 0;
                        padding: 0;
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background-color: #000000;
                        color: #ffffff;
                        line-height: 1.6;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: #000000;
                    }}
                    .header {{
                        text-align: center;
                        padding: 40px 20px;
                        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                        border-radius: 15px;
                        margin-bottom: 30px;
                        border: 2px solid #333333;
                    }}
                    .logo {{
                        font-size: 28px;
                        font-weight: bold;
                        color: #ffffff;
                        margin-bottom: 10px;
                        text-shadow: 0 2px 4px rgba(0,0,0,0.5);
                    }}
                    .subtitle {{
                        font-size: 16px;
                        color: #cccccc;
                        margin-bottom: 0;
                    }}
                    .content {{
                        background-color: #1a1a1a;
                        padding: 40px;
                        border-radius: 15px;
                        border: 1px solid #333333;
                        margin-bottom: 30px;
                    }}
                    .greeting {{
                        font-size: 20px;
                        font-weight: 600;
                        color: #ffffff;
                        margin-bottom: 20px;
                    }}
                    .otp-container {{
                        text-align: center;
                        margin: 40px 0;
                        padding: 30px;
                        background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
                        border-radius: 12px;
                        border: 2px solid #4a4a4a;
                    }}
                    .otp-label {{
                        font-size: 16px;
                        color: #cccccc;
                        margin-bottom: 15px;
                        display: block;
                    }}
                    .otp-code {{
                        font-family: 'Courier New', monospace;
                        font-size: 36px;
                        font-weight: bold;
                        color: #00d4ff;
                        letter-spacing: 8px;
                        background-color: #000000;
                        padding: 20px 40px;
                        border-radius: 8px;
                        border: 2px solid #00d4ff;
                        display: inline-block;
                        text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
                        box-shadow: 0 0 20px rgba(0, 212, 255, 0.2);
                    }}
                    .warning {{
                        background-color: #2d1b1b;
                        border: 1px solid #ff6b6b;
                        border-radius: 8px;
                        padding: 20px;
                        margin: 30px 0;
                        text-align: center;
                    }}
                    .warning-icon {{
                        color: #ff6b6b;
                        font-size: 24px;
                        margin-bottom: 10px;
                    }}
                    .warning-text {{
                        color: #ff6b6b;
                        font-weight: 600;
                        margin-bottom: 5px;
                    }}
                    .warning-subtext {{
                        color: #cccccc;
                        font-size: 14px;
                    }}
                    .footer {{
                        text-align: center;
                        padding: 30px 20px;
                        background-color: #0a0a0a;
                        border-radius: 10px;
                        border-top: 1px solid #333333;
                    }}
                    .footer-text {{
                        color: #888888;
                        font-size: 12px;
                        margin: 0;
                    }}
                    .security-note {{
                        background-color: #1a1a2e;
                        border: 1px solid #16213e;
                        border-radius: 8px;
                        padding: 15px;
                        margin-top: 20px;
                    }}
                    .security-text {{
                        color: #a0a0a0;
                        font-size: 11px;
                        margin: 0;
                        font-style: italic;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="logo">📚 Paper Portal</div>
                        <p class="subtitle">Academic Paper Management System</p>
                    </div>

                    <div class="content">
                        <h1 class="greeting">Email Verification Required</h1>
                        <p style="color: #cccccc; margin-bottom: 30px;">
                            Welcome to Paper Portal! To complete your registration and access academic papers, please verify your email address using the code below.
                        </p>

                        <div class="otp-container">
                            <span class="otp-label">Your Verification Code</span>
                            <div class="otp-code">{otp}</div>
                        </div>

                        <div class="warning">
                            <div class="warning-icon">⏰</div>
                            <div class="warning-text">Code Expires in 10 Minutes</div>
                            <div class="warning-subtext">Please use this code immediately to complete your verification</div>
                        </div>

                        <p style="color: #cccccc; text-align: center;">
                            If you didn't request this verification code, please ignore this email.
                        </p>
                    </div>

                    <div class="footer">
                        <div class="security-note">
                            <p class="security-text">
                                🔒 This is an automated message from Paper Portal. For security reasons, never share your verification code with anyone.
                            </p>
                        </div>
                        <p class="footer-text" style="margin-top: 20px;">
                            © 2025 Paper Portal - Secure Academic Document Management
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
        
        # Try Resend first (recommended for production)
        if RESEND_CONFIGURED:
            try:
                # Ensure API key is set (in case it wasn't set at startup)
                resend.api_key = RESEND_API_KEY
                
                # Send email using Resend SDK
                email_response = resend.Emails.send({
                    "from": RESEND_FROM_EMAIL,
                    "to": [email],  # User's email address from login/signup
                    "subject": "Your Paper Portal Verification Code",
                    "html": html_body
                })
                
                print(f"✓ Email sent successfully via Resend")
                print(f"   From: {RESEND_FROM_EMAIL}")
                print(f"   To: {email}")
                print(f"   OTP: {otp}")
                return True
            except Exception as e:
                print(f"❌ Resend error: {type(e).__name__}: {e}")
                print(f"   From: {RESEND_FROM_EMAIL}")
                print(f"   To: {email}")
                print(f"   API Key configured: {'Yes' if RESEND_API_KEY else 'No'}")
                print(f"   Falling back to SMTP...\n")
        
        # Fallback to SMTP if Resend fails or not configured
        if SMTP_CONFIGURED:
            try:
                message = MIMEMultipart()
                message["From"] = SMTP_FROM_EMAIL
                message["To"] = email
                message["Subject"] = "Your Paper Portal Verification Code"
                message.attach(MIMEText(html_body, "html"))
                
                # Send via SMTP with timeout
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15) as server:
                    server.starttls()
                    server.login(SMTP_USER, SMTP_PASS)
                    server.send_message(message)
                
                print(f"✓ Email sent successfully via SMTP ({SMTP_SERVER}) to {email}")
                return True
                
            except smtplib.SMTPAuthenticationError as e:
                print(f"❌ SMTP authentication failed: {e}")
                print(f"   Reason: Check SMTP_USER and SMTP_PASS in environment variables")
                print(f"   Server: {SMTP_SERVER}:{SMTP_PORT}")
                if "gmail.com" in SMTP_SERVER:
                    print(f"   Note: For Gmail, use App Password (not regular password)")
                    print(f"   Check: https://myaccount.google.com/apppasswords\n")
                else:
                    print(f"   Note: Verify your SMTP credentials are correct\n")
                return True
                
            except (smtplib.SMTPException, OSError, ConnectionError) as e:
                print(f"❌ SMTP connection error: {type(e).__name__}: {e}")
                print(f"   Server: {SMTP_SERVER}:{SMTP_PORT}")
                print(f"   Note: Some cloud platforms (Render, Railway, etc.) may block SMTP connections")
                print(f"   Recommendation: Use Resend API or a provider with SMTP relay (SendGrid, Mailgun)")
                print(f"   Get free API key at https://resend.com\n")
                return True
            
            except Exception as e:
                print(f"❌ Unexpected SMTP error: {type(e).__name__}: {e}\n")
                return True
        
        # If we get here, no email service worked
        print(f"⚠️  No email service available for sending\n")
        return True
    
    except Exception as e:
        print(f"❌ Critical error in send_otp_email: {type(e).__name__}: {e}\n")
        return True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

def require_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# ========== FastAPI App ==========
app = FastAPI(title="Paper Portal API", version="2.0.0")

# Startup event to log configuration
@app.on_event("startup")
async def startup_event():
    print("\n" + "="*70)
    print("🚀 Paper Portal API Starting...")
    print("="*70)
    print(f"✓ Database: {'Neon DB (SSL/TLS enabled)' if 'neon.tech' in DATABASE_URL else 'PostgreSQL'}")
    print(f"✓ Email: {'✓ Configured' if EMAIL_CONFIGURED else '❌ NOT CONFIGURED (Console output only)'}")
    if not EMAIL_CONFIGURED:
        print(f"  └─ Set GMAIL_USER and GMAIL_PASS in .env to enable email sending")
    print("="*70 + "\n")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory as static files for direct serving
# This allows frontend to access files directly via /uploads/{filename}
try:
    app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
except Exception as e:
    print(f"Warning: Could not mount uploads directory: {e}")


# ========== Health & Status Endpoints ==========

@app.get("/health")
def health_check():
    """Check API health and configuration status"""
    # Test database connection
    db_status = "unknown"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)[:50]}"
    
    return {
        "status": "healthy",
        "database": {
            "status": db_status,
            "url": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else "local",
            "type": "neon" if "neon.tech" in DATABASE_URL else ("postgresql" if DATABASE_URL.startswith("postgresql") else "sqlite")
        },
        "email": "configured" if EMAIL_CONFIGURED else "console_only",
        "optimizations": {
            "eager_loading": True,
            "indexes": "configured (run add_indexes.py for existing databases)",
            "connection_pooling": True
        }
    }

@app.get("/health/email")
def email_health_check():
    """Check email configuration and provider status"""
    status_info = {
        "status": "unknown",
        "providers": {},
        "active_provider": None,
        "mode": "console_output_only"
    }
    
    # Check Resend
    if RESEND_CONFIGURED:
        try:
            # Validate Resend API key is set (basic check)
            if not RESEND_API_KEY:
                status_info["providers"]["resend"] = {
                    "status": "misconfigured",
                    "error": "RESEND_API_KEY is empty"
                }
            else:
                # Basic validation - Resend API key should be non-empty
                status_info["providers"]["resend"] = {
                    "status": "configured",
                    "from_email": RESEND_FROM_EMAIL,
                    "note": "Ready to send emails via Resend API"
                }
                status_info["active_provider"] = "resend"
        except Exception as e:
            status_info["providers"]["resend"] = {
                "status": "error",
                "error": str(e)
            }
    else:
        status_info["providers"]["resend"] = {
            "status": "not_configured",
            "error": "Set RESEND_API_KEY in environment"
        }
    
    # Check SMTP (generic - works with Gmail, SendGrid, Mailgun, etc.)
    if SMTP_CONFIGURED:
        try:
            # Test SMTP connection without sending email
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
            
            status_info["providers"]["smtp"] = {
                "status": "healthy",
                "email": SMTP_FROM_EMAIL,
                "smtp_server": SMTP_SERVER,
                "smtp_port": SMTP_PORT
            }
            
            # If Resend is not active, SMTP becomes primary
            if not status_info["active_provider"]:
                status_info["active_provider"] = "smtp"
        
        except smtplib.SMTPAuthenticationError as e:
            status_info["providers"]["smtp"] = {
                "status": "authentication_failed",
                "email": SMTP_FROM_EMAIL,
                "error": "Invalid credentials",
                "action": "Check SMTP_USER and SMTP_PASS, ensure credentials are correct"
            }
        
        except (OSError, smtplib.SMTPException) as e:
            status_info["providers"]["smtp"] = {
                "status": "connection_failed",
                "error": str(e),
                "note": "Some cloud platforms (Render, Railway, etc.) may block outbound SMTP connections"
            }
        
        except Exception as e:
            status_info["providers"]["smtp"] = {
                "status": "error",
                "error": str(e)
            }
    else:
        status_info["providers"]["smtp"] = {
            "status": "not_configured",
            "error": "Set SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASS in environment"
        }
    
    # Determine overall status
    if status_info["active_provider"]:
        status_info["status"] = "healthy"
        status_info["message"] = f"Email service ready via {status_info['active_provider']}"
    elif RESEND_AVAILABLE or SMTP_CONFIGURED:
        status_info["status"] = "degraded"
        status_info["message"] = "Email service available but not fully configured"
    else:
        status_info["status"] = "not_configured"
        status_info["message"] = "No email provider configured"
    
    return status_info


# ========== Auth Endpoints ==========

# OTP Endpoints
@app.post("/send-otp")
def send_otp(request: SendOTPRequest, db: Session = Depends(get_db)):
    """Send OTP to email for login verification"""
    # Check if user exists
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please register first.")
    
    # Check if this is an admin (admins should use admin-login)
    if user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admins must use /admin-login endpoint. OTP is not required for admin login."
        )
    
    otp = generate_otp()
    
    # Store OTP with expiration (10 minutes) and type
    otp_storage[request.email] = {
        "otp": otp,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        "type": "login"
    }
    
    # Send email
    email_sent = send_otp_email(request.email, otp)
    
    # Return response with email status
    response = {
        "message": "OTP sent to your email" if EMAIL_CONFIGURED else "OTP generated (check console/logs for code)",
        "email": request.email,
        "email_configured": EMAIL_CONFIGURED,
        "otp_sent": email_sent
    }
    
    if not EMAIL_CONFIGURED:
        response["warning"] = "Email not configured. OTP is shown in server logs. Configure RESEND_API_KEY or GMAIL_USER/GMAIL_PASS."
    
    return response

@app.post("/verify-otp")
def verify_otp(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    """Legacy endpoint - Verify OTP for email-based login (passwordless) - DEPRECATED"""
    # This endpoint is kept for backward compatibility but is deprecated
    # New flow requires password + OTP for login
    if request.email not in otp_storage:
        raise HTTPException(status_code=400, detail="OTP not found or expired")
    
    stored_otp = otp_storage[request.email]
    
    # Check if OTP is expired
    if datetime.now(timezone.utc) > stored_otp["expires_at"]:
        del otp_storage[request.email]
        raise HTTPException(status_code=400, detail="OTP has expired")
    
    # Check if OTP matches
    if stored_otp["otp"] != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Check if this email belongs to an admin (admins cannot use OTP login)
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user and existing_user.is_admin:
        del otp_storage[request.email]
        raise HTTPException(
            status_code=403, 
            detail="Admins must use traditional email/password login at /admin-login"
        )
    
    # Mark email as verified in storage
    del otp_storage[request.email]
    
    # Get or create student user (without password for email-based login)
    if not existing_user:
        # Create new student user with email-verified access
        new_user = User(
            email=request.email,
            name=request.email.split('@')[0],  # Use email prefix as name
            password_hash=get_password_hash(f"otp-verified-{request.email}"),  # Dummy password
            is_admin=False,
            email_verified=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        user = new_user
    else:
        # Update existing student user - mark email as verified
        existing_user.email_verified = True
        db.commit()
        db.refresh(existing_user)
        user = existing_user
    
    # Generate token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user)
    }

@app.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user - Step 1: Validate and send OTP"""
    # Validate password match
    if request.password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    # Check if user already exists
    db_user = db.query(User).filter(User.email == request.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate password strength (optional - add more validation if needed)
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # Generate OTP
    otp = generate_otp()
    
    # Store registration data temporarily
    registration_storage[request.email] = {
        "name": request.name,
        "password": request.password,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10)
    }
    
    # Store OTP with expiration (10 minutes)
    otp_storage[request.email] = {
        "otp": otp,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        "type": "registration"
    }
    
    # Send email
    email_sent = send_otp_email(request.email, otp)
    
    # Return response
    response = {
        "message": "OTP sent to your email. Please verify to complete registration.",
        "email": request.email,
        "email_configured": EMAIL_CONFIGURED,
        "otp_sent": email_sent
    }
    
    if not EMAIL_CONFIGURED:
        response["warning"] = "Email not configured. OTP is shown in server logs. Configure RESEND_API_KEY or GMAIL_USER/GMAIL_PASS."
    
    return response

@app.post("/register/verify-otp", response_model=RegisterVerifyResponse)
def register_verify_otp(request: RegisterVerifyOTPRequest, db: Session = Depends(get_db)):
    """Register a new user - Step 2: Verify OTP and create user"""
    # Check if OTP exists
    if request.email not in otp_storage:
        raise HTTPException(status_code=400, detail="OTP not found or expired. Please register again.")
    
    stored_otp = otp_storage[request.email]
    
    # Check if this is a registration OTP
    if stored_otp.get("type") != "registration":
        raise HTTPException(status_code=400, detail="Invalid OTP type. Please use the registration endpoint.")
    
    # Check if OTP is expired
    if datetime.now(timezone.utc) > stored_otp["expires_at"]:
        del otp_storage[request.email]
        if request.email in registration_storage:
            del registration_storage[request.email]
        raise HTTPException(status_code=400, detail="OTP has expired. Please register again.")
    
    # Check if OTP matches
    if stored_otp["otp"] != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Check if registration data exists
    if request.email not in registration_storage:
        del otp_storage[request.email]
        raise HTTPException(status_code=400, detail="Registration data not found. Please register again.")
    
    reg_data = registration_storage[request.email]
    
    # Check if registration data is expired
    if datetime.now(timezone.utc) > reg_data["expires_at"]:
        del otp_storage[request.email]
        del registration_storage[request.email]
        raise HTTPException(status_code=400, detail="Registration session expired. Please register again.")
    
    # Check if user was created in the meantime
    db_user = db.query(User).filter(User.email == request.email).first()
    if db_user:
        del otp_storage[request.email]
        del registration_storage[request.email]
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(reg_data["password"])
    new_user = User(
        email=request.email,
        name=reg_data["name"],
        password_hash=hashed_password,
        is_admin=False,
        email_verified=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Clean up storage
    del otp_storage[request.email]
    del registration_storage[request.email]
    
    # Generate token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(new_user)
    }

@app.post("/create-admin", response_model=UserResponse)
def create_admin(user: UserCreate, db: Session = Depends(get_db)):
    """Create an admin user (one-time setup endpoint)"""
    # Check if user exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        # If user exists, make them admin
        if not db_user.is_admin:
            db_user.is_admin = True
            db_user.email_verified = True
            if user.password:
                db_user.password_hash = get_password_hash(user.password)
            db.commit()
            db.refresh(db_user)
            return db_user
        else:
            raise HTTPException(status_code=400, detail="User is already an admin")
    
    # Create new admin user
    hashed_password = get_password_hash(user.password)
    admin_user = User(
        email=user.email,
        name=user.name,
        password_hash=hashed_password,
        is_admin=True,
        email_verified=True  # Admins are pre-verified
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    return admin_user

@app.post("/login", response_model=Token)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login with email, password, and OTP"""
    # Find user
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password first
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if OTP exists
    if request.email not in otp_storage:
        raise HTTPException(status_code=400, detail="OTP not found or expired. Please request a new OTP.")
    
    stored_otp = otp_storage[request.email]
    
    # Check if this is a login OTP (not registration)
    if stored_otp.get("type") == "registration":
        raise HTTPException(status_code=400, detail="Invalid OTP type. Please use the login OTP.")
    
    # Check if OTP is expired
    if datetime.now(timezone.utc) > stored_otp["expires_at"]:
        del otp_storage[request.email]
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new OTP.")
    
    # Check if OTP matches
    if stored_otp["otp"] != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Clean up OTP storage
    del otp_storage[request.email]
    
    # Generate token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/admin-login", response_model=Token)
def admin_login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Admin login with email and password - admins MUST use this endpoint"""
    user = db.query(User).filter(User.email == form_data.username).first()
    
    # Check if user exists and has correct password
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is actually an admin
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for administrators only. Students should use OTP verification."
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current logged in user info"""
    return current_user

# ========== Profile Endpoints ==========
class ProfileUpdate(BaseModel):
    age: Optional[int] = None
    year: Optional[str] = None
    university: Optional[str] = None
    department: Optional[str] = None
    roll_no: Optional[str] = None
    student_id: Optional[str] = None


@app.put("/profile", response_model=UserResponse)
def update_profile(update: ProfileUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in update.dict(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@app.post("/profile/photo", response_model=UserResponse)
async def upload_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    allowed = {".jpg", ".jpeg", ".png", ".webp"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail="Invalid image type")
    save_path = UPLOAD_DIR / f"photo_{current_user.id}_{int(datetime.now(timezone.utc).timestamp())}{ext}"
    with save_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    current_user.photo_path = str(save_path)
    db.commit()
    db.refresh(current_user)
    return current_user


@app.post("/profile/id-card", response_model=UserResponse)
async def upload_id_card(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    allowed = {".jpg", ".jpeg", ".png", ".pdf"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail="Invalid file type")
    save_path = UPLOAD_DIR / f"id_{current_user.id}_{int(datetime.now(timezone.utc).timestamp())}{ext}"
    with save_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    current_user.id_card_path = str(save_path)
    current_user.id_verified = False
    current_user.verified_by = None
    current_user.verified_at = None
    db.commit()
    db.refresh(current_user)
    return current_user


@app.get("/admin/verification-requests", response_model=List[UserResponse])
def list_verification_requests(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    users = db.query(User).filter(User.id_card_path.isnot(None), User.id_verified == False).all()
    return users


class VerifyAction(BaseModel):
    approve: bool
    reason: Optional[str] = None


@app.post("/admin/verify-user/{user_id}", response_model=UserResponse)
def verify_user(user_id: int, action: VerifyAction, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.id_verified = bool(action.approve)
    user.verified_by = admin.id if action.approve else None
    user.verified_at = datetime.now(timezone.utc) if action.approve else None
    db.commit()
    db.refresh(user)
    return user

# ========== Admin Dashboard ==========
@app.get("/admin/dashboard", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Get dashboard statistics for admin"""
    stats = DashboardStats(
        total_papers=db.query(Paper).count(),
        pending_papers=db.query(Paper).filter(Paper.status == SubmissionStatus.PENDING).count(),
        approved_papers=db.query(Paper).filter(Paper.status == SubmissionStatus.APPROVED).count(),
        rejected_papers=db.query(Paper).filter(Paper.status == SubmissionStatus.REJECTED).count(),
        total_courses=db.query(Course).count(),
        total_users=db.query(User).count()
    )
    return stats

# ========== Course Endpoints ==========
@app.post("/courses", response_model=CourseResponse)
def create_course(course: CourseCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Admin: Create a new course"""
    # Check if code exists
    existing = db.query(Course).filter(Course.code == course.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Course code already exists")
    
    db_course = Course(**course.dict())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@app.get("/courses", response_model=List[CourseResponse])
def get_courses(db: Session = Depends(get_db)):
    """Get all courses"""
    return db.query(Course).order_by(Course.code).all()

@app.post("/courses/check-or-create")
def check_or_create_course(
    code: str = Query(...),
    name: str = Query(...),
    db: Session = Depends(get_db)
):
    """Check if course exists, return info about it"""
    existing_course = db.query(Course).filter(Course.code == code).first()
    
    if existing_course:
        return {
            "exists": True,
            "course": CourseResponse.from_orm(existing_course)
        }
    
    return {
        "exists": False,
        "message": "Course not found. Admin should create it or provide correct code."
    }

@app.post("/courses/admin/create-with-paper")
def create_course_for_paper(
    code: str = Query(...),
    name: str = Query(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Admin: Create a new course when paper submission references unknown course"""
    # Check if code already exists
    existing = db.query(Course).filter(Course.code == code).first()
    if existing:
        return {
            "created": False,
            "message": "Course already exists",
            "course": CourseResponse.from_orm(existing)
        }
    
    # Create new course
    new_course = Course(
        code=code,
        name=name,
        description=f"Created for paper submission"
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    
    return {
        "created": True,
        "message": "New course created successfully",
        "course": CourseResponse.from_orm(new_course)
    }

@app.get("/courses/{course_id}", response_model=CourseResponse)
def get_course(course_id: int, db: Session = Depends(get_db)):
    """Get a specific course"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@app.put("/courses/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: int,
    course_update: CourseUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Admin: Update course details"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if new code already exists
    if course_update.code and course_update.code != course.code:
        existing = db.query(Course).filter(Course.code == course_update.code).first()
        if existing:
            raise HTTPException(status_code=400, detail="Course code already exists")
    
    # Update fields
    update_data = course_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(course, field, value)
    
    course.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(course)
    return course

@app.delete("/courses/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Admin: Delete a course"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    db.delete(course)
    db.commit()
    return {"message": "Course deleted successfully"}

# ========== Paper Endpoints ==========
@app.post("/papers/upload")
async def upload_paper(
    file: UploadFile = File(...),
    course_id: int = Form(...),
    title: str = Form(...),
    paper_type: PaperType = Form(...),
    description: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    semester: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a paper for review"""
    # Validate course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Validate file type
    allowed_extensions = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # Save file
    file_path = UPLOAD_DIR / f"{datetime.now(timezone.utc).timestamp()}_{file.filename}"
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create paper record
    paper = Paper(
        course_id=course_id,
        uploaded_by=current_user.id,
        title=title,
        description=description,
        paper_type=paper_type,
        year=year,
        semester=semester,
        file_path=str(file_path),
        file_name=file.filename,
        file_size=file_path.stat().st_size,
        status=SubmissionStatus.PENDING
    )
    
    db.add(paper)
    db.commit()
    db.refresh(paper)
    
    return {"message": "Paper uploaded successfully and pending approval", "paper_id": paper.id}

@app.get("/papers", response_model=List[PaperResponse])
def get_papers(
    course_id: Optional[int] = None,
    paper_type: Optional[PaperType] = None,
    year: Optional[int] = None,
    semester: Optional[str] = None,
    status: Optional[SubmissionStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get papers with filters"""
    query = db.query(Paper)
    
    # Non-admins can only see approved papers
    if not current_user.is_admin:
        query = query.filter(Paper.status == SubmissionStatus.APPROVED)
    elif status:
        query = query.filter(Paper.status == status)
    
    # Apply filters
    if course_id:
        query = query.filter(Paper.course_id == course_id)
    if paper_type:
        query = query.filter(Paper.paper_type == paper_type)
    if year:
        query = query.filter(Paper.year == year)
    if semester:
        query = query.filter(Paper.semester == semester)
    
    # Optimize: Use eager loading to avoid N+1 queries
    papers = query.options(
        joinedload(Paper.course),
        joinedload(Paper.uploader)
    ).order_by(Paper.uploaded_at.desc()).all()
    
    return [format_paper_response(paper, current_user.is_admin) for paper in papers]

@app.get("/papers/pending", response_model=List[PaperResponse])
def get_pending_papers(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Admin: View pending submissions"""
    # Optimize: Use eager loading to avoid N+1 queries
    papers = db.query(Paper).options(
        joinedload(Paper.course),
        joinedload(Paper.uploader)
    ).filter(Paper.status == SubmissionStatus.PENDING).order_by(Paper.uploaded_at.desc()).all()
    return [format_paper_response(paper, True) for paper in papers]

@app.get("/papers/public/all", response_model=List[PaperResponse])
def get_public_papers(
    course_id: Optional[int] = None,
    paper_type: Optional[PaperType] = None,
    year: Optional[int] = None,
    semester: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all approved papers (public access, no authentication required)"""
    query = db.query(Paper).filter(Paper.status == SubmissionStatus.APPROVED)
    
    # Apply filters
    if course_id:
        query = query.filter(Paper.course_id == course_id)
    if paper_type:
        query = query.filter(Paper.paper_type == paper_type)
    if year:
        query = query.filter(Paper.year == year)
    if semester:
        query = query.filter(Paper.semester == semester)
    
    # Optimize: Use eager loading to avoid N+1 queries
    papers = query.options(
        joinedload(Paper.course),
        joinedload(Paper.uploader)
    ).order_by(Paper.uploaded_at.desc()).all()
    return [format_paper_response(paper, False) for paper in papers]

@app.get("/papers/{paper_id}", response_model=PaperResponse)
def get_paper(paper_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get a specific paper"""
    # Optimize: Use eager loading to avoid N+1 queries
    paper = db.query(Paper).options(
        joinedload(Paper.course),
        joinedload(Paper.uploader)
    ).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Check access
    if paper.status != SubmissionStatus.APPROVED and not current_user.is_admin and paper.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return format_paper_response(paper, current_user.is_admin)

@app.patch("/papers/{paper_id}/review")
def review_paper(
    paper_id: int,
    review: PaperReview,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Admin: Approve or reject papers"""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if review.status == SubmissionStatus.REJECTED and not review.rejection_reason:
        raise HTTPException(status_code=400, detail="Rejection reason required")
    
    paper.status = review.status
    paper.reviewed_by = admin.id
    paper.reviewed_at = datetime.now(timezone.utc)
    paper.rejection_reason = review.rejection_reason
    
    db.commit()
    
    return {"message": f"Paper {review.status.value} successfully"}

@app.put("/papers/{paper_id}/edit")
def edit_paper(
    paper_id: int,
    course_id: Optional[str] = Form(None),
    paper_type: Optional[str] = Form(None),
    year: Optional[str] = Form(None),
    semester: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Admin: Edit paper details - accepts both course code and course ID"""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Update course if provided
    if course_id:
        # Try to parse as integer (course ID) first
        try:
            course_id_int = int(course_id)
            course = db.query(Course).filter(Course.id == course_id_int).first()
        except ValueError:
            # If not an integer, treat as course code
            course = db.query(Course).filter(Course.code == course_id).first()
        
        if not course:
            raise HTTPException(status_code=404, detail=f"Course '{course_id}' not found")
        paper.course_id = course.id
    
    # Update paper type if provided
    if paper_type:
        try:
            paper.paper_type = PaperType(paper_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid paper type: {paper_type}")
    
    # Update year if provided
    if year:
        try:
            paper.year = int(year)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid year: {year}")
    
    # Update semester if provided
    if semester:
        paper.semester = semester
    
    paper.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(paper)
    
    return {"message": "Paper updated successfully", "paper": format_paper_response(paper, True)}

@app.delete("/papers/{paper_id}")
def delete_paper(paper_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    """Admin: Delete a paper"""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Delete file
    try:
        os.remove(paper.file_path)
    except OSError as e:
        print(f"Warning: Could not delete file {paper.file_path}: {e}")
    
    db.delete(paper)
    db.commit()
    return {"message": "Paper deleted successfully"}

@app.get("/papers/{paper_id}/preview")
def preview_paper(paper_id: int, db: Session = Depends(get_db)):
    """Get paper preview metadata - Public access for approved papers"""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Only approved papers can be previewed without authentication
    if paper.status != SubmissionStatus.APPROVED:
        raise HTTPException(status_code=403, detail="Paper not approved yet")
    
    # Check if file exists
    if not os.path.exists(paper.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
    
    # Get MIME type
    mime_type = get_mime_type(paper.file_name)
    
    return {
        "paper_id": paper.id,
        "file_name": paper.file_name,
        "file_path": paper.file_path,
        "file_size": paper.file_size,
        "mime_type": mime_type,
        "can_preview": can_preview_file(paper.file_name)
    }

@app.get("/papers/{paper_id}/download")
def download_paper(paper_id: int, db: Session = Depends(get_db)):
    """Download paper file - Public access for approved papers"""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Only approved papers can be downloaded without authentication
    if paper.status != SubmissionStatus.APPROVED:
        raise HTTPException(status_code=403, detail="Paper not approved yet")
    
    # Check if file exists
    if not os.path.exists(paper.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
    
    from fastapi.responses import FileResponse
    return FileResponse(paper.file_path, filename=paper.file_name)

# ========== Helper Functions ==========
def format_paper_response(paper: Paper, include_private_info: bool = False):
    """Format paper for response"""
    paper_dict = {
        "id": paper.id,
        "course_id": paper.course_id,
        "course_code": paper.course.code if paper.course else None,
        "course_name": paper.course.name if paper.course else None,
        "uploader_name": paper.uploader.name if paper.uploader else "Unknown",
        "uploader_email": paper.uploader.email if (paper.uploader and include_private_info) else None,
        "title": paper.title,
        "description": paper.description,
        "paper_type": paper.paper_type,
        "year": paper.year,
        "semester": paper.semester,
        "file_name": paper.file_name,
        "file_size": paper.file_size,
        "file_path": paper.file_path,
        "status": paper.status,
        "uploaded_at": paper.uploaded_at,
        "reviewed_at": paper.reviewed_at,
        "rejection_reason": paper.rejection_reason if include_private_info else None
    }
    return PaperResponse(**paper_dict)

def get_mime_type(filename: str) -> str:
    """Get MIME type for a file"""
    mime_types = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.txt': 'text/plain',
        '.zip': 'application/zip',
    }
    
    ext = Path(filename).suffix.lower()
    return mime_types.get(ext, 'application/octet-stream')

def can_preview_file(filename: str) -> bool:
    """Check if file can be previewed in browser"""
    previewable_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.txt'}
    ext = Path(filename).suffix.lower()
    return ext in previewable_extensions

# ========== Health Check ==========
@app.get("/")
def root():
    return {"message": "Paper Portal API v2.0", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
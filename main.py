# main.py
from __future__ import annotations  # Enable forward references
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Query, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Text, Enum as SQLEnum, DateTime, text, Index, or_, LargeBinary, JSON, inspect
from sqlalchemy.orm import declarative_base, Session, sessionmaker, relationship, joinedload
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from enum import Enum
import shutil
import os
from pathlib import Path
from passlib.context import CryptContext
from jose import JWTError, jwt
from dotenv import load_dotenv
import httpx
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio

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
EMAIL_SERVICE_URL = os.getenv("EMAIL_SERVICE_URL", "").strip()  # Optional external mailer (e.g., Nodemailer service)
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "re_W7dx377D_4VR7e4gGzoAgs8uFUhCpcPGj").strip()
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
EMAIL_CONFIGURED = bool(EMAIL_SERVICE_URL) or RESEND_CONFIGURED or SMTP_CONFIGURED

if not EMAIL_CONFIGURED:
    print("\n⚠️  WARNING: Email not configured!")
    print("   Option 1 (Recommended): Set RESEND_API_KEY and RESEND_FROM_EMAIL")
    print("   Option 2: Set SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASS")
    print("   OTP emails will be printed to console only for now")
    print("\n")
elif EMAIL_SERVICE_URL:
    print("\n✓ External Email Service configured")
    print(f"   Service URL: {EMAIL_SERVICE_URL}")
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


def ensure_column_exists(
    engine,
    table_name: str,
    column_name: str,
    column_type_by_dialect: dict[str, str],
) -> None:
    """
    Ensure a column exists on the specified table. Adds the column if missing.
    This provides a lightweight alternative to migrations for critical fixes.
    """
    try:
        inspector = inspect(engine)
        existing_columns = {col["name"] for col in inspector.get_columns(table_name)}
    except Exception as exc:
        print(f"⚠️  Could not inspect table '{table_name}': {exc}")
        return

    if column_name in existing_columns:
        return

    dialect = engine.dialect.name
    column_sql = column_type_by_dialect.get(dialect, column_type_by_dialect.get("default"))

    if not column_sql:
        print(f"⚠️  No column definition provided for dialect '{dialect}' on table '{table_name}'")
        return

    alter_statement = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}"
    try:
        with engine.begin() as conn:
            conn.execute(text(alter_statement))
        print(f"✅ Added missing column '{column_name}' to '{table_name}' ({dialect})")
    except Exception as exc:
        print(f"⚠️  Failed to add column '{column_name}' to '{table_name}': {exc}")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
optional_oauth2_scheme = HTTPBearer(auto_error=False)

# Create uploads directory
UPLOAD_DIR_STR = os.getenv("UPLOAD_DIR", "uploads")
UPLOAD_DIR = Path(UPLOAD_DIR_STR)
UPLOAD_DIR.mkdir(exist_ok=True)

# In-memory password reset data storage (use Redis for production)
password_reset_storage = {}

# Background task: Clean up expired password reset data
def cleanup_expired_data():
    """Clean up expired password reset data"""
    current_time = datetime.now(timezone.utc)
    
    # Clean expired password reset data
    expired_reset_emails = [
        email for email, data in password_reset_storage.items()
        if current_time > data.get("expires_at", datetime.min.replace(tzinfo=timezone.utc))
    ]
    for email in expired_reset_emails:
        del password_reset_storage[email]
    
    if expired_reset_emails:
        print(f"🧹 Cleaned up {len(expired_reset_emails)} expired password reset sessions")

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
    photo_path = Column(String(500), nullable=True)  # Kept for backward compatibility
    id_card_path = Column(String(500), nullable=True)  # Kept for backward compatibility
    photo_data = Column(LargeBinary, nullable=True)  # Store file content in database
    id_card_data = Column(LargeBinary, nullable=True)  # Store file content in database
    id_verified = Column(Boolean, default=False)
    verified_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    email_verified = Column(Boolean, default=False)
    admin_feedback = Column(JSON, nullable=True)  # JSON field for admin feedback/rejection messages
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
    # New optional department/program field (e.g., BTECH, BBA, CCCT)
    department = Column(String(255), nullable=True, index=True)
    
    file_path = Column(String(500), nullable=True)  # Kept for backward compatibility, now nullable
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer)
    file_data = Column(LargeBinary, nullable=True)  # Store file content in database
    
    status = Column(SQLEnum(SubmissionStatus), default=SubmissionStatus.PENDING, index=True)
    reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at = Column(DateTime)
    rejection_reason = Column(Text)  # Kept for backward compatibility
    admin_feedback = Column(JSON, nullable=True)  # JSON field for admin feedback/rejection messages
    
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

# Create tables (and backfill critical columns if they were added after deployment)
Base.metadata.create_all(bind=engine)

JSON_COLUMN_SQL = {
    "postgresql": "JSONB",
    "sqlite": "TEXT",
    "mysql": "JSON",
    "mssql": "NVARCHAR(MAX)",
    "default": "JSON",
}

ensure_column_exists(engine, "users", "admin_feedback", JSON_COLUMN_SQL)
ensure_column_exists(engine, "papers", "admin_feedback", JSON_COLUMN_SQL)

# Ensure new department column exists on papers table
DEPARTMENT_COLUMN_SQL = {
    "postgresql": "VARCHAR(255)",
    "sqlite": "TEXT",
    "mysql": "VARCHAR(255)",
    "mssql": "NVARCHAR(255)",
    "default": "VARCHAR(255)",
}
ensure_column_exists(engine, "papers", "department", DEPARTMENT_COLUMN_SQL)

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


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Helper function for normalizing file paths (needed by UserResponse)
def normalize_file_path(file_path: Optional[str]) -> Optional[str]:
    """Normalize file path to just filename for frontend consumption"""
    if not file_path:
        return None
    
    # If it's an absolute path, extract just the filename
    if os.path.isabs(file_path):
        file_path = Path(file_path).name
    # Remove 'uploads/' prefix if present
    if file_path.startswith('uploads/') or file_path.startswith('uploads\\'):
        file_path = file_path.replace('uploads/', '').replace('uploads\\', '')
    # Ensure it's just the filename (relative to uploads/)
    return Path(file_path).name

def find_file_in_uploads(stored_path: str) -> Optional[Path]:
    """
    Find file in uploads directory based on stored path.
    Returns the file path if found, None otherwise.
    Handles various path formats from different database migrations.
    """
    if not stored_path:
        return None
    
    # Extract filename from stored path
    if os.path.isabs(stored_path):
        filename = Path(stored_path).name
    else:
        if stored_path.startswith('uploads/') or stored_path.startswith('uploads\\'):
            filename = stored_path.replace('uploads/', '').replace('uploads\\', '')
            filename = Path(filename).name
        else:
            filename = Path(stored_path).name
    
    # Try multiple possible file locations
    possible_paths = []
    
    # First, try the stored_path exactly as it is (most reliable for new uploads)
    if not os.path.isabs(stored_path):
        if stored_path.startswith('uploads/') or stored_path.startswith('uploads\\'):
            clean_stored = stored_path.replace('uploads/', '').replace('uploads\\', '')
            possible_paths.append(UPLOAD_DIR / clean_stored)
        else:
            possible_paths.append(UPLOAD_DIR / stored_path)
    
    # Second, try the extracted filename
    if filename:
        possible_paths.append(UPLOAD_DIR / filename)
    
    # Try each possible path
    for path in possible_paths:
        try:
            resolved_path = path.resolve()
            uploads_dir = UPLOAD_DIR.resolve()
            # Security: Ensure file is within uploads directory
            if str(resolved_path).startswith(str(uploads_dir)) and resolved_path.exists() and resolved_path.is_file():
                return resolved_path
        except Exception:
            continue
    
    return None

class UserResponse(BaseModel):
    admin_feedback: Optional[dict] = None  # JSON field for admin feedback/rejection messages
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
    
    @field_validator('photo_path', 'id_card_path', mode='after')
    @classmethod
    def normalize_paths(cls, v: Optional[str]) -> Optional[str]:
        """Normalize file paths to just filename"""
        return normalize_file_path(v) if v else None

class RegisterVerifyResponse(BaseModel):
    access_token: str
    token_type: str
    user: "UserResponse"

# Password Reset Schemas
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str
    confirm_password: str

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
    department: Optional[str] = None
    file_name: str
    file_path: str
    file_size: Optional[int]
    status: SubmissionStatus
    uploaded_at: datetime
    reviewed_at: Optional[datetime]
    rejection_reason: Optional[str]
    admin_feedback: Optional[dict] = None

class PaperReview(BaseModel):
    status: SubmissionStatus
    rejection_reason: Optional[str] = None  # Kept for backward compatibility
    admin_feedback: Optional[dict] = None  # JSON field for admin feedback/rejection messages

class PaperUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    paper_type: Optional[PaperType] = None
    course_id: Optional[int] = None
    year: Optional[int] = None
    semester: Optional[str] = None
    department: Optional[str] = None

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
    Send OTP to email using Resend (primary) or SMTP (fallback).
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
            print(f"    Configure RESEND_API_KEY or SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASS in .env\n")
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
        text_body = f"""Paper Portal - Verification Code

Your verification code is: {otp}

This code expires in 10 minutes. If you didn't request this code, you can ignore this email.
"""
        
        # 0) Preferred: External Nodemailer service (if configured)
        if EMAIL_SERVICE_URL:
            try:
                # Use SMTP_FROM_EMAIL if available, otherwise RESEND_FROM_EMAIL
                from_email = SMTP_FROM_EMAIL if SMTP_FROM_EMAIL else RESEND_FROM_EMAIL
                payload = {
                    "to": email,
                    "from": from_email,
                    "subject": "Your Paper Portal Verification Code",
                    "html": html_body,
                    "text": text_body
                }
                print(f"📧 Attempting to send via External Email Service: {EMAIL_SERVICE_URL}")
                with httpx.Client(timeout=10) as client:
                    r = client.post(f"{EMAIL_SERVICE_URL.rstrip('/')}/send-email", json=payload)
                    if r.status_code >= 200 and r.status_code < 300:
                        print(f"✓ Email sent successfully via External Mailer to {email}")
                        return True
                    else:
                        print(f"❌ External Mailer error: {r.status_code} - {r.text[:200]}")
                        print(f"   Falling back to Resend/SMTP...\n")
            except httpx.TimeoutException:
                print(f"❌ External Mailer timeout: Service at {EMAIL_SERVICE_URL} did not respond")
                print(f"   Check if email service is running and accessible")
                print(f"   Falling back to Resend/SMTP...\n")
            except httpx.ConnectError:
                print(f"❌ External Mailer connection failed: Cannot reach {EMAIL_SERVICE_URL}")
                print(f"   Check if email service is running and EMAIL_SERVICE_URL is correct")
                print(f"   Falling back to Resend/SMTP...\n")
            except Exception as e:
                print(f"❌ External Mailer request failed: {type(e).__name__}: {e}")
                print(f"   Falling back to Resend/SMTP...\n")
        else:
            print(f"ℹ️  EMAIL_SERVICE_URL not configured. Skipping external email service.")
            print(f"   Set EMAIL_SERVICE_URL=http://localhost:4000 to use Node.js email service\n")

        # 1) Try Resend API
        if RESEND_CONFIGURED:
            try:
                # Send email via Resend API
                from_header = RESEND_FROM_EMAIL if "<" in RESEND_FROM_EMAIL else f"Paper Portal <{RESEND_FROM_EMAIL}>"
                email_response = resend.Emails.send({
                    "from": from_header,
                    "to": [email],
                    "subject": "Your Paper Portal Verification Code",
                    "html": html_body,
                    "text": text_body
                })
                
                # Check if response is valid (Resend returns dict with 'id' or 'error')
                if email_response and isinstance(email_response, dict):
                    if 'id' in email_response:
                        print(f"✓ Email sent successfully via Resend to {email} (ID: {email_response.get('id', 'N/A')})")
                        return True
                    elif 'error' in email_response:
                        error_msg = email_response.get('error', {}).get('message', 'Unknown error')
                        print(f"❌ Resend API error: {error_msg}")
                        print(f"   Falling back to SMTP...\n")
                    else:
                        # Response received but format unexpected
                        print(f"✓ Email sent via Resend to {email}")
                        return True
                else:
                    # Response is None or unexpected format - assume success
                    print(f"✓ Email sent via Resend to {email}")
                    return True
                    
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Resend error: {type(e).__name__}: {error_msg}")
                
                # Check for specific error types and provide helpful messages
                if "403" in error_msg or "Forbidden" in error_msg:
                    print(f"   Reason: API key may not have permission or is invalid")
                    print(f"   Check: https://resend.com/api-keys")
                    print(f"   Note: onboarding@resend.dev only works for your account email")
                elif "422" in error_msg or "validation" in error_msg.lower():
                    print(f"   Reason: Invalid request format or email address")
                elif "domain" in error_msg.lower() or "not verified" in error_msg.lower():
                    print(f"   Reason: Domain not verified. onboarding@resend.dev only works for your account email")
                    print(f"   Solution: Use Resend SMTP (configure SMTP_SERVER=smtp.resend.com) or verify a domain")
                
                print(f"   Falling back to SMTP...\n")
        
        # 2) Fallback to SMTP (generic or Resend SMTP)
        # Prefer configured SMTP first; else, if we have a RESEND_API_KEY, attempt Resend SMTP smart fallback
        use_smart_resend_smtp = False
        smtp_server = SMTP_SERVER
        smtp_port = SMTP_PORT
        smtp_user = SMTP_USER
        smtp_pass = SMTP_PASS
        if not SMTP_CONFIGURED and RESEND_API_KEY:
            # Smart fallback to Resend SMTP
            use_smart_resend_smtp = True
            smtp_server = "smtp.resend.com"
            smtp_port = 587
            smtp_user = "resend"
            smtp_pass = RESEND_API_KEY

        if SMTP_CONFIGURED or use_smart_resend_smtp:
            try:
                message = MIMEMultipart()
                # Preserve display name if provided, else use configured SMTP_FROM_EMAIL
                from_header = RESEND_FROM_EMAIL if "<" in RESEND_FROM_EMAIL else (SMTP_FROM_EMAIL or RESEND_FROM_EMAIL)
                message["From"] = from_header
                message["To"] = email
                message["Subject"] = "Your Paper Portal Verification Code"
                message.attach(MIMEText(html_body, "html"))
                # Add text alternative for better deliverability
                message.attach(MIMEText(text_body, "plain"))
                
                # Send via SMTP with timeout
                with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
                    server.starttls()
                    if smtp_user and smtp_pass:
                        server.login(smtp_user, smtp_pass)
                    server.send_message(message)
                
                print(f"✓ Email sent successfully via SMTP ({smtp_server}) to {email}")
                return True
                
            except smtplib.SMTPAuthenticationError as e:
                print(f"❌ SMTP authentication failed: {e}")
                if use_smart_resend_smtp:
                    print(f"   Attempted Resend SMTP with provided API key. Ensure your sender domain is verified in Resend.")
                    print(f"   Verify domain: https://resend.com/domains")
                else:
                    print(f"   Reason: Check SMTP_USER and SMTP_PASS credentials")
                    print(f"   Note: Use App Password (not regular password)")
                    print(f"   Check: https://myaccount.google.com/apppasswords")
                print()
                return True
                
            except (smtplib.SMTPException, OSError) as e:
                print(f"❌ SMTP error: {type(e).__name__}: {e}")
                print(f"   Note: Some platforms may have SMTP network restrictions")
                print(f"   Recommendation: Use Resend API or verify your domain for any-recipient sending")
                print(f"   Get API key: https://resend.com\n")
                return True
            
            except Exception as e:
                print(f"❌ Unexpected error sending email: {type(e).__name__}: {e}\n")
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

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_oauth2_scheme), 
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if token is provided, otherwise return None"""
    if not credentials:
        return None
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        token_data = TokenData(email=email)
    except JWTError:
        return None
    
    user = db.query(User).filter(User.email == token_data.email).first()
    return user

# ========== FastAPI App ==========
app = FastAPI(title="Paper Portal API", version="2.0.0")

# Keep-alive background task to prevent auto-shutdown on free tier platforms
async def keep_alive_task():
    """Background task to keep server alive - maintains active event loop"""
    while True:
        try:
            # Sleep for 5 minutes (300 seconds)
            # Render free tier spins down after 15 minutes of inactivity
            # This keeps the process active, preventing idle detection
            await asyncio.sleep(300)
            # Log keep-alive heartbeat (this keeps the process active)
            print("💓 Keep-alive heartbeat - service is active")
        except asyncio.CancelledError:
            break
        except Exception as e:
            # Log error but continue the keep-alive loop
            print(f"Keep-alive task error (non-critical): {e}")
            await asyncio.sleep(300)

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
    
    # Start keep-alive task to prevent auto-shutdown
    asyncio.create_task(keep_alive_task())
    print("✓ Keep-alive task started to prevent automatic shutdown\n")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API endpoint to serve uploaded files (works better on cloud platforms)
@app.get("/uploads/{filename:path}")
async def serve_uploaded_file(filename: str, db: Session = Depends(get_db)):
    """
    Serve uploaded files (photos, ID cards, papers)
    First checks database, then falls back to filesystem for backward compatibility
    """
    from fastapi.responses import Response
    
    # Try to find file in database first
    # Check if it's a user photo or ID card
    if filename.startswith("photo_"):
        # Extract user ID from filename (format: photo_{user_id}_{timestamp}.ext)
        try:
            parts = filename.replace("photo_", "").split("_")
            if parts:
                user_id = int(parts[0])
                user = db.query(User).filter(User.id == user_id).first()
                if user and user.photo_data:
                    ext = Path(filename).suffix.lower()
                    media_type = get_mime_type_from_ext(ext)
                    return Response(
                        content=user.photo_data,
                        media_type=media_type,
                        headers={"Content-Disposition": f'inline; filename="{Path(filename).name}"'}
                    )
        except (ValueError, IndexError):
            pass
    
    if filename.startswith("id_"):
        # Extract user ID from filename (format: id_{user_id}_{timestamp}.ext)
        try:
            parts = filename.replace("id_", "").split("_")
            if parts:
                user_id = int(parts[0])
                user = db.query(User).filter(User.id == user_id).first()
                if user and user.id_card_data:
                    ext = Path(filename).suffix.lower()
                    media_type = get_mime_type_from_ext(ext)
                    return Response(
                        content=user.id_card_data,
                        media_type=media_type,
                        headers={"Content-Disposition": f'inline; filename="{Path(filename).name}"'}
                    )
        except (ValueError, IndexError):
            pass
    
    # Check papers - look for files with timestamp prefix
    # Try exact match first
    papers = db.query(Paper).filter(Paper.file_path == filename).all()
    
    # If no exact match, try URL-decoded version
    if not papers:
        from urllib.parse import unquote
        decoded_filename = unquote(filename)
        if decoded_filename != filename:
            papers = db.query(Paper).filter(Paper.file_path == decoded_filename).all()
    
    # If still no match, try matching by extracting filename from stored path
    # (handles cases where file_path might have been normalized differently)
    if not papers:
        # Try to find papers where the filename matches the end of file_path
        all_papers = db.query(Paper).filter(Paper.file_data.isnot(None)).all()
        for paper in all_papers:
            if paper.file_path:
                # Check if the requested filename matches the stored file_path
                if paper.file_path == filename or paper.file_path.endswith(filename):
                    papers = [paper]
                    break
                # Also check if the original filename matches
                if paper.file_name == filename or paper.file_name == Path(filename).name:
                    papers = [paper]
                    break
    
    if papers:
        paper = papers[0]  # Get first match
        if paper.file_data:
            media_type = get_mime_type(paper.file_name)
            return Response(
                content=paper.file_data,
                media_type=media_type,
                headers={"Content-Disposition": f'inline; filename="{paper.file_name}"'}
            )
    
    # Fallback to filesystem for backward compatibility (old files)
    from fastapi.responses import FileResponse
    file_path = find_file_in_uploads(filename)
    
    if not file_path or not file_path.exists():
        direct_path = UPLOAD_DIR / filename
        try:
            resolved_path = direct_path.resolve()
            uploads_dir = UPLOAD_DIR.resolve()
            if str(resolved_path).startswith(str(uploads_dir)) and resolved_path.exists() and resolved_path.is_file():
                file_path = resolved_path
        except Exception:
            pass
    
    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"File not found: '{filename}'"
        )
    
    # Security check
    try:
        file_path = file_path.resolve()
        uploads_dir = UPLOAD_DIR.resolve()
        if not str(file_path).startswith(str(uploads_dir)):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid file path")
    
    ext = Path(filename).suffix.lower()
    media_type = get_mime_type_from_ext(ext)
    
    return FileResponse(
        str(file_path),
        media_type=media_type,
        filename=Path(filename).name
    )

def get_mime_type_from_ext(ext: str) -> str:
    """Get MIME type from file extension"""
    mime_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.pdf': 'application/pdf',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    }
    return mime_map.get(ext.lower(), 'application/octet-stream')

# Mount uploads directory as static files for direct serving (fallback for local development)
# This allows frontend to access files directly via /uploads/{filename}
# Note: On cloud platforms, the API endpoint above is preferred
try:
    app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
except Exception as e:
    print(f"Warning: Could not mount uploads directory: {e}")


# ========== Health & Status Endpoints ==========

@app.get("/health")
def health_check():
    """Check API health and configuration status - Also used for keep-alive"""
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
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

@app.get("/wake")
def wake_up():
    """Wake-up endpoint - Simple endpoint to wake up the service from sleep"""
    return {
        "status": "awake",
        "message": "Service is active",
        "timestamp": datetime.now(timezone.utc).isoformat()
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


@app.post("/register", response_model=RegisterVerifyResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user - Create account directly"""
    # Validate email domain - must be @jklu.edu.in
    if not request.email.endswith("@jklu.edu.in"):
        raise HTTPException(
            status_code=400, 
            detail="Only @jklu.edu.in email addresses are allowed for registration"
        )
    
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
    
    # Create new user directly
    hashed_password = get_password_hash(request.password)
    new_user = User(
        email=request.email,
        name=request.name,
        password_hash=hashed_password,
        is_admin=False,
        email_verified=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
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
    """Login with email and password"""
    # Validate email domain - must be @jklu.edu.in
    if not request.email.endswith("@jklu.edu.in"):
        raise HTTPException(
            status_code=400, 
            detail="Only @jklu.edu.in email addresses are allowed for login"
        )
    
    # Find user
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
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
            detail="This endpoint is for administrators only. Students should use the regular login endpoint."
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

# ========== Forgot Password Endpoints ==========
@app.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Send OTP to email for password reset"""
    try:
        # Check if user exists
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            # Don't reveal if user exists or not for security
            return {
                "message": "If the email exists, a password reset OTP has been sent.",
                "email": request.email,
                "success": True
            }
        
        # Generate OTP
        otp = generate_otp()
        
        # Store OTP with expiration (10 minutes) and type
        password_reset_storage[request.email] = {
            "otp": otp,
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
            "type": "password_reset"
        }
        
        # Send email
        email_sent = send_otp_email(request.email, otp)
        
        return {
            "message": "If the email exists, a password reset OTP has been sent.",
            "email": request.email,
            "email_configured": EMAIL_CONFIGURED,
            "otp_sent": email_sent,
            "success": True
        }
    except Exception as e:
        # Log error but don't reveal details to user
        print(f"Error in forgot_password: {e}")
        # Still return success message for security
        return {
            "message": "If the email exists, a password reset OTP has been sent.",
            "email": request.email,
            "success": True
        }

@app.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using OTP"""
    # Validate password match
    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    # Validate password strength
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # Check if OTP exists
    if request.email not in password_reset_storage:
        raise HTTPException(status_code=400, detail="OTP not found or expired. Please request a new password reset.")
    
    stored_data = password_reset_storage[request.email]
    
    # Check if this is a password reset OTP
    if stored_data.get("type") != "password_reset":
        raise HTTPException(status_code=400, detail="Invalid OTP type. Please use the password reset OTP.")
    
    # Check if OTP is expired
    if datetime.now(timezone.utc) > stored_data["expires_at"]:
        del password_reset_storage[request.email]
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new password reset.")
    
    # Check if OTP matches
    if stored_data["otp"] != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Find user
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        del password_reset_storage[request.email]
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update password
    user.password_hash = get_password_hash(request.new_password)
    db.commit()
    
    # Clean up storage
    del password_reset_storage[request.email]
    
    return {
        "message": "Password reset successfully. You can now login with your new password."
    }

# ========== Profile Endpoints ==========
class ProfileUpdate(BaseModel):
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
    
    # Read file content into memory
    file_content = await file.read()
    
    # Store file data in database
    current_user.id_card_data = file_content
    current_user.id_card_path = f"id_{current_user.id}_{int(datetime.now(timezone.utc).timestamp())}{ext}"  # Keep for reference
    current_user.id_verified = False
    current_user.verified_by = None
    current_user.verified_at = None
    db.commit()
    db.refresh(current_user)
    return current_user


@app.get("/admin/verification-requests", response_model=List[UserResponse])
def list_verification_requests(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    # Check for users with ID cards (either in database or filesystem)
    users = db.query(User).filter(
        or_(
            User.id_card_data.isnot(None),
            User.id_card_path.isnot(None)
        ),
        User.id_verified == False
    ).all()
    return users


class VerifyAction(BaseModel):
    approve: bool
    reason: Optional[str] = None
    admin_feedback: Optional[dict] = None  # JSON field for admin feedback/rejection messages


@app.post("/admin/verify-user/{user_id}", response_model=UserResponse)
def verify_user(user_id: int, action: VerifyAction, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.id_verified = bool(action.approve)
    user.verified_by = admin.id if action.approve else None
    user.verified_at = datetime.now(timezone.utc) if action.approve else None
    
    # Store admin feedback in JSON format when rejecting
    if not action.approve:
        if action.admin_feedback:
            user.admin_feedback = action.admin_feedback
        elif action.reason:
            # Convert old reason to new JSON format for consistency
            user.admin_feedback = {
                "message": action.reason,
                "rejected_at": datetime.now(timezone.utc).isoformat(),
                "rejected_by": admin.id
            }
    else:
        # Clear admin feedback if approved
        user.admin_feedback = None
    
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
    course_id: Optional[int] = Form(None),
    course_code: Optional[str] = Form(None),
    course_name: Optional[str] = Form(None),
    title: str = Form(...),
    paper_type: PaperType = Form(...),
    description: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    semester: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a paper for review"""
    # Handle course selection - either course_id or course_code must be provided
    if not course_id and not course_code:
        raise HTTPException(status_code=400, detail="Either course_id or course_code must be provided")
    
    course = None
    if course_id:
        # Use provided course_id
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
    elif course_code:
        # Validate course code
        course_code = course_code.strip()
        if not course_code:
            raise HTTPException(status_code=400, detail="Course code cannot be empty")
        
        # Check if course exists by code
        course = db.query(Course).filter(Course.code == course_code).first()
        if not course:
            normalized_name = (course_name or course_code).strip()
            if not normalized_name:
                normalized_name = course_code
            # Create new course if it doesn't exist
            course = Course(
                code=course_code,
                name=normalized_name,
                description=f"Auto-created during paper upload"
            )
            db.add(course)
            db.commit()
            db.refresh(course)
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required")
    
    # Validate file type
    allowed_extensions = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # Read file content into memory
    file_content = await file.read()
    file_size = len(file_content)
    
    # Generate filename with timestamp prefix for reference
    timestamp = datetime.now(timezone.utc).timestamp()
    stored_file_path = f"{timestamp}_{file.filename}"
    
    # Create paper record with file data stored in database
    paper = Paper(
        course_id=course.id,
        uploaded_by=current_user.id,
        title=title,
        description=description,
        paper_type=paper_type,
        year=year,
        semester=semester,
        department=department,
        file_path=stored_file_path,  # Keep for reference/backward compatibility
        file_name=file.filename,
        file_size=file_size,
        file_data=file_content,  # Store file content in database
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
    department: Optional[str] = None,
    status: Optional[SubmissionStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get papers with filters"""
    query = db.query(Paper)
    
    # Non-admins (logged-in students) can see:
    # - All approved papers (from any user)
    # - Their own papers (pending, approved, or rejected)
    if not current_user.is_admin:
        query = query.filter(
            or_(
                Paper.status == SubmissionStatus.APPROVED,  # All approved papers
                Paper.uploaded_by == current_user.id  # Or their own papers (any status)
            )
        )
    elif status:
        # Admins can filter by status
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
    if department:
        query = query.filter(Paper.department == department)
    
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
    department: Optional[str] = None,
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
    if department:
        query = query.filter(Paper.department == department)
    
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
    
    if review.status == SubmissionStatus.REJECTED and not review.rejection_reason and not review.admin_feedback:
        raise HTTPException(status_code=400, detail="Rejection reason or admin feedback required")
    
    paper.status = review.status
    paper.reviewed_by = admin.id
    paper.reviewed_at = datetime.now(timezone.utc)
    paper.rejection_reason = review.rejection_reason  # Keep for backward compatibility
    
    # Store admin feedback in JSON format
    if review.status == SubmissionStatus.REJECTED:
        if review.admin_feedback:
            paper.admin_feedback = review.admin_feedback
        elif review.rejection_reason:
            # Convert old rejection_reason to new JSON format for consistency
            paper.admin_feedback = {
                "message": review.rejection_reason,
                "rejected_at": datetime.now(timezone.utc).isoformat(),
                "rejected_by": admin.id
            }
    else:
        # Clear admin feedback if approved
        paper.admin_feedback = None
    
    db.commit()
    
    return {"message": f"Paper {review.status.value} successfully"}

@app.post("/admin/papers/approve-all")
def approve_all_pending_papers(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Admin: Approve all pending papers at once"""
    pending_papers = db.query(Paper).filter(Paper.status == SubmissionStatus.PENDING).all()
    
    if not pending_papers:
        return {
            "message": "No pending papers to approve",
            "approved_count": 0
        }
    
    approved_count = 0
    for paper in pending_papers:
        paper.status = SubmissionStatus.APPROVED
        paper.reviewed_by = admin.id
        paper.reviewed_at = datetime.now(timezone.utc)
        paper.admin_feedback = None  # Clear any previous feedback
        approved_count += 1
    
    db.commit()
    
    return {
        "message": f"Successfully approved {approved_count} paper(s)",
        "approved_count": approved_count
    }

@app.put("/papers/{paper_id}/edit")
def edit_paper(
    paper_id: int,
    course_id: Optional[str] = Form(None),
    paper_type: Optional[str] = Form(None),
    year: Optional[str] = Form(None),
    semester: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
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
    # Update department if provided
    if department is not None:
        paper.department = department
    
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
    
    # File is stored in database, so no need to delete from filesystem
    # Only delete from filesystem if it exists there (backward compatibility)
    if paper.file_path:
        try:
            file_path = find_file_in_uploads(paper.file_path)
            if file_path and file_path.exists():
                os.remove(file_path)
        except OSError as e:
            print(f"Warning: Could not delete file {paper.file_path}: {e}")
    
    db.delete(paper)
    db.commit()
    return {"message": "Paper deleted successfully"}

@app.get("/papers/{paper_id}/preview")
def preview_paper(
    paper_id: int, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get paper preview metadata - Public access for approved papers, admin access for pending papers"""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Check access permissions
    # Admins can preview any paper (including pending)
    # Logged-in users can preview approved papers or their own papers
    # Non-logged-in users can only preview approved papers
    if paper.status != SubmissionStatus.APPROVED:
        if not current_user:
            raise HTTPException(status_code=403, detail="Paper not approved yet. Please login to access.")
        if not current_user.is_admin and paper.uploaded_by != current_user.id:
            raise HTTPException(status_code=403, detail="Paper not approved yet")
    
    # Check if file exists in database
    if not paper.file_data:
        # Fallback: check filesystem for backward compatibility
        stored_path = paper.file_path
        file_path = find_file_in_uploads(stored_path) if stored_path else None
        
        if not file_path or not file_path.exists():
            raise HTTPException(
                status_code=404, 
                detail=f"File not found. This paper's file was stored in a previous database and is no longer available. Paper ID: {paper_id}, Stored path: {stored_path}"
            )
    
    # Get MIME type
    mime_type = get_mime_type(paper.file_name)
    
    return {
        "paper_id": paper.id,
        "file_name": paper.file_name,
        "file_path": paper.file_path or "",
        "file_size": paper.file_size,
        "mime_type": mime_type,
        "can_preview": can_preview_file(paper.file_name)
    }

@app.get("/papers/{paper_id}/download")
async def download_paper(
    paper_id: int, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Download paper file - Public access for approved papers, admin access for pending papers"""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Check access permissions
    # Admins can download any paper (including pending)
    # Logged-in users can download approved papers or their own papers
    # Non-logged-in users can only download approved papers
    if paper.status != SubmissionStatus.APPROVED:
        if not current_user:
            raise HTTPException(status_code=403, detail="Paper not approved yet. Please login to access.")
        if not current_user.is_admin and paper.uploaded_by != current_user.id:
            raise HTTPException(status_code=403, detail="Paper not approved yet")
    
    # Check if file exists in database
    if paper.file_data:
        # Serve from database
        from fastapi.responses import Response
        mime_type = get_mime_type(paper.file_name)
        return Response(
            content=paper.file_data,
            media_type=mime_type,
            headers={"Content-Disposition": f'attachment; filename="{paper.file_name}"'}
        )
    
    # Fallback: check filesystem for backward compatibility
    stored_path = paper.file_path
    file_path = find_file_in_uploads(stored_path) if stored_path else None
    
    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"File not found. This paper's file was stored in a previous database and is no longer available. Paper ID: {paper_id}, Stored path: {stored_path}"
        )
    
    # Final security check - ensure file is within uploads directory
    try:
        file_path = file_path.resolve()
        uploads_dir = UPLOAD_DIR.resolve()
        if not str(file_path).startswith(str(uploads_dir)):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        print(f"Error resolving file path: {e}")
        raise HTTPException(status_code=404, detail="File path invalid")
    
    from fastapi.responses import FileResponse
    return FileResponse(str(file_path), filename=paper.file_name)

@app.get("/admin/diagnose/files")
def diagnose_files(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Diagnostic endpoint to check file status for all papers"""
    papers = db.query(Paper).all()
    
    results = []
    uploads_dir_path = str(UPLOAD_DIR.resolve())
    
    # Get list of actual files on disk
    files_on_disk = set()
    try:
        if UPLOAD_DIR.exists():
            files_on_disk = {f.name for f in UPLOAD_DIR.iterdir() if f.is_file()}
    except Exception as e:
        print(f"Error listing uploads directory: {e}")
    
    for paper in papers:
        stored_path = paper.file_path
        
        # Check if file exists in database
        file_in_db = paper.file_data is not None
        
        # Use helper function to check if file exists in filesystem (backward compatibility)
        file_path = find_file_in_uploads(stored_path) if stored_path else None
        file_exists_fs = file_path is not None and file_path.exists()
        
        # File exists if it's in database OR filesystem
        file_exists = file_in_db or file_exists_fs
        
        # Extract filename for display
        filename = Path(stored_path).name if stored_path else None
        
        results.append({
            "paper_id": paper.id,
            "paper_title": paper.title,
            "stored_path": stored_path,
            "extracted_filename": filename,
            "file_exists": file_exists,
            "file_in_database": file_in_db,
            "file_in_filesystem": file_exists_fs,
            "status": paper.status.value
        })
    
    return {
        "uploads_directory": uploads_dir_path,
        "total_papers": len(results),
        "files_on_disk_count": len(files_on_disk),
        "papers_with_missing_files": sum(1 for r in results if not r["file_exists"]),
        "papers": results
    }

# ========== Helper Functions ==========
def format_user_response(user: User) -> dict:
    """Format user for response with normalized file paths"""
    user_dict = {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "is_admin": user.is_admin,
        "email_verified": user.email_verified,
        "age": user.age,
        "year": user.year,
        "university": user.university,
        "department": user.department,
        "roll_no": user.roll_no,
        "student_id": user.student_id,
        "photo_path": normalize_file_path(user.photo_path),
        "id_card_path": normalize_file_path(user.id_card_path),
        "id_verified": user.id_verified,
        "created_at": user.created_at
    }
    return user_dict

def format_paper_response(paper: Paper, include_private_info: bool = False):
    """Format paper for response"""
    # Normalize file_path to be relative to uploads/ for frontend consumption
    # Ensure file_path is never None - use original if normalization returns None
    file_path = normalize_file_path(paper.file_path)
    if file_path is None and paper.file_path:
        # If normalization failed but we have a file_path, use it as-is
        file_path = paper.file_path
    elif file_path is None:
        # If no file_path at all, use empty string
        file_path = ""
    
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
        "department": paper.department,
        "file_name": paper.file_name or "",  # Ensure file_name is never None
        "file_size": paper.file_size,
        "file_path": file_path,  # Normalized to just filename, never None
        "status": paper.status,
        "uploaded_at": paper.uploaded_at,
        "reviewed_at": paper.reviewed_at,
        "rejection_reason": paper.rejection_reason if include_private_info else None,
        "admin_feedback": paper.admin_feedback if (include_private_info or paper.status == SubmissionStatus.REJECTED) else None
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
    # Railway requires binding to 0.0.0.0 and using PORT environment variable
    # Default to 8000 if PORT is not set
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple script to create tables in Railway PostgreSQL
"""

import os
import sys
from sqlalchemy import create_engine, text, Column, Integer, String, Boolean, ForeignKey, Text, Enum as SQLEnum, DateTime, LargeBinary, JSON, Index
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone
from enum import Enum

# Railway PostgreSQL connection string
RAILWAY_DB_URL = "postgresql://postgres:yvFPUoOUFxjaiLqtimFIZRDgcqavpCeU@yamabiko.proxy.rlwy.net:21623/railway"

Base = declarative_base()

# Define enums
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

# Define models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    age = Column(Integer, nullable=True)
    year = Column(String(20), nullable=True)
    university = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    roll_no = Column(String(100), nullable=True)
    student_id = Column(String(100), nullable=True)
    photo_path = Column(String(500), nullable=True)
    id_card_path = Column(String(500), nullable=True)
    photo_data = Column(LargeBinary, nullable=True)
    id_card_data = Column(LargeBinary, nullable=True)
    id_verified = Column(Boolean, default=False)
    verified_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    email_verified = Column(Boolean, default=False)
    admin_feedback = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

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
    department = Column(String(255), nullable=True, index=True)
    
    file_path = Column(String(500), nullable=True)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer)
    file_data = Column(LargeBinary, nullable=True)
    
    status = Column(SQLEnum(SubmissionStatus), default=SubmissionStatus.PENDING, index=True)
    reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at = Column(DateTime)
    rejection_reason = Column(Text)
    admin_feedback = Column(JSON, nullable=True)
    
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('idx_paper_status_uploaded', 'status', 'uploaded_at'),
        Index('idx_paper_course_status', 'course_id', 'status'),
        Index('idx_paper_type_year', 'paper_type', 'year'),
    )

print("=" * 70)
print("Creating Tables in Railway PostgreSQL")
print("=" * 70)
print(f"Connecting to Railway PostgreSQL...")

try:
    # Create engine
    engine = create_engine(
        RAILWAY_DB_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={"connect_timeout": 10}
    )
    
    # Test connection
    print("Testing connection...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"Connected! PostgreSQL: {version.split(',')[0]}")
    
    # Create all tables
    print("\nCreating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")
    
    # Verify
    print("\nVerifying tables...")
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    expected = ['users', 'courses', 'papers']
    for table in expected:
        if table in tables:
            print(f"  [OK] {table}")
        else:
            print(f"  [MISSING] {table}")
    
    print("\n" + "=" * 70)
    print("SUCCESS! Database setup complete.")
    print("=" * 70)
    print("\nNext: Update Railway backend service DATABASE_URL to:")
    print(RAILWAY_DB_URL)
    print()

except Exception as e:
    print(f"\nERROR: {e}")
    sys.exit(1)


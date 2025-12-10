#!/usr/bin/env python3
"""
Script to add performance indexes to existing database.
Run this after deploying the optimized code to ensure indexes are created.

Usage:
    python add_indexes.py
"""

import os
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL - check for SQLite first
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Check if SQLite file exists
    sqlite_path = "paper_portal.db"
    if os.path.exists(sqlite_path):
        DATABASE_URL = f"sqlite:///{sqlite_path}"
        print(f"📁 Found SQLite database: {sqlite_path}")
    else:
        DATABASE_URL = "postgresql://user:password@localhost/paper_portal"

def add_indexes():
    """Add performance indexes to existing database"""
    print("="*70)
    print("🔧 Adding Performance Indexes to Database")
    print("="*70)
    
    try:
        # Create engine based on database type
        if "sqlite" in DATABASE_URL.lower():
            # SQLite connection
            engine = create_engine(
                DATABASE_URL,
                connect_args={"check_same_thread": False},
                pool_pre_ping=True,
            )
        elif "neon.tech" in DATABASE_URL or "neondb" in DATABASE_URL:
            # Neon DB connection with SSL
            engine = create_engine(
                DATABASE_URL,
                connect_args={
                    "sslmode": "require",
                    "connect_timeout": 10,
                },
                pool_pre_ping=True,
            )
        else:
            # PostgreSQL connection
            engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        
        # Check if database is PostgreSQL or SQLite
        db_type = "unknown"
        try:
            with engine.connect() as conn:
                if "sqlite" in DATABASE_URL.lower():
                    result = conn.execute(text("SELECT sqlite_version()"))
                    db_type = "sqlite"
                    print(f"✓ Connected to SQLite database")
                else:
                    result = conn.execute(text("SELECT version()"))
                    db_type = "postgresql"
                    print(f"✓ Connected to PostgreSQL database")
        except Exception as e:
            print(f"❌ Error connecting to database: {e}")
            return False
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Indexes are the same for both PostgreSQL and SQLite
                indexes = [
                    # Individual indexes on papers table
                    ("idx_paper_course_id", "CREATE INDEX IF NOT EXISTS idx_paper_course_id ON papers(course_id)"),
                    ("idx_paper_uploaded_by", "CREATE INDEX IF NOT EXISTS idx_paper_uploaded_by ON papers(uploaded_by)"),
                    ("idx_paper_title", "CREATE INDEX IF NOT EXISTS idx_paper_title ON papers(title)"),
                    ("idx_paper_paper_type", "CREATE INDEX IF NOT EXISTS idx_paper_paper_type ON papers(paper_type)"),
                    ("idx_paper_year", "CREATE INDEX IF NOT EXISTS idx_paper_year ON papers(year)"),
                    ("idx_paper_semester", "CREATE INDEX IF NOT EXISTS idx_paper_semester ON papers(semester)"),
                    ("idx_paper_status", "CREATE INDEX IF NOT EXISTS idx_paper_status ON papers(status)"),
                    ("idx_paper_uploaded_at", "CREATE INDEX IF NOT EXISTS idx_paper_uploaded_at ON papers(uploaded_at)"),
                    
                    # Composite indexes for common query patterns
                    ("idx_paper_status_uploaded", "CREATE INDEX IF NOT EXISTS idx_paper_status_uploaded ON papers(status, uploaded_at)"),
                    ("idx_paper_course_status", "CREATE INDEX IF NOT EXISTS idx_paper_course_status ON papers(course_id, status)"),
                    ("idx_paper_type_year", "CREATE INDEX IF NOT EXISTS idx_paper_type_year ON papers(paper_type, year)"),
                ]
                
                # Create indexes
                created = 0
                skipped = 0
                
                for index_name, sql in indexes:
                    try:
                        conn.execute(text(sql))
                        conn.commit()
                        print(f"✓ Created index: {index_name}")
                        created += 1
                    except Exception as e:
                        # Check if index already exists
                        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                            print(f"⊘ Index already exists: {index_name}")
                            skipped += 1
                        else:
                            print(f"⚠️  Error creating {index_name}: {e}")
                
                print("\n" + "="*70)
                print(f"✅ Index creation complete!")
                print(f"   Created: {created} indexes")
                print(f"   Skipped: {skipped} indexes (already exist)")
                print("="*70)
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error: {e}")
                return False
    
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

if __name__ == "__main__":
    success = add_indexes()
    exit(0 if success else 1)


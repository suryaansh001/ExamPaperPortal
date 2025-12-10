"""
Comprehensive Bulk Import Script for Past Papers

Features:
- Direct database integration (no API calls)
- Comprehensive OCR processing with fallback patterns
- Filename-based extraction and validation
- Automatic course creation
- PDF storage in database (file_data column)
- Neon DB support with SSL/TLS

Usage:
    python -m ExamSystemBackend.bulk_import_past_papers [--max-files N] [--auto-approve] [--admin-user-id ID]
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone

# OCR and PDF libraries
try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
    import PyPDF2
except ImportError as e:
    print(f"Error: Missing required library - {e}")
    print("Please install required packages:")
    print("pip install pdf2image pillow pytesseract PyPDF2")
    exit(1)

# Database libraries
try:
    from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, LargeBinary, Enum as SQLEnum, JSON
    from sqlalchemy.orm import declarative_base, Session, sessionmaker, relationship
    from sqlalchemy.exc import IntegrityError
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Error: Missing required library - {e}")
    print("Please install required packages:")
    print("pip install sqlalchemy psycopg2-binary python-dotenv")
    exit(1)

# Setup logging with UTF-8 encoding for file handler
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bulk_import_past_papers.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Check if Tesseract is available
TESSERACT_AVAILABLE = False
try:
    pytesseract.get_tesseract_version()
    TESSERACT_AVAILABLE = True
    logger.info("Tesseract OCR is available")
except (Exception, NameError):
    logger.warning("Tesseract OCR is not available. OCR will be skipped. Install Tesseract for OCR support.")

# Load environment variables
load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/paper_portal")

# Neon DB requires SSL/TLS connections
if "neon.tech" in DATABASE_URL or "neondb" in DATABASE_URL:
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
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={
            "connect_timeout": 10,
        }
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Enum definitions (matching main.py)
from enum import Enum

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

# Database Models - Match existing schema exactly
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

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
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"))
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    title = Column(String(255), nullable=False)
    description = Column(Text)
    paper_type = Column(SQLEnum(PaperType), nullable=False)
    year = Column(Integer)
    semester = Column(String(20))
    department = Column(String(255), nullable=True)
    
    file_path = Column(String(500), nullable=True)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer)
    file_data = Column(LargeBinary, nullable=True)  # Store PDF binary data
    
    status = Column(SQLEnum(SubmissionStatus), default=SubmissionStatus.PENDING)
    reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime)
    rejection_reason = Column(Text)
    admin_feedback = Column(JSON, nullable=True)
    
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    course = relationship("Course", back_populates="papers")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

# Root folder that contains subfolders like:
#   pastpaper/OK December 2023/...
PAST_PAPER_ROOT = Path(__file__).resolve().parent.parent / "pastpaper"


class ComprehensiveOCRProcessor:
    """
    Comprehensive OCR processor with:
    - Multi-method text extraction (direct + OCR)
    - Comprehensive fallback regex patterns
    - Filename-based extraction and validation
    - Confidence scoring and decision making
    """
    
    def __init__(self):
        # Enhanced regex patterns with comprehensive fallbacks
        self.patterns = {
            # Course code patterns with fallbacks
            'course_code': [
                # Pattern 1: "FA1102: Management Accounting" format
                r'\b([A-Z]{2}\d{4})\s*[:]',  # FA1102:, CS1234:, etc.
                r'\b([A-Z]{2}\d{4})\b',  # Standard: CS1234, MA1102, FA1102
                r'\b([A-Z]{3}\d{3,4})\b',  # CSE101
                r'Course\s+Code\s*[:\-]?\s*([A-Z]{2,3}\d{3,4})',
                r'Subject\s+Code\s*[:\-]?\s*([A-Z]{2,3}\d{3,4})',
                r'\(([A-Z]{2}-[0-9]{4})\)',  # Fallback: (CS-1218)
                r'\(([A-Z]{2,4}-\d{3,4})\)',  # Fallback: (CSAI-1234)
                r'\b([A-Z]{2,4}[-\s]?\d{3,4}[A-Z]?)\b',  # Generic with optional suffix
            ],
            
            # Course name patterns with fallbacks
            'course_name': [
                # Primary: "FA1102: Management Accounting" format
                r'\b[A-Z]{2}\d{4}\s*:\s*([A-Z][A-Za-z\s&,\-()]+?)(?:\n|Roll|Time:|Max\.|Marks|Semester)',
                # Primary: Look for course name after course code with colon/dash
                r'[A-Z]{2,4}\d{3,4}\s*[:\-]\s*([A-Z][A-Za-z\s&,\-()]+?)(?:\n|Time:|Max\.|Marks|Semester|Roll)',
                # Look for "Course Name:" or "Subject Name:" labels
                r'(?:Course|Subject)\s+Name\s*[:\-]?\s*([A-Z][A-Za-z\s&,\-()]+?)(?:\n|Course\s+Code|Subject\s+Code|Max|Time)',
                # Look for "Paper:" label
                r'Paper\s*[:\-]?\s*([A-Z][A-Za-z\s&,\-()]+?)(?:\n|Marks|Time|Semester)',
                # Look for course name on same line as course code (no label)
                r'[A-Z]{2,4}\d{3,4}\s+([A-Z][A-Za-z\s&,\-]{10,60}?)(?:\s*\n|Time:|Max\.|Marks|Semester)',
            ],
            
            # Semester patterns with multiple fallbacks
            'semester': [
                # Pattern 1: "BBA, Semester III, 2023-26" or "Semester III"
                r'(?:BBA|BCA|BTech|B\.?Tech)[,\s]+Semester\s+([IVX]+|\d+)',
                r'Semester\s+([IVX]+|\d+)(?:\s*[,,\n]|$)',
                r'Semester:\s*([0-9]+(?:st|nd|rd|th)?)',
                r'Semester\s*[:\-]?\s*([IVX]+|\d+)',
                r'SEM[ESTER]\s[:-]?\s*([IVX]+|\d+)',
                r'(\d+)\s*(st|nd|rd|th)\s*SEMESTER',
                r'SEM\s*([IVX]+|\d+)',
                r'Semester\s+([IVXLC]+)\s+[A-Za-z.]+\s+[A-Za-z]+',
                r'Semester\s+([IVXLC]+)\s*[,\n]',
            ],
            
            # Programme patterns with fallbacks
            'programme': [
                r'Programme\s*[:\-]?\s*(B\.?Tech|BCA|BBA|M\.?Tech|MCA|MBA)',
                r'Program\s*[:\-]?\s*(B\.?Tech|BCA|BBA|M\.?Tech|MCA|MBA)',
                r'(B\.?Tech|BCA|BBA|M\.?Tech|MCA|MBA)\s+(?:Semester|SEM)',
                r'\b(B\.?\s*B\.?\s*A\.?|B\.?\s*Tech\.?|M\.?\s*Tech\.?|B\.?\s*E\.?|BBA|B\.?Sc\.?)\b',
                r'Semester\s+[IVXLC]+\s+([A-Za-z.]+)\s+[A-Za-z]+',
            ],
            
            # Branch patterns
            'branch': [
                r'Branch\s*[:\-]?\s*([A-Za-z\s]+)',
                r'Specialization\s*[:\-]?\s*([A-Za-z\s]+)',
                r'\b(CSE|ECE|EEE|ME|CE|IT|CS)\b',
                r'Semester\s+[IVXLC]+\s+[A-Za-z.]+\s+([A-Za-z]+)',
            ],
            
            # Department patterns
            'department': [
                r'Department\s*[:\-]?\s*([A-Za-z\s&]+)',
                r'Department\s+of\s+(.*?)(?=\n)',
                r'DEPARTMENT\s+OF\s+(.*?)(?=\n)',
                r'INSTITUTE\s+OF\s+([A-Z\s&]+?)(?=\n|End)',
            ],
            
            # Year patterns
            'year': [
                r'(20[12]\d)\s*-\s*20\d{2}',
                r'\b(20[12]\d)\b',
                r'YEAR\s*[:\-]?\s*(20\d{2})',
                r'(\d{4})\s*[-–]\s*(\d{2,4})',
                r'(?:Date|December|October|November)\s+\d+,?\s+(20\d{2})',
            ],
            
            # Exam type patterns
            'exam_type': [
                r'(End\s*Term|Mid\s*Term)\s+Examination',  # "End Term Examination" or "Mid Term Examination"
                r'(END\s*TERM|MID\s*TERM|FINAL|EXTERNAL)',
                r'(End-Term|Mid-Term)\s+Examination',
                r'(Endterm|Midterm)',
                r'\b(End\s*Term|Mid\s*Term|Final)\b',
            ],
        }
    
    def roman_to_number(self, roman: str) -> str:
        """Convert Roman numeral to integer string"""
        roman_dict = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100}
        roman = roman.upper()
        result = 0
        prev_value = 0
        
        for char in reversed(roman):
            value = roman_dict.get(char, 0)
            if value >= prev_value:
                result += value
            else:
                result -= value
            prev_value = value
        
        return str(result)
    
    def infer_semester_from_course_code(self, course_code: str) -> Optional[str]:
        """
        Infer semester from course code based on common patterns.
        Many universities use course codes where the number indicates the year/semester.
        Examples:
        - CS11xx, AS11xx, CC11xx -> First year (SEM I or II)
        - CS12xx, AS12xx -> Second year (SEM III or IV)
        - CS13xx, CS14xx -> Third/Fourth year (SEM V-VIII)
        """
        if not course_code:
            return None
        
        # Extract the numeric part
        match = re.search(r'\d+', course_code)
        if not match:
            return None
        
        num_str = match.group(0)
        if len(num_str) < 3:
            return None
        
        # Get first two digits
        first_two = int(num_str[:2])
        
        # Common patterns:
        # 11xx, 10xx -> First year courses (SEM I or II) - default to I
        if first_two in [10, 11]:
            return 'I'
        # 12xx -> Second year courses (SEM III or IV) - default to III
        elif first_two == 12:
            return 'III'
        # 13xx -> Third year first semester (SEM V)
        elif first_two == 13:
            return 'V'
        # 14xx -> Third year second semester or fourth year (SEM VI or VII) - default to VI
        elif first_two == 14:
            return 'VI'
        # 20xx, 21xx -> Could be second year (SEM III or IV) - default to III
        elif first_two in [20, 21]:
            return 'III'
        # 22xx, 23xx -> Could be third year (SEM V or VI) - default to V
        elif first_two in [22, 23]:
            return 'V'
        
        return None
    
    def extract_from_filename(self, filename: str, folder_path: Path) -> Dict:
        """Extract information from filename and folder structure"""
        logger.info(f"\n[FILENAME EXTRACTION] Processing: {filename}")
        
        info = {
            'file_name': filename,
            'file_path': str(folder_path / filename),
            'course_code': None,
            'course_name': None,
            'semester': None,
            'year': None,
            'programme': None,
            'paper_type': 'other',
            'source': 'filename',
            'confidence': {}
        }
        
        # Extract course code and name from filename
        base_name = Path(filename).stem
        
        # Try multiple filename patterns
        patterns = [
            r'^([A-Z]{2,3}\d{3,4})\s*[-–]\s*(.+)$',  # CS1234-Name
            r'^([A-Z]{2,3}\d{3,4})\s+(.+)$',  # CS1234 Name
            r'^([A-Z]{2,3}\d{3,4})(.+)$',  # CS1234Name
            r'^([A-Z]{1,2}[a-z]?[-]?\d{3,4})\s*[-–]\s*(.+)$',  # Cs-1138-Name or Ee-1223-Name (case insensitive)
            r'^([A-Z]{1,2}[a-z]?[-]?\d{3,4})\s+(.+)$',  # Cs-1138 Name
            r'^([A-Z]{1,2}[a-z]?[-]?\d{3,4})(.+)$',  # Cs-1138Name
        ]
        
        for pattern in patterns:
            match = re.match(pattern, base_name, re.IGNORECASE)
            if match:
                code = match.group(1).upper().strip()
                # Normalize course code: remove dashes, ensure proper format
                code = code.replace('-', '').replace(' ', '')
                # Validate it looks like a course code (2-4 letters followed by 3-4 digits)
                if re.match(r'^[A-Z]{2,4}\d{3,4}[A-Z]?$', code):
                    info['course_code'] = code
                    info['course_name'] = match.group(2).strip().replace('-', ' ').strip()
                    info['confidence']['course_code'] = 'high'
                    info['confidence']['course_name'] = 'high'
                    logger.info(f"  [OK] Course Code: {info['course_code']}")
                    logger.info(f"  [OK] Course Name: {info['course_name']}")
                    break
        
        # Extract from folder structure
        folder_name = folder_path.name
        # Get all parent folders up to but not including PAST_PAPER_ROOT
        parent_folders = []
        for p in folder_path.parents:
            if p == PAST_PAPER_ROOT or p == PAST_PAPER_ROOT.parent:
                break
            parent_folders.append(p.name)
        all_folders = [folder_name] + parent_folders
        
        # Extract semester from folders - multiple patterns
        for folder in all_folders:
            # Pattern 1: SEM I, SEM II, SEM 1, SEM 2, etc.
            semester_match = re.search(r'SEM\s*([IVX]+|\d+)', folder, re.IGNORECASE)
            if semester_match:
                sem_val = semester_match.group(1)
                # Convert roman to number if needed
                if re.match(r'^[IVX]+$', sem_val, re.IGNORECASE):
                    sem_val = self.roman_to_number(sem_val)
                info['semester'] = sem_val
                info['confidence']['semester'] = 'high'
                logger.info(f"  [OK] Semester: {info['semester']} (from SEM pattern)")
                break
            
            # Pattern 2: "1st year", "2nd year", "3rd year", "4th year"
            year_match = re.search(r'(\d+)(?:st|nd|rd|th)\s*year', folder, re.IGNORECASE)
            if year_match:
                year_num = int(year_match.group(1))
                # Convert year to semester range (1st year = SEM I or II, 2nd year = SEM III or IV, etc.)
                if year_num == 1:
                    # First year could be SEM I or II - default to I
                    info['semester'] = 'I'
                    info['confidence']['semester'] = 'medium'
                    logger.info(f"  [OK] Semester: {info['semester']} (inferred from 1st year)")
                elif year_num == 2:
                    info['semester'] = 'III'
                    info['confidence']['semester'] = 'medium'
                    logger.info(f"  [OK] Semester: {info['semester']} (inferred from 2nd year)")
                elif year_num == 3:
                    info['semester'] = 'V'
                    info['confidence']['semester'] = 'medium'
                    logger.info(f"  [OK] Semester: {info['semester']} (inferred from 3rd year)")
                elif year_num == 4:
                    info['semester'] = 'VII'
                    info['confidence']['semester'] = 'medium'
                    logger.info(f"  [OK] Semester: {info['semester']} (inferred from 4th year)")
                break
        
        # Fallback: Infer semester from course code if not found in folders
        if not info.get('semester') and info.get('course_code'):
            semester = self.infer_semester_from_course_code(info['course_code'])
            if semester:
                info['semester'] = semester
                info['confidence']['semester'] = 'low'
                logger.info(f"  [OK] Semester: {info['semester']} (inferred from course code)")
        
        # Extract year from folders
        for folder in all_folders:
            year_match = re.search(r'(20\d{2})', folder)
            if year_match:
                info['year'] = int(year_match.group(1))
                info['confidence']['year'] = 'high'
                logger.info(f"  [OK] Year: {info['year']}")
                break
        
        # Extract programme from folders
        for folder in all_folders:
            prog_match = re.search(r'(B\.?Tech|BCA|BBA|M\.?Tech|MCA|MBA)', folder, re.IGNORECASE)
            if prog_match:
                info['programme'] = prog_match.group(1).upper().replace('.', '')
                info['confidence']['programme'] = 'high'
                logger.info(f"  [OK] Programme: {info['programme']}")
                break

        # Determine paper type from folders
        folder_text = ' '.join(all_folders).lower()
        if 'end term' in folder_text or 'endterm' in folder_text:
            info['paper_type'] = 'endterm'
            info['confidence']['paper_type'] = 'high'
        elif 'mid term' in folder_text or 'midterm' in folder_text:
            info['paper_type'] = 'midterm'
            info['confidence']['paper_type'] = 'high'
        
        return info
    
    def extract_text_from_pdf(self, pdf_path: Path, max_pages: int = 3) -> str:
        """
        Extract text from PDF using multiple methods
        1. Direct text extraction (fast)
        2. OCR as fallback (more accurate for scanned documents)
        """
        logger.info(f"\n[TEXT EXTRACTION] Processing: {pdf_path.name}")
        extracted_text = ""
        
        # Method 1: Direct text extraction
        try:
            logger.info("  [*] Trying direct text extraction...")
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = min(len(pdf_reader.pages), max_pages)
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    extracted_text += text + "\n"
            
            if len(extracted_text.strip()) > 100:
                logger.info(f"  [OK] Direct extraction successful ({len(extracted_text)} chars)")
                return extracted_text
            else:
                logger.info("  [*] Direct extraction yielded minimal text, trying OCR...")
        
        except Exception as e:
            logger.warning(f"  [WARN] Direct extraction failed: {e}")
        
        # Method 2: OCR extraction (only if Tesseract is available)
        if not TESSERACT_AVAILABLE:
            logger.warning("  [WARN] Tesseract not available, skipping OCR. Using extracted text as-is.")
            return extracted_text
        
        try:
            logger.info("  [*] Running OCR extraction...")
            images = convert_from_path(
                pdf_path,
                first_page=1,
                last_page=max_pages,
                dpi=300  # High DPI for better accuracy
            )
            
            logger.info(f"  [*] Converted {len(images)} page(s) to images")
            
            ocr_text = ""
            for i, image in enumerate(images):
                # Use best OCR settings
                custom_config = r'--oem 3 --psm 6'  # PSM 6: Uniform block of text
                text = pytesseract.image_to_string(image, config=custom_config)
                ocr_text += f"\n{'='*50}\n PAGE {i+1} \n{'='*50}\n{text}"
                logger.info(f"  [OK] OCR page {i+1} completed ({len(text)} chars)")
            
            logger.info(f"  [OK] OCR extraction successful ({len(ocr_text)} chars)")
            # Combine direct extraction with OCR
            if ocr_text:
                extracted_text = extracted_text + "\n" + ocr_text
            
        except Exception as e:
            logger.warning(f"  [WARN] OCR extraction failed: {e}. Using direct extraction only.")
            # Don't raise - continue with whatever text we have
        
        return extracted_text
    
    def extract_from_ocr(self, text: str, filename: str) -> Dict:
        """Extract structured information from OCR text using regex patterns"""
        logger.info(f"\n[OCR EXTRACTION] Extracting structured data...")
        
        info = {
            'course_code': None,
            'course_name': None,
            'semester': None,
            'year': None,
            'programme': None,
            'branch': None,
            'department': None,
            'exam_type': None,
            'paper_type': 'other',
            'source': 'ocr',
            'confidence': {}
        }
        
        # Extract each field using patterns
        for field, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    if field == 'course_code':
                        # Normalize: remove dashes and spaces
                        code = match.group(1).upper().replace('-', '').replace(' ', '')
                        # Validate it's a proper course code
                        if re.match(r'^[A-Z]{2,4}\d{3,4}[A-Z]?$', code):
                            info[field] = code
                    elif field == 'course_name':
                        # Extract and clean course name
                        name = match.group(1).strip()
                        # Clean up common OCR artifacts
                        name = re.sub(r'\s+', ' ', name)
                        name = re.sub(r'[:\-]\s*$', '', name)
                        
                        # Validate it's a reasonable course name
                        if (5 <= len(name) <= 100 and 
                            not re.match(r'^[^A-Za-z]+$', name) and
                            not name.lower() in ['jk lakshmipat university', 'university', 'institute', 'department']):
                            info[field] = name
                    elif field == 'year':
                        year = int(match.group(1))
                        if 2010 <= year <= 2030:
                            info[field] = year
                        else:
                            continue
                    elif field == 'semester':
                        sem_val = match.group(1)
                        # Convert roman to number if needed
                        if re.match(r'^[IVXLC]+$', sem_val, re.IGNORECASE):
                            sem_val = self.roman_to_number(sem_val)
                        info[field] = sem_val
                    elif field == 'programme':
                        # Normalize programme
                        prog = match.group(1).strip()
                        prog = re.sub(r'\s+', '.', prog).upper().replace('.', '')
                        info[field] = prog
                    else:
                        extracted = match.group(1).strip()
                        if extracted:
                            info[field] = extracted
                    
                    # Only set confidence if we actually extracted something
                    if info.get(field):
                        info['confidence'][field] = 'high'
                        logger.info(f"  [OK] {field.replace('_', ' ').title()}: {info[field]}")
                        break

        # Determine paper type from exam_type
        if info.get('exam_type'):
            exam_type_lower = info['exam_type'].lower()
            if 'end' in exam_type_lower or 'final' in exam_type_lower:
                info['paper_type'] = 'endterm'
            elif 'mid' in exam_type_lower:
                info['paper_type'] = 'midterm'
        
        return info
    
    def compare_and_merge(self, filename_info: Dict, ocr_info: Dict) -> Dict:
        """
        Compare filename and OCR extractions, merge them intelligently
        Returns merged info with validation status
        """
        logger.info(f"\n[COMPARISON & MERGE] Validating and merging data...")
        
        merged = {
            'file_name': filename_info['file_name'],
            'file_path': filename_info['file_path'],
            'course_code': None,
            'course_name': None,
            'semester': None,
            'year': None,
            'programme': None,
            'branch': None,
            'department': None,
            'paper_type': filename_info['paper_type'],
            'title': None,
            'validation': {},
            'confidence': {},
            'decision': None,
            'overall_confidence': 0
        }
        
        # Helper function to normalize for comparison
        def normalize(value):
            if value is None:
                return ""
            return str(value).upper().strip().replace(' ', '').replace('-', '').replace('.', '')
        
        # Helper function to check if a string looks like a valid course name
        def is_valid_course_name(name):
            if not name:
                return False
            name_lower = name.lower()
            invalid_patterns = [
                'jk lakshmipat', 'jklu', 'university', 'institute of', 
                'department of', 'examination', 'end term', 'mid term'
            ]
            return not any(pattern in name_lower for pattern in invalid_patterns)
        
        # Compare and merge each field
        fields_to_compare = ['course_code', 'course_name', 'semester', 'year', 'programme']
        
        for field in fields_to_compare:
            fn_val = filename_info.get(field)
            ocr_val = ocr_info.get(field)
            
            # Special handling for course_name
            if field == 'course_name':
                if fn_val and ocr_val:
                    if is_valid_course_name(ocr_val):
                        if normalize(fn_val) == normalize(ocr_val):
                            merged[field] = fn_val
                            merged['validation'][field] = 'match'
                            merged['confidence'][field] = 100
                            logger.info(f"  [OK] {field}: MATCH ({fn_val})")
                        else:
                            merged[field] = fn_val
                            merged['validation'][field] = 'partial'
                            merged['confidence'][field] = 80
                            logger.info(f"  [~] {field}: PARTIAL MATCH (using filename: {fn_val})")
                    else:
                        merged[field] = fn_val
                        merged['validation'][field] = 'filename_preferred'
                        merged['confidence'][field] = 90
                        logger.info(f"  [OK] {field}: FROM FILENAME (OCR extracted invalid name)")
                elif fn_val:
                    merged[field] = fn_val
                    merged['validation'][field] = 'filename_only'
                    merged['confidence'][field] = 85
                    logger.info(f"  [OK] {field}: FROM FILENAME ({fn_val})")
                elif ocr_val and is_valid_course_name(ocr_val):
                    merged[field] = ocr_val
                    merged['validation'][field] = 'ocr_only'
                    merged['confidence'][field] = 70
                    logger.info(f"  [~] {field}: FROM OCR ({ocr_val})")
                else:
                    merged['validation'][field] = 'missing'
                    merged['confidence'][field] = 0
                    logger.warning(f"  [X] {field}: NOT FOUND")
                continue
            
            # For other fields
            if fn_val and ocr_val:
                if normalize(fn_val) == normalize(ocr_val):
                    merged[field] = fn_val
                    merged['validation'][field] = 'match'
                    merged['confidence'][field] = 100
                    logger.info(f"  [OK] {field}: MATCH ({fn_val})")
                else:
                    if field == 'course_code':
                        merged[field] = fn_val
                        merged['validation'][field] = 'mismatch_prefer_filename'
                        merged['confidence'][field] = 60
                    else:
                        merged[field] = ocr_val
                        merged['validation'][field] = 'mismatch_prefer_ocr'
                        merged['confidence'][field] = 60
                    logger.warning(f"  [X] {field}: MISMATCH (FN: {fn_val}, OCR: {ocr_val})")
            elif fn_val:
                merged[field] = fn_val
                merged['validation'][field] = 'filename_only'
                merged['confidence'][field] = 70
                logger.info(f"  [~] {field}: FROM FILENAME ({fn_val})")
            elif ocr_val:
                merged[field] = ocr_val
                merged['validation'][field] = 'ocr_only'
                merged['confidence'][field] = 70
                logger.info(f"  [~] {field}: FROM OCR ({ocr_val})")
            else:
                merged['validation'][field] = 'missing'
                merged['confidence'][field] = 0
                logger.warning(f"  [X] {field}: NOT FOUND")
        
        # Add OCR-only fields
        ocr_only_fields = ['branch', 'department', 'exam_type']
        for field in ocr_only_fields:
            if ocr_info.get(field):
                merged[field] = ocr_info[field]
                merged['confidence'][field] = 80
        
        # Update paper type if exam_type is more specific
        if merged.get('exam_type'):
            exam_type_lower = merged['exam_type'].lower()
            if 'end' in exam_type_lower and merged['paper_type'] != 'endterm':
                merged['paper_type'] = 'endterm'
            elif 'mid' in exam_type_lower and merged['paper_type'] != 'midterm':
                merged['paper_type'] = 'midterm'
        
        # Calculate overall confidence and make decision
        course_code_conf = merged['confidence'].get('course_code', 0)
        course_name_conf = merged['confidence'].get('course_name', 0)
        
        if course_code_conf >= 80:
            confidences = [v for k, v in merged['confidence'].items() if v > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            merged['overall_confidence'] = int(avg_confidence)
            
            if course_code_conf == 100 and course_name_conf >= 70 and avg_confidence >= 70:
                merged['decision'] = 'ACCEPT'
            elif course_code_conf >= 80 and course_name_conf >= 70 and avg_confidence >= 60:
                merged['decision'] = 'ACCEPT'
            elif course_code_conf >= 80 and avg_confidence >= 60:
                merged['decision'] = 'ACCEPT'
            else:
                merged['decision'] = 'REVIEW'
        elif course_code_conf >= 70:
            # Course code confidence is 70 (from filename), but if we have course name and other data, mark as REVIEW
            confidences = [v for k, v in merged['confidence'].items() if v > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            merged['overall_confidence'] = int(avg_confidence)
            
            # If we have course code, course name, and reasonable confidence, mark as REVIEW (not REJECT)
            if course_name_conf >= 70 and avg_confidence >= 60:
                merged['decision'] = 'REVIEW'
            else:
                merged['decision'] = 'REVIEW'
        elif course_code_conf >= 60:
            merged['decision'] = 'REVIEW'
            merged['overall_confidence'] = course_code_conf
        else:
            merged['decision'] = 'REJECT'
            merged['overall_confidence'] = course_code_conf
        
        # Generate title
        title_parts = []
        if merged['course_code']:
            title_parts.append(merged['course_code'])
        if merged['course_name']:
            title_parts.append(merged['course_name'])
        if merged['paper_type'] != 'other':
            title_parts.append(merged['paper_type'].replace('_', ' ').title())
        if merged['semester']:
            title_parts.append(f"Sem {merged['semester']}")
        if merged['year']:
            title_parts.append(str(merged['year']))
        
        merged['title'] = ' - '.join(title_parts) if title_parts else Path(filename_info['file_name']).stem
        
        logger.info(f"\n  [*] DECISION: {merged['decision']} (Confidence: {merged['overall_confidence']}%)")
        logger.info(f"  [*] TITLE: {merged['title']}")
        
        return merged
    
    def process_single_pdf(self, pdf_path: Path) -> Dict:
        """Process a single PDF file through the complete pipeline"""
        logger.info(f"\n{'='*70}")
        logger.info(f"PROCESSING: {pdf_path.name}")
        logger.info(f"{'='*70}")
        
        folder_path = pdf_path.parent
        result = {'success': False}
        
        try:
            # Step 1: Extract from filename
            filename_info = self.extract_from_filename(pdf_path.name, folder_path)
            
            # Step 2: Extract text from PDF
            text = self.extract_text_from_pdf(pdf_path)
            
            # Step 3: Extract structured info from OCR text
            ocr_info = self.extract_from_ocr(text, pdf_path.name)
            
            # Step 4: Compare and merge
            merged_info = self.compare_and_merge(filename_info, ocr_info)
            
            # Store text preview
            merged_info['extracted_text_preview'] = text[:500].strip()
            merged_info['text_length'] = len(text)
            
            result = merged_info
            result['success'] = True
            result['processed_at'] = datetime.now(timezone.utc).isoformat()
            
        except Exception as e:
            logger.error(f"[ERROR] Error processing {pdf_path.name}: {e}")
            import traceback
            traceback.print_exc()
            result = {
                'success': False,
                'error': str(e),
                'file_name': pdf_path.name,
                'file_path': str(pdf_path)
            }
        
        return result
    
    def normalize_semester(self, semester: Optional[str]) -> Optional[str]:
        """Normalize semester format to Roman numerals"""
        if not semester:
            return None
        
        semester_str = str(semester).strip().upper()
        semester_str = re.sub(r'^(SEM|SEMESTER)\s*', '', semester_str)
        
        # Map numbers to Roman numerals
        num_to_roman = {
            '1': 'I', '2': 'II', '3': 'III', '4': 'IV',
            '5': 'V', '6': 'VI', '7': 'VII', '8': 'VIII'
        }
        
        if semester_str in num_to_roman:
            return num_to_roman[semester_str]
        
        if re.match(r'^[IVXLC]+$', semester_str):
            return semester_str
        
        return semester_str
    
    def get_or_create_course(self, db: Session, course_code: str, course_name: str) -> Optional[Course]:
        """Get existing course or create new one"""
        if not course_code:
            logger.warning("Cannot create/get course without course code")
            return None
        
        # Normalize course code - ALWAYS UPPERCASE
        course_code = course_code.upper().strip()
        
        if course_name:
            course_name = course_name.strip()
        
        # Check if course exists
        course = db.query(Course).filter(Course.code == course_code).first()
        
        if course:
            logger.info(f"  [*] Found existing course: {course.code} - {course.name}")
            if course_name and course.name != course_name:
                logger.info(f"  [*] Updating course name: {course.name} -> {course_name}")
                course.name = course_name
                course.updated_at = datetime.now(timezone.utc)
                db.commit()
            return course
        
        # Create new course
        if not course_name:
            course_name = f"Course {course_code}"
            logger.warning(f"  [*] No course name provided, using default: {course_name}")
        
        course = Course(
            code=course_code,
            name=course_name,
            description=f"Auto-created from bulk import on {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
        )
        
        try:
            db.add(course)
            db.commit()
            db.refresh(course)
            logger.info(f"  [OK] Created new course: {course.code} - {course.name}")
            return course
        except IntegrityError as e:
            db.rollback()
            logger.error(f"  [ERROR] Error creating course: {e}")
            course = db.query(Course).filter(Course.code == course_code).first()
            return course
    
    def _generate_description(self, merged_info: Dict) -> str:
        """Generate description from merged info"""
        desc_parts = []
        
        if merged_info.get('department'):
            desc_parts.append(f"Department: {merged_info['department']}")
        
        if merged_info.get('programme'):
            desc_parts.append(f"Programme: {merged_info['programme']}")
        
        if merged_info.get('branch'):
            desc_parts.append(f"Branch: {merged_info['branch']}")
        
        if merged_info.get('exam_type'):
            desc_parts.append(f"Exam Type: {merged_info['exam_type']}")
        
        if merged_info.get('year'):
            desc_parts.append(f"Year: {merged_info['year']}")
        
        if merged_info.get('semester'):
            desc_parts.append(f"Semester: {merged_info['semester']}")
        
        return " | ".join(desc_parts) if desc_parts else "Imported from past paper archive."
    
    def create_paper_record(self, db: Session, merged_info: Dict, admin_user_id: Optional[int] = None, auto_approve: bool = False) -> Tuple[Optional[Paper], bool]:
        """
        Create paper record in database, or update existing one if duplicate found
        Returns: (paper, was_updated) tuple where was_updated is True if existing paper was updated
        """
        try:
            # Get or create course
            course = self.get_or_create_course(
                db,
                merged_info.get('course_code'),
                merged_info.get('course_name')
            )
            
            if not course:
                logger.error("  [ERROR] Cannot create paper without course")
                return None, False
            
            # Normalize semester
            semester = self.normalize_semester(merged_info.get('semester'))
            
            # Determine paper type - map to database ENUM values (lowercase)
            paper_type = merged_info.get('paper_type', 'other')
            paper_type_map = {
                'endterm': PaperType.ENDTERM,
                'end_term': PaperType.ENDTERM,
                'end term': PaperType.ENDTERM,
                'final': PaperType.ENDTERM,
                'midterm': PaperType.MIDTERM,
                'mid_term': PaperType.MIDTERM,
                'mid term': PaperType.MIDTERM,
                'mst': PaperType.MIDTERM,
                'quiz': PaperType.QUIZ,
                'test': PaperType.QUIZ,
                'assignment': PaperType.ASSIGNMENT,
                'project': PaperType.PROJECT,
                'practice': PaperType.OTHER,
                'other': PaperType.OTHER
            }
            paper_type_enum = paper_type_map.get(paper_type.lower(), PaperType.OTHER)
            
            # Check for duplicate paper
            # Match by: course_id, file_name, year, semester, paper_type
            existing_paper = db.query(Paper).filter(
                Paper.course_id == course.id,
                Paper.file_name == merged_info['file_name']
            ).first()
            
            # Also check by file_path if available
            if not existing_paper and merged_info.get('file_path'):
                existing_paper = db.query(Paper).filter(
                    Paper.course_id == course.id,
                    Paper.file_path == merged_info['file_path']
                ).first()
            
            if existing_paper:
                # Update existing paper with new information
                logger.info(f"  [*] Found existing paper (ID: {existing_paper.id}), updating...")
                
                # Update fields that might have changed
                existing_paper.title = merged_info.get('title', merged_info['file_name'])
                existing_paper.description = self._generate_description(merged_info)
                existing_paper.paper_type = paper_type_enum
                existing_paper.year = merged_info.get('year')
                existing_paper.semester = semester
                existing_paper.department = merged_info.get('department') or merged_info.get('programme')
                existing_paper.updated_at = datetime.now(timezone.utc)
                
                # Update file data if file exists
                file_path = Path(merged_info['file_path'])
                if file_path.exists():
                    try:
                        with open(file_path, 'rb') as f:
                            file_data = f.read()
                        existing_paper.file_data = file_data
                        existing_paper.file_size = len(file_data)
                        logger.info(f"  [OK] Updated PDF file data: {len(file_data)} bytes")
                    except Exception as e:
                        logger.warning(f"  [WARN] Could not read PDF file for update: {e}")
                
                # Update status if auto_approve is enabled
                if auto_approve:
                    should_approve = (
                        merged_info.get('decision') == 'ACCEPT' or
                        (merged_info.get('decision') == 'REVIEW' and merged_info.get('overall_confidence', 0) >= 70)
                    )
                    if should_approve and existing_paper.status != SubmissionStatus.APPROVED:
                        existing_paper.status = SubmissionStatus.APPROVED
                        existing_paper.reviewed_by = admin_user_id
                        existing_paper.reviewed_at = datetime.now(timezone.utc)
                        logger.info(f"  [OK] Updated status to APPROVED")
                
                db.commit()
                db.refresh(existing_paper)
                
                logger.info(f"  [OK] Updated existing paper record: ID {existing_paper.id}, Status: {existing_paper.status.value}")
                return existing_paper, True
            
            # Determine status based on decision and auto_approve
            status = SubmissionStatus.PENDING
            if auto_approve:
                if merged_info.get('decision') == 'ACCEPT':
                    status = SubmissionStatus.APPROVED
                elif merged_info.get('decision') == 'REVIEW' and merged_info.get('overall_confidence', 0) >= 70:
                    # Auto-approve REVIEW decisions with 70%+ confidence
                    status = SubmissionStatus.APPROVED
                elif merged_info.get('decision') == 'REJECT':
                    status = SubmissionStatus.REJECTED
            elif merged_info.get('decision') == 'REJECT':
                status = SubmissionStatus.REJECTED
            
            # Get file size and read file content
            file_path = Path(merged_info['file_path'])
            file_size = file_path.stat().st_size if file_path.exists() else 0
            
            # Read PDF file as binary data
            file_data = None
            try:
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                logger.info(f"  [OK] Read PDF file: {len(file_data)} bytes")
            except Exception as e:
                logger.warning(f"  [WARN] Could not read PDF file: {e}")
            
            # Create new paper record
            paper = Paper(
                course_id=course.id,
                uploaded_by=admin_user_id,
                title=merged_info.get('title', merged_info['file_name']),
                description=self._generate_description(merged_info),
                paper_type=paper_type_enum,
                year=merged_info.get('year'),
                semester=semester,
                department=merged_info.get('department') or merged_info.get('programme'),
                file_path=merged_info['file_path'],
                file_name=merged_info['file_name'],
                file_size=file_size,
                file_data=file_data,
                status=status,
                reviewed_by=admin_user_id if status == SubmissionStatus.APPROVED else None,
                reviewed_at=datetime.now(timezone.utc) if status == SubmissionStatus.APPROVED else None
            )
            
            db.add(paper)
            db.commit()
            db.refresh(paper)
            
            logger.info(f"  [OK] Created new paper record: ID {paper.id}, Status: {status.value}, Type: {paper_type_enum.value}")
            return paper, False
            
        except Exception as e:
            db.rollback()
            logger.error(f"  [ERROR] Error creating paper record: {e}")
            import traceback
            traceback.print_exc()
            return None, False


def get_admin_user_id(db: Session) -> Optional[int]:
    """Get the first admin user ID from database"""
    admin_user = db.query(User).filter(User.is_admin == True).first()
    if admin_user:
        return admin_user.id
    return None


def main() -> None:
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Bulk Import Past Papers with Comprehensive OCR Processing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all files
  python -m ExamSystemBackend.bulk_import_past_papers
  
  # Process first 10 files
  python -m ExamSystemBackend.bulk_import_past_papers --max-files 10
  
  # Process and auto-approve ACCEPT decisions
  python -m ExamSystemBackend.bulk_import_past_papers --auto-approve
  
  # Process with specific admin user ID
  python -m ExamSystemBackend.bulk_import_past_papers --admin-user-id 1 --auto-approve
        """
    )
    
    parser.add_argument('--max-files', type=int, help='Maximum number of files to process')
    parser.add_argument('--auto-approve', action='store_true', help='Auto-approve papers with ACCEPT decision or REVIEW with 70%+ confidence')
    parser.add_argument('--admin-user-id', type=int, help='Admin user ID for uploaded_by field')
    
    args = parser.parse_args()
    
    if not PAST_PAPER_ROOT.exists():
        logger.error(f"Past paper root not found: {PAST_PAPER_ROOT}")
        return

    logger.info(f"\n{'#'*70}")
    logger.info(f"COMPREHENSIVE BULK IMPORT OF PAST PAPERS")
    logger.info(f"Papers Directory: {PAST_PAPER_ROOT}")
    logger.info(f"Auto-approve ACCEPT decisions: {args.auto_approve}")
    logger.info(f"{'#'*70}\n")
    
    # Initialize processor
    processor = ComprehensiveOCRProcessor()
    
    # Find all PDFs
    pdf_files = list(PAST_PAPER_ROOT.rglob("*.pdf"))
    total_files = len(pdf_files)
    
    if not pdf_files:
        logger.error(f"No PDF files found under {PAST_PAPER_ROOT}")
        return

    if args.max_files:
        pdf_files = pdf_files[:args.max_files]
    
    logger.info(f"Found {total_files} PDF files, processing {len(pdf_files)}")
    
    # Get admin user ID
    db = SessionLocal()
    admin_user_id = args.admin_user_id
    if not admin_user_id:
        admin_user_id = get_admin_user_id(db)
        if admin_user_id:
            logger.info(f"Using admin user ID: {admin_user_id}")
        else:
            logger.warning("No admin user found. Papers will be uploaded without uploaded_by field.")
    db.close()
    
    # Process all PDFs
    results = []
    db_stats = {
        'total_processed': 0,
        'courses_created': 0,
        'courses_updated': 0,
        'papers_created': 0,
        'papers_updated': 0,
        'papers_skipped': 0,
        'papers_approved': 0,
        'papers_pending': 0,
        'papers_rejected': 0,
        'errors': 0
    }
    
    db = SessionLocal()
    
    try:
        for idx, pdf_path in enumerate(pdf_files, 1):
            logger.info(f"\n\n{'#'*70}")
            logger.info(f"FILE {idx}/{len(pdf_files)}")
            logger.info(f"{'#'*70}")
            
            try:
                # Process PDF
                result = processor.process_single_pdf(pdf_path)
                
                if not result.get('success'):
                    db_stats['errors'] += 1
                    results.append(result)
                    continue
                
                logger.info(f"\n[DB {idx}/{len(pdf_files)}] Saving to database: {result['file_name']}")
                
                # Track courses before
                courses_before = db.query(Course).count()
                
                # Create or update paper record
                paper, was_updated = processor.create_paper_record(db, result, admin_user_id, args.auto_approve)
                
                if paper:
                    if was_updated:
                        db_stats['papers_updated'] += 1
                        result['action'] = 'updated'
                    else:
                        db_stats['papers_created'] += 1
                        result['action'] = 'created'
                    
                    # Track courses created/updated
                    courses_after = db.query(Course).count()
                    if courses_after > courses_before:
                        db_stats['courses_created'] += 1
                    else:
                        # Check if course name was updated
                        course = db.query(Course).filter(Course.id == paper.course_id).first()
                        if course and result.get('course_name') and course.name != result['course_name']:
                            db_stats['courses_updated'] += 1
                    
                    # Track status
                    if paper.status == SubmissionStatus.APPROVED:
                        db_stats['papers_approved'] += 1
                    elif paper.status == SubmissionStatus.PENDING:
                        db_stats['papers_pending'] += 1
                    elif paper.status == SubmissionStatus.REJECTED:
                        db_stats['papers_rejected'] += 1
                    
                    # Add DB info to result
                    result['db_paper_id'] = paper.id
                    result['db_course_id'] = paper.course_id
                    result['db_status'] = paper.status.value
                else:
                    db_stats['errors'] += 1
                
                db_stats['total_processed'] += 1
                results.append(result)
                
            except Exception as exc:
                logger.error(f"[SKIP] Failed to import {pdf_path.name}: {exc}")
                db_stats['errors'] += 1
                results.append({
                    'success': False,
                    'error': str(exc),
                    'file_name': pdf_path.name,
                    'file_path': str(pdf_path)
                })
    
    finally:
        db.close()
    
    # Save results to JSON
    output_dir = Path("bulk_import_results")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"bulk_import_results_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    
    output_data = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'summary': {
            'total_processed': db_stats['total_processed'],
            'courses_created': db_stats['courses_created'],
            'courses_updated': db_stats['courses_updated'],
            'papers_created': db_stats['papers_created'],
            'papers_updated': db_stats['papers_updated'],
            'papers_skipped': db_stats['papers_skipped'],
            'papers_approved': db_stats['papers_approved'],
            'papers_pending': db_stats['papers_pending'],
            'papers_rejected': db_stats['papers_rejected'],
            'errors': db_stats['errors'],
        },
        'results': results
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n[OK] Results saved to: {output_path}")
    
    # Print summary
    print("\n\n" + "="*70)
    print("BULK IMPORT SUMMARY")
    print("="*70)
    print(f"Total files processed: {db_stats['total_processed']}")
    print(f"\nCourses:")
    print(f"  [OK] Created: {db_stats['courses_created']}")
    print(f"  [*] Updated: {db_stats['courses_updated']}")
    print(f"\nPapers:")
    print(f"  [OK] Created: {db_stats['papers_created']}")
    print(f"  [*] Updated: {db_stats['papers_updated']}")
    print(f"  [~] Skipped: {db_stats['papers_skipped']}")
    print(f"\nPaper Status:")
    print(f"  [OK] Approved: {db_stats['papers_approved']}")
    print(f"  [~] Pending: {db_stats['papers_pending']}")
    print(f"  [X] Rejected: {db_stats['papers_rejected']}")
    print(f"  [X] Errors: {db_stats['errors']}")
    print("="*70)
    print(f"\n[OK] Processing complete!")
    print(f"Results saved in: {output_path}")
    print(f"Check log file: bulk_import_past_papers.log for details")


if __name__ == "__main__":
    main()

from main import SessionLocal, Course
from sqlalchemy import func

def cleanup_courses():
    session = SessionLocal()
    try:
        # Find duplicates by code
        # We want to keep "CODING_PYTHON" (Coding Hour - python) and "CODING_DAA" (Coding Hour DAA)
        # Or maybe better: keep the ones with IDs that associate with challenges. 
        # But challenges map to course_id. If duplicate courses exist, challenges might be split.
        
        # Let's inspect what we have first
        courses = session.query(Course).all()
        print("Existing courses:")
        for c in courses:
            print(f"ID: {c.id}, Code: {c.code}, Name: {c.name}")
            
        # Strategy:
        # If we have "CODING_PYTHON" (ID X) and "CODING_PYTHON" (ID Y), delete one.
        # But wait, code is Unique? If code is unique, how do we have duplicates?
        # Maybe the duplicates have different codes?
        # The user report:
        # 1. "Coding Hour DAA"
        # 2. "Coding Hour - python"
        # 3. "Coding Hour - Python" (different casing in Name? Code might differ)
        # 4. "Coding Hour - DAA" (different name)
        
        # We need to see the codes.
        
        # If we find distinct courses that are effectively duplicates, we need to merge them.
        # i.e., move challenges to the "main" course and delete the "duplicate".
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    cleanup_courses()

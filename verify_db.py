#!/usr/bin/env python3
"""Quick verification script to check database state"""

from main import SessionLocal, DailyContest, ContestQuestion, Course

def verify_database():
    db = SessionLocal()
    
    try:
        contests = db.query(DailyContest).all()
        questions = db.query(ContestQuestion).count()
        courses = db.query(Course).filter(
            Course.code.in_(['CODING_PYTHON', 'CODING_DAA'])
        ).count()
        
        print(f'✅ Total Contests: {len(contests)}')
        print(f'✅ Total Questions: {questions}')
        print(f'✅ Coding Hour Courses: {courses}')
        
        if contests:
            print(f'\n📋 Sample Contest:')
            c = contests[0]
            print(f'  Date: {c.date}')
            print(f'  Title: {c.title}')
            print(f'  Questions: {len(c.questions)}')
            
            if c.questions:
                q = c.questions[0]
                print(f'\n  First Question:')
                print(f'    Title: {q.title}')
                print(f'    Languages: {list(q.code_snippets.keys())}')
        else:
            print('\n⚠️  No contests found. Run: python seed_contests.py')
            
    finally:
        db.close()

if __name__ == '__main__':
    verify_database()

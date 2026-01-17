from main import SessionLocal, Course, DailyContest, ContestQuestion

db = SessionLocal()
try:
    print("Verifying Coding Hour C update...")
    
    # Check Course
    course = db.query(Course).filter(Course.code == "CODING_C").first()
    if course:
        print(f"✅ Course Found: {course.name} ({course.code}) - {course.description}")
    else:
        print(f"❌ Course CODING_C NOT found!")
        
    # Check Contests
    if course:
        contests = db.query(DailyContest).filter(DailyContest.course_id == course.id).all()
        print(f"found {len(contests)} contests for CODING_C")
        for c in contests:
            print(f"  Contest: {c.title} ({c.date})")
            questions = db.query(ContestQuestion).filter(ContestQuestion.contest_id == c.id).all()
            for q in questions:
                print(f"    Q: {q.title}")
                print(f"       C Code present: {'c' in q.code_snippets}")
                # print(f"       Code keys: {list(q.code_snippets.keys())}")

finally:
    db.close()

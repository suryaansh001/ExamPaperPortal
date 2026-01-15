from main import SessionLocal, Course, DailyChallenge, Base, engine, User, get_password_hash
from datetime import datetime

def seed_data():
    session = SessionLocal()
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    # 1. Sync Sequence (Fix for User ID collision on Postgres)
    if engine.dialect.name == 'postgresql':
        print("Syncing primary key sequence for users table...")
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT setval(pg_get_serial_sequence('users', 'id'), coalesce(max(id),0) + 1, false) FROM users;"))
            conn.commit()

    # 1. Ensure Courses Exist
    courses_data = [
        {"code": "CODING_PYTHON", "name": "Coding Hour - python", "description": " Python coding challenges"},
        {"code": "CODING_DAA", "name": "Coding Hour DAA", "description": " Design and Analysis of Algorithms challenges"},
    ]

    created_courses = {}

    for c_data in courses_data:
        course = session.query(Course).filter(Course.code == c_data["code"]).first()
        if not course:
            course = Course(code=c_data["code"], name=c_data["name"], description=c_data["description"])
            session.add(course)
            session.commit()
            session.refresh(course)
            print(f"Created course: {course.name}")
        else:
            print(f"Course already exists: {course.name}")
        created_courses[c_data["code"]] = course.id

    # 2. Add Challenges for Python
    python_challenges = [
        {
            "date": "Day 1",
            "question": "Write a Python function to check if a number is prime.",
            "code": "def is_prime(n):\n    if n <= 1: return False\n    for i in range(2, int(n**0.5) + 1):\n        if n % i == 0:\n            return False\n    return True",
            "explanation": "We iterate from 2 to sqrt(n). If n is divisible by any number, it's not prime.",
            "media": "https://example.com/prime.pdf"
        },
        {
            "date": "Day 2",
            "question": "Reverse a string in Python.",
            "code": "s = 'hello'\nreversed_s = s[::-1]\nprint(reversed_s)",
            "explanation": "String slicing `[::-1]` creates a copy of the string in reverse order.",
            "media": None
        },
        {
            "date": "Day 3",
            "question": "Find factorial of a number using recursion.",
            "code": "def factorial(n):\n    return 1 if n == 0 else n * factorial(n-1)",
            "explanation": "Recursive base case is n=0 returning 1. Otherwise n * factorial(n-1).",
            "media": None
        },
        {
            "date": "Day 4",
            "question": "Check if a string is a palindrome.",
            "code": "def is_palindrome(s):\n    return s == s[::-1]",
            "explanation": "Compare the string with its reverse.",
            "media": None
        },
        {
            "date": "Day 5",
            "question": "Find the largest element in a list.",
            "code": "lst = [10, 20, 5, 40]\nprint(max(lst))",
            "explanation": "Use the built-in `max()` function.",
            "media": None
        }
    ]

    for data in python_challenges:
        exists = session.query(DailyChallenge).filter(DailyChallenge.course_id == created_courses["CODING_PYTHON"], DailyChallenge.date == data["date"]).first()
        if not exists:
            challenge = DailyChallenge(
                course_id=created_courses["CODING_PYTHON"],
                date=data["date"],
                question=data["question"],
                code_snippet=data["code"],
                explanation=data["explanation"],
                media_link=data["media"]
            )
            session.add(challenge)
            print(f"Added Python challenge: {data['date']}")
        else:
            print(f"Python challenge {data['date']} already exists")

    # 3. Add Challenges for DAA
    daa_challenges = [
        {
            "date": "Day 1",
            "question": "Implement Binary Search.",
            "code": "def binary_search(arr, target):\n    l, r = 0, len(arr)-1\n    while l <= r:\n        mid = (l + r) // 2\n        if arr[mid] == target: return mid\n        elif arr[mid] < target: l = mid + 1\n        else: r = mid - 1\n    return -1",
            "explanation": "Divide and conquer. Check middle element, adjust bounds.",
            "media": None
        },
        {
            "date": "Day 2",
            "question": "Implement Merge Sort.",
            "code": "# Merge sort implementation...",
            "explanation": "Recursively split array into halves and merge them sorted.",
            "media": None
        },
         {
            "date": "Day 3",
            "question": "Solve 0/1 Knapsack Problem.",
            "code": "# DP solution...",
            "explanation": "Use dynamic programming to maximize value within weight limit.",
            "media": None
        },
         {
            "date": "Day 4",
            "question": "Find shortest path using Dijkstra.",
            "code": "# Dijkstra algorithm...",
            "explanation": "Greedy approach using priority queue.",
            "media": None
        },
         {
            "date": "Day 5",
            "question": "Matrix Chain Multiplication.",
            "code": "# MCM DP...",
            "explanation": "Find most efficient way to multiply matrices.",
            "media": None
        }
    ]

    for data in daa_challenges:
        exists = session.query(DailyChallenge).filter(DailyChallenge.course_id == created_courses["CODING_DAA"], DailyChallenge.date == data["date"]).first()
        if not exists:
            challenge = DailyChallenge(
                course_id=created_courses["CODING_DAA"],
                date=data["date"],
                question=data["question"],
                code_snippet=data["code"],
                explanation=data["explanation"],
                media_link=data["media"]
            )
            session.add(challenge)
            print(f"Added DAA challenge: {data['date']}")
        else:
            print(f"DAA challenge {data['date']} already exists")

    
    # 4. Create Coding Hour Admin Users
    admin_users = [
        {"email": "coding_ta1@jklu.edu.in", "name": "Coding TA 1", "password": "ta1_password", "role": "coding_ta"},
        {"email": "coding_ta2@jklu.edu.in", "name": "Coding TA 2", "password": "ta2_password", "role": "coding_ta"},
    ]
    
    for a_data in admin_users:
        user = session.query(User).filter(User.email == a_data["email"]).first()
        if not user:
            user = User(
                email=a_data["email"],
                name=a_data["name"],
                password_hash=get_password_hash(a_data["password"]),
                is_admin=True,
                admin_role=a_data["role"],
                email_verified=True
            )
            session.add(user)
            print(f"Created Admin User: {a_data['email']} / {a_data['password']}")
        else:
            # Ensure existing user has correct role
            if user.admin_role != a_data["role"]:
                user.admin_role = a_data["role"]
                session.add(user)
                print(f"Updated role for {a_data['email']}")
            print(f"Admin User already exists: {a_data['email']}")

    session.commit()
    session.close()

if __name__ == "__main__":
    seed_data()

#!/usr/bin/env python3
"""
Seed script for creating sample DailyContest data with multi-language code support.
This demonstrates the new multi-question, multi-language format.
"""

from main import SessionLocal, Course, DailyContest, ContestQuestion, User, get_password_hash, Base, engine
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

def seed_contests():
    """Create sample contests with multiple questions and multi-language code"""
    db = SessionLocal()
    
    try:
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        # Sync sequence for PostgreSQL
        if engine.dialect.name == 'postgresql':
            print("Syncing primary key sequences...")
            with engine.connect() as conn:
                conn.execute(text("SELECT setval(pg_get_serial_sequence('users', 'id'), coalesce(max(id),0) + 1, false) FROM users;"))
                conn.commit()
        
        # Ensure courses exist
        courses_data = [
            {"code": "CODING_PYTHON", "name": "Coding Hour - python", "description": "Python coding challenges"},
            {"code": "CODING_DAA", "name": "Coding Hour DAA", "description": "Design and Analysis of Algorithms challenges"},
        ]
        
        created_courses = {}
        
        for c_data in courses_data:
            course = db.query(Course).filter(Course.code == c_data["code"]).first()
            if not course:
                course = Course(code=c_data["code"], name=c_data["name"], description=c_data["description"])
                db.add(course)
                db.commit()
                db.refresh(course)
                print(f"✅ Created course: {course.name}")
            else:
                print(f"⏭️  Course already exists: {course.name}")
            created_courses[c_data["code"]] = course.id
        
        # Create Python contests with multiple questions
        python_contests = [
            {
                "date": "Week 1 - Day 1",
                "title": "Python Basics",
                "description": "Introduction to Python fundamentals",
                "questions": [
                    {
                        "order": 1,
                        "title": "Check Prime Number",
                        "question": "Write a function to check if a number is prime.\n\nInput: An integer n\nOutput: True if prime, False otherwise",
                        "code_snippets": {
                            "python": "def is_prime(n):\n    if n <= 1:\n        return False\n    for i in range(2, int(n**0.5) + 1):\n        if n % i == 0:\n            return False\n    return True\n\n# Test\nprint(is_prime(17))  # True\nprint(is_prime(4))   # False",
                            "c": "#include <stdio.h>\n#include <math.h>\n#include <stdbool.h>\n\nbool is_prime(int n) {\n    if (n <= 1) return false;\n    for (int i = 2; i <= sqrt(n); i++) {\n        if (n % i == 0) return false;\n    }\n    return true;\n}\n\nint main() {\n    printf(\"%d\\n\", is_prime(17));  // 1 (true)\n    printf(\"%d\\n\", is_prime(4));   // 0 (false)\n    return 0;\n}",
                            "cpp": "#include <iostream>\n#include <cmath>\nusing namespace std;\n\nbool is_prime(int n) {\n    if (n <= 1) return false;\n    for (int i = 2; i <= sqrt(n); i++) {\n        if (n % i == 0) return false;\n    }\n    return true;\n}\n\nint main() {\n    cout << is_prime(17) << endl;  // 1 (true)\n    cout << is_prime(4) << endl;   // 0 (false)\n    return 0;\n}"
                        },
                        "explanation": "**Approach:**\n1. Numbers ≤ 1 are not prime\n2. Check divisibility from 2 to √n\n3. If any number divides n, it's not prime\n\n**Time Complexity:** O(√n)\n**Space Complexity:** O(1)",
                        "media_link": None
                    },
                    {
                        "order": 2,
                        "title": "Reverse a String",
                        "question": "Write a function to reverse a string.\n\nInput: A string s\nOutput: Reversed string",
                        "code_snippets": {
                            "python": "def reverse_string(s):\n    return s[::-1]\n\n# Alternative using loop\ndef reverse_string_loop(s):\n    result = \"\"\n    for char in s:\n        result = char + result\n    return result\n\n# Test\nprint(reverse_string(\"hello\"))  # \"olleh\"",
                            "c": "#include <stdio.h>\n#include <string.h>\n\nvoid reverse_string(char *s) {\n    int len = strlen(s);\n    for (int i = 0; i < len/2; i++) {\n        char temp = s[i];\n        s[i] = s[len-1-i];\n        s[len-1-i] = temp;\n    }\n}\n\nint main() {\n    char str[] = \"hello\";\n    reverse_string(str);\n    printf(\"%s\\n\", str);  // \"olleh\"\n    return 0;\n}"
                        },
                        "explanation": "**Python Approach:**\n- Use slicing `[::-1]` for simplicity\n- Or build string in reverse order\n\n**C Approach:**\n- Swap characters from both ends\n- Move towards center\n\n**Time Complexity:** O(n)\n**Space Complexity:** O(1) for in-place",
                        "media_link": None
                    }
                ]
            },
            {
                "date": "Week 1 - Day 2",
                "title": "Recursion Basics",
                "description": "Understanding recursive functions",
                "questions": [
                    {
                        "order": 1,
                        "title": "Factorial using Recursion",
                        "question": "Calculate factorial of a number using recursion.\n\nInput: Non-negative integer n\nOutput: n! (factorial of n)",
                        "code_snippets": {
                            "python": "def factorial(n):\n    # Base case\n    if n == 0 or n == 1:\n        return 1\n    # Recursive case\n    return n * factorial(n - 1)\n\n# Test\nprint(factorial(5))  # 120\nprint(factorial(0))  # 1",
                            "cpp": "#include <iostream>\nusing namespace std;\n\nint factorial(int n) {\n    if (n == 0 || n == 1)\n        return 1;\n    return n * factorial(n - 1);\n}\n\nint main() {\n    cout << factorial(5) << endl;  // 120\n    cout << factorial(0) << endl;  // 1\n    return 0;\n}"
                        },
                        "explanation": "**Recursion Structure:**\n1. **Base case:** n = 0 or 1 returns 1\n2. **Recursive case:** n * factorial(n-1)\n\n**Example:** factorial(5)\n- 5 * factorial(4)\n- 5 * 4 * factorial(3)\n- 5 * 4 * 3 * factorial(2)\n- 5 * 4 * 3 * 2 * factorial(1)\n- 5 * 4 * 3 * 2 * 1 = 120\n\n**Time Complexity:** O(n)\n**Space Complexity:** O(n) due to call stack",
                        "media_link": None
                    }
                ]
            }
        ]
        
        # Create DAA contests
        daa_contests = [
            {
                "date": "Week 1 - Day 1",
                "title": "Searching Algorithms",
                "description": "Binary Search and Linear Search",
                "questions": [
                    {
                        "order": 1,
                        "title": "Binary Search",
                        "question": "Implement binary search on a sorted array.\n\nInput: Sorted array arr, target value\nOutput: Index of target, or -1 if not found",
                        "code_snippets": {
                            "python": "def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    \n    while left <= right:\n        mid = (left + right) // 2\n        \n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    \n    return -1\n\n# Test\narr = [1, 3, 5, 7, 9, 11]\nprint(binary_search(arr, 7))   # 3\nprint(binary_search(arr, 4))   # -1",
                            "c": "#include <stdio.h>\n\nint binary_search(int arr[], int n, int target) {\n    int left = 0, right = n - 1;\n    \n    while (left <= right) {\n        int mid = left + (right - left) / 2;\n        \n        if (arr[mid] == target)\n            return mid;\n        else if (arr[mid] < target)\n            left = mid + 1;\n        else\n            right = mid - 1;\n    }\n    \n    return -1;\n}\n\nint main() {\n    int arr[] = {1, 3, 5, 7, 9, 11};\n    int n = 6;\n    printf(\"%d\\n\", binary_search(arr, n, 7));   // 3\n    printf(\"%d\\n\", binary_search(arr, n, 4));   // -1\n    return 0;\n}",
                            "cpp": "#include <iostream>\nusing namespace std;\n\nint binary_search(int arr[], int n, int target) {\n    int left = 0, right = n - 1;\n    \n    while (left <= right) {\n        int mid = left + (right - left) / 2;\n        \n        if (arr[mid] == target)\n            return mid;\n        else if (arr[mid] < target)\n            left = mid + 1;\n        else\n            right = mid - 1;\n    }\n    \n    return -1;\n}\n\nint main() {\n    int arr[] = {1, 3, 5, 7, 9, 11};\n    int n = 6;\n    cout << binary_search(arr, n, 7) << endl;   // 3\n    cout << binary_search(arr, n, 4) << endl;   // -1\n    return 0;\n}"
                        },
                        "explanation": "**Binary Search Algorithm:**\n1. Start with left=0, right=n-1\n2. Calculate mid = (left + right) / 2\n3. If arr[mid] == target, return mid\n4. If arr[mid] < target, search right half\n5. If arr[mid] > target, search left half\n6. Repeat until found or left > right\n\n**Key Points:**\n- Array must be sorted\n- Divide and conquer approach\n- Eliminates half the search space each iteration\n\n**Time Complexity:** O(log n)\n**Space Complexity:** O(1)",
                        "media_link": None
                    }
                ]
            }
        ]
        
        # Insert Python contests
        for contest_data in python_contests:
            try:
                existing = db.query(DailyContest).filter(
                    DailyContest.date == contest_data["date"],
                    DailyContest.course_id == created_courses["CODING_PYTHON"]
                ).first()
                
                if existing:
                    print(f"⏭️  Contest already exists: {contest_data['date']}")
                    continue
                
                contest = DailyContest(
                    course_id=created_courses["CODING_PYTHON"],
                    date=contest_data["date"],
                    title=contest_data["title"],
                    description=contest_data["description"]
                )
                db.add(contest)
                db.flush()
                
                for q_data in contest_data["questions"]:
                    question = ContestQuestion(
                        contest_id=contest.id,
                        order=q_data["order"],
                        title=q_data["title"],
                        question=q_data["question"],
                        code_snippets=q_data["code_snippets"],
                        explanation=q_data["explanation"],
                        media_link=q_data["media_link"]
                    )
                    db.add(question)
                
                db.commit()  # Commit each contest separately
                print(f"✅ Created Python contest: {contest_data['date']} with {len(contest_data['questions'])} questions")
            except IntegrityError as e:
                db.rollback()
                print(f"⏭️  Skipping Python contest {contest_data['date']}: already exists or conflict")
                continue
            except Exception as e:
                db.rollback()
                print(f"❌ Error creating Python contest {contest_data['date']}: {e}")
                continue
        
        # Insert DAA contests
        for contest_data in daa_contests:
            try:
                existing = db.query(DailyContest).filter(
                    DailyContest.date == contest_data["date"],
                    DailyContest.course_id == created_courses["CODING_DAA"]
                ).first()
                
                if existing:
                    print(f"⏭️  Contest already exists: {contest_data['date']}")
                    continue
                
                contest = DailyContest(
                    course_id=created_courses["CODING_DAA"],
                    date=contest_data["date"],
                    title=contest_data["title"],
                    description=contest_data["description"]
                )
                db.add(contest)
                db.flush()
                
                for q_data in contest_data["questions"]:
                    question = ContestQuestion(
                        contest_id=contest.id,
                        order=q_data["order"],
                        title=q_data["title"],
                        question=q_data["question"],
                        code_snippets=q_data["code_snippets"],
                        explanation=q_data["explanation"],
                        media_link=q_data["media_link"]
                    )
                    db.add(question)
                
                db.commit()  # Commit each DAA contest separately
                print(f"✅ Created DAA contest: {contest_data['date']} with {len(contest_data['questions'])} questions")
            except IntegrityError as e:
                db.rollback()
                print(f"⏭️  Skipping DAA contest {contest_data['date']}: already exists or conflict")
                continue
            except Exception as e:
                db.rollback()
                print(f"❌ Error creating DAA contest {contest_data['date']}: {e}")
                continue
        
        # Create coding TA users
        admin_users = [
            {"email": "coding_ta1@jklu.edu.in", "name": "Coding TA 1", "password": "ta1_password", "role": "coding_ta"},
            {"email": "coding_ta2@jklu.edu.in", "name": "Coding TA 2", "password": "ta2_password", "role": "coding_ta"},
        ]
        
        for a_data in admin_users:
            user = db.query(User).filter(User.email == a_data["email"]).first()
            if not user:
                user = User(
                    email=a_data["email"],
                    name=a_data["name"],
                    password_hash=get_password_hash(a_data["password"]),
                    is_admin=True,
                    admin_role=a_data["role"],
                    email_verified=True
                )
                db.add(user)
                print(f"✅ Created Admin User: {a_data['email']} / {a_data['password']}")
            else:
                if user.admin_role != a_data["role"]:
                    user.admin_role = a_data["role"]
                    db.add(user)
                    print(f"✅ Updated role for {a_data['email']}")
                print(f"⏭️  Admin User already exists: {a_data['email']}")
        
        db.commit()
        print("\n✅ Seed data created successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🌱 Seeding contest data...\n")
    seed_contests()

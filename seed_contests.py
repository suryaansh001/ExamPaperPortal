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
            {"code": "CODING_C", "name": "Coding Hour C", "description": "Weekly C coding challenges"},
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
        
        # Create C contests with multiple questions
        c_contests = [
            {
                "date": "Week 1",
                "title": "C Fundamentals",
                "description": "Introduction to C programming basics",
                "questions": [
                    {
                        "order": 1,
                        "title": "Check Prime Number",
                        "question": "Write a C function to check if a number is prime.\n\nInput: An integer n\nOutput: 1 (true) if prime, 0 (false) otherwise",
                        "code_snippets": {
                            "c": "#include <stdio.h>\n#include <math.h>\n#include <stdbool.h>\n\nbool is_prime(int n) {\n    if (n <= 1) return false;\n    for (int i = 2; i <= sqrt(n); i++) {\n        if (n % i == 0) return false;\n    }\n    return true;\n}\n\nint main() {\n    printf(\"%d\\n\", is_prime(17));  // 1 (true)\n    printf(\"%d\\n\", is_prime(4));   // 0 (false)\n    return 0;\n}"
                        },
                        "explanation": "**Approach:**\n1. Numbers <= 1 are not prime\n2. Check divisibility from 2 to sqrt(n)\n3. If any number divides n, it's not prime\n\n**Time Complexity:** O(sqrt(n))\n**Space Complexity:** O(1)",
                        "media_link": None
                    },
                    {
                        "order": 2,
                        "title": "Reverse a String",
                        "question": "Write a C function to reverse a string in-place.\n\nInput: A string s\nOutput: Reversed string",
                        "code_snippets": {
                            "c": "#include <stdio.h>\n#include <string.h>\n\nvoid reverse_string(char *s) {\n    int len = strlen(s);\n    for (int i = 0; i < len/2; i++) {\n        char temp = s[i];\n        s[i] = s[len-1-i];\n        s[len-1-i] = temp;\n    }\n}\n\nint main() {\n    char str[] = \"hello\";\n    reverse_string(str);\n    printf(\"%s\\n\", str);  // \"olleh\"\n    return 0;\n}"
                        },
                        "explanation": "**Approach:**\n- Swap characters from both ends\n- Move towards center\n\n**Time Complexity:** O(n)\n**Space Complexity:** O(1) for in-place",
                        "media_link": None
                    }
                ]
            },
            {
                "date": "Week 2",
                "title": "Pointers and Arrays",
                "description": "Understanding pointers and memory",
                "questions": [
                    {
                        "order": 1,
                        "title": "Array Reversal using Pointers",
                        "question": "Reverse an array using pointers.\n\nInput: Array of integers\nOutput: Reversed array",
                        "code_snippets": {
                            "c": "#include <stdio.h>\n\nvoid reverse_array(int *arr, int size) {\n    int *start = arr;\n    int *end = arr + size - 1;\n    while (start < end) {\n        int temp = *start;\n        *start = *end;\n        *end = temp;\n        start++;\n        end--;\n    }\n}\n\nint main() {\n    int arr[] = {1, 2, 3, 4, 5};\n    int n = 5;\n    reverse_array(arr, n);\n    for(int i=0; i<n; i++) printf(\"%d \", arr[i]);\n    return 0;\n}"
                        },
                        "explanation": "Use two pointers, one at start and one at end. Swap values and move pointers until they meet.",
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
        
        # Insert C contests
        for contest_data in c_contests:
            try:
                existing = db.query(DailyContest).filter(
                    DailyContest.date == contest_data["date"],
                    DailyContest.course_id == created_courses["CODING_C"]
                ).first()
                
                if existing:
                    print(f"⏭️  Contest already exists: {contest_data['date']}")
                    continue
                
                contest = DailyContest(
                    course_id=created_courses["CODING_C"],
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
                print(f"✅ Created C contest: {contest_data['date']} with {len(contest_data['questions'])} questions")
            except IntegrityError as e:
                db.rollback()
                print(f"⏭️  Skipping C contest {contest_data['date']}: already exists or conflict")
                continue
            except Exception as e:
                db.rollback()
                print(f"❌ Error creating C contest {contest_data['date']}: {e}")
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

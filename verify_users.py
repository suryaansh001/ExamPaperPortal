
try:
    from main import SessionLocal, User, engine
    from sqlalchemy import text
except ImportError:
    import sys
    import os
    # Add parent directory to path to allow importing main
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from main import SessionLocal, User, engine
    from sqlalchemy import text

def verify_users():
    session = SessionLocal()
    try:
        print("Checking for coding_ta users...")
        users = session.query(User).filter(User.admin_role == 'coding_ta').all()
        
        if not users:
            print("No users found with admin_role = 'coding_ta'")
        
        for user in users:
            print(f"User: {user.email}")
            print(f"  Name: {user.name}")
            print(f"  Role: {user.admin_role}")
            print(f"  Is Admin: {user.is_admin}")
            print("-" * 20)
            
        print("\nChecking specifically for coding_ta1 and coding_ta2...")
        specific_emails = ["coding_ta1@jklu.edu.in", "coding_ta2@jklu.edu.in"]
        for email in specific_emails:
            user = session.query(User).filter(User.email == email).first()
            if user:
                print(f"User {email} FOUND:")
                print(f"  Role: {user.admin_role}")
                print(f"  Is Admin: {user.is_admin}")
            else:
                print(f"User {email} NOT FOUND")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    verify_users()

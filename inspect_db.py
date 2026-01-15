from main import SessionLocal, User, Course, DailyChallenge, engine
from sqlalchemy import inspect

def inspect_db():
    session = SessionLocal()
    try:
        inspector = inspect(engine)
        
        print("\n=== Table Schema: users ===")
        columns = inspector.get_columns('users')
        column_names = [c['name'] for c in columns]
        print(f"Columns: {column_names}")
        
        required_columns = ['admin_role', 'photo_data', 'id_card_data']
        for col in required_columns:
            if col in column_names:
                print(f"✅ Column '{col}' exists.")
            else:
                print(f"❌ Column '{col}' MISSING!")

        print("\n=== Users List ===")
        users = session.query(User).all()
        for u in users:
            role_str = f" ({u.admin_role})" if u.admin_role else ""
            print(f"ID: {u.id}, Email: {u.email}, Name: {u.name}, Admin: {u.is_admin}{role_str}")

        print("\n=== Courses List ===")
        courses = session.query(Course).all()
        for c in courses:
            print(f"ID: {c.id}, Code: {c.code}, Name: {c.name}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    inspect_db()

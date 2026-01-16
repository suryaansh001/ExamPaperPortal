from main import DATABASE_URL, SessionLocal, DailyContest
from dotenv import load_dotenv
import os

# Ensure clean env load just in case (though main does it)
load_dotenv()

EXPECTED_URL = 'postgresql://postgres:QDGGiRSmLDjVeFCRLxbyaTGdUhAGplia@switchyard.proxy.rlwy.net:59511/railway'

print(f"--- Configuration Check ---")
print(f"Loaded DATABASE_URL matches user provided: {DATABASE_URL == EXPECTED_URL}")
if DATABASE_URL != EXPECTED_URL:
    print(f"Loaded: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'HIDDEN'}")
    print(f"Expect: {EXPECTED_URL.split('@')[-1]}")
else:
    print("URL matches correctly.")

print(f"\n--- Database Content Check ---")
try:
    db = SessionLocal()
    count = db.query(DailyContest).count()
    print(f"Row count in 'daily_contests': {count}")
    
    if count > 0:
        print("Sample data:")
        for c in db.query(DailyContest).all():
            print(f" - {c.date} (ID: {c.id})")
    
    db.close()
except Exception as e:
    print(f"Connection failed: {e}")

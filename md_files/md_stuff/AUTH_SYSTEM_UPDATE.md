# Authentication System Update - Implementation Guide

## Overview
The system now supports **dual authentication**:
- **Students**: Email-based OTP verification (passwordless)
- **Admins**: Traditional email + password login

## Database Changes

### User Model Updates
The `User` model now includes an `email_verified` field:

```python
class User(Base):
    # ... existing fields ...
    email_verified = Column(Boolean, default=False)
```

### Migration Steps

**If you have an existing database:**

1. **Add the new column to existing users table:**
```sql
ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;

-- Update existing admins to verified
UPDATE users SET email_verified = TRUE WHERE is_admin = TRUE;
```

2. **Or drop and recreate the database (DEVELOPMENT ONLY - will lose data):**
```bash
# Connect to PostgreSQL
psql -U user -d paper_portal

# Drop all tables
DROP TABLE papers CASCADE;
DROP TABLE courses CASCADE;
DROP TABLE users CASCADE;

# Exit psql
\q

# Run setup script to recreate everything
python setup.py
```

## Authentication Flow

### Student Authentication (OTP-based)

1. **Frontend Route**: `/login` → Uses `OTPVerification.tsx`
2. **Backend Endpoints**:
   - `POST /send-otp` - Send 6-digit OTP to email
   - `POST /verify-otp` - Verify OTP and create/login user

**Flow:**
```
Student → Enter Email → Receive OTP → Enter OTP → Auto-login → Dashboard
```

**Key Features:**
- No password required for students
- OTP expires in 10 minutes
- Email automatically verified upon successful OTP verification
- Creates new user if doesn't exist
- Prevents admins from using OTP login

### Admin Authentication (Password-based)

1. **Frontend Route**: `/admin-login` → Uses `AdminLogin.tsx`
2. **Backend Endpoint**: `POST /admin-login`

**Flow:**
```
Admin → Enter Email + Password → Verify credentials → Admin Dashboard
```

**Key Features:**
- Traditional email/password login
- Only users with `is_admin=True` can use this endpoint
- Pre-verified (email_verified=True by default)
- Cannot use OTP verification system

## API Endpoints

### Public Access (No Auth)
- `GET /` - API info
- `GET /papers/public/all` - Browse approved papers

### Student Authentication
- `POST /send-otp` - Request OTP
  ```json
  {
    "email": "student@example.com"
  }
  ```
- `POST /verify-otp` - Verify OTP and login
  ```json
  {
    "email": "student@example.com",
    "otp": "123456"
  }
  ```

### Admin Authentication
- `POST /admin-login` - Admin login (form-urlencoded)
  ```
  username=admin@university.edu
  password=admin123
  ```

### Legacy (Still works for backward compatibility)
- `POST /login` - Traditional login for any user
- `POST /register` - Create new user (not recommended for students)

## Email Configuration

### Current Implementation (Console Output)
OTP is currently printed to the console for demo purposes:

```python
print(f"\n{'='*50}")
print(f"OTP for {email}: {otp}")
print(f"{'='*50}\n")
```

### Production Setup (SMTP)

**Environment Variables** (`.env` file):
```env
# SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-specific-password
```

**Enable Email Sending:**
Uncomment in `main.py` → `send_otp_email()`:
```python
with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.send_message(message)
```

### Using Celery for Email Tasks (Recommended for Production)

**Why Celery?**
- Non-blocking email sending
- Retry failed emails
- Better scalability
- Background task processing

**Setup Instructions:**

1. **Install Dependencies:**
```bash
pip install celery redis
```

2. **Install Redis:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# macOS
brew install redis
brew services start redis

# Or use Docker
docker run -d -p 6379:6379 redis:alpine
```

3. **Create `celery_app.py`:**
```python
from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

celery_app = Celery(
    'paper_portal',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)
```

4. **Create `tasks.py`:**
```python
from celery_app import celery_app
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

@celery_app.task(bind=True, max_retries=3)
def send_otp_email_task(self, email: str, otp: str):
    """
    Celery task to send OTP email asynchronously
    """
    try:
        message = MIMEMultipart()
        message["From"] = SENDER_EMAIL
        message["To"] = email
        message["Subject"] = "Your Paper Portal Verification Code"
        
        body = f"""
        <html>
            <body>
                <h2>Paper Portal - Email Verification</h2>
                <p>Your verification code is:</p>
                <h1 style="color: #007bff; letter-spacing: 5px;">{otp}</h1>
                <p>This code will expire in 10 minutes.</p>
                <p>If you didn't request this code, please ignore this email.</p>
            </body>
        </html>
        """
        
        message.attach(MIMEText(body, "html"))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(message)
        
        return {"status": "success", "email": email}
    
    except Exception as exc:
        # Retry in 60 seconds if failed
        raise self.retry(exc=exc, countdown=60)
```

5. **Update `main.py` to use Celery:**
```python
# Import the task
from tasks import send_otp_email_task

# Modify send_otp_email function
def send_otp_email(email: str, otp: str):
    """Queue OTP email to be sent via Celery"""
    try:
        # Console output for demo
        print(f"\n{'='*50}")
        print(f"OTP for {email}: {otp}")
        print(f"{'='*50}\n")
        
        # Queue the email task (non-blocking)
        send_otp_email_task.delay(email, otp)
        
        return True
    except Exception as e:
        print(f"Failed to queue email: {e}")
        return False
```

6. **Run Celery Worker:**
```bash
# In a separate terminal
celery -A celery_app worker --loglevel=info
```

7. **Update `.env`:**
```env
# Add Celery configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Frontend Routes

| Route | Component | Purpose | Auth Required |
|-------|-----------|---------|---------------|
| `/` | PublicHome | Browse papers | No |
| `/login` | OTPVerification | Student login | No |
| `/admin-login` | AdminLogin | Admin login | No |
| `/dashboard` | StudentDashboard | Submit papers | Yes (Student) |
| `/admin` | AdminDashboard | Review/manage | Yes (Admin) |

## Testing the System

### Test Student OTP Login:

1. Go to `http://localhost:5173/login`
2. Enter any email (e.g., `test@student.com`)
3. Check console for OTP: `OTP for test@student.com: 123456`
4. Enter the OTP code
5. Should auto-login and redirect to student dashboard

### Test Admin Login:

1. Go to `http://localhost:5173/admin-login`
2. Use credentials:
   - Email: `admin@university.edu`
   - Password: `admin123`
3. Should redirect to admin dashboard

### Create New Admin:

```python
# Run in Python shell
from setup import create_admin_user
create_admin_user("newadmin@university.edu", "New Admin", "securepass123")
```

## Security Considerations

1. **OTP Storage**: Currently in-memory dict. Use Redis for production:
   ```python
   import redis
   redis_client = redis.Redis(host='localhost', port=6379, db=1)
   
   # Store OTP
   redis_client.setex(
       f"otp:{email}",
       600,  # 10 minutes
       otp
   )
   ```

2. **Rate Limiting**: Add rate limiting to prevent OTP spam:
   ```bash
   pip install slowapi
   ```

3. **Email Verification**: OTP system provides email verification. Admin accounts are pre-verified.

4. **Password Strength**: Enforce strong passwords for admins.

## Troubleshooting

### Database Errors
```bash
# Check if email_verified column exists
psql -U user -d paper_portal -c "\d users"

# If missing, add it:
psql -U user -d paper_portal -c "ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;"
```

### OTP Not Sending
- Check console output (demo mode)
- Verify SMTP credentials in `.env`
- Uncomment SMTP code in `send_otp_email()`

### Admin Can't Login
- Verify `is_admin=True` in database
- Ensure using `/admin-login` endpoint, not `/login`
- Check password hash matches

### Student Can't Use OTP
- Verify email is not an admin account
- Check OTP hasn't expired (10 min)
- Ensure OTP matches exactly (6 digits)

## Summary of Changes

✅ **Backend:**
- Added `/admin-login` endpoint for admins
- Modified `/verify-otp` to prevent admin access
- Added `email_verified` field to User model
- Updated OTP verification flow

✅ **Frontend:**
- Created `AdminLogin.tsx` component
- Updated `App.tsx` with `/admin-login` route
- Modified `OTPVerification.tsx` with admin login link
- Updated `PublicHome.tsx` header with both login options

✅ **Database:**
- Added `email_verified` column to users table
- Updated `setup.py` to set verification status

✅ **Documentation:**
- Complete authentication flow documentation
- Celery setup guide for production emails
- Security best practices

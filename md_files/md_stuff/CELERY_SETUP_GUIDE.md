# Paper Portal - Celery Email Setup Guide

This document explains how to set up and run the Paper Portal system with Celery for asynchronous email sending.

## Prerequisites

- Python 3.9+
- PostgreSQL (for database)
- Redis (for Celery broker and result backend)
- Gmail account with App Password enabled

## System Architecture

```
┌─────────────────┐
│   FastAPI App   │  main.py
└────────┬────────┘
         │
         ├──→ Tasks Queue (Redis)
         │
    ┌────┴────────────┬──────────────┐
    │                 │              │
┌───▼────┐      ┌──────▼──────┐  ┌──▼────────┐
│ Celery │      │   Console   │  │   Redis   │
│ Worker │      │   Output    │  │  Database │
└────────┘      └─────────────┘  └───────────┘
```

## Setup Instructions

### 1. Install Dependencies

```bash
# Create and activate virtual environment
python -m venv exams
source exams/bin/activate  # On Windows: exams\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 2. Setup Redis

Redis is required to queue email tasks. You have three options:

#### Option A: Install Redis Locally (Linux/Mac)
```bash
# macOS with Homebrew
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server
```

#### Option B: Use Docker
```bash
docker run -d -p 6379:6379 redis:latest
```

#### Option C: Use Redis Cloud (Cloud Hosting)
1. Go to https://redis.com/try-free/
2. Create a free Redis instance
3. Copy the connection URL and add to `.env`:
   ```
   CELERY_BROKER_URL="redis://user:password@host:port/0"
   CELERY_RESULT_BACKEND="redis://user:password@host:port/0"
   ```

### 3. Configure Gmail Credentials

1. **Enable 2-Factor Authentication** on your Gmail account:
   - Go to https://myaccount.google.com/
   - Navigate to Security → 2-Step Verification

2. **Generate App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer" (or your device)
   - Generate and copy the 16-character password

3. **Update `.env` file**:
   ```env
   GMAIL_USER="your-email@gmail.com"
   GMAIL_PASS="xxxx xxxx xxxx xxxx"  # The 16-character app password (spaces included)
   ```

### 4. Setup Database

```bash
# Update DATABASE_URL in .env if needed
# Default: postgresql://postgres:secure123@localhost:5432/exam_paper_portal

# The app auto-creates tables on first run
# Ensure PostgreSQL is running and database exists
```

## Running the Application

### Terminal 1: Start Celery Worker

```bash
# Activate virtual environment
source exams/bin/activate

# Start Celery worker
celery -A tasks worker --loglevel=info
```

You should see output like:
```
 -------------- celery@your-machine v5.5.3 (vineyard)
--- ***** -----
-- ******* ----
- *** --- * ---
- ** ---------- [config]
- ** ----------
- *** --- * --- OS:   Linux-5.10.0
- ** ---------- Broker:   redis://localhost:6379/0
- *** --- * --- Workers:  1
-- ******* ----   Tasks:   2
--- ***** -----
```

### Terminal 2: Start FastAPI Server

```bash
# Activate virtual environment
source exams/bin/activate

# Start FastAPI with Uvicorn
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Application startup complete
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Terminal 3: Start Frontend Development Server

```bash
cd frontend
npm install
npm run dev
```

## Using the Application

### 1. Student Registration via OTP

**Flow:**
```
Student → Email → Send OTP → FastAPI → Celery Queue → Email Sent
                 ↓
             (Async Processing)
                 ↓
            Console Output (Demo) / Gmail (Production)
```

**API Endpoint - Send OTP:**
```bash
POST /send-otp
Content-Type: application/json

{
  "email": "student@example.com"
}

Response:
{
  "message": "OTP sent to your email",
  "email": "student@example.com"
}
```

Check the **Celery Worker terminal** for OTP output:
```
[2024-11-02 10:30:00,000: INFO/MainProcess] Task tasks.send_otp_email_task[xxxxx] received
[2024-11-02 10:30:05,000: INFO/MainProcess] Task tasks.send_otp_email_task[xxxxx] succeeded
```

**API Endpoint - Verify OTP:**
```bash
POST /verify-otp
Content-Type: application/json

{
  "email": "student@example.com",
  "otp": "123456"
}

Response:
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "student@example.com",
    "name": "student",
    "is_admin": false,
    "email_verified": true
  }
}
```

### 2. Admin Login

```bash
POST /admin-login
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "admin_password"
}

Response:
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 2,
    "email": "admin@example.com",
    "name": "Admin User",
    "is_admin": true,
    "email_verified": true
  }
}
```

## Monitoring Celery Tasks

### View Tasks in Console

The Celery worker shows real-time task execution:

```
[2024-11-02 10:30:00,000: INFO/MainProcess] Received task: tasks.send_otp_email_task[xxxxx]
[2024-11-02 10:30:02,000: INFO/Task] Sending OTP to student@example.com
[2024-11-02 10:30:03,000: INFO/MainProcess] Task succeeded
```

### View Task Logs

Celery saves logs. Access via:
```bash
# Show last 100 lines of celery logs
tail -100 celery.log
```

### Optional: Flower (Web UI for Celery Monitoring)

For production monitoring, install Flower:

```bash
pip install flower

# Run Flower (starts on http://localhost:5555)
celery -A tasks flower
```

## Environment Variables Reference

**`.env` file structure:**

```env
# Database
DATABASE_URL='postgresql://postgres:secure123@localhost:5432/exam_paper_portal'
SECRET_KEY='your-secret-key-here'

# File Upload
UPLOAD_DIR='uploads'
MAX_UPLOAD_SIZE=10485760

# Gmail Configuration
GMAIL_USER="your-email@gmail.com"
GMAIL_PASS="xxxx xxxx xxxx xxxx"
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT="587"

# Celery / Redis Configuration
CELERY_BROKER_URL="redis://localhost:6379/0"
CELERY_RESULT_BACKEND="redis://localhost:6379/0"
```

## Troubleshooting

### 1. "Connection refused: [Errno 111] Connection refused"

**Problem:** Celery can't connect to Redis

**Solution:**
```bash
# Check if Redis is running
redis-cli ping  # Should return PONG

# If not running, start Redis
redis-server

# Or with Docker
docker ps  # Check if Redis container is running
```

### 2. "GMAIL_USER and GMAIL_PASS environment variables must be set"

**Problem:** Email credentials missing

**Solution:**
1. Verify `.env` file exists in project root
2. Check GMAIL_USER and GMAIL_PASS are set correctly
3. Restart FastAPI server after updating `.env`

### 3. "SMTPAuthenticationError: [Gmail] Please log in via your web browser"

**Problem:** Gmail blocked the login attempt

**Solution:**
1. Go to https://myaccount.google.com/device-activity/security-event
2. Allow the access attempt
3. Ensure you're using **App Password** (16 characters), not regular password
4. Re-generate app password if needed

### 4. OTP received but email not sent

**Problem:** Celery task queued but email not sent

**Check:**
1. Celery worker terminal - does it show task received?
2. Gmail credentials correct?
3. Internet connection available?
4. Gmail account not blocked by security policy?

**Debugging:**
```bash
# Check Celery task status
celery -A tasks inspect active  # Show active tasks
celery -A tasks inspect registered  # Show registered tasks
```

### 5. Celery Worker Won't Start

**Problem:** "No module named 'tasks'"

**Solution:**
```bash
# Ensure you're in the correct directory
cd /home/sury/proj/CouncilProjects/examsystem

# Verify tasks.py exists
ls -la tasks.py

# Activate virtual environment
source exams/bin/activate

# Start worker from project root
celery -A tasks worker --loglevel=info
```

## Deployment Considerations

### Development Mode (Current Setup)
- ✅ Console output for OTP display
- ✅ Automatic email retry (max 3 times)
- ✅ Redis local broker
- ✅ Gmail SMTP for actual email sending

### Production Mode

For production deployment:

1. **Use Cloud Redis** (AWS ElastiCache, Redis Cloud, etc.)
2. **Configure Email Service**:
   - Option A: Use SendGrid API (replace SMTP)
   - Option B: Use AWS SES
   - Option C: Use dedicated mail server
3. **Set up Monitoring**: Use Flower or New Relic
4. **Database**: Use managed PostgreSQL (AWS RDS, etc.)
5. **Environment**: Use `.env` from secrets manager (AWS Secrets Manager, etc.)

Example production `.env`:
```env
DATABASE_URL='postgresql://prod_user:prod_pass@prod-db.rds.amazonaws.com/exam_portal'
SECRET_KEY='long-random-string-for-production'
CELERY_BROKER_URL='redis://redis-prod.elasticache.amazonaws.com:6379/0'
CELERY_RESULT_BACKEND='redis://redis-prod.elasticache.amazonaws.com:6379/0'
GMAIL_USER='noreply@example.com'
GMAIL_PASS='secure-app-password'
```

## API Flow Diagram

```
┌─────────────┐
│   Student   │
└──────┬──────┘
       │
       ├─ POST /send-otp
       │  └─→ FastAPI queues task
       │      └─→ Celery worker receives
       │          └─→ Sends email (async)
       │              └─→ Prints OTP to console (demo)
       │
       ├─ Check console for OTP
       │
       └─ POST /verify-otp
          └─→ FastAPI validates OTP
              └─→ Creates/Updates user
                  └─→ Returns JWT token
```

## Additional Resources

- [Celery Documentation](https://docs.celeryproject.io/)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Redis Documentation](https://redis.io/documentation)
- [Gmail App Passwords](https://support.google.com/accounts/answer/185833)

## Next Steps

1. ✅ Complete basic Celery setup
2. ✅ Test OTP email functionality
3. ⏭️ Set up production email service (SendGrid/AWS SES)
4. ⏭️ Configure monitoring (Flower)
5. ⏭️ Deploy to cloud platform

# Paper Portal - Quick Setup Guide

## Overview

Paper Portal is a web application for managing and browsing academic papers. It features:
- ✅ Public paper browsing (no login required)
- ✅ Student email-based OTP verification
- ✅ Admin paper management and approval
- ✅ Paper upload with flexible course/year selection
- ✅ Direct Gmail SMTP email support (no Celery/Redis needed)

## Prerequisites

- **Python 3.9+**
- **PostgreSQL 12+**
- **Node.js 18+** and npm
- **Gmail account** (for OTP emails)

## Step 1: Gmail Setup (for Testing Email OTP)

### Option A: Testing with Console Output (No Gmail Needed)
- OTP codes will print to FastAPI console
- No email sending required
- Perfect for development/testing

### Option B: Actual Email Sending via Gmail

1. **Enable 2-Factor Authentication**:
   - Go to https://myaccount.google.com/
   - Navigate to Security → 2-Step Verification → Enable

2. **Generate App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer"
   - Google will show a 16-character password (with spaces)

3. **Update `.env` file**:
   ```env
   GMAIL_USER="your-email@gmail.com"
   GMAIL_PASS="xxxx xxxx xxxx xxxx"  # 16-character app password with spaces
   ```

## Step 2: Environment Setup

### Clone/Navigate to project:
```bash
cd /home/sury/proj/CouncilProjects/examsystem
```

### Create virtual environment:
```bash
python3 -m venv exams
source exams/bin/activate  # On Windows: exams\Scripts\activate
```

### Install dependencies:
```bash
pip install -r requirements.txt
```

### Configure database:
```env
# In .env, ensure DATABASE_URL is set:
DATABASE_URL='postgresql://postgres:secure123@localhost:5432/exam_paper_portal'

# Database tables auto-create on first run
# Ensure PostgreSQL is running and database exists
```

## Step 3: Run the Application

### Terminal 1 - Start Backend:
```bash
source exams/bin/activate
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Terminal 2 - Start Frontend:
```bash
cd frontend
npm install  # If first time
npm run dev
```

You should see:
```
VITE v5.x.x  ready in xxx ms
➜  Local:   http://localhost:5173/
```

## Step 4: Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Using the Application

### 1. **Public Homepage** (No login required)
```
http://localhost:5173/
```
- Browse all approved papers
- Search papers by title, author, course
- Filter by paper type, year
- Preview and download papers
- Login/Admin links in header

### 2. **Student Registration & Login**
```
http://localhost:5173/login
```
- Enter email address
- Click "Send OTP"
- **Check FastAPI console** for OTP code
- Enter OTP to create account and login
- Now you can upload papers

### 3. **Upload Papers** (After student login)
```
http://localhost:5173/dashboard
```
- Enter paper title and description
- Select or type course code
- Select paper type (quiz, midterm, endterm, assignment, project)
- Select or type year
- Select semester
- Upload PDF/image file
- Submit for admin review

### 4. **Admin Login**
```
http://localhost:5173/admin-login
```
- Email: admin@example.com (create via database or API)
- Password: (set when creating admin)

### 5. **Admin Dashboard** (After admin login)
```
http://localhost:5173/admin
```
- View pending paper submissions
- Review paper details
- Approve or reject papers with comments
- Edit paper information (course, type, year, semester)
- Manage courses
- Auto-create new courses for submitted papers

## API Endpoints Overview

### Public Endpoints
```bash
# Get all approved papers
GET /papers/public/all

# Download approved paper
GET /papers/{paper_id}/download

# Preview approved paper
GET /papers/{paper_id}/preview
```

### Auth Endpoints
```bash
# Send OTP to email
POST /send-otp
{
  "email": "student@example.com"
}

# Verify OTP and login
POST /verify-otp
{
  "email": "student@example.com",
  "otp": "123456"
}

# Admin login
POST /admin-login
{
  "email": "admin@example.com",
  "password": "password"
}
```

### Student Endpoints (Requires Auth)
```bash
# Upload paper
POST /papers/upload
(multipart/form-data: title, description, paper_type, course_id, year, semester, file)

# Get student's papers
GET /papers/my-papers
```

### Admin Endpoints (Requires Admin Auth)
```bash
# Get pending papers
GET /papers/pending

# Approve paper
POST /papers/{paper_id}/approve

# Reject paper
POST /papers/{paper_id}/reject
{
  "reason": "rejection reason"
}

# Edit paper
PUT /papers/{paper_id}/edit
(form-data: course_id, paper_type, year, semester)

# Create course
POST /courses/admin/create
{
  "code": "CS101",
  "name": "Introduction to Computer Science",
  "description": "Basic CS concepts"
}
```

## Testing OTP Flow

### Console Output Mode (For Testing)
1. Go to http://localhost:5173/login
2. Enter test email: `test@example.com`
3. Click "Send OTP"
4. **Check FastAPI terminal** - OTP will be printed:
   ```
   ============================================================
   OTP for test@example.com: 123456
   Expires in: 10 minutes
   ============================================================
   ```
5. Copy the OTP and enter it in the app
6. Done! You're logged in

### Gmail Mode (For Production Testing)
1. Set GMAIL_USER and GMAIL_PASS in .env
2. Go to http://localhost:5173/login
3. Enter your email
4. Click "Send OTP"
5. Check your Gmail inbox for the OTP email
6. Enter the code in the app

## Troubleshooting

### "Connection refused" error
- **Ensure PostgreSQL is running**: `sudo systemctl start postgresql`
- **Check DATABASE_URL in .env**

### OTP not appearing
- **Check FastAPI console** for console output mode
- **Check Gmail inbox** if using Gmail mode
- **Check spam folder** in Gmail

### Email sending fails
- **Verify Gmail credentials** in .env
- **Ensure App Password is used** (not regular password)
- **Check internet connection**
- **Gmail may block the login** - go to https://myaccount.google.com/device-activity and allow access

### Frontend won't connect to backend
- **Ensure backend is running** on port 8000
- **Check CORS settings** in main.py
- **Open browser console** (F12) for error messages

### Database tables not created
- Run this manually if needed:
  ```python
  python
  >>> from main import Base, engine
  >>> Base.metadata.create_all(bind=engine)
  >>> exit()
  ```

## File Structure

```
examsystem/
├── main.py                 # FastAPI backend
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── contexts/       # Auth & Theme contexts
│   │   └── main.tsx
│   └── package.json
├── uploads/                # Paper upload directory
└── run_services.sh         # Startup script
```

## Next Steps

1. ✅ Setup complete!
2. 🔄 Test student OTP login
3. 🔄 Create admin account
4. 🔄 Test paper upload and approval workflow
5. 🔄 Test public browsing

## Additional Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **React Docs**: https://react.dev/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **Gmail Setup**: https://support.google.com/accounts/answer/185833

## Support

For issues or questions, check:
- FastAPI console logs (Terminal 1)
- Frontend console (Browser F12)
- `.env` configuration
- Database connection settings

---

**Happy coding! 🚀**

# Complete Setup & Running Guide

## Prerequisites

- Python 3.9+
- Node.js 16+
- PostgreSQL 12+
- Git

## Full Setup Instructions

### Step 1: Backend Setup

```bash
# Navigate to project root
cd /home/sury/proj/CouncilProjects/examsystem

# Create and activate virtual environment
python -m venv exams
source exams/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup database and create initial admin/student users
python setup.py
```

**Default Credentials Created:**
- Admin: `admin@university.edu` / `admin123`
- Student: `student@university.edu` / `student123`

### Step 2: Start Backend Server

```bash
# Make sure virtual environment is activated
source exams/bin/activate

# Start the backend server
uvicorn main:app --reload
```

**Backend Running on:** `http://localhost:8000`

**API Documentation Available at:**
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Step 3: Frontend Setup

In a new terminal:

```bash
# Navigate to frontend directory
cd /home/sury/proj/CouncilProjects/examsystem/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

**Frontend Running on:** `http://localhost:5173` or `http://localhost:3000`

### Step 4: Access the Application

1. Open your browser and go to: `http://localhost:5173`
2. You should see the login page
3. Login with admin or student credentials

---

## Features Verification

### Admin Features (Login as admin@university.edu / admin123)
- [ ] View Dashboard statistics
- [ ] Review pending papers
- [ ] Approve/Reject submissions
- [ ] Create courses
- [ ] Edit courses
- [ ] Delete courses

### Student Features (Login as student@university.edu / student123)
- [ ] Upload papers for review
- [ ] View uploaded papers
- [ ] Filter papers by course/type/year/semester
- [ ] See approval status of submissions

### General Features
- [ ] Dark mode toggle
- [ ] Responsive design
- [ ] Smooth animations
- [ ] Error messages display correctly
- [ ] Token-based authentication

---

## What Was Fixed for Compatibility

### 1. **Login Authentication**
- ✅ Fixed: Backend expects form-urlencoded data
- Updated AuthContext to use URLSearchParams
- Now properly passes username/password to backend

### 2. **Course Management**
- ✅ Fixed: JSON headers for course API calls
- Added proper Authorization headers
- Improved error handling

### 3. **Paper Upload**
- ✅ Working: FormData for multipart file upload
- Proper error messages from backend
- File validation

### 4. **Error Handling**
- ✅ Improved: All components now display backend error messages
- Better user feedback
- Proper type safety

### 5. **API Configuration**
- ✅ Added: Centralized api.ts utility
- Automatic token injection
- Consistent error handling
- Ready for future enhancements

---

## File Structure

```
examsystem/
├── frontend/                    # React TypeScript app
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── contexts/           # Auth & Theme contexts
│   │   ├── utils/
│   │   │   └── api.ts          # API configuration
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── COMPATIBILITY_CHANGES.md
│   ├── QUICK_REFERENCE.md
│   ├── package.json
│   └── tailwind.config.js
│
├── main.py                      # FastAPI backend
├── setup.py                     # Database initialization
├── requirements.txt             # Python dependencies
├── README.md                    # Project documentation
└── uploads/                     # Paper uploads storage
```

---

## Troubleshooting

### "Port already in use"
```bash
# Kill process using port 8000 (backend)
lsof -ti:8000 | xargs kill -9

# Kill process using port 5173 (frontend)
lsof -ti:5173 | xargs kill -9
```

### "ModuleNotFoundError: No module named..."
```bash
# Ensure virtual environment is activated and reinstall
source exams/bin/activate
pip install -r requirements.txt
```

### "Database connection error"
```bash
# Check PostgreSQL is running
sudo service postgresql status

# Or with Docker
docker-compose up -d

# Reset database
python setup.py  # This recreates tables with sample data
```

### "CORS error in browser console"
- Verify backend is running on correct port
- Check CORS middleware is enabled in main.py
- Try hard refresh (Ctrl+Shift+R)

### "Token validation failed"
- Clear localStorage: Open DevTools → Application → Storage → LocalStorage → Clear
- Login again
- Check token isn't expired (24 hours)

### "npm install fails"
```bash
# Clear npm cache and try again
npm cache clean --force
npm install
```

---

## Development Workflow

### Making Code Changes

**Backend Changes:**
1. Edit files in project root (main.py, etc.)
2. Server auto-reloads (uvicorn --reload)
3. Check logs in terminal for errors

**Frontend Changes:**
1. Edit files in src/ directory
2. Vite auto-reloads in browser
3. Check DevTools Console for errors

### Testing Endpoints

**Using cURL:**
```bash
# Login
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@university.edu&password=admin123"

# Create Course
curl -X POST "http://localhost:8000/courses" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"CS5501","name":"New Course"}'
```

**Using Swagger UI:**
1. Go to `http://localhost:8000/docs`
2. Click on endpoint
3. Click "Try it out"
4. Enter parameters
5. Click "Execute"

---

## Database Management

### Access PostgreSQL

```bash
# Connect to database
psql -U paper_portal_user -d paper_portal -h localhost
Password: (use password from DATABASE_URL)

# Common commands
\dt                    # List tables
SELECT * FROM users;  # View users
SELECT * FROM papers; # View papers
\q                    # Quit
```

### Backup Database

```bash
pg_dump -U paper_portal_user paper_portal > backup.sql
```

### Restore Database

```bash
psql -U paper_portal_user paper_portal < backup.sql
```

---

## Production Deployment

### Environment Variables

Create `.env` file in project root:
```
DATABASE_URL=postgresql://user:password@host/db_name
SECRET_KEY=your-super-secret-key-here
UPLOAD_DIR=/path/to/uploads
```

### Security Checklist

- [ ] Change default admin password
- [ ] Set strong SECRET_KEY
- [ ] Enable HTTPS/SSL
- [ ] Set restrictive CORS origins
- [ ] Use environment variables for secrets
- [ ] Enable rate limiting
- [ ] Validate all file uploads
- [ ] Regular database backups
- [ ] Monitor server logs
- [ ] Use cloud storage for uploads (S3, etc.)

### Build Frontend for Production

```bash
cd frontend
npm run build
# Output in dist/ directory
```

---

## Next Steps

1. ✅ Complete the setup instructions above
2. ✅ Verify all features work
3. ✅ Review COMPATIBILITY_CHANGES.md for technical details
4. ✅ Check QUICK_REFERENCE.md for API endpoints
5. Read main.py to understand backend structure
6. Explore src/ components to understand frontend structure
7. Make customizations as needed

---

## Support & Resources

- **Backend API Docs:** `http://localhost:8000/docs`
- **FastAPI:** https://fastapi.tiangolo.com/
- **React:** https://react.dev/
- **PostgreSQL:** https://www.postgresql.org/docs/

---

## Quick Commands Summary

```bash
# Terminal 1 - Backend
cd /home/sury/proj/CouncilProjects/examsystem
source exams/bin/activate
uvicorn main:app --reload

# Terminal 2 - Frontend
cd /home/sury/proj/CouncilProjects/examsystem/frontend
npm run dev

# Access application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**That's it! Your system is ready to use. 🚀**


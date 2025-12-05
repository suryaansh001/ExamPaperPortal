# Exam Paper Portal - Complete Setup Guide

A full-stack paper submission and management system with admin authentication, approval workflows, and course management.

## Features

### 🔐 Authentication System
- JWT-based authentication
- Secure password hashing (bcrypt)
- Role-based access control (Admin/Student)
- Session management

### 👨‍💼 Admin Dashboard
- Login with email/password
- Dashboard statistics overview
- Pending papers review (Approve/Reject)
- Course management (Create/Edit/Delete)
- View all submissions with filters

### 👨‍🎓 Student Features
- Register and login
- Upload papers (PDF, images, docs)
- View approved papers
- Filter by course, type, year, semester

### 📊 Multi-Level Filtering
- Course-based filtering
- Paper type (Quiz, Midterm, Endterm, Assignment, Project)
- Year and semester filters
- Status-based filtering (admin only)

## Tech Stack

- **Backend:** FastAPI + PostgreSQL
- **Auth:** JWT tokens with python-jose
- **Password:** bcrypt hashing with passlib
- **ORM:** SQLAlchemy
- **Frontend:** React (Admin Dashboard)

## Installation

### 1. Prerequisites
```bash
# Install Python 3.9+
python --version

# Install PostgreSQL
# For Ubuntu/Debian:
sudo apt-get install postgresql postgresql-contrib

# For macOS:
brew install postgresql
```

### 2. Clone and Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Or use a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Database Setup

**Option A: Using Docker (Easiest)**
```bash
# Start PostgreSQL container
docker-compose up -d

# Database will be available at:
# Host: localhost:5432
# Database: paper_portal
# User: paper_portal_user
# Password: secure_password
```

**Option B: Local PostgreSQL**
```bash
# Create database
createdb paper_portal

# Or using psql:
psql -U postgres
CREATE DATABASE paper_portal;
\q
```

### 4. Configure Database Connection

Edit `main.py` and update the DATABASE_URL:
```python
DATABASE_URL = "postgresql://username:password@localhost/paper_portal"
```

If using Docker setup, use:
```python
DATABASE_URL = "postgresql://paper_portal_user:secure_password@localhost/paper_portal"
```

### 5. Initialize Database

Run the setup script to create tables and admin account:
```bash
python setup.py
```

This will create:
- All database tables
- Admin user: `admin@university.edu` / `admin123`
- Student user: `student@university.edu` / `student123`
- Sample courses (CS1108, CS2201, CS3301, CS4401)

### 6. Start the Server

```bash
# For local development
uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}

# Or for Render deployment (uses PORT env var automatically)
uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}
```

Server will start at: `http://localhost:10000` (or use PORT environment variable)

## Usage

### API Documentation

Access interactive API docs at:
- Swagger UI: `http://localhost:10000/docs` (or use PORT env var)
- ReDoc: `http://localhost:10000/redoc` (or use PORT env var)

### Admin Dashboard

The React admin dashboard is included in the artifacts. To use it:

1. Copy the React component code
2. Set up a React project or use it in your existing app
3. Update `API_BASE` constant to point to your backend
4. Login with admin credentials

**Default Admin Credentials:**
- Email: `admin@university.edu`
- Password: `admin123`

⚠️ **Change these in production!**

### Common API Workflows

#### 1. Register a New User
```bash
curl -X POST "http://localhost:10000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newstudent@uni.edu",
    "name": "Jane Smith",
    "password": "password123"
  }'
```

#### 2. Login
```bash
curl -X POST "http://localhost:10000/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@university.edu&password=admin123"
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

#### 3. Upload a Paper (Student)
```bash
curl -X POST "http://localhost:10000/papers/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@midterm.pdf" \
  -F "course_id=1" \
  -F "title=CS1108 Midterm 2024" \
  -F "paper_type=midterm" \
  -F "year=2024" \
  -F "semester=Fall 2024"
```

#### 4. Get Pending Papers (Admin)
```bash
curl -X GET "http://localhost:10000/papers/pending" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

#### 5. Approve/Reject Paper (Admin)
```bash
# Approve
curl -X PATCH "http://localhost:10000/papers/1/review" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "approved"}'

# Reject
curl -X PATCH "http://localhost:10000/papers/1/review" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "rejected",
    "rejection_reason": "Incomplete information"
  }'
```

#### 6. Get Papers with Filters
```bash
curl -X GET "http://localhost:10000/papers?course_id=1&paper_type=midterm&year=2024" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 7. Create a Course (Admin)
```bash
curl -X POST "http://localhost:10000/courses" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "CS5501",
    "name": "Advanced AI",
    "description": "Deep learning and neural networks"
  }'
```

#### 8. Update Course (Admin)
```bash
curl -X PUT "http://localhost:10000/courses/1" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python Programming - Updated",
    "description": "New description"
  }'
```

## Admin Dashboard Features

### Dashboard Tab
- Total papers count
- Pending papers count
- Approved/Rejected counts
- Total courses and users

### Pending Papers Tab
- View all pending submissions
- See uploader details
- Approve with one click
- Reject with reason
- Real-time updates

### Courses Tab
- View all courses
- Add new courses
- Edit course details (code, name, description)
- Delete courses (cascades to papers)

## Security Notes

### Production Deployment Checklist

1. **Change Secret Key**
   ```python
   SECRET_KEY = "your-super-secret-key-here"  # Generate a strong random key
   ```

2. **Change Default Passwords**
   ```bash
   # After setup, immediately change admin password
   ```

3. **Use Environment Variables**
   ```bash
   export DATABASE_URL="postgresql://..."
   export SECRET_KEY="..."
   ```

4. **Enable HTTPS**
   - Use SSL certificates
   - Update CORS settings
   - Set secure cookie flags

5. **Add Rate Limiting**
   ```bash
   pip install slowapi
   ```

6. **File Upload Security**
   - Validate file types strictly
   - Scan uploads for malware
   - Set file size limits
   - Use cloud storage (S3, etc.)

7. **Database Security**
   - Use strong passwords
   - Enable SSL connections
   - Regular backups
   - Restrict access

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
sudo service postgresql status

# Check connection
psql -U postgres -d paper_portal
```

### Token Expired
- Tokens expire after 24 hours
- Login again to get a new token

### File Upload Fails
- Check `uploads/` directory exists and is writable
- Verify file size is under limit
- Check file extension is allowed

### CORS Errors
- Update CORS middleware in `main.py`
- Add your frontend URL to `allow_origins`

## File Structure

```
paper-portal/
├── main.py                 # FastAPI backend
├── setup.py               # Database initialization
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # PostgreSQL container
├── uploads/              # Uploaded files directory
└── README.md             # This file
```

## Database Schema

### Users Table
- id, email, name, password_hash, is_admin, created_at

### Courses Table
- id, code, name, description, created_at, updated_at

### Papers Table
- id, course_id, uploaded_by, title, description
- paper_type, year, semester
- file_path, file_name, file_size
- status, reviewed_by, reviewed_at, rejection_reason
- uploaded_at, updated_at

## API Endpoints Summary

### Authentication
- `POST /register` - Register new user
- `POST /login` - Login and get token
- `GET /me` - Get current user info

### Admin
- `GET /admin/dashboard` - Get statistics

### Courses
- `POST /courses` - Create course (admin)
- `GET /courses` - List all courses
- `GET /courses/{id}` - Get course details
- `PUT /courses/{id}` - Update course (admin)
- `DELETE /courses/{id}` - Delete course (admin)

### Papers
- `POST /papers/upload` - Upload paper
- `GET /papers` - List papers (with filters)
- `GET /papers/pending` - Pending papers (admin)
- `GET /papers/{id}` - Get paper details
- `PATCH /papers/{id}/review` - Approve/reject (admin)
- `GET /papers/{id}/download` - Download file
- `DELETE /papers/{id}` - Delete paper (admin)

## Support

For issues or questions:
1. Check the API docs at `/docs`
2. Review this README
3. Check database connection and logs

## License

MIT License - Feel free to modify and use for your institution!# ExamSystemBackend

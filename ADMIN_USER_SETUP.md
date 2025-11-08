# Admin User Setup Complete ✅

## Admin User Created Successfully

An admin user has been added to the database with **all super admin powers**.

### Admin Credentials

- **Email**: `examportaljklu@jklu.edu.in`
- **Name**: `Portal_exam`
- **Password**: `Aexamadmin@123`
- **User ID**: 4
- **Admin Status**: ✅ True (Super Admin)
- **Email Verified**: ✅ True

### Admin Privileges Granted

The admin user has access to **all admin-protected endpoints**:

#### Dashboard & Statistics
- ✅ `GET /admin/dashboard` - View system statistics

#### User Management
- ✅ `GET /admin/verification-requests` - View ID verification requests
- ✅ `POST /admin/verify-user/{user_id}` - Approve/reject user verification

#### Course Management
- ✅ `POST /courses` - Create new courses
- ✅ `PUT /courses/{course_id}` - Update course details
- ✅ `DELETE /courses/{course_id}` - Delete courses
- ✅ `POST /courses/admin/create-with-paper` - Create courses for paper submissions

#### Paper Management
- ✅ `GET /papers/pending` - View all pending paper submissions
- ✅ `GET /papers` - View all papers (including pending/rejected)
- ✅ `PATCH /papers/{paper_id}/review` - Approve or reject papers
- ✅ `PUT /papers/{paper_id}/edit` - Edit paper details
- ✅ `DELETE /papers/{paper_id}` - Delete papers

### Login Instructions

To login as admin, use the **admin-login endpoint**:

**Endpoint**: `POST /admin-login`

**Request Format** (form-urlencoded):
```
username=examportaljklu@jklu.edu.in
password=Aexamadmin@123
```

**cURL Example**:
```bash
curl -X POST "http://localhost:8000/admin-login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=examportaljklu@jklu.edu.in&password=Aexamadmin@123"
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Environment Variables

Admin credentials have been added to `.env` file (lines 1-3):
```
ADMIN_EMAIL=examportaljklu@jklu.edu.in
ADMIN_NAME=Portal_exam
ADMIN_PASSWORD=Aexamadmin@123
```

### Security Notes

⚠️ **IMPORTANT**:
1. Keep these credentials secure
2. Never commit `.env` file to version control
3. Change the default password in production
4. Use strong passwords for admin accounts
5. Admin users bypass OTP verification (use `/admin-login` endpoint)

### Scripts Created

1. **`add_admin_user.py`** - Script to add admin users to database
   - Usage: `python add_admin_user.py <email> <name> <password>`
   - Or run interactively: `python add_admin_user.py`
   - Automatically reads from `.env` if `ADMIN_EMAIL` and `ADMIN_PASSWORD` are set

2. **`add_admin_to_env.py`** - Script to add admin credentials to `.env` file
   - Usage: `python add_admin_to_env.py`

### Additional Admin Users

To create additional admin users, you can:

1. **Use the script**:
   ```bash
   python add_admin_user.py <email> <name> <password>
   ```

2. **Use the API endpoint** (if you're already logged in as admin):
   ```bash
   POST /create-admin
   {
     "email": "newadmin@example.com",
     "name": "New Admin",
     "password": "securepassword123"
   }
   ```

3. **Promote existing user to admin**:
   - The script will detect if a user exists and offer to promote them

### Testing Admin Access

You can test admin access by:

1. **Login**:
   ```bash
   POST /admin-login
   ```

2. **Get your profile** (verify admin status):
   ```bash
   GET /me
   Authorization: Bearer <token>
   ```
   Response should show `"is_admin": true`

3. **Access admin dashboard**:
   ```bash
   GET /admin/dashboard
   Authorization: Bearer <token>
   ```

---

**Setup Date**: 2025-11-08  
**Status**: ✅ Complete


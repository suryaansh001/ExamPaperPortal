# Neon Database Tables - Complete List

## All PostgreSQL Tables in Your Neon Database

### 1. **users** Table
**Purpose**: Stores user accounts (students and admins)

**Columns**:
- `id` (INTEGER, PRIMARY KEY, INDEXED)
- `email` (VARCHAR, UNIQUE, NOT NULL, INDEXED)
- `name` (VARCHAR, NOT NULL)
- `password_hash` (VARCHAR, NOT NULL)
- `is_admin` (BOOLEAN, DEFAULT FALSE)
- `age` (INTEGER, NULLABLE)
- `year` (VARCHAR(20), NULLABLE)
- `university` (VARCHAR(255), NULLABLE)
- `department` (VARCHAR(255), NULLABLE)
- `roll_no` (VARCHAR(100), NULLABLE)
- `student_id` (VARCHAR(100), NULLABLE)
- `photo_path` (VARCHAR(500), NULLABLE) - Backward compatibility
- `id_card_path` (VARCHAR(500), NULLABLE) - Backward compatibility
- `photo_data` (BYTEA/LargeBinary, NULLABLE) - **STORES FILE CONTENT** ⚠️
- `id_card_data` (BYTEA/LargeBinary, NULLABLE) - **STORES FILE CONTENT** ⚠️
- `id_verified` (BOOLEAN, DEFAULT FALSE)
- `verified_by` (INTEGER, FOREIGN KEY → users.id)
- `verified_at` (TIMESTAMP, NULLABLE)
- `email_verified` (BOOLEAN, DEFAULT FALSE)
- `admin_feedback` (JSONB, NULLABLE)
- `created_at` (TIMESTAMP, DEFAULT NOW())

**Indexes**:
- Primary key on `id`
- Unique index on `email`
- Index on `email`

**Foreign Keys**:
- `verified_by` → `users.id` (ON DELETE SET NULL)

**Storage Impact**: 
- ⚠️ `photo_data` and `id_card_data` store binary file data (can be large)
- These are the main space consumers in this table

---

### 2. **courses** Table
**Purpose**: Stores course information

**Columns**:
- `id` (INTEGER, PRIMARY KEY, INDEXED)
- `code` (VARCHAR(50), UNIQUE, NOT NULL, INDEXED)
- `name` (VARCHAR(255), NOT NULL)
- `description` (TEXT, NULLABLE)
- `created_at` (TIMESTAMP, DEFAULT NOW())
- `updated_at` (TIMESTAMP, DEFAULT NOW(), AUTO UPDATE)

**Indexes**:
- Primary key on `id`
- Unique index on `code`
- Index on `code`

**Foreign Keys**: None

**Storage Impact**: 
- ✅ Small table, minimal storage usage
- Only text data, no binary files

---

### 3. **papers** Table
**Purpose**: Stores exam papers and assignments

**Columns**:
- `id` (INTEGER, PRIMARY KEY, INDEXED)
- `course_id` (INTEGER, FOREIGN KEY → courses.id, INDEXED, ON DELETE CASCADE)
- `uploaded_by` (INTEGER, FOREIGN KEY → users.id, INDEXED, ON DELETE SET NULL)
- `title` (VARCHAR(255), NOT NULL, INDEXED)
- `description` (TEXT, NULLABLE)
- `paper_type` (ENUM: quiz, midterm, endterm, assignment, project, NOT NULL, INDEXED)
- `year` (INTEGER, INDEXED)
- `semester` (VARCHAR(20), INDEXED)
- `department` (VARCHAR(255), NULLABLE, INDEXED)
- `file_path` (VARCHAR(500), NULLABLE) - Backward compatibility
- `file_name` (VARCHAR(255), NOT NULL)
- `file_size` (INTEGER, NULLABLE)
- `file_data` (BYTEA/LargeBinary, NULLABLE) - **STORES FILE CONTENT** ⚠️⚠️⚠️
- `status` (ENUM: pending, approved, rejected, DEFAULT 'pending', INDEXED)
- `reviewed_by` (INTEGER, FOREIGN KEY → users.id, ON DELETE SET NULL)
- `reviewed_at` (TIMESTAMP, NULLABLE)
- `rejection_reason` (TEXT, NULLABLE) - Backward compatibility
- `admin_feedback` (JSONB, NULLABLE)
- `uploaded_at` (TIMESTAMP, DEFAULT NOW(), INDEXED)
- `updated_at` (TIMESTAMP, DEFAULT NOW(), AUTO UPDATE)

**Indexes**:
- Primary key on `id`
- Index on `course_id`
- Index on `uploaded_by`
- Index on `title`
- Index on `paper_type`
- Index on `year`
- Index on `semester`
- Index on `department`
- Index on `status`
- Index on `uploaded_at`
- Composite index: `idx_paper_status_uploaded` (status, uploaded_at)
- Composite index: `idx_paper_course_status` (course_id, status)
- Composite index: `idx_paper_type_year` (paper_type, year)

**Foreign Keys**:
- `course_id` → `courses.id` (ON DELETE CASCADE)
- `uploaded_by` → `users.id` (ON DELETE SET NULL)
- `reviewed_by` → `users.id` (ON DELETE SET NULL)

**Storage Impact**: 
- ⚠️⚠️⚠️ **MAJOR SPACE CONSUMER** - `file_data` stores complete PDF/document files as binary data
- This is likely the main reason your Neon DB disk is full
- Each paper file can be several MB, and with many papers, this adds up quickly

---

## Summary

### Total Tables: **3**

1. **users** - User accounts and profile data
2. **courses** - Course information
3. **papers** - Exam papers and documents

### Storage Hotspots (Likely causing disk full):

1. **papers.file_data** - ⚠️⚠️⚠️ **BIGGEST CONSUMER**
   - Stores complete PDF/document files
   - Each paper can be 1-10+ MB
   - If you have 100+ papers, this can easily be 100MB-1GB+

2. **users.photo_data** - ⚠️
   - Stores user profile photos
   - Typically 100KB-2MB per photo

3. **users.id_card_data** - ⚠️
   - Stores ID card images
   - Typically 200KB-3MB per ID card

### Recommendations to Free Up Space:

1. **Delete old/rejected papers**:
   ```sql
   DELETE FROM papers WHERE status = 'rejected';
   DELETE FROM papers WHERE uploaded_at < NOW() - INTERVAL '1 year';
   ```

2. **Delete papers with large files**:
   ```sql
   -- Find largest files
   SELECT id, file_name, file_size, uploaded_at 
   FROM papers 
   WHERE file_data IS NOT NULL 
   ORDER BY file_size DESC 
   LIMIT 20;
   ```

3. **Delete old user photos/ID cards**:
   ```sql
   -- Clear photo data for unverified users older than 6 months
   UPDATE users 
   SET photo_data = NULL, id_card_data = NULL 
   WHERE id_verified = FALSE 
   AND created_at < NOW() - INTERVAL '6 months';
   ```

4. **Check table sizes**:
   ```sql
   SELECT 
     schemaname,
     tablename,
     pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
   FROM pg_tables
   WHERE schemaname = 'public'
   ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
   ```

5. **Check row counts**:
   ```sql
   SELECT 'users' as table_name, COUNT(*) as row_count FROM users
   UNION ALL
   SELECT 'courses', COUNT(*) FROM courses
   UNION ALL
   SELECT 'papers', COUNT(*) FROM papers;
   ```


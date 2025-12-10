# Backend Changes for File Preview Feature

## Summary

Updated the FastAPI backend to support direct file serving and improved file preview capabilities. These changes enable the frontend to directly access uploaded files through a dedicated static files endpoint and provide metadata about files for preview support.

---

## Changes Made

### 1. **Import Additions** (Line 4)
Added StaticFiles middleware for serving static files:
```python
from fastapi.staticfiles import StaticFiles
```

### 2. **Static Files Mount** (Lines 262-267)
Mounted the uploads directory as static files to serve them directly:
```python
# Mount uploads directory as static files for direct serving
# This allows frontend to access files directly via /uploads/{filename}
try:
    app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
except Exception as e:
    print(f"Warning: Could not mount uploads directory: {e}")
```

**Benefits:**
- Direct file access without API calls
- Faster loading for images and PDFs
- Easier for preview in browsers
- Reduced server load for static content

### 3. **PaperResponse Model Update** (Line 171)
Added `file_path` field to include path information in API responses:
```python
class PaperResponse(BaseModel):
    # ... other fields ...
    file_path: str  # NEW: Path to the uploaded file
    # ... other fields ...
```

### 4. **New Preview Endpoint** (Lines 541-564)
Added dedicated endpoint for getting file preview information:
```python
@app.get("/papers/{paper_id}/preview")
def preview_paper(paper_id: int, ...):
    """Get paper preview metadata and file info for admin review"""
    # Returns MIME type, file path, and preview capability info
```

**Response Example:**
```json
{
  "paper_id": 1,
  "file_name": "exam.pdf",
  "file_path": "uploads/1730570400.123_exam.pdf",
  "file_size": 2048576,
  "mime_type": "application/pdf",
  "can_preview": true
}
```

### 5. **Enhanced Download Endpoint** (Lines 567-586)
Improved download endpoint with file existence checking:
```python
@app.get("/papers/{paper_id}/download")
def download_paper(paper_id: int, ...):
    """Download paper file with better error handling"""
    # Added file existence validation
    # Improved MIME type handling
```

### 6. **Helper Functions** (Lines 609-631)

#### `get_mime_type(filename: str) -> str`
Returns appropriate MIME type for files:
```python
def get_mime_type(filename: str) -> str:
    """Get MIME type for a file"""
    mime_types = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.txt': 'text/plain',
        '.zip': 'application/zip',
    }
```

#### `can_preview_file(filename: str) -> bool`
Determines if file can be previewed in browser:
```python
def can_preview_file(filename: str) -> bool:
    """Check if file can be previewed in browser"""
    previewable_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.txt'}
    return ext in previewable_extensions
```

### 7. **Format Paper Response Update** (Lines 605-607)
Added `file_path` to paper response formatting:
```python
def format_paper_response(paper: Paper, include_private_info: bool = False):
    paper_dict = {
        # ... other fields ...
        "file_path": paper.file_path,  # NEW
        # ... other fields ...
    }
```

---

## API Endpoints

### Updated Endpoints

#### GET /papers/pending
**Response now includes `file_path`:**
```json
[
  {
    "id": 1,
    "file_path": "uploads/1730570400.123_paper.pdf",
    "file_name": "paper.pdf",
    "file_size": 2048576,
    "status": "pending"
  }
]
```

#### GET /papers
**Response now includes `file_path`:**
```json
[
  {
    "id": 1,
    "file_path": "uploads/1730570400.123_paper.pdf",
    ...
  }
]
```

### New Endpoints

#### GET /papers/{paper_id}/preview
**Purpose:** Get preview metadata for a paper

**Requires:** Authentication + (Admin OR Paper Owner)

**Response:**
```json
{
  "paper_id": 1,
  "file_name": "exam.pdf",
  "file_path": "uploads/1730570400.123_exam.pdf",
  "file_size": 2048576,
  "mime_type": "application/pdf",
  "can_preview": true
}
```

**Status Codes:**
- 200: Success
- 403: Access denied
- 404: Paper or file not found

### Direct File Access

#### GET /uploads/{filename}
**Purpose:** Direct access to uploaded files

**Example:**
```
http://localhost:8000/uploads/1730570400.123_paper.pdf
```

**Benefits:**
- Faster loading than API proxy
- Browser can directly display PDFs
- Images load with standard HTML img tags

---

## File Structure

```
Backend/
├── main.py (Updated)
│   ├── Imports: Added StaticFiles
│   ├── App Setup: Added static files mount
│   ├── Models: Updated PaperResponse
│   ├── Endpoints: Added /preview, Enhanced /download
│   └── Helpers: Added get_mime_type, can_preview_file
│
└── uploads/ (Directory - served via StaticFiles)
    ├── 1730570400.123_paper1.pdf
    ├── 1730570401.456_paper2.jpg
    ├── 1730570402.789_paper3.docx
    └── ...
```

---

## MIME Types Supported

| Extension | MIME Type |
|-----------|-----------|
| .pdf | application/pdf |
| .jpg | image/jpeg |
| .jpeg | image/jpeg |
| .png | image/png |
| .gif | image/gif |
| .doc | application/msword |
| .docx | application/vnd.openxmlformats-officedocument.wordprocessingml.document |
| .txt | text/plain |
| .zip | application/zip |
| Other | application/octet-stream |

---

## Previewable File Types

Files that can be previewed directly in browser:
- PDF (.pdf)
- Images (.jpg, .jpeg, .png, .gif)
- Text (.txt)

Files that require download:
- Documents (.doc, .docx)
- Archives (.zip)
- Other formats

---

## Security Considerations

### Authorization Checks
1. **Preview Endpoint**: Only admin or paper owner can preview
2. **Download Endpoint**: Admin or approved papers only
3. **Static Files**: Direct access via /uploads (consider adding auth middleware)

### File Validation
- File existence check before serving
- File path validation to prevent directory traversal
- MIME type validation

### Recommendations for Production
1. **Add Authentication Middleware** to /uploads route
2. **Implement Rate Limiting** on download/preview endpoints
3. **Add Virus Scanning** for uploaded files
4. **Use CDN** for static file serving
5. **Enable GZIP Compression** for text-based files
6. **Add Cache Headers** for static files

---

## Configuration

### Environment Variables
```bash
# Existing - no new variables needed
UPLOAD_DIR=uploads
```

### Directory Permissions
Ensure uploads directory has proper permissions:
```bash
chmod 755 uploads
```

---

## Testing Checklist

- [ ] Static files mount works
- [ ] PDF files serve correctly
- [ ] Images display in preview
- [ ] Document files show download option
- [ ] Preview endpoint returns correct MIME types
- [ ] Download endpoint works for authorized users
- [ ] File access control works (403 for unauthorized)
- [ ] File not found returns 404
- [ ] Large files don't timeout
- [ ] Admin can preview all pending papers

---

## Performance Impact

### Improvements
1. **Faster Preview Loading**: Direct static file serving is faster than proxy through API
2. **Reduced Server Load**: Static files not processed through Python
3. **Browser Caching**: Static files can be cached by browser
4. **Parallel Requests**: Multiple files can load simultaneously

### Considerations
1. **Disk Space**: Ensure adequate space for uploads
2. **File I/O**: Monitor disk I/O on large deployments
3. **Bandwidth**: Consider bandwidth limits for large files

---

## Deployment Notes

### Before Deploying

1. **Verify Uploads Directory**
   ```bash
   mkdir -p uploads
   chmod 755 uploads
   ```

2. **Update CORS Settings** if needed for production domain

3. **Enable HTTPS** in production

4. **Configure Security Headers** for static file serving

### Restart Required
After these changes, restart the backend server:
```bash
uvicorn main:app --reload  # Development
# or
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app  # Production
```

---

## Database Queries Affected

No database schema changes. Only:
- Updated response model includes existing `file_path` field
- No new tables or columns needed

---

## Backward Compatibility

✅ **Fully Backward Compatible**
- Existing endpoints still work
- Added fields are optional in responses
- New endpoints don't break existing ones
- Database schema unchanged

---

## Monitoring

### Check Backend Health
```bash
curl http://localhost:8000/docs
```

### Test File Serving
```bash
# List available files
ls -la uploads/

# Test static file serving
curl http://localhost:8000/uploads/{filename}
```

### Check Logs
```bash
# Backend logs should show:
# - "Mounting application..." for static files
# - Successful requests to /uploads/
# - Preview endpoint calls
```

---

## Rollback Plan

If issues occur:

1. **Remove Static Mount** (if causes problems)
   ```python
   # Comment out: app.mount("/uploads", ...)
   ```

2. **Remove Preview Endpoint** (if not needed)
   ```python
   # Comment out: @app.get("/papers/{paper_id}/preview")
   ```

3. **Keep file_path in Response** (safe, no side effects)

---

## Future Enhancements

1. **Add Thumbnail Generation** for images
2. **Implement Compression** for PDF files
3. **Add Virus Scanning** integration
4. **Enable Search** in PDFs
5. **Add Watermarking** for sensitive documents
6. **Implement Access Logging** for audits
7. **Add File Version History**
8. **Support Cloud Storage** (S3, etc.)

---

## Related Files

- Frontend: `frontend/src/components/FilePreviewModal.tsx`
- Frontend: `frontend/src/components/AdminDashboard.tsx`
- Documentation: `frontend/FILE_PREVIEW_FEATURE.md`


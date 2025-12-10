# Database Storage Migration Guide

## Overview
The application has been updated to store PDFs and images directly in the Neon DB (PostgreSQL) database instead of the local filesystem. This ensures that files persist across rebuilds on Render and other cloud platforms.

## Changes Made

### 1. Database Schema Updates
Added new BYTEA columns to store file data:
- `users.photo_data` - Stores user profile photos
- `users.id_card_data` - Stores user ID card images/PDFs
- `papers.file_data` - Stores paper files (PDFs, images, documents)

The existing `file_path`, `photo_path`, and `id_card_path` columns are kept for backward compatibility and reference.

### 2. Upload Endpoints Updated
- `/profile/photo` - Now stores photo data in `users.photo_data`
- `/profile/id-card` - Now stores ID card data in `users.id_card_data`
- `/papers/upload` - Now stores paper files in `papers.file_data`

### 3. Download/Serve Endpoints Updated
- `/uploads/{filename}` - Checks database first, falls back to filesystem for old files
- `/papers/{paper_id}/download` - Serves files from database
- `/papers/{paper_id}/preview` - Checks database for file existence

### 4. Backward Compatibility
The system maintains backward compatibility:
- Old files stored in the filesystem can still be accessed
- New uploads are stored in the database
- The system checks the database first, then falls back to filesystem

## Database Migration

### Automatic Migration
When you run the application, SQLAlchemy will automatically add the new columns to your database schema. The new columns are nullable, so existing records won't be affected.

### Manual Migration (Optional)
If you want to migrate existing files from the filesystem to the database, you can create a migration script. However, this is optional - the system will work with both storage methods.

## Benefits

1. **Persistence**: Files are stored in the database and persist across rebuilds
2. **No Filesystem Dependencies**: Works on platforms like Render where the filesystem is ephemeral
3. **Backup**: Files are included in database backups automatically
4. **Consistency**: All data (including files) is in one place

## Testing

After deployment:
1. Upload a new paper - it should be stored in the database
2. Upload a profile photo - it should be stored in the database
3. Download/view files - they should be served from the database
4. Old files (if any) should still work via filesystem fallback

## Notes

- File size limits: PostgreSQL BYTEA can store files up to 1GB, but for performance, consider limiting uploads to reasonable sizes (e.g., 50MB for papers, 5MB for photos)
- The filesystem `uploads/` directory is no longer required for new uploads, but kept for backward compatibility
- Database size will increase as files are stored, so monitor your Neon DB storage quota


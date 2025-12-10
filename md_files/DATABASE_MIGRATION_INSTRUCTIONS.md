# Database Migration Instructions

## 🎯 Quick Answer

**Yes, you need to add the new columns to your database!**

The new columns (`photo_data`, `id_card_data`, `file_data`) need to be added to your existing database tables.

## ✅ Automatic vs Manual Migration

### Option 1: Automatic (Recommended) - Use Migration Script

I've created a migration script that will safely add the columns:

```bash
cd ExamSystemBackend
python add_file_storage_columns.py
```

**What it does:**
- ✅ Checks if columns already exist
- ✅ Adds missing columns safely
- ✅ Preserves all existing data
- ✅ Makes `file_path` nullable for backward compatibility

### Option 2: Manual SQL (If you prefer)

If you want to add the columns manually, run these SQL commands in your Neon DB console:

```sql
-- Add columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS photo_data BYTEA;
ALTER TABLE users ADD COLUMN IF NOT EXISTS id_card_data BYTEA;

-- Add columns to papers table
ALTER TABLE papers ADD COLUMN IF NOT EXISTS file_data BYTEA;

-- Make file_path nullable (for backward compatibility)
ALTER TABLE papers ALTER COLUMN file_path DROP NOT NULL;
```

## 📋 Step-by-Step Migration

### Step 1: Run the Migration Script

```bash
cd ExamSystemBackend
python add_file_storage_columns.py
```

**Expected Output:**
```
======================================================================
Database Migration: Adding File Storage Columns
======================================================================

Checking and adding columns...

📋 Users table:
  Adding column users.photo_data...
  ✅ Added users.photo_data
  Adding column users.id_card_data...
  ✅ Added users.id_card_data

📋 Papers table:
  Adding column papers.file_data...
  ✅ Added papers.file_data
  Making file_path nullable for backward compatibility...
  ✅ Made file_path nullable

======================================================================
✅ Migration completed successfully!
======================================================================
```

### Step 2: Verify the Migration

You can verify the columns were added by checking your database:

```sql
-- Check users table columns
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('photo_data', 'id_card_data');

-- Check papers table columns
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'papers' 
AND column_name IN ('file_data', 'file_path');
```

### Step 3: Test the Application

After migration:
1. Start your backend: `uvicorn main:app --reload`
2. Upload a new paper → Should be stored in database
3. Upload a profile photo → Should be stored in database
4. Check that files are accessible

## ⚠️ Important Notes

1. **Existing Data**: All existing data is preserved. The new columns are nullable, so existing records won't be affected.

2. **Backward Compatibility**: 
   - Old files in filesystem will still work
   - New uploads go to database
   - System checks database first, then filesystem

3. **No Data Loss**: This migration only ADDS columns. It doesn't delete or modify existing data.

4. **Safe to Run Multiple Times**: The script checks if columns exist before adding them, so it's safe to run multiple times.

## 🔍 Troubleshooting

### Error: "Table does not exist"
**Solution**: Run your app first to create the tables, then run the migration script.

### Error: "Column already exists"
**Solution**: This is fine! The script will skip columns that already exist.

### Error: "Permission denied"
**Solution**: Make sure your `DATABASE_URL` has the correct permissions to alter tables.

## ✅ After Migration

Once the migration is complete:
- ✅ New uploads will be stored in the database
- ✅ Files will persist across rebuilds on Render
- ✅ Old filesystem files will still work
- ✅ No frontend changes needed

## 🚀 Next Steps

1. Run the migration script
2. Deploy your updated backend
3. Test file uploads
4. Verify files are stored in database

That's it! Your database is now ready for file storage! 🎉


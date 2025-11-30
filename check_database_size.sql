-- SQL Script to Check Neon Database Size and Table Information
-- Run this in your Neon SQL Editor or psql connection

-- 1. Check total database size
SELECT pg_size_pretty(pg_database_size(current_database())) AS database_size;

-- 2. Check size of each table (including indexes)
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS indexes_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 3. Count rows in each table
SELECT 'users' as table_name, COUNT(*) as row_count FROM users
UNION ALL
SELECT 'courses', COUNT(*) FROM courses
UNION ALL
SELECT 'papers', COUNT(*) FROM papers
ORDER BY row_count DESC;

-- 4. Check largest files in papers table
SELECT 
    id,
    title,
    file_name,
    pg_size_pretty(octet_length(file_data)) AS file_size_bytes,
    status,
    uploaded_at
FROM papers
WHERE file_data IS NOT NULL
ORDER BY octet_length(file_data) DESC
LIMIT 20;

-- 5. Check total size of binary data in papers table
SELECT 
    COUNT(*) as total_papers_with_files,
    pg_size_pretty(SUM(octet_length(file_data))) AS total_file_data_size
FROM papers
WHERE file_data IS NOT NULL;

-- 6. Check total size of binary data in users table (photos and ID cards)
SELECT 
    COUNT(*) FILTER (WHERE photo_data IS NOT NULL) as users_with_photos,
    COUNT(*) FILTER (WHERE id_card_data IS NOT NULL) as users_with_id_cards,
    pg_size_pretty(SUM(octet_length(photo_data))) AS total_photo_size,
    pg_size_pretty(SUM(octet_length(id_card_data))) AS total_id_card_size
FROM users;

-- 7. Check papers by status
SELECT 
    status,
    COUNT(*) as count,
    pg_size_pretty(SUM(octet_length(file_data))) AS total_size
FROM papers
WHERE file_data IS NOT NULL
GROUP BY status
ORDER BY SUM(octet_length(file_data)) DESC;

-- 8. Check oldest papers (potential candidates for deletion)
SELECT 
    id,
    title,
    file_name,
    pg_size_pretty(octet_length(file_data)) AS file_size,
    status,
    uploaded_at,
    uploaded_at < NOW() - INTERVAL '6 months' AS older_than_6_months
FROM papers
WHERE file_data IS NOT NULL
ORDER BY uploaded_at ASC
LIMIT 20;

-- 9. Check all indexes and their sizes
SELECT
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) AS index_size
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexname::regclass) DESC;

-- 10. Summary of space usage by table
SELECT 
    'users' as table_name,
    COUNT(*) as rows,
    pg_size_pretty(SUM(octet_length(photo_data) + octet_length(id_card_data))) AS binary_data_size
FROM users
UNION ALL
SELECT 
    'papers',
    COUNT(*),
    pg_size_pretty(SUM(octet_length(file_data)))
FROM papers
UNION ALL
SELECT 
    'courses',
    COUNT(*),
    '0 bytes'::text
FROM courses;


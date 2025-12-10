-- Add public_link_id column to papers table (if not exists)
ALTER TABLE papers 
ADD COLUMN IF NOT EXISTS public_link_id VARCHAR(100) UNIQUE;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_papers_public_link_id ON papers(public_link_id);

-- Generate unique public link IDs for all papers that don't have one
-- Using PostgreSQL's gen_random_uuid() and encoding to hex
UPDATE papers
SET public_link_id = SUBSTRING(REPLACE(gen_random_uuid()::text, '-', ''), 1, 16)
WHERE public_link_id IS NULL OR public_link_id = '';

-- Verify the update
SELECT 
    COUNT(*) as total_papers,
    COUNT(public_link_id) as papers_with_links,
    COUNT(*) - COUNT(public_link_id) as papers_without_links
FROM papers;

-- Show sample of generated links (first 10 approved papers)
SELECT 
    id,
    title,
    status,
    public_link_id,
    CONCAT('https://yourapp.railway.app/public/papers/', public_link_id) as public_url
FROM papers
WHERE public_link_id IS NOT NULL
ORDER BY id
LIMIT 10;

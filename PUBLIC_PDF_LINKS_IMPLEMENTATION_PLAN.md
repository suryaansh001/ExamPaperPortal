# Public PDF Links Implementation Plan

## Overview
Implement a system to generate unique, shareable public links for each PDF that can be accessed without authentication and used directly in AI tools like ChatGPT.

## Current Situation Analysis
- PDFs are stored in database (`file_data` column in `papers` table)
- Current download endpoint: `/papers/{paper_id}/download` (requires auth for pending papers)
- Paper model has: `id`, `file_name`, `file_data`, `status`, etc.

---

## Implementation Steps

### Step 1: Add Public Link Field to Database
**What to do:**
- Add a `public_link_id` column to the `papers` table
- This will be a unique, randomly generated string (UUID or secure random string)
- Auto-generate on paper creation

**Files to modify:**
- `main.py` - Add column to Paper model

**Code changes:**
```python
# In Paper class
public_link_id = Column(String(100), unique=True, nullable=True, index=True)
```

**Migration approach:**
- Use the existing `ensure_column_exists()` function
- For existing papers, generate public_link_id values

**Risks:**
- ✅ Low risk - column is nullable initially
- ⚠️ Need to handle migration for existing papers

**Benefits:**
- Permanent, unique identifier for each paper
- URL-friendly and secure

---

### Step 2: Auto-Generate Public Link IDs
**What to do:**
- When a paper is uploaded, automatically generate a unique public_link_id
- Use UUID4 or secure random string (e.g., `uuid.uuid4().hex[:16]`)

**Files to modify:**
- `main.py` - Modify `/papers/upload` endpoint

**Code changes:**
```python
import uuid

# In upload_paper function
new_paper = Paper(
    # ...existing fields...
    public_link_id=uuid.uuid4().hex[:16],  # 16-char unique ID
)
```

**Risks:**
- ✅ Very low risk - UUID collisions are astronomically unlikely
- ✅ No performance impact

**Benefits:**
- Automatic, no manual intervention needed
- Cryptographically secure randomness

---

### Step 3: Create Public PDF Endpoint
**What to do:**
- Create new endpoint: `/public/papers/{public_link_id}`
- This endpoint will serve the PDF directly without authentication
- Set proper headers for inline display (not download)
- Only serve approved papers

**Files to modify:**
- `main.py` - Add new endpoint

**Code changes:**
```python
from fastapi.responses import Response

@app.get("/public/papers/{public_link_id}")
async def get_public_paper(
    public_link_id: str,
    db: Session = Depends(get_db)
):
    """Publicly accessible PDF endpoint - no authentication required"""
    paper = db.query(Paper).filter(
        Paper.public_link_id == public_link_id,
        Paper.status == SubmissionStatus.APPROVED
    ).first()
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found or not publicly available")
    
    if not paper.file_data:
        raise HTTPException(status_code=404, detail="File data not available")
    
    # Serve PDF with inline display headers
    return Response(
        content=paper.file_data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{paper.file_name}"',
            "Content-Type": "application/pdf",
            "Access-Control-Allow-Origin": "*",  # Allow cross-origin access
        }
    )
```

**Risks:**
- ⚠️ **MEDIUM**: Anyone with the link can access the PDF
  - Mitigation: Links are hard to guess (16+ random characters)
  - Mitigation: Only approved papers are accessible
- ⚠️ **LOW**: Potential for abuse/bandwidth usage
  - Mitigation: Add rate limiting if needed
  - Mitigation: Monitor usage patterns

**Benefits:**
- ✅ No authentication needed - easy sharing
- ✅ Works with ChatGPT and other AI tools
- ✅ Can be embedded in websites/apps
- ✅ Direct PDF viewing in browser

---

### Step 4: Add Public Link to API Responses
**What to do:**
- Include the full public URL in paper response objects
- Format: `https://yourapp.railway.app/public/papers/{public_link_id}`

**Files to modify:**
- `main.py` - Update `PaperResponse` schema

**Code changes:**
```python
class PaperResponse(BaseModel):
    # ...existing fields...
    public_link_id: Optional[str] = None
    public_url: Optional[str] = None
    
    @classmethod
    def from_paper(cls, paper: Paper, base_url: str = ""):
        public_url = None
        if paper.public_link_id and paper.status == SubmissionStatus.APPROVED:
            public_url = f"{base_url}/public/papers/{paper.public_link_id}"
        
        return cls(
            # ...existing fields...
            public_link_id=paper.public_link_id,
            public_url=public_url,
        )
```

**Risks:**
- ✅ Low risk - just adding fields to response

**Benefits:**
- Frontend gets ready-to-use URLs
- Easy to copy/share

---

### Step 5: Frontend Integration (If Needed)
**What to do:**
- Add "Copy Public Link" button in paper listing
- Add "Share to ChatGPT" button that opens ChatGPT with pre-filled prompt

**Frontend code example:**
```javascript
// Copy public link
function copyPublicLink(publicUrl) {
    navigator.clipboard.writeText(publicUrl);
    alert('Link copied to clipboard!');
}

// Share to ChatGPT
function shareToChatGPT(publicUrl, paperTitle) {
    const prompt = `Please analyze this exam paper titled "${paperTitle}": ${publicUrl}`;
    const chatGptUrl = "https://chat.openai.com/?q=" + encodeURIComponent(prompt);
    window.open(chatGptUrl, '_blank');
}

// Share to Claude
function shareToClaude(publicUrl, paperTitle) {
    const prompt = `Please analyze this exam paper titled "${paperTitle}": ${publicUrl}`;
    const claudeUrl = "https://claude.ai/new?q=" + encodeURIComponent(prompt);
    window.open(claudeUrl, '_blank');
}
```

**HTML example:**
```html
<button onclick="copyPublicLink('${paper.public_url}')">📋 Copy Link</button>
<button onclick="shareToChatGPT('${paper.public_url}', '${paper.title}')">🤖 Analyze with ChatGPT</button>
<button onclick="shareToClaude('${paper.public_url}', '${paper.title}')">💬 Analyze with Claude</button>
```

**Risks:**
- ✅ No backend risks
- ⚠️ UX consideration: Make it clear the link is public

**Benefits:**
- One-click sharing
- Better user experience

---

### Step 6: Backfill Existing Papers
**What to do:**
- Create a migration script to generate public_link_id for existing papers
- Run once after deployment

**Files to create:**
- `py_tools/generate_public_links.py`

**Code:**
```python
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import engine, Paper, SessionLocal
import uuid

def generate_public_links():
    db = SessionLocal()
    try:
        # Get all papers without public_link_id
        papers = db.query(Paper).filter(Paper.public_link_id == None).all()
        
        print(f"Found {len(papers)} papers without public links")
        
        for paper in papers:
            paper.public_link_id = uuid.uuid4().hex[:16]
            print(f"Generated link for paper {paper.id}: {paper.public_link_id}")
        
        db.commit()
        print(f"✅ Successfully generated public links for {len(papers)} papers")
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    generate_public_links()
```

**Risks:**
- ✅ Low risk - only updates null values
- ⚠️ Run only once to avoid duplicates

**Benefits:**
- Existing papers get public links
- No data loss

---

## Complete Implementation Summary

### Files to Create:
1. `py_tools/generate_public_links.py` - Migration script

### Files to Modify:
1. `main.py` - Add column, endpoint, update schemas

### Database Changes:
- Add `public_link_id` column (VARCHAR(100), unique, indexed)

### API Changes:
- New endpoint: `GET /public/papers/{public_link_id}`
- Updated response: Include `public_link_id` and `public_url` in PaperResponse

---

## Security Considerations

### ✅ Safe:
- Only approved papers are accessible
- Public link IDs are random and hard to guess (2^64 possibilities for 16-char hex)
- No personal user information exposed
- Read-only access (no modifications possible)
- CORS headers allow embedding

### ⚠️ Considerations:
1. **Privacy**: Once a paper is approved, it's publicly accessible
   - **Solution**: Make this clear in the UI when uploading
   - **Solution**: Add option to revoke/regenerate links if needed

2. **Bandwidth**: Public links could be heavily shared
   - **Solution**: Monitor usage via logs
   - **Solution**: Add rate limiting if abuse detected
   - **Solution**: Consider CDN for popular papers

3. **SEO**: Public URLs might be indexed by search engines
   - **Solution**: Add `robots.txt` rules if needed
   - **Solution**: Or embrace it for discoverability

4. **Link Revocation**: No way to revoke a link once shared
   - **Solution**: Add ability to regenerate public_link_id
   - **Solution**: Add "disable public access" flag per paper

---

## Advanced Features (Optional - Future)

### 1. Analytics Tracking
```python
# Track views per public link
class PaperView(Base):
    __tablename__ = "paper_views"
    id = Column(Integer, primary_key=True)
    paper_id = Column(Integer, ForeignKey("papers.id"))
    viewed_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(String(500))
```

### 2. Short URLs
```python
# Use base62 encoding for shorter links
# Instead of: /public/papers/a1b2c3d4e5f6g7h8
# Use: /p/xK9mN2
```

### 3. Link Expiration (Optional)
```python
# Add expiration dates for temporary sharing
public_link_expires_at = Column(DateTime, nullable=True)
```

### 4. QR Code Generation
```python
import qrcode
from io import BytesIO

@app.get("/papers/{paper_id}/qr")
def get_qr_code(paper_id: int):
    # Generate QR code for public link
    # Return as PNG image
```

---

## Testing Checklist

- [ ] Upload new paper → verify public_link_id is generated
- [ ] Access `/public/papers/{public_link_id}` → PDF displays in browser
- [ ] Try accessing pending paper → should return 404
- [ ] Try accessing with invalid link → should return 404
- [ ] Copy link and paste in ChatGPT → verify AI can access PDF
- [ ] Test CORS headers → verify cross-origin access works
- [ ] Run migration script → verify existing papers get links
- [ ] Test on mobile → verify PDF opens correctly
- [ ] Test with different browsers (Chrome, Firefox, Safari)

---

## Deployment Steps

1. **Add column to database model** (main.py)
2. **Deploy to staging/production** (auto-migration via ensure_column_exists)
3. **Run backfill script** (`python py_tools/generate_public_links.py`)
4. **Test public endpoint** with a sample link
5. **Update frontend** (if applicable)
6. **Monitor logs** for any issues
7. **Update documentation** for users

---

## Environment Variables (Optional)

```env
# Add to .env if you want configurable base URL
PUBLIC_BASE_URL=https://yourapp.railway.app
ENABLE_PUBLIC_LINKS=true
PUBLIC_LINK_LENGTH=16  # Characters in random ID
```

---

## Example Usage Flow

### For Developers:
1. Upload paper → Get response with `public_url`
2. Copy `public_url` from API response
3. Share link anywhere (email, chat, ChatGPT, etc.)

### For Users with Frontend:
1. Browse papers → Click "Copy Public Link" button
2. Or click "Analyze with ChatGPT" → Opens ChatGPT with PDF link
3. AI tool fetches PDF directly from public endpoint

### For AI Tools (ChatGPT):
1. User pastes: "Analyze this paper: https://yourapp.railway.app/public/papers/a1b2c3d4e5f6g7h8"
2. ChatGPT fetches the PDF via the public link
3. ChatGPT analyzes and responds

---

## Pros and Cons

### ✅ Pros:
1. **Easy Sharing**: Single link, works everywhere
2. **AI Integration**: Perfect for ChatGPT, Claude, etc.
3. **No Auth Required**: Frictionless access for viewers
4. **Permanent Links**: Don't break over time
5. **Embeddable**: Can use in websites, presentations
6. **Mobile Friendly**: Opens PDFs directly on phones
7. **SEO Potential**: Papers can be discovered via search

### ⚠️ Cons:
1. **Privacy Concerns**: Anyone with link can access
2. **No Access Control**: Can't revoke without changing link
3. **Bandwidth**: Popular papers consume more resources
4. **Spam Risk**: Links could be shared maliciously
5. **Copyright**: Public access might conflict with some content
6. **No Analytics**: Don't know who's accessing (unless you add tracking)

---

## Risk Mitigation Strategies

### High Priority:
1. **Clear UI Warning**: "This paper will be publicly accessible via a shareable link"
2. **Approved Only**: Only serve approved papers
3. **Random IDs**: Use cryptographically secure random strings
4. **Rate Limiting**: Prevent abuse (optional)

### Medium Priority:
1. **Link Regeneration**: Allow users to generate new link if old one leaked
2. **Disable Option**: Add flag to disable public access per paper
3. **Monitoring**: Log access patterns to detect abuse

### Low Priority:
1. **Analytics**: Track popular papers
2. **Expiration**: Time-limited links (if needed)
3. **Watermarking**: Add user info to PDFs (complex)

---

## Conclusion

This implementation provides a robust, secure, and user-friendly way to share exam papers publicly. The main trade-off is between convenience (public access) and privacy (no access control). For an exam paper portal where papers are meant to be shared, this is generally acceptable.

**Recommended Approach:**
- Implement Steps 1-4 (core functionality)
- Add Step 5 (frontend) based on your UI needs
- Run Step 6 (backfill) after deployment
- Monitor usage and add advanced features as needed

**Estimated Implementation Time:**
- Backend (Steps 1-4): 1-2 hours
- Frontend (Step 5): 1-2 hours
- Testing & Deployment: 1 hour
- **Total: 3-5 hours**

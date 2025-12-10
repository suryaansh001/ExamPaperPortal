#!/usr/bin/env python3
"""
Test script to verify public PDF links implementation.
This script demonstrates the new public sharing functionality.

Usage:
    python py_tools/test_public_links.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import SessionLocal, Paper, SubmissionStatus
from dotenv import load_dotenv

load_dotenv()


def test_public_links():
    """Test and demonstrate public link functionality"""
    db = SessionLocal()
    
    try:
        print("="*80)
        print("PUBLIC PDF LINKS - IMPLEMENTATION TEST")
        print("="*80)
        
        # Get base URL
        base_url = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
        print(f"\n📍 Base URL: {base_url}")
        
        # Count papers by status
        total_papers = db.query(Paper).count()
        approved_papers = db.query(Paper).filter(
            Paper.status == SubmissionStatus.APPROVED
        ).all()
        pending_papers = db.query(Paper).filter(
            Paper.status == SubmissionStatus.PENDING
        ).count()
        
        papers_with_links = db.query(Paper).filter(
            Paper.public_link_id != None,
            Paper.public_link_id != ""
        ).count()
        
        print(f"\n📊 Database Statistics:")
        print(f"   Total papers:           {total_papers}")
        print(f"   Approved papers:        {len(approved_papers)}")
        print(f"   Pending papers:         {pending_papers}")
        print(f"   Papers with public IDs: {papers_with_links}")
        
        # Show approved papers with public links
        if approved_papers:
            print("\n" + "="*80)
            print("✅ APPROVED PAPERS WITH PUBLIC LINKS")
            print("="*80)
            
            for i, paper in enumerate(approved_papers[:10], 1):  # Show first 10
                public_url = f"{base_url}/public/papers/{paper.public_link_id}" if paper.public_link_id else "❌ No link"
                
                print(f"\n{i}. 📄 {paper.title}")
                print(f"   Course: {paper.course.name if paper.course else 'N/A'}")
                print(f"   Year: {paper.year or 'N/A'} | Type: {paper.paper_type.value}")
                print(f"   File: {paper.file_name}")
                print(f"   Status: {paper.status.value}")
                
                if paper.public_link_id:
                    print(f"\n   🔗 Public Link ID: {paper.public_link_id}")
                    print(f"   🌐 Public URL: {public_url}")
                    print(f"\n   💬 Share to ChatGPT:")
                    chatgpt_url = f'https://chat.openai.com/?q={paper.title.replace(" ", "+")}'
                    print(f'      Prompt: "Please analyze this exam paper: {public_url}"')
                    print(f'      URL: {chatgpt_url}')
                    
                    print(f"\n   🤖 Share to Claude:")
                    print(f'      Prompt: "Please help me understand this exam paper: {public_url}"')
                    
                    print(f"\n   📋 Copy & Paste Link:")
                    print(f"      {public_url}")
                else:
                    print(f"   ⚠️  No public link ID - run generate_public_links.py")
            
            if len(approved_papers) > 10:
                print(f"\n... and {len(approved_papers) - 10} more approved papers")
        else:
            print("\n⚠️  No approved papers found")
            print("   Papers need to be approved before they can be publicly accessed")
        
        # Show sample frontend code
        print("\n" + "="*80)
        print("💻 FRONTEND INTEGRATION EXAMPLES")
        print("="*80)
        
        if approved_papers and approved_papers[0].public_link_id:
            sample_paper = approved_papers[0]
            sample_url = f"{base_url}/public/papers/{sample_paper.public_link_id}"
            
            print("\n1️⃣  Copy Link Button (Vanilla JavaScript):")
            print("-" * 80)
            print(f'''
<button onclick="copyPublicLink('{sample_url}')">
    📋 Copy Public Link
</button>

<script>
function copyPublicLink(url) {{
    navigator.clipboard.writeText(url).then(() => {{
        alert('Link copied to clipboard!');
    }});
}}
</script>
''')
            
            print("\n2️⃣  Share to ChatGPT Button:")
            print("-" * 80)
            print(f'''
<button onclick="shareToChatGPT('{sample_url}', '{sample_paper.title}')">
    🤖 Analyze with ChatGPT
</button>

<script>
function shareToChatGPT(pdfUrl, paperTitle) {{
    const prompt = `Please analyze this exam paper titled "${{paperTitle}}": ${{pdfUrl}}`;
    const chatGptUrl = "https://chat.openai.com/?q=" + encodeURIComponent(prompt);
    window.open(chatGptUrl, '_blank');
}}
</script>
''')
            
            print("\n3️⃣  React Component Example:")
            print("-" * 80)
            print(f'''
import React from 'react';

const PaperCard = ({{ paper }}) => {{
    const copyLink = () => {{
        navigator.clipboard.writeText(paper.public_url);
        alert('Link copied!');
    }};
    
    const shareToAI = (service) => {{
        const prompt = `Analyze this paper: ${{paper.public_url}}`;
        const urls = {{
            chatgpt: 'https://chat.openai.com/?q=',
            claude: 'https://claude.ai/new?q=',
        }};
        window.open(urls[service] + encodeURIComponent(prompt));
    }};
    
    return (
        <div className="paper-card">
            <h3>{{paper.title}}</h3>
            <button onClick={{copyLink}}>📋 Copy Link</button>
            <button onClick={{() => shareToAI('chatgpt')}}>
                🤖 ChatGPT
            </button>
            <button onClick={{() => shareToAI('claude')}}>
                💬 Claude
            </button>
        </div>
    );
}};
''')
        
        # Show API response example
        print("\n4️⃣  API Response Example:")
        print("-" * 80)
        if approved_papers and approved_papers[0].public_link_id:
            sample = approved_papers[0]
            print(f'''
GET /papers/{{paper_id}}

Response:
{{
    "id": {sample.id},
    "title": "{sample.title}",
    "status": "{sample.status.value}",
    "public_link_id": "{sample.public_link_id}",
    "public_url": "{base_url}/public/papers/{sample.public_link_id}",
    ...
}}
''')
        
        # Show curl test commands
        print("\n" + "="*80)
        print("🧪 TESTING COMMANDS")
        print("="*80)
        
        if approved_papers and approved_papers[0].public_link_id:
            sample = approved_papers[0]
            public_url = f"{base_url}/public/papers/{sample.public_link_id}"
            
            print("\n✅ Test public endpoint (should work - no auth needed):")
            print(f"   curl -I '{public_url}'")
            
            print("\n✅ Download PDF:")
            print(f"   curl -o test.pdf '{public_url}'")
            
            print("\n✅ Test with browser:")
            print(f"   {public_url}")
        
        print("\n" + "="*80)
        print("✅ IMPLEMENTATION COMPLETE!")
        print("="*80)
        print("\nNext Steps:")
        print("1. Run: python py_tools/generate_public_links.py --dry-run")
        print("   (to see what would be generated)")
        print("\n2. Run: python py_tools/generate_public_links.py")
        print("   (to generate public links for existing papers)")
        print("\n3. Set PUBLIC_BASE_URL in .env:")
        print(f"   PUBLIC_BASE_URL=https://yourapp.railway.app")
        print("\n4. Test a public link in your browser")
        print("\n5. Share a link with ChatGPT or Claude!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    test_public_links()

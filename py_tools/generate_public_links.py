#!/usr/bin/env python3
"""
Generate public link IDs for existing papers in the database.
This script adds unique public_link_id to papers that don't have one.

Usage:
    python py_tools/generate_public_links.py
"""

import sys
import os

# Add parent directory to path to import main modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import SessionLocal, Paper
import uuid


def generate_public_links(dry_run=False):
    """
    Generate public_link_id for all papers that don't have one.
    
    Args:
        dry_run: If True, only show what would be done without making changes
    """
    db = SessionLocal()
    
    try:
        # Get all papers without public_link_id
        papers_without_links = db.query(Paper).filter(
            (Paper.public_link_id == None) | (Paper.public_link_id == "")
        ).all()
        
        total_papers = db.query(Paper).count()
        papers_needing_update = len(papers_without_links)
        
        print("="*70)
        print("PUBLIC LINK GENERATION REPORT")
        print("="*70)
        print(f"Total papers in database: {total_papers}")
        print(f"Papers needing public links: {papers_needing_update}")
        print(f"Papers already have links: {total_papers - papers_needing_update}")
        print("="*70)
        
        if papers_needing_update == 0:
            print("\n✅ All papers already have public links!")
            return
        
        if dry_run:
            print("\n🔍 DRY RUN MODE - No changes will be made\n")
        else:
            print("\n🚀 Generating public links...\n")
        
        # Generate links for papers
        updated_count = 0
        import sys
        
        for i, paper in enumerate(papers_without_links, 1):
            # Generate unique public link ID
            public_link_id = uuid.uuid4().hex[:16]
            
            # Check for collision (extremely unlikely but be safe)
            while db.query(Paper).filter(Paper.public_link_id == public_link_id).first():
                public_link_id = uuid.uuid4().hex[:16]
            
            if not dry_run:
                paper.public_link_id = public_link_id
            
            # Display live progress
            status_emoji = "📝" if paper.status.value == "approved" else "⏳"
            progress_pct = (i / papers_needing_update) * 100
            
            # Progress bar
            bar_length = 40
            filled = int(bar_length * i / papers_needing_update)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            print(f"\r[{bar}] {progress_pct:5.1f}% ({i}/{papers_needing_update}) | "
                  f"{status_emoji} ID:{paper.id:4d} | {paper.title[:30]:30s}", end='', flush=True)
            
            # Every 10 papers or last one, print newline and details
            if i % 10 == 0 or i == papers_needing_update:
                print()  # New line
                print(f"   └─ {paper.status.value:10s} | Link: {public_link_id}")
            
            updated_count += 1
        
        if not dry_run:
            # Commit all changes
            db.commit()
            print(f"\n✅ Successfully generated public links for {updated_count} papers")
        else:
            print(f"\n📊 Would generate links for {updated_count} papers")
            print("\nRun without --dry-run flag to apply changes")
        
        # Show sample public URLs
        if not dry_run and updated_count > 0:
            print("\n" + "="*70)
            print("SAMPLE PUBLIC URLS (for approved papers)")
            print("="*70)
            
            # Get a few approved papers with new links
            approved_samples = [p for p in papers_without_links 
                              if p.status.value == "approved"][:3]
            
            if approved_samples:
                base_url = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
                for paper in approved_samples:
                    public_url = f"{base_url}/public/papers/{paper.public_link_id}"
                    print(f"\n📄 {paper.title}")
                    print(f"   🔗 {public_url}")
                    print(f"   💬 ChatGPT prompt:")
                    print(f'      "Please analyze this exam paper: {public_url}"')
            else:
                print("\n⚠️  No approved papers to show sample URLs")
                print("   Papers need to be approved before public URLs work")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()
    
    print("\n" + "="*70)


def show_statistics():
    """Show statistics about papers with/without public links"""
    db = SessionLocal()
    
    try:
        total = db.query(Paper).count()
        with_links = db.query(Paper).filter(
            Paper.public_link_id != None,
            Paper.public_link_id != ""
        ).count()
        without_links = total - with_links
        
        approved_total = db.query(Paper).filter(Paper.status == "approved").count()
        approved_with_links = db.query(Paper).filter(
            Paper.status == "approved",
            Paper.public_link_id != None,
            Paper.public_link_id != ""
        ).count()
        
        print("\n" + "="*70)
        print("PUBLIC LINKS STATISTICS")
        print("="*70)
        print(f"Total papers:                {total:6d}")
        print(f"  ✅ With public links:      {with_links:6d}")
        print(f"  ❌ Without public links:   {without_links:6d}")
        print(f"\nApproved papers:             {approved_total:6d}")
        print(f"  ✅ With public links:      {approved_with_links:6d}")
        print(f"  ❌ Without public links:   {approved_total - approved_with_links:6d}")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate public link IDs for existing papers"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics only without making changes"
    )
    
    args = parser.parse_args()
    
    if args.stats:
        show_statistics()
    else:
        generate_public_links(dry_run=args.dry_run)
        if not args.dry_run:
            print("\n💡 Tip: Run with --stats flag to see current statistics")

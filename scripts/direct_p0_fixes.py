#!/usr/bin/env python3
"""
DIRECT P0 FIXES - Simplified approach without pipeline dependencies
Reads source data → transforms directly → writes output
"""

import json
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent

def load_json(path: str):
    """Load JSON with encoding handling"""
    try:
        return json.load(open(ROOT / path, encoding="utf-8"))
    except UnicodeDecodeError:
        # Try with error replacement
        return json.load(open(ROOT / path, encoding="utf-8", errors="replace"))

def fix_milestones():
    """Fix 1: Build milestones from proposals_archive"""
    print("\n[1/3] Building milestones.json...")
    
    proposals = load_json("data/proposals_archive.json")
    props = proposals.get("proposals", [])
    
    # Phase extraction logic
    def get_phase(title):
        title = (title or "").lower()
        if "event" in title or "compt" in title: return "event_planning"
        if "video" in title or "media" in title or "content" in title: return "media_production"
        if "park" in title or "skate" in title: return "infrastructure"
        if "scholarship" in title or "grant" in title: return "funding"
        return "general"
    
    # Status mapping
    def get_status(prop):
        status = prop.get("status", "").lower()
        executed = prop.get("executed", False)
        if executed: return "completed"
        if status in ["active", "in_progress"]: return "in_progress"
        if status == "cancelled": return "cancelled"
        return "not_started"
    
    milestones = []
    for p in props:
        milestone = {
            "id": p.get("id"),
            "proposal_id": p.get("proposal_id"),
            "title": p.get("title"),
            "phase": get_phase(p.get("title")),
            "status": get_status(p),
            "started_date": p.get("created_date"),
            "completion_percentage": 100 if p.get("executed") else 0,
            "description": p.get("description", ""),
            "amount_usdc": p.get("spend_total_usd", 0),
        }
        milestones.append(milestone)
    
    output = {
        "milestones": milestones,
        "generated_at": datetime.now().isoformat(),
        "total_count": len(milestones)
    }
    
    with open(ROOT / "data" / "milestones.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"   ✓ Created {len(milestones)} milestones")
    return len(milestones)

def fix_members_sport():
    """Fix 2: Enrich members with sport field"""
    print("\n[2/3] Enriching members.json with sport data...")
    
    members = load_json("data/members.json")
    mmembers = members.get("members", [])
    
    # Build sport inference from spend_ledger
    spend = load_json("data/spend_ledger.json")
    spend_rows = spend.get("spend", [])
    
    # Create member_id -> sports mapping
    member_sports = {}
    sports_keywords = {
        "skateboard": ["sk8", "skate", "skateboard"],
        "surfing": ["surf", "waves", "ocean"],
        "bmx": ["bmx", "bike", "cycling"],
        "snowboard": ["snow", "snowboard", "ski"],
        "windsport": ["wind", "kite", "foil"],
        "climbing": ["climb", "rock"],
    }
    
    for row in spend_rows:
        member_id = row.get("member_id")
        title = (row.get("title", "") or "").lower()
        
        if member_id:
            for sport, keywords in sports_keywords.items():
                if any(kw in title for kw in keywords):
                    if member_id not in member_sports:
                        member_sports[member_id] = sport
                    break
    
    # Assign sport to members
    enriched = 0
    for member in mmembers:
        mid = member.get("id")
        if mid in member_sports:
            member["sport"] = member_sports[mid]
            enriched += 1
        else:
            member["sport"] = None
    
    output = {
        "members": mmembers,
        "generated_at": datetime.now().isoformat(),
        "total_count": len(mmembers),
        "enriched_count": enriched,
        "enrichment_percentage": round(100 * enriched / len(mmembers), 1) if mmembers else 0
    }
    
    with open(ROOT / "data" / "members.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"   ✓ Enriched {enriched}/{len(mmembers)} members ({100*enriched//len(mmembers)}%)")
    return enriched

def fix_spend_category():
    """Fix 3: Try to enrich spend_ledger with category"""
    print("\n[3/3] Checking spend_ledger categories...")
    
    spend = load_json("data/spend_ledger.json")
    spend_rows = spend.get("spend", [])
    
    # Try to load proposal_tags with categories
    proposals_classified = load_json("data/proposals_classified.json")
    classified = proposals_classified.get("proposals", [])
    
    # Build proposal_id -> category map
    category_map = {}
    for p in classified:
        proposal_id = p.get("proposal_id")
        category = p.get("semantic_category")
        if proposal_id and category:
            category_map[proposal_id] = category
    
    # Try to assign categories
    enriched = 0
    for row in spend_rows:
        proposal_id = row.get("proposal_id")
        if proposal_id and proposal_id in category_map:
            row["semantic_category"] = category_map[proposal_id]
            enriched += 1
    
    with open(ROOT / "data" / "spend_ledger.json", "w", encoding="utf-8") as f:
        json.dump(spend, f, indent=2, ensure_ascii=False)
    
    if enriched > 0:
        print(f"   ✓ Enriched {enriched}/{len(spend_rows)} spend rows with category")
    else:
        print(f"   ⚠ Could not enrich categories (classifications unavailable)")
        print(f"     Run: python scripts/classify_proposals_local.py first")
    
    return enriched

if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════╗
    ║      DIRECT P0 FIXES — Simplified Execution       ║
    ║  No pipeline dependencies · Direct JSON transform  ║
    ╚════════════════════════════════════════════════════╝
    """)
    
    try:
        m_count = fix_milestones()
        s_enriched = fix_members_sport()
        c_enriched = fix_spend_category()
        
        print("\n" + "=" * 55)
        print("RESULTS:")
        print(f"  Milestones:  {m_count} records created")
        print(f"  Members:     {s_enriched} with sport enriched")
        print(f"  Categories:  {c_enriched} spend rows enriched")
        print("=" * 55)
        
        print("\nNext: Run audit_baseline.py to measure improvement")
        sys.exit(0)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

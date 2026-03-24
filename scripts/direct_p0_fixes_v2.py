#!/usr/bin/env python3
"""
DIRECT P0 FIXES v2 - Using correct JSON structure
{"dataset": "...", "records": [...]} format
"""

import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent

def load_json(path: str):
    """Load JSON safely"""
    try:
        return json.load(open(ROOT / path, encoding="utf-8"))
    except UnicodeDecodeError:
        return json.load(open(ROOT / path, encoding="utf-8", errors="replace"))

def fix_milestones():
    """Fix 1: Build milestones from proposals_archive"""
    print("\n[1/3] Building milestones.json...")
    
    archive = load_json("data/proposals_archive.json")
    proposals = archive.get("records", [])
    
    def get_phase(title):
        title = (title or "").lower()
        if "event" in title or "compt" in title: return "event_planning"
        if "video" in title or "media" in title or "content" in title: return "media_production"
        if "park" in title or "skate" in title: return "infrastructure"
        if "scholarship" in title or "grant" in title: return "funding"
        return "general"
    
    def get_status(prop):
        status = prop.get("status", "").lower()
        executed = prop.get("executed", False)
        if executed: return "completed"
        if status in ["active", "in_progress"]: return "in_progress"
        if status == "cancelled": return "cancelled"
        return "not_started"
    
    milestones = []
    for p in proposals:
        milestone = {
            "id": p.get("id"),
            "proposal_id": p.get("proposal_id"),
            "title": p.get("title"),
            "phase": get_phase(p.get("title")),
            "status": get_status(p),
            "started_date": p.get("created_date"),
            "completion_percentage": 100 if p.get("executed") else 0,
            "amount_usdc": p.get("spend_total_usd", 0),
        }
        milestones.append(milestone)
    
    output = {
        "dataset": "milestones",
        "as_of": datetime.now().isoformat(),
        "version": 1,
        "records": milestones,
        "total_count": len(milestones)
    }
    
    with open(ROOT / "data" / "milestones.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"   Created {len(milestones)} milestones")
    return len(milestones)

def fix_members_sport():
    """Fix 2: Enrich members with sport field"""
    print("\n[2/3] Enriching members.json with sport data...")
    
    members_raw = load_json("data/members.json")
    members = members_raw.get("records", [])
    
    # Load spend ledger for inference
    spend_raw = load_json("data/spend_ledger.json")
    spend_rows = spend_raw.get("records", [])
    
    # Map member_id -> sport from spend titles
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
        # Try both fields
        member_id = row.get("member_id") or row.get("recipient_address")
        title = (row.get("title", "") or row.get("project_name", "")).lower()
        
        if member_id:
            for sport, keywords in sports_keywords.items():
                if any(kw in title for kw in keywords):
                    if member_id not in member_sports:
                        member_sports[member_id] = sport
                    break
    
    # Assign sport to members
    enriched = 0
    for member in members:
        mid = member.get("member_id")
        if mid in member_sports:
            member["sport"] = member_sports[mid]
            enriched += 1
    
    output = {
        "dataset": "members",
        "as_of": datetime.now().isoformat(),
        "version": members_raw.get("version", 1),
        "coverage": members_raw.get("coverage"),
        "records": members,
        "enrichment": {
            "sport_enriched": enriched,
            "sport_total": len(members),
            "sport_percentage": round(100 * enriched / len(members), 1) if members else 0
        }
    }
    
    with open(ROOT / "data" / "members.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    pct = 100 * enriched // len(members) if members else 0
    print(f"   Enriched {enriched}/{len(members)} members with sport ({pct}%)")
    return enriched

def fix_spend_category():
    """Fix 3: Enrich spend_ledger with semantic_category"""
    print("\n[3/3] Checking spend_ledger categories...")
    
    spend_raw = load_json("data/spend_ledger.json")
    spend_records = spend_raw.get("records", [])
    
    # Try to load classified proposals
    try:
        classified_raw = load_json("data/proposals_classified.json")
        classified = classified_raw.get("records", [])
        
        # Map proposal_id -> category
        category_map = {}
        for p in classified:
            proposal_id = p.get("proposal_id")
            category = p.get("semantic_category")
            if proposal_id and category:
                category_map[proposal_id] = category
        
        # Assign categories
        enriched = 0
        for row in spend_records:
            proposal_id = row.get("proposal_id")
            if proposal_id and proposal_id in category_map:
                row["semantic_category"] = category_map[proposal_id]
                enriched += 1
        
        with open(ROOT / "data" / "spend_ledger.json", "w", encoding="utf-8") as f:
            json.dump(spend_raw, f, indent=2, ensure_ascii=False)
        
        pct = 100 * enriched // len(spend_records) if spend_records else 0
        print(f"   Enriched {enriched}/{len(spend_records)} spend rows with category ({pct}%)")
        return enriched
    except:
        print(f"   WARNING: proposals_classified.json not found")
        print(f"   Run: python scripts/classify_proposals_local.py first")
        return 0

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════╗
║    P0 FIXES v2 - Direct JSON Transform    ║
╚═══════════════════════════════════════════╝
    """)
    
    try:
        m_count = fix_milestones()
        s_enriched = fix_members_sport()
        c_enriched = fix_spend_category()
        
        print("\n" + "=" * 50)
        print("RESULTS:")
        print(f"  Milestones:  {m_count} records created")
        print(f"  Members:     {s_enriched} enriched with sport")
        print(f"  Categories:  {c_enriched} spend rows enriched")
        print("=" * 50)
        print("\nNext: python run_audit_baseline.py")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

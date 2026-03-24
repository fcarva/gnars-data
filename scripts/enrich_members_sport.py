#!/usr/bin/env python3
"""
Enrich members.json with sport data
Popula o campo 'sport' para todos os membros
"""

import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save(path: Path, payload: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")


def infer_sport_from_proposals(members: list, spend_ledger: list) -> dict:
    """
    Inferir sport a partir de dados de proposals/spend_ledger
    Busca por tags semânticas no título das propostas
    """
    sport_map = {}
    
    # Build mapping of recipient -> proposals
    recipient_proposals = defaultdict(list)
    
    # Sport keywords
    keywords = {
        'skate': ['sk8', 'skate', 'skateboard', 'skating', 'board', 'rails', 'ramp'],
        'surf': ['surf', 'waves', 'wave', 'ocean', 'water sports'],
        'bmx': ['bmx', 'bike', 'cycling', 'bicycle'],
        'snow': ['snow', 'snowboard', 'ski', 'skiing'],
        'wind': ['wind', 'kite', 'kiting'],
        'climb': ['climb', 'bouldering', 'rock'],
        'other': []
    }
    
    # Check proposals for sport mentions  
    for record in spend_ledger:
        recipient = str(record.get('recipient_address', '')).lower()
        title = str(record.get('title', '')).lower()
        project_name = str(record.get('project_name', '')).lower()
        
        text = f"{title} {project_name}"
        
        for sport, kws in keywords.items():
            if sport == 'other':
                continue
            for kw in kws:
                if kw in text:
                    if recipient not in sport_map:
                        sport_map[recipient] = sport
                    break
    
    return sport_map


def main() -> None:
    members_data = load(DATA / "members.json")
    spend_data = load(DATA / "spend_ledger.json")
    
    members = members_data.get("records", [])
    spend = spend_data.get("records", [])
    
    # Infer sports from proposals
    sport_map = infer_sport_from_proposals(members, spend)
    
    enriched = 0
    pre_existing = 0
    
    for member in members:
        address = str(member.get("address", "")).lower()
        
        # Skip if already has sport
        if member.get("sport"):
            pre_existing += 1
            continue
        
        # Try to assign from map
        if address in sport_map:
            member["sport"] = sport_map[address]
            enriched += 1
        else:
            # Default to None/uncategorized
            member["sport"] = None
    
    members_data["records"] = members
    save(DATA / "members.json", members_data)
    
    print(f"✅ Enriched members.json with sport data")
    print(f"   - Before: {pre_existing} with sport")
    print(f"   - Added: {enriched} new sports")
    print(f"   - Total coverage: {pre_existing + enriched}/{len(members)} ({100*(pre_existing+enriched)/len(members):.1f}%)")
    
    # Show distribution
    sports = {}
    for m in members:
        sport = m.get("sport") or "uncategorized"
        sports[sport] = sports.get(sport, 0) + 1
    
    print(f"\n   Sport distribution:")
    for sport, count in sorted(sports.items(), key=lambda x: -x[1])[:10]:
        print(f"     - {sport}: {count}")


if __name__ == "__main__":
    main()

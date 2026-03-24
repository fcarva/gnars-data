#!/usr/bin/env python3
"""Debug version with detailed output"""
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent

print("STEP 1: Load source files")
archive = json.load(open(ROOT / "data" / "proposals_archive.json", encoding="utf-8"))
members_data = json.load(open(ROOT / "data" / "members.json", encoding="utf-8"))
spend_data = json.load(open(ROOT / "data" / "spend_ledger.json", encoding="utf-8"))

print(f"  proposals_archive.json: {len(archive.get('records', []))} records")
print(f"  members.json: {len(members_data.get('records', []))} records")
print(f"  spend_ledger.json: {len(spend_data.get('records', []))} records")

print("\nSTEP 2: Build milestones")
proposals = archive.get("records", [])
milestones = []
for p in proposals:
    m = {
        "id": p.get("proposal_number"),
        "proposal_id": p.get("proposal_number"),
        "title": p.get("title"),
        "phase": "general",
        "status": "not_started",
    }
    milestones.append(m)

print(f"  Created {len(milestones)} milestone records")

print("\nSTEP 3: Save milestones")
output = {
    "dataset": "milestones",
    "as_of": datetime.now().isoformat(),
    "version": 1,
    "records": milestones,
}
path = ROOT / "data" / "milestones.json"
json.dump(output, open(path, "w", encoding="utf-8"), indent=2)
print(f"  Saved to {path}")

print("\nSTEP 4: Verify")
verify = json.load(open(ROOT / "data" / "milestones.json", encoding="utf-8"))
print(f"  Verification: {len(verify.get('records', []))} records")

print("\nDONE")

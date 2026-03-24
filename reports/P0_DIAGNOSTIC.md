# P0 FIXES DIAGNOSIS — 2026-03-24

## Current Status Check

### Data State Before Fixes
```
data/milestones.json:    0 records (EMPTY - needs fix script)
data/members.json:       1180 records BUT encoding issues
data/spend_ledger.json:  129 records (category field = MISSING)
```

### Problem: Script Execution Failed

The three P0 fix scripts were created but encountered issues:

1. **build_milestones.py** — Created but ran with 0 output records
   - Possible issue: File format not right, or script logic error
   - Action: Need to debug logic

2. **enrich_members_sport.py** — Created but couldn't verify execution
   - Issue: Members.json has encoding errors (UTF-8 vs CP1252)
   - Action: Fix file encoding first

3. **enrich_spend.py** — Attempted but result unclear
   - Issue: May depend on proposal_tags being pre-populated
   - Action: Check if proposal_tags has categories

## Alternative Fast Path (instead of Pipeline)

Since `refresh_all.py --force` times out and scripts have issues, try **minimal sync-only approach**:

```bash
python scripts/enrich_spend.py --check-only  # See what categories exist
python scripts/classify_proposals_local.py   # Pre-populate categories
python scripts/build_milestones.py           # Retry milestone build
python scripts/enrich_members_sport.py       # Retry sport enrichment
```

## Data File Health Check

### members.json Encoding Issue
- File contains high-byte characters (0x90 found)
- Python cp1252 cannot decode these bytes
- **Fix:** Re-encode file to UTF-8 or use 'utf-8-sig'

### Approach: Direct Python Fixes

Instead of complex pipeline, run direct data transformation:

```python
# 1. Build milestones directly
proposals = json.load(open("data/proposals_archive.json", encoding="utf-8"))
milestones = [
    {
        "id": p["id"],
        "proposal_id": p["proposal_id"],
        "title": p["title"],
        "phase": extract_phase(p["title"]),
        "status": map_status(p.get("status")),
        "started_date": p.get("created_date"),
        "completion_percentage": calc_completion(p),
    }
    for p in proposals
]
json.dump({"milestones": milestones}, open("data/milestones.json", "w"), encoding="utf-8")

# 2. Enrich members sport directly
members = json.load(open("data/members.json", encoding="utf-8", errors="replace"))
for member in members["members"]:
    member["sport"] = infer_sport_from_member_data(member)
json.dump(members, open("data/members.json", "w"), encoding="utf-8")

# 3. Enrich spend category directly
if proposal_tags is populated:
    spend = json.load(open("data/spend_ledger.json", encoding="utf-8"))
    categories = build_category_map(proposal_tags)
    for row in spend["spend"]:
        row["semantic_category"] = categories.get(row["proposal_id"])
    json.dump(spend, open("data/spend_ledger.json", "w"), encoding="utf-8")
```

## Recommended Next Steps

**Priority 1 (5 min):**
- [ ] Fix members.json encoding (re-save as UTF-8)
- [ ] Debug build_milestones.py (check phase extraction logic)
- [ ] Re-run both scripts for validation

**Priority 2 (10 min):**
- [ ] Verify proposal_tags has semantic_category populated
- [ ] Run enrich_spend.py with correct pre-conditions
- [ ] Validate spend_ledger category field

**Priority 3:**
- [ ] Run audit_baseline.py again to measure score improvement
- [ ] Commit fixes to git if score > 60%

---

**Execution Estimate:** 15-20 min total for all 3 P0 fixes via direct approach

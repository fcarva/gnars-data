#!/usr/bin/env python3
"""
GNARS-DATA P0 FIXES MASTER SCRIPT
Executa os 3 fixes críticos na ordem correta
"""

import subprocess
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

print("""
╔════════════════════════════════════════════════════════════════╗
║          GNARS-DATA P0 FIXES - MASTER EXECUTION               ║
║  3 Critical Fixes in Order (Total: ~2 hours)                  ║
╚════════════════════════════════════════════════════════════════╝
""")

steps = [
    {
        "name": "FIX 1: Treasury Category Data",
        "script": "scripts/enrich_spend.py",
        "desc": "Fill 100% missing category field in spend_ledger.json",
        "time": "15 min"
    },
    {
        "name": "FIX 2: Build Milestones",
        "script": "scripts/build_milestones.py",
        "desc": "Create milestones.json with 222 proposal deliverables",
        "time": "2 min"
    },
    {
        "name": "FIX 3: Enrich Members Sport",
        "script": "scripts/enrich_members_sport.py",
        "desc": "Populate sport field for members (98% empty → 50%+)",
        "time": "2 min"
    },
    {
        "name": "STEP 4: Full Pipeline",
        "script": "scripts/refresh_all.py",
        "desc": "Run complete ETL pipeline to derive all aggregations",
        "time": "5 min"
    },
    {
        "name": "STEP 5: Validation",
        "script": "run_audit_baseline.py",
        "desc": "Re-test to verify score improvement",
        "time": "1 min"
    }
]

print("📋 STEPS TO EXECUTE:\n")
for i, step in enumerate(steps, 1):
    print(f"{i}. {step['name']} ({step['time']})")
    print(f"   └─ {step['desc']}\n")

print("─" * 65)
print("\nStarting execution...\n")

# Step 1: Enrich spend
print("\n█ STEP 1/5: Enriching spend_ledger with category data...")
print("─" * 65)
result = subprocess.run(
    ["python", str(ROOT / "scripts" / "enrich_spend.py")],
    cwd=str(ROOT),
    capture_output=True,
    text=True
)
print(result.stdout)
if result.returncode != 0:
    print(f"ERROR: {result.stderr}")

# Step 2: Build milestones
print("\n█ STEP 2/5: Building milestones.json...")
print("─" * 65)
result = subprocess.run(
    ["python", str(ROOT / "scripts" / "build_milestones.py")],
    cwd=str(ROOT),
    capture_output=True,
    text=True
)
print(result.stdout)
if result.returncode != 0:
    print(f"ERROR: {result.stderr}")

# Step 3: Enrich members sport
print("\n█ STEP 3/5: Enriching members with sport data...")
print("─" * 65)
result = subprocess.run(
    ["python", str(ROOT / "scripts" / "enrich_members_sport.py")],
    cwd=str(ROOT),
    capture_output=True,
    text=True
)
print(result.stdout)
if result.returncode != 0:
    print(f"ERROR: {result.stderr}")

# Step 4: Full pipeline
print("\n█ STEP 4/5: Running full pipeline...")
print("─" * 65)
result = subprocess.run(
    ["python", str(ROOT / "scripts" / "refresh_all.py"), "--force"],
    cwd=str(ROOT),
    capture_output=True,
    text=True,
    timeout=300  # 5 min timeout
)
# Just show last 20 lines
lines = result.stdout.split('\n')
for line in lines[-20:]:
    if line.strip():
        print(line)

# Step 5: Validate
print("\n█ STEP 5/5: Running validation audit...")
print("─" * 65)
result = subprocess.run(
    ["python", str(ROOT / "run_audit_baseline.py")],
    cwd=str(ROOT),
    capture_output=True,
    text=True
)
print(result.stdout)

print("\n" + "=" * 65)
print("✅ P0 FIXES COMPLETE")
print("=" * 65)
print("\nNext Steps:")
print("  1. Check reports/audit_baseline.json for new score")
print("  2. If score > 60%, commit and deploy to main")
print("  3. Proceed to P1 fixes (Votes data) if needed")

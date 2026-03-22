from __future__ import annotations

import concurrent.futures
import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

PYTHON = sys.executable
ROOT = Path(__file__).resolve().parents[1]

INCREMENTAL = "--incremental" in sys.argv
DERIVE_ONLY = "--derive-only" in sys.argv
WEEKLY_SNAPSHOT_VOTES = "--weekly-snapshot-votes" in sys.argv

PARALLEL_STEPS: list[tuple[str, str, list[str]]] = [
    ("sync", "sync_gnars.py", []),
    ("sync_proposals", "sync_proposals.py", []),
    ("sync_treasury", "sync_treasury.py", []),
    ("sync_snapshot", "sync_snapshot.py --no-votes", []),
    ("sync_nouns_activity", "sync_nouns_activity.py", []),
]

WEEKLY_STEPS: list[tuple[str, str, list[str]]] = [
    ("sync_snapshot_votes", "sync_snapshot.py --force", []),
]

SEQUENTIAL_STEPS: list[tuple[str, str, list[str]]] = [
    ("fetch_dune", "fetch_dune_data.py", []),
    (
        "classify",
        "classify_proposals_local.py --incremental" if INCREMENTAL else "classify_proposals_local.py",
        ["data/proposals_archive.json"],
    ),
    (
        "enrich_members",
        "enrich_members.py",
        ["data/proposals_archive.json", "data/timeline_events.json"],
    ),
    (
        "enrich_spend",
        "enrich_spend.py",
        ["data/spend_ledger.json", "data/proposal_tags.json"],
    ),
    ("reconcile", "reconcile_treasury.py", ["data/spend_ledger.json"]),
    ("derive", "derive_analytics.py", []),
    ("derive_funding", "derive_funding_analysis.py", []),
    ("audit", "audit_gaps.py", []),
    ("export", "export_csv.py", []),
]

DERIVE_ONLY_STEPS: list[tuple[str, str, list[str]]] = [
    ("derive", "derive_analytics.py", []),
    ("derive_funding", "derive_funding_analysis.py", []),
    ("export", "export_csv.py", []),
]


def run_step(name: str, script: str, prereqs: list[str]) -> bool:
    for req in prereqs:
        if not (ROOT / req).exists():
            print(f"  [skip] {name}: prerequisite missing - {req}")
            return False
    print(f"\n-- {name} --")
    script_parts = shlex.split(script)
    result = subprocess.run([PYTHON, str(ROOT / "scripts" / script_parts[0]), *script_parts[1:]], cwd=ROOT)
    if result.returncode != 0:
        print(f"  [FAIL] {name}")
        return False
    print("  [ok]")
    return True


def copy_to_web() -> None:
    files = [
        "dao_metrics.json",
        "sankey_impact.json",
        "sankey_workstream.json",
        "sport_funding.json",
        "milestones.json",
        "members.json",
    ]
    dest = ROOT / "web" / "public" / "data"
    dest.mkdir(parents=True, exist_ok=True)
    for filename in files:
        src = ROOT / "data" / filename
        if src.exists():
            shutil.copy(src, dest / filename)
            print(f"  copied {filename}")


def main() -> None:
    if DERIVE_ONLY:
        print("\n-- derive-only mode --")
        failed: list[str] = []
        for step in DERIVE_ONLY_STEPS:
            if not run_step(*step):
                failed.append(step[0])

        print("\n-- copy to web --")
        copy_to_web()
        if failed:
            print(f"\nFailed: {', '.join(failed)}")
            sys.exit(1)
        print("\nAll steps completed.")
        return

    failed: list[str] = []

    print("\n-- Phase 1: syncing (parallel) --")
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(run_step, *step): step[0] for step in PARALLEL_STEPS}
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            ok = future.result()
            print(f"  {'[ok]' if ok else '[FAIL]'} {name}")
            if not ok:
                failed.append(name)

    print("\n-- Phase 2: enriching + deriving --")
    for name, script, prereqs in SEQUENTIAL_STEPS:
        if not run_step(name, script, prereqs):
            failed.append(name)

    if WEEKLY_SNAPSHOT_VOTES:
        print("\n-- Phase 3: weekly snapshot votes --")
        for name, script, prereqs in WEEKLY_STEPS:
            if not run_step(name, script, prereqs):
                failed.append(name)

    print("\n-- copy to web --")
    copy_to_web()

    rec_path = ROOT / "reports" / "reconciliation.json"
    if rec_path.exists():
        rec = json.loads(rec_path.read_text(encoding="utf-8"))
        status = "\u2713 RECONCILED" if rec.get("reconciled") else "\u26a0 DISCREPANCY"
        print(
            f"\nTREASURY {status} · gap ${rec.get('gap_usd', 0):,.0f} · "
            f"spend coverage {rec.get('spend_coverage_pct', 0)}%"
        )

    if failed:
        print(f"\nFailed: {', '.join(failed)}")
        sys.exit(1)

    print("\nAll steps completed.")


if __name__ == "__main__":
    main()

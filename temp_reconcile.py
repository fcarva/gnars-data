from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ETH_PRICE = 2800.0
ROOT = Path(__file__).resolve().parents[1]


def load_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    rows = payload.get("records")
    return rows if isinstance(rows, list) else []


def reconcile() -> dict:
    auctions_path = ROOT / "raw" / "auctions_all.json"
    auction_usd = 0.0
    if auctions_path.exists():
        auction_rows = load_records(auctions_path)
        auction_eth = sum(float(row.get("amount_eth") or row.get("amount") or 0) for row in auction_rows)
        auction_usd = auction_eth * ETH_PRICE

    spend_rows = load_records(ROOT / "data" / "spend_ledger.json")
    spend_usdc = sum(float(row.get("amount") or 0) for row in spend_rows if str(row.get("asset") or row.get("asset_symbol") or "").upper() == "USDC")
    spend_eth = sum(float(row.get("amount") or 0) for row in spend_rows if str(row.get("asset") or row.get("asset_symbol") or "").upper() == "ETH")
    spend_usd = spend_usdc + (spend_eth * ETH_PRICE)

    treasury_payload = json.loads((ROOT / "data" / "treasury.json").read_text(encoding="utf-8"))
    current_usd = float(
        treasury_payload.get("total_usd")
        or treasury_payload.get("overview", {}).get("treasury_page_total_value_usd")
        or 0
    )

    expected = auction_usd - spend_usd
    gap = abs(expected - current_usd)
    reconciled = gap < 1000

    total_records = len(spend_rows)
    with_txhash = sum(1 for row in spend_rows if row.get("tx_hash"))
    with_project = sum(1 for row in spend_rows if row.get("project_id"))
    with_category = sum(
        1
        for row in spend_rows
        if row.get("category") and str(row.get("category")).strip().lower() not in {"uncategorized", "other", ""}
    )

    report = {
        "auction_revenue_usd": round(auction_usd),
        "spend_total_usd": round(spend_usd),
        "expected_balance_usd": round(expected),
        "actual_balance_usd": round(current_usd),
        "gap_usd": round(gap),
        "reconciled": reconciled,
        "spend_records_total": total_records,
        "spend_with_txhash": with_txhash,
        "spend_with_project": with_project,
        "spend_with_category": with_category,
        "spend_coverage_pct": round((with_category / total_records) * 100) if total_records else 0,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    reports_dir = ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "reconciliation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    status = "\u2713 RECONCILED" if reconciled else "\u26a0 DISCREPANCY"
    tx_pct = round((with_txhash / total_records) * 100) if total_records else 0
    project_pct = round((with_project / total_records) * 100) if total_records else 0

    print(
        f"""
TREASURY RECONCILIATION
--------------------------------
Funding in (auctions):    ${auction_usd:>10,.0f}
Spend out (ledger):      -${spend_usd:>10,.0f}
Expected balance:         ${expected:>10,.0f}
Actual balance:           ${current_usd:>10,.0f}
Gap:                      ${gap:>10,.0f}
Status: {status}
--------------------------------
Spend ledger coverage:
  Total records:          {total_records}
  With tx_hash:           {with_txhash}  ({tx_pct}%)
  With project_id:        {with_project}  ({project_pct}%)
  With category:          {with_category}  ({report['spend_coverage_pct']}%)
"""
    )

    return report


if __name__ == "__main__":
    reconcile()

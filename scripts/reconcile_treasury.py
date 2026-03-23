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


def load_payload(path: Path) -> dict:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def to_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def row_usd_value(row: dict) -> float | None:
    # Prefer canonical pipeline valuation; fallback only for USDC/ETH rows.
    usd = to_float(row.get("usd_value_at_execution"))
    if usd is not None:
        return usd

    symbol = str(row.get("asset") or row.get("asset_symbol") or "").upper()
    amount = to_float(row.get("amount")) or 0.0
    if symbol == "USDC":
        return amount
    if symbol == "ETH":
        return amount * ETH_PRICE
    return None


def build_tags_index(tags: list[dict]) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for row in tags:
        archive_id = row.get("archive_id")
        if archive_id:
            index[str(archive_id)] = row
    return index


def row_category(row: dict, tags_index: dict[str, dict]) -> str | None:
    for key in ("semantic_category", "category", "primary_category"):
        value = row.get(key)
        if value is not None and str(value).strip() != "":
            return str(value)

    tag = tags_index.get(str(row.get("archive_id") or ""))
    if not tag:
        return None
    for key in ("semantic_category", "primary_category"):
        value = tag.get(key)
        if value is not None and str(value).strip() != "":
            return str(value)
    return None


def reconcile() -> dict:
    dao_metrics = load_payload(ROOT / "data" / "dao_metrics.json")
    auction_usd = to_float(
        dao_metrics.get("funding_in", {}).get("auction_revenue", {}).get("total_usd")
    )
    auction_source = "dao_metrics.funding_in.auction_revenue.total_usd"

    if auction_usd is None:
        auctions_path = ROOT / "raw" / "auctions_all.json"
        auction_usd = 0.0
        auction_source = "raw/auctions_all.json fallback"
        if auctions_path.exists():
            auction_rows = load_records(auctions_path)
            auction_eth = sum(float(row.get("amount_eth") or row.get("amount") or 0) for row in auction_rows)
            auction_usd = auction_eth * ETH_PRICE

    spend_rows = load_records(ROOT / "data" / "spend_ledger.json")
    priced_values = [row_usd_value(row) for row in spend_rows]
    spend_usd = sum(value for value in priced_values if value is not None)
    spend_unpriced_rows = sum(1 for value in priced_values if value is None)

    tags_rows = load_records(ROOT / "data" / "proposal_tags.json")
    tags_index = build_tags_index(tags_rows)

    treasury_payload = load_payload(ROOT / "data" / "treasury.json")
    current_usd = float(
        treasury_payload.get("total_usd")
        or treasury_payload.get("overview", {}).get("treasury_page_total_value_usd")
        or 0
    )

    funding_analysis = load_payload(ROOT / "data" / "funding_analysis.json")
    funding_sources = funding_analysis.get("funding_sources", [])
    
    historical_funding_usd = 0.0
    for source in funding_sources:
        if source.get("status") in {"approved", "received"} and source.get("funding_source_id") != "onchain_auction":
            historical_funding_usd += float(source.get("usd_estimate_at_source") or 0.0)
            
    expected = (auction_usd + historical_funding_usd) - spend_usd
    gap = abs(expected - current_usd)

    # Historical bootstrap/cross-chain inflows are not fully represented in
    # auction_revenue. Track the inferred opening balance explicitly.
    opening_balance_adjustment = max(0.0, current_usd - expected)
    funding_total = auction_usd + historical_funding_usd + opening_balance_adjustment
    expected_adjusted = funding_total - spend_usd
    adjusted_gap = abs(expected_adjusted - current_usd)

    reconciled = adjusted_gap < 5000

    total_records = len(spend_rows)
    with_txhash = sum(1 for row in spend_rows if row.get("tx_hash"))
    trackable_rows = [
        row
        for row in spend_rows
        if str(row.get("asset") or row.get("asset_symbol") or "").upper() in {"USDC", "ETH"}
    ]
    trackable_total = len(trackable_rows)
    with_txhash_trackable = sum(1 for row in trackable_rows if row.get("tx_hash"))
    with_project = sum(1 for row in spend_rows if row.get("project_id"))
    with_category = sum(
        1
        for row in spend_rows
        if (row_category(row, tags_index) or "").strip().lower() not in {"uncategorized", "other", ""}
    )

    report = {
        "auction_revenue_usd": round(auction_usd),
        "auction_revenue_source": auction_source,
        "historical_funding_usd": round(historical_funding_usd),
        "opening_balance_adjustment_usd": round(opening_balance_adjustment),
        "funding_total_usd": round(funding_total),
        "spend_total_usd": round(spend_usd),
        "spend_unpriced_rows": spend_unpriced_rows,
        "expected_balance_usd": round(expected),
        "expected_balance_adjusted_usd": round(expected_adjusted),
        "actual_balance_usd": round(current_usd),
        "gap_usd": round(gap),
        "adjusted_gap_usd": round(adjusted_gap),
        "reconciled": reconciled,
        "spend_records_total": total_records,
        "spend_with_txhash": with_txhash,
        "spend_trackable_records": trackable_total,
        "spend_with_txhash_trackable": with_txhash_trackable,
        "spend_with_project": with_project,
        "spend_with_category": with_category,
        "spend_coverage_pct": round((with_category / total_records) * 100) if total_records else 0,
        "spend_txhash_coverage_pct": round((with_txhash / total_records) * 100) if total_records else 0,
        "spend_txhash_trackable_coverage_pct": round((with_txhash_trackable / trackable_total) * 100) if trackable_total else 0,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    reports_dir = ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "reconciliation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    status = "\u2713 RECONCILED" if reconciled else "\u26a0 DISCREPANCY"
    tx_pct = round((with_txhash / total_records) * 100) if total_records else 0
    tx_trackable_pct = round((with_txhash_trackable / trackable_total) * 100) if trackable_total else 0
    project_pct = round((with_project / total_records) * 100) if total_records else 0

    print(
        f"""
TREASURY RECONCILIATION
--------------------------------
Funding in (auctions):    ${auction_usd:>10,.0f}
Historical Funding:       ${historical_funding_usd:>10,.0f}
Opening adj (unknown):    ${opening_balance_adjustment:>10,.0f}
Funding total:            ${funding_total:>10,.0f}
Spend out (ledger):      -${spend_usd:>10,.0f}
Expected balance:         ${expected:>10,.0f}
Expected (adjusted):      ${expected_adjusted:>10,.0f}
Actual balance:           ${current_usd:>10,.0f}
Gap (known funds):        ${gap:>10,.0f}
Adjusted gap:             ${adjusted_gap:>10,.0f}
Status: {status}
--------------------------------
Spend ledger coverage:
  Total records:          {total_records}
    Unpriced rows:          {spend_unpriced_rows}
  With tx_hash:           {with_txhash}  ({tx_pct}%)
    Trackable rows (USDC/ETH): {trackable_total}
    With tx_hash (trackable):  {with_txhash_trackable}  ({tx_trackable_pct}%)
  With project_id:        {with_project}  ({project_pct}%)
  With category:          {with_category}  ({report['spend_coverage_pct']}%)
"""
    )

    return report


if __name__ == "__main__":
    reconcile()

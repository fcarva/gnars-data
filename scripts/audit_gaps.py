from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REPORTS = ROOT / "reports"


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def records(payload: dict) -> list[dict]:
    rows = payload.get("records")
    return rows if isinstance(rows, list) else []


def has_value(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


def write_report(lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / "data_gaps.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def check_sankey_completeness(spend: list[dict], dao_metrics: dict) -> str:
    eth_price = 2800
    total_in_ledger = sum(
        (row.get("amount", 0) if str(row.get("asset") or row.get("asset_symbol") or "").upper() == "USDC" else row.get("amount", 0) * eth_price)
        for row in spend
    )
    categorized = sum(
        (row.get("amount", 0) if str(row.get("asset") or row.get("asset_symbol") or "").upper() == "USDC" else row.get("amount", 0) * eth_price)
        for row in spend
        if row.get("category") and str(row.get("category")).strip() not in {"uncategorized", "Other", ""}
    )
    sankey_total = (dao_metrics.get("sankey_total_k", 0) or 0) * 1000
    coverage = round((categorized / total_in_ledger) * 100) if total_in_ledger else 0

    return f"""
SANKEY COMPLETENESS
--------------------------------
Total in spend_ledger:    ${total_in_ledger:>10,.0f}
Categorized (in Sankey):  ${categorized:>10,.0f}
Sankey total (from JSON): ${sankey_total:>10,.0f}
Coverage:                  {coverage}%
Drift (ledger vs sankey):  ${abs(categorized - sankey_total):>10,.0f}
"""


def main() -> None:
    spend = records(load(DATA / "spend_ledger.json"))
    tags = records(load(DATA / "proposal_tags.json"))
    members = records(load(DATA / "members.json"))
    props = records(load(DATA / "proposals_archive.json"))
    dao_metrics = load(DATA / "dao_metrics.json")

    spend_no_project = sum(1 for row in spend if not has_value(row.get("project_id")))
    spend_no_category = sum(
        1
        for row in spend
        if not has_value(row.get("semantic_category"))
        and not has_value(row.get("category"))
        and not has_value(row.get("primary_category"))
    )
    spend_no_sport = sum(1 for row in spend if not has_value(row.get("sport")))
    spend_no_recipient_name = sum(
        1 for row in spend if not has_value(row.get("recipient_name")) and not has_value(row.get("recipient_display_name"))
    )

    tags_no_semantic = sum(1 for row in tags if not has_value(row.get("semantic_category")))
    tags_no_sport = sum(1 for row in tags if not has_value(row.get("sport")))
    tags_no_breakdown = sum(1 for row in tags if not has_value(row.get("capital_breakdown")))
    tags_no_confidence = sum(
        1 for row in tags if row.get("semantic_confidence") is None and row.get("confidence") is None
    )

    members_athlete = [
        row
        for row in members
        if "athlete" in [str(v).lower() for v in row.get("tags", [])]
        or "athlete" in [str(v).lower() for v in row.get("domains", [])]
    ]
    members_no_sport = sum(1 for row in members_athlete if not has_value(row.get("sport")))
    members_no_totals = sum(
        1
        for row in members
        if row.get("total_received_usdc") is None and row.get("total_received_eth") is None
    )

    proposals_uncategorized = sum(
        1
        for row in props
        if not has_value(row.get("category"))
        and not has_value(row.get("primary_category"))
        and not has_value(row.get("semantic_category"))
    )

    gaps = {
        "spend_no_project": spend_no_project,
        "spend_no_category": spend_no_category,
        "spend_no_sport": spend_no_sport,
        "spend_no_recipient_name": spend_no_recipient_name,
        "tags_no_semantic": tags_no_semantic,
        "tags_no_sport": tags_no_sport,
        "tags_no_capital_breakdown": tags_no_breakdown,
        "tags_no_confidence": tags_no_confidence,
        "members_no_sport": members_no_sport,
        "members_no_totals": members_no_totals,
        "proposals_uncategorized": proposals_uncategorized,
    }

    lines = ["# Data Gaps Report", "", "| Field | Missing |", "|---|---|"]
    lines.extend(f"| {k} | {v} |" for k, v in gaps.items())

    sankey_report = check_sankey_completeness(spend, dao_metrics)
    lines.extend(["", "## Sankey Completeness", "", "```text", sankey_report.strip("\n"), "```"])

    write_report(lines)
    print("\n".join(lines))
    print(sankey_report)


if __name__ == "__main__":
    main()

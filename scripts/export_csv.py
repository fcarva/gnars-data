from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
EXPORTS_DIR = ROOT / "exports"


def load_json(name: str) -> dict[str, Any]:
    path = DATA_DIR / f"{name}.json"
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_csv(filename: str, rows: list[dict[str, Any]]) -> None:
    path = EXPORTS_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"[ok] wrote {path.relative_to(ROOT)}")


def export_proposals() -> None:
    data = load_json("proposals")
    rows = []
    for record in data["records"]:
        rows.append(
            {
                "proposal_id": record["proposal_id"],
                "number": record["number"],
                "chain": record["chain"],
                "title": record["title"],
                "status": record["status"],
                "proposer_display_name": record["proposer"]["display_name"],
                "proposer_address": record["proposer"]["address"],
                "ended_at": record["timing"]["ended_at"],
                "votes_for": record["voting"]["for"],
                "votes_against": record["voting"]["against"],
                "votes_abstain": record["voting"]["abstain"],
                "threshold": record["voting"]["threshold"],
                "budget_eth": record["budget"]["eth"],
                "budget_usdc": record["budget"]["usdc"],
                "budget_usd_estimate": record["budget"]["usd_estimate"],
                "tags": "|".join(record["tags"]),
                "proposal_url": record["links"]["proposal_url"]
            }
        )
    write_csv("proposals.csv", rows)


def export_members() -> None:
    data = load_json("members")
    rows = []
    for record in data["records"]:
        rows.append(
            {
                "member_id": record["member_id"],
                "display_name": record["display_name"],
                "address": record["address"],
                "role": record["role"],
                "status": record["status"],
                "domains": "|".join(record["domains"]),
                "token_count": record["metrics"]["token_count"],
                "active_votes": record["metrics"]["active_votes"],
                "votes_count": record["metrics"]["votes_count"],
                "attendance_pct": record["metrics"]["attendance_pct"],
                "like_pct": record["metrics"]["like_pct"],
                "member_url": record["links"]["member_url"],
                "farcaster": record["links"]["farcaster"],
                "github": record["links"]["github"]
            }
        )
    write_csv("members.csv", rows)


def export_treasury() -> None:
    data = load_json("treasury")
    rows = []
    for record in data["records"]:
        rows.append(
            {
                "as_of": data["as_of"],
                "wallet_address": data["wallet"]["address"],
                "asset_id": record["asset_id"],
                "asset_type": record["asset_type"],
                "symbol": record["symbol"],
                "name": record["name"],
                "token_address": record["token_address"],
                "amount": record["amount"],
                "value_usd": record["value_usd"],
                "source_url": record["source_url"]
            }
        )
    write_csv("treasury.csv", rows)


def export_projects() -> None:
    data = load_json("projects")
    rows = []
    for record in data["records"]:
        rows.append(
            {
                "project_id": record["project_id"],
                "name": record["name"],
                "status": record["status"],
                "category": record["category"],
                "origin_proposals": "|".join(record["origin_proposals"]),
                "owner_addresses": "|".join(record["owner_addresses"]),
                "budget_eth": record["budget"]["eth"],
                "budget_usdc": record["budget"]["usdc"],
                "objective": record["objective"],
                "outputs": "|".join(record["outputs"]),
                "kpis": "|".join(record["kpis"])
            }
        )
    write_csv("projects.csv", rows)


def export_sources() -> None:
    data = load_json("sources")
    rows = []
    for record in data["records"]:
        rows.append(
            {
                "source_id": record["source_id"],
                "name": record["name"],
                "type": record["type"],
                "status": record["status"],
                "url": record["url"],
                "sync_mode": record["sync_mode"],
                "cadence": record["cadence"],
                "sections": "|".join(record["sections"]),
                "notes": record["notes"]
            }
        )
    write_csv("sources.csv", rows)


def main() -> int:
    export_proposals()
    export_members()
    export_treasury()
    export_projects()
    export_sources()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


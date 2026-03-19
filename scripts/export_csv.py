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


def json_cell(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


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


def export_contracts() -> None:
    data = load_json("contracts")
    rows = []
    for record in data["records"]:
        rows.append(
            {
                "contract_id": record["contract_id"],
                "ecosystem": record["ecosystem"],
                "network": record["network"],
                "chain_id": record["chain_id"],
                "address": record["address"],
                "label": record["label"],
                "kind": record["kind"],
                "status": record["status"],
                "proxy_for": record["proxy_for"],
                "explorer_url": record["explorer_url"],
                "source_urls": "|".join(record["source_urls"]),
                "notes": record["notes"]
            }
        )
    write_csv("contracts.csv", rows)


def export_proposals_archive() -> None:
    data = load_json("proposals_archive")
    rows = []
    for record in data["records"]:
        rows.append(
            {
                "archive_id": record["archive_id"],
                "platform": record["platform"],
                "space": record["space"],
                "chain": record["chain"],
                "proposal_key": record["proposal_key"],
                "proposal_number": record["proposal_number"],
                "title": record["title"],
                "status": record["status"],
                "status_display": record["status_display"],
                "proposer": record["proposer"],
                "proposer_label": record["proposer_label"],
                "created_at": record["created_at"],
                "start_at": record["start_at"],
                "end_at": record["end_at"],
                "snapshot_block": record["snapshot_block"],
                "quorum": record["quorum"],
                "choices_json": json_cell(record["choices"]),
                "scores_by_choice_json": json_cell(record["scores_by_choice"]),
                "scores_total": record["scores_total"],
                "transaction_count": len(record["transactions"]),
                "vote_count": len(record["votes"]),
                "cover_image_url": record["cover_image_url"],
                "content_summary": record["content_summary"],
                "content_markdown": record["content_markdown"],
                "source_url": record["links"]["source_url"],
                "canonical_url": record["links"]["canonical_url"],
                "discussion_url": record["links"]["discussion_url"],
                "explorer_url": record["links"]["explorer_url"],
                "raw_snapshot": record.get("raw_snapshot"),
            }
        )
    write_csv("proposals_archive.csv", rows)


def export_proposal_tags() -> None:
    data = load_json("proposal_tags")
    rows = []
    for record in data["records"]:
        rows.append(
            {
                "archive_id": record["archive_id"],
                "title": record["title"],
                "platform": record["platform"],
                "chain": record["chain"],
                "proposal_number": record["proposal_number"],
                "source_url": record["source_url"],
                "tagging_status": record["tagging_status"],
                "review_state": record["review_state"],
                "scope": record["scope"],
                "primary_category": record["primary_category"],
                "secondary_categories": "|".join(record["secondary_categories"]),
                "funding_category": record["funding_category"],
                "lifecycle_stage": record["lifecycle_stage"],
                "entities": "|".join(record["entities"]),
                "confidence": record["confidence"],
                "requires_human_review": record["requires_human_review"],
                "model_provider": record["model_provider"],
                "model_name": record["model_name"],
                "guidelines_version": record["guidelines_version"],
                "rationale": record["rationale"],
                "notes": record["notes"],
                "updated_at": record["updated_at"],
            }
        )
    write_csv("proposal_tags.csv", rows)


def export_proposal_transactions() -> None:
    data = load_json("proposals_archive")
    rows = []
    for record in data["records"]:
        for transaction in record["transactions"]:
            rows.append(
                {
                    "archive_id": record["archive_id"],
                    "platform": record["platform"],
                    "chain": record["chain"],
                    "proposal_number": record["proposal_number"],
                    "title": record["title"],
                    "source_url": record["links"]["source_url"],
                    "index": transaction.get("index"),
                    "kind": transaction.get("kind"),
                    "target": transaction.get("target"),
                    "token_contract": transaction.get("token_contract"),
                    "sender": transaction.get("sender"),
                    "recipient": transaction.get("recipient"),
                    "token_id": transaction.get("token_id"),
                    "amount_eth": transaction.get("amount_eth"),
                    "amount_raw": transaction.get("amount_raw"),
                    "amount_normalized": transaction.get("amount_normalized"),
                    "value_wei": transaction.get("value_wei"),
                    "selector": transaction.get("selector"),
                    "calldata": transaction.get("calldata"),
                }
            )
    write_csv("proposal_transactions.csv", rows)


def export_proposal_votes() -> None:
    data = load_json("proposals_archive")
    rows = []
    for record in data["records"]:
        for vote in record["votes"]:
            rows.append(
                {
                    "archive_id": record["archive_id"],
                    "platform": record["platform"],
                    "space": record["space"],
                    "chain": record["chain"],
                    "proposal_number": record["proposal_number"],
                    "title": record["title"],
                    "source_url": record["links"]["source_url"],
                    "voter": vote.get("voter"),
                    "voter_ens_name": vote.get("voterEnsName"),
                    "choice_json": json_cell(vote.get("choice")),
                    "votes_raw": vote.get("votes"),
                    "vp": vote.get("vp"),
                    "vp_by_strategy_json": json_cell(vote.get("vp_by_strategy")),
                    "reason": vote.get("reason"),
                    "created": vote.get("created"),
                    "timestamp": vote.get("timestamp"),
                    "ipfs": vote.get("ipfs"),
                    "transaction_hash": vote.get("transactionHash"),
                }
            )
    write_csv("proposal_votes.csv", rows)


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


def export_people() -> None:
    data = load_json("people")
    rows = []
    for record in data["records"]:
        rows.append(
            {
                "person_id": record["person_id"],
                "slug": record["slug"],
                "display_name": record["display_name"],
                "address": record["address"],
                "status": record["status"],
                "role": record["role"],
                "roles": "|".join(record["roles"]),
                "tags": "|".join(record["tags"]),
                "domains": "|".join(record["domains"]),
                "holder_token_count": record["governance"]["holder_token_count"],
                "delegated_token_count": record["governance"]["delegated_token_count"],
                "active_votes": record["governance"]["active_votes"],
                "votes_count": record["governance"]["votes_count"],
                "attendance_pct": record["governance"]["attendance_pct"],
                "like_pct": record["governance"]["like_pct"],
                "proposals_authored_count": record["governance"]["proposals_authored_count"],
                "votes_cast_count": record["governance"]["votes_cast_count"],
                "eth_received": record["receipts"]["eth_received"],
                "usdc_received": record["receipts"]["usdc_received"],
                "gnars_received": record["receipts"]["gnars_received"],
                "fungible_transfer_count": record["receipts"]["fungible_transfer_count"],
                "nft_received_count": record["receipts"]["nft_received_count"],
                "member_url": record["identity"]["member_url"],
                "farcaster": record["identity"]["farcaster"],
                "github": record["identity"]["github"],
                "authored_proposals": "|".join(record["relationships"]["authored_proposals"]),
                "owned_projects": "|".join(record["relationships"]["owned_projects"]),
                "related_projects": "|".join(record["relationships"]["related_projects"]),
                "notes": record["notes"],
            }
        )
    write_csv("people.csv", rows)


def export_treasury() -> None:
    data = load_json("treasury")
    rows = []
    for record in data["records"]:
        rows.append(
            {
                "as_of": data["as_of"],
                "wallet_address": data["wallet"]["address"],
                "homepage_treasury_label_usd": data["overview"]["homepage_treasury_label_usd"],
                "treasury_page_total_value_usd": data["overview"]["treasury_page_total_value_usd"],
                "treasury_page_display_total_usd": data["overview"]["treasury_page_display_total_usd"],
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


def export_project_updates() -> None:
    data = load_json("project_updates")
    rows = []
    for record in data["records"]:
        rows.append(
            {
                "update_id": record["update_id"],
                "project_id": record["project_id"],
                "date": record["date"],
                "title": record["title"],
                "kind": record["kind"],
                "status": record["status"],
                "summary": record["summary"],
                "related_proposals": "|".join(record["related_proposals"]),
                "related_addresses": "|".join(record["related_addresses"]),
                "links": "|".join(record["links"]),
                "notes": record["notes"],
            }
        )
    write_csv("project_updates.csv", rows)


def export_project_rollups() -> None:
    data = load_json("project_rollups")
    rows = []
    for record in data["records"]:
        rows.append(
            {
                "project_id": record["project_id"],
                "slug": record["slug"],
                "name": record["name"],
                "status": record["status"],
                "category": record["category"],
                "origin_proposals": "|".join(record["origin_proposals"]),
                "owner_addresses": "|".join(record["owner_addresses"]),
                "budget_eth": record["budget"]["eth"],
                "budget_usdc": record["budget"]["usdc"],
                "budget_gnars": record["budget"]["gnars"],
                "spent_eth": record["spent"]["eth"],
                "spent_usdc": record["spent"]["usdc"],
                "spent_gnars": record["spent"]["gnars"],
                "utilization_eth_pct": record["utilization_pct"]["eth"],
                "utilization_usdc_pct": record["utilization_pct"]["usdc"],
                "utilization_gnars_pct": record["utilization_pct"]["gnars"],
                "updates_count": record["updates_count"],
                "last_update_date": record["last_update_date"],
                "recipient_count": len(record["recipients"]),
                "nft_receipt_count": len(record["nft_receipts"]),
                "objective": record["objective"],
                "outputs": "|".join(record["outputs"]),
                "kpis": "|".join(record["kpis"]),
                "notes": record["notes"],
            }
        )
    write_csv("project_rollups.csv", rows)


def export_spend_ledger() -> None:
    data = load_json("spend_ledger")
    rows = []
    for record in data["records"]:
        rows.append(
            {
                "ledger_id": record["ledger_id"],
                "archive_id": record["archive_id"],
                "proposal_key": record["proposal_key"],
                "proposal_number": record["proposal_number"],
                "title": record["title"],
                "status": record["status"],
                "chain": record["chain"],
                "project_id": record["project_id"],
                "project_name": record["project_name"],
                "proposer": record["proposer"],
                "proposal_end_at": record["proposal_end_at"],
                "proposal_created_at": record["proposal_created_at"],
                "asset_symbol": record["asset_symbol"],
                "asset_name": record["asset_name"],
                "asset_kind": record["asset_kind"],
                "token_contract": record["token_contract"],
                "recipient_address": record["recipient_address"],
                "recipient_display_name": record["recipient_display_name"],
                "amount": record["amount"],
                "source_url": record["source_url"],
                "canonical_url": record["canonical_url"],
            }
        )
    write_csv("spend_ledger.csv", rows)


def export_dao_metrics() -> None:
    data = load_json("dao_metrics")
    overview = data["overview"]
    rows = [
        {
            "as_of": data["as_of"],
            "proposal_count": overview["proposal_count"],
            "active_proposal_count": overview["active_proposal_count"],
            "people_count": overview["people_count"],
            "holders_count": overview["holders_count"],
            "delegates_count": overview["delegates_count"],
            "contributors_count": overview["contributors_count"],
            "athletes_count": overview["athletes_count"],
            "recipients_count": overview["recipients_count"],
            "proposers_count": overview["proposers_count"],
            "workstream_count": overview["workstream_count"],
            "treasury_assets_count": overview["treasury_assets_count"],
            "treasury_total_value_usd": overview["treasury_total_value_usd"],
            "outflows_eth": overview["outflows_eth"],
            "outflows_usdc": overview["outflows_usdc"],
            "outflows_gnars": overview["outflows_gnars"],
            "fungible_transfer_count": overview["fungible_transfer_count"],
            "nft_transfer_count": overview["nft_transfer_count"],
            "proposal_status_counts_json": json_cell(overview["proposal_status_counts"]),
            "leaderboards_json": json_cell(data["leaderboards"]),
            "recent_json": json_cell(data["recent"]),
        }
    ]
    write_csv("dao_metrics.csv", rows)


def export_timeline_events() -> None:
    data = load_json("timeline_events")
    rows = []
    for record in data["records"]:
        rows.append(
            {
                "event_id": record["event_id"],
                "date": record["date"],
                "title": record["title"],
                "summary": record["summary"],
                "kind": record["kind"],
                "status": record["status"],
                "project_id": record["project_id"],
                "project_name": record["project_name"],
                "archive_id": record["archive_id"],
                "proposal_number": record["proposal_number"],
                "people_addresses": "|".join(record["people_addresses"]),
                "proposal_ids": "|".join(record["proposal_ids"]),
                "links": "|".join(record["links"]),
                "source": record["source"],
                "thumbnail_url": record["thumbnail_url"],
            }
        )
    write_csv("timeline_events.csv", rows)


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
    export_contracts()
    export_proposals()
    export_proposals_archive()
    export_proposal_tags()
    export_proposal_transactions()
    export_proposal_votes()
    export_members()
    export_people()
    export_treasury()
    export_projects()
    export_project_updates()
    export_project_rollups()
    export_spend_ledger()
    export_dao_metrics()
    export_timeline_events()
    export_sources()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

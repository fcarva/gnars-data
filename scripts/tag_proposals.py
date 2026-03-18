from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
ARCHIVE_PATH = DATA_DIR / "proposals_archive.json"
TAGS_PATH = DATA_DIR / "proposal_tags.json"
GUIDELINES_VERSION = "2026-03-18"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def isoformat_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def archive_sort_key(record: dict[str, Any]) -> tuple[str, str]:
    return (record.get("created_at") or "", record["archive_id"])


def normalized_title(proposal: dict[str, Any]) -> str:
    raw_title = (proposal.get("title") or "").strip()
    if not raw_title:
        return proposal["archive_id"]
    first_line = raw_title.splitlines()[0].strip()
    return first_line.lstrip("#").strip() or raw_title


def seed_tag_record(proposal: dict[str, Any], *, scope: str, timestamp: str) -> dict[str, Any]:
    return {
        "archive_id": proposal["archive_id"],
        "title": normalized_title(proposal),
        "platform": proposal["platform"],
        "chain": proposal["chain"],
        "proposal_number": proposal["proposal_number"],
        "source_url": proposal["links"]["source_url"],
        "tagging_status": "queued",
        "review_state": "pending",
        "scope": scope,
        "primary_category": None,
        "secondary_categories": [],
        "funding_category": None,
        "lifecycle_stage": None,
        "entities": [],
        "confidence": None,
        "requires_human_review": True,
        "model_provider": None,
        "model_name": None,
        "guidelines_version": GUIDELINES_VERSION,
        "rationale": None,
        "notes": "Seeded for pilot tagging queue.",
        "updated_at": timestamp,
    }


def ensure_top_level_shape(payload: dict[str, Any], *, timestamp: str) -> dict[str, Any]:
    payload.setdefault("dataset", "proposal_tags")
    payload.setdefault("version", 1)
    payload.setdefault("records", [])
    payload["as_of"] = timestamp
    return payload


def init_pilot(count: int, *, scope: str) -> int:
    archive = load_json(ARCHIVE_PATH)
    payload = ensure_top_level_shape(load_json(TAGS_PATH), timestamp=isoformat_utc(utc_now()))

    candidates = sorted(archive["records"], key=archive_sort_key, reverse=True)[:count]
    target_ids = {proposal["archive_id"] for proposal in candidates}
    kept_records = [
        record
        for record in payload["records"]
        if record.get("scope") != scope or record["archive_id"] in target_ids
    ]
    payload["records"] = kept_records
    existing = {record["archive_id"]: record for record in payload["records"]}

    added = 0
    timestamp = isoformat_utc(utc_now())
    for proposal in candidates:
        if proposal["archive_id"] in existing:
            existing_record = existing[proposal["archive_id"]]
            existing_record["title"] = normalized_title(proposal)
            existing_record["platform"] = proposal["platform"]
            existing_record["chain"] = proposal["chain"]
            existing_record["proposal_number"] = proposal["proposal_number"]
            existing_record["source_url"] = proposal["links"]["source_url"]
            existing_record["guidelines_version"] = GUIDELINES_VERSION
            continue
        payload["records"].append(seed_tag_record(proposal, scope=scope, timestamp=timestamp))
        existing[proposal["archive_id"]] = payload["records"][-1]
        added += 1

    payload["records"] = sorted(payload["records"], key=lambda record: record["updated_at"], reverse=True)
    payload["as_of"] = timestamp
    write_json(TAGS_PATH, payload)
    return added


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed and maintain proposal tagging queues.")
    parser.add_argument(
        "--init-pilot",
        type=int,
        default=0,
        help="Ensure the proposal_tags dataset contains at least N seeded proposals.",
    )
    parser.add_argument(
        "--scope",
        default="pilot-30",
        help="Scope label to stamp onto newly seeded proposal tag records.",
    )
    args = parser.parse_args()

    if args.init_pilot <= 0:
        print("[ok] no proposal tagging changes requested")
        return 0

    added = init_pilot(args.init_pilot, scope=args.scope)
    print(f"[ok] proposal_tags initialized or refreshed; added {added} queued records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save(path: Path, payload: dict) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def normalize(value: object) -> str:
    return str(value or "").strip().lower()


def member_name(member: dict, address: str) -> str:
    return (
        str(member.get("display_name") or "").strip()
        or str(member.get("member_id") or "").strip()
        or (address[:6] + "..." + address[-4:] if len(address) > 10 else address)
    )


def pick_category(tag: dict) -> str:
    return (
        tag.get("semantic_category")
        or tag.get("primary_category")
        or tag.get("funding_category")
        or "uncategorized"
    )


def main() -> None:
    spend_payload = load(DATA / "spend_ledger.json")
    tags_payload = load(DATA / "proposal_tags.json")
    members_payload = load(DATA / "members.json")

    spend = spend_payload.get("records") or []
    tags = tags_payload.get("records") or []
    members = members_payload.get("records") or []

    tag_map = {str(t.get("archive_id") or ""): t for t in tags}
    mem_map = {normalize(m.get("address")): m for m in members if m.get("address")}

    enriched = 0
    for row in spend:
        archive_id = str(row.get("archive_id") or "")
        tag = tag_map.get(archive_id)

        if not row.get("project_id") and archive_id:
            row["project_id"] = archive_id

        if tag:
            row["category"] = pick_category(tag)
            if tag.get("sport") is not None:
                row["sport"] = tag.get("sport")
            if tag.get("capital_breakdown") is not None:
                row["capital_breakdown"] = tag.get("capital_breakdown")
            if tag.get("semantic_confidence") is not None and row.get("confidence") is None:
                row["confidence"] = tag.get("semantic_confidence")
            elif tag.get("confidence") is not None and row.get("confidence") is None:
                row["confidence"] = tag.get("confidence")

        recipient = normalize(row.get("recipient_address") or row.get("recipient"))
        member = mem_map.get(recipient)
        if member:
            row["recipient_name"] = member_name(member, recipient)
            if member.get("sport") and not row.get("sport"):
                row["sport"] = member.get("sport")
            row["recipient_sport"] = member.get("sport")
            row["recipient_tags"] = member.get("tags") or member.get("domains") or []

        if row.get("project_id") or row.get("category") or row.get("recipient_name"):
            enriched += 1

    spend_payload["records"] = spend
    save(DATA / "spend_ledger.json", spend_payload)
    print(f"Enriched {enriched}/{len(spend)} spend records with proposal linkage.")


if __name__ == "__main__":
    main()

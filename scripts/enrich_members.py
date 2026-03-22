from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

SPORT_KEYWORDS = {
    "sk8": ["skate", "skateboarding", "street", "park", "vert", "bowl", "trick", "grind", "skater"],
    "surf": ["surf", "surfing", "wave", "wsl", "qs", "longboard", "shortboard", "surfer", "ocean"],
    "bmx": ["bmx", "bike", "bicycle", "dirt", "flatland", "rider", "cycling"],
    "snow": ["snow", "snowboard", "snowboarding", "mountain", "slope", "halfpipe"],
    "mx": ["motocross", "moto", "mx", "dirt bike"],
    "mtb": ["mountain bike", "mtb", "downhill", "trail"],
}


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save(path: Path, payload: dict) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def detect_sport(text: str) -> str | None:
    t = text.lower()
    scores = {sport: sum(1 for kw in kws if kw in t) for sport, kws in SPORT_KEYWORDS.items()}
    best_sport = None
    best_score = 0
    for sport, score in scores.items():
        if score > best_score:
            best_score = score
            best_sport = sport
    return best_sport if best_score > 0 else None


def normalize_address(value: object) -> str:
    return str(value or "").strip().lower()


def _sport_from_person(person: dict) -> str | None:
    explicit = str(person.get("sport") or "").strip().lower()
    if explicit in {"sk8", "surf", "bmx", "snow", "mx", "mtb"}:
        return explicit
    parts = [
        str(person.get("role") or ""),
        str(person.get("headline") or ""),
        str(person.get("history_short") or ""),
        str(person.get("notes") or ""),
        " ".join(str(v or "") for v in (person.get("domains") or [])),
        " ".join(str(v or "") for v in (person.get("tags") or [])),
        " ".join(str(v or "") for v in (person.get("tribes") or [])),
    ]
    return detect_sport(" ".join(parts))


def _build_members_from_people(people_records: list[dict]) -> list[dict]:
    members: list[dict] = []
    for person in people_records:
        address = normalize_address(person.get("address"))
        if not address:
            continue
        identity = person.get("identity") or {}
        governance = person.get("governance") or {}
        receipts = person.get("receipts") or {}
        relationships = person.get("relationships") or {}
        tags = [str(tag).lower() for tag in (person.get("tags") or []) if str(tag or "").strip()]
        sport = _sport_from_person(person)

        members.append(
            {
                "member_id": str(person.get("person_id") or person.get("slug") or address),
                "display_name": str(person.get("display_name") or person.get("address_short") or address),
                "address": address,
                "role": str(person.get("role") or "community member"),
                "status": str(person.get("status") or "active"),
                "domains": [str(value) for value in (person.get("domains") or [])],
                "links": {
                    "member_url": identity.get("member_url") or person.get("member_url"),
                    "farcaster": identity.get("farcaster"),
                    "github": identity.get("github"),
                },
                "metrics": {
                    "token_count": int(governance.get("holder_token_count") or 0),
                    "active_votes": int(governance.get("active_votes") or 0),
                    "votes_count": int(governance.get("votes_count") or 0),
                    "attendance_pct": int(governance.get("attendance_pct") or 0),
                    "like_pct": int(governance.get("like_pct") or 0),
                },
                "notes": str(person.get("notes") or person.get("history_short") or ""),
                "tags": tags,
                "sport": sport,
                "total_received_usdc": float(receipts.get("usdc_received") or 0),
                "total_received_eth": float(receipts.get("eth_received") or 0),
                "funded_proposal_count": len(relationships.get("payout_proposals") or []),
                "proof_record_count": int(person.get("proof_count") or 0),
                "delivery_count": int(person.get("delivery_count") or 0),
                "last_proof_date": None,
            }
        )
    return members


def get_member_tags(member: dict) -> list[str]:
    tags = [str(v).lower() for v in (member.get("tags") or [])]
    domains = [str(v).lower() for v in (member.get("domains") or [])]
    return sorted(set(tags + domains))


def _count_proof_records(
    member_id: str,
    member_address: str,
    timeline_events: list[dict],
) -> tuple[int, str | None]:
    proof_kinds = {"proof", "delivery", "media_proof"}
    lower_member_id = str(member_id or "").strip().lower()

    member_events = []
    for event in timeline_events:
        actor = str(event.get("actor") or "").strip().lower()
        if not lower_member_id or actor != lower_member_id:
            continue

        kind = str(event.get("kind") or "").strip().lower()
        if kind in proof_kinds:
            member_events.append(event)

    count = len(member_events)
    dates = [
        event.get("timestamp") or event.get("created_at") or event.get("date")
        for event in member_events
        if event.get("timestamp") or event.get("created_at") or event.get("date")
    ]
    last = max(dates) if dates else None
    return count, last


def main() -> None:
    members_payload = load(DATA / "members.json")
    people_payload = load(DATA / "people.json")
    spend_payload = load(DATA / "spend_ledger.json")
    props_payload = load(DATA / "proposals_archive.json")
    timeline_payload = load(DATA / "timeline_events.json")

    members = members_payload.get("records") or []
    people_records = people_payload.get("records") if isinstance(people_payload, dict) else []
    seed_has_athletes = any("athlete" in [str(tag).lower() for tag in (row.get("tags") or [])] for row in members)
    if people_records and (len(members) < 50 or not seed_has_athletes):
        members = _build_members_from_people(people_records)
        members_payload["as_of"] = people_payload.get("as_of", members_payload.get("as_of"))
        members_payload["source"] = "people.json"

    spend = spend_payload.get("records") or []
    props = props_payload.get("records") or []
    timeline_events = timeline_payload if isinstance(timeline_payload, list) else timeline_payload.get("records", [])

    addr_to_props: dict[str, list[dict]] = defaultdict(list)
    for p in props:
        proposer = normalize_address(p.get("proposer") or p.get("author") or p.get("address"))
        if proposer:
            addr_to_props[proposer].append(p)

    addr_to_spend: dict[str, list[dict]] = defaultdict(list)
    for s in spend:
        recipient = normalize_address(s.get("recipient_address") or s.get("recipient"))
        if recipient:
            addr_to_spend[recipient].append(s)

    enriched = 0
    for member in members:
        addr = normalize_address(member.get("address"))
        if not addr:
            continue

        tags = get_member_tags(member)
        is_athlete = "athlete" in tags

        if is_athlete and not member.get("sport"):
            authored = addr_to_props.get(addr, [])
            combined_text = " ".join(
                (
                    str(p.get("title") or "")
                    + " "
                    + str(p.get("summary") or "")
                    + " "
                    + str(p.get("description") or "")
                )
                for p in authored
            )
            sport = detect_sport(combined_text)
            if sport:
                member["sport"] = sport
                enriched += 1

        payouts = addr_to_spend.get(addr, [])
        member["total_received_usdc"] = round(
            sum(float(s.get("amount") or 0) for s in payouts if str(s.get("asset_symbol") or "").upper() == "USDC"),
            6,
        )
        member["total_received_eth"] = round(
            sum(float(s.get("amount") or 0) for s in payouts if str(s.get("asset_symbol") or "").upper() == "ETH"),
            6,
        )
        member["funded_proposal_count"] = len(
            {
                str(s.get("archive_id") or "")
                for s in payouts
                if s.get("archive_id")
            }
        )

        count, last = _count_proof_records(
            str(member.get("member_id") or member.get("id") or ""),
            str(member.get("address") or ""),
            timeline_events,
        )
        member["proof_record_count"] = count
        member["last_proof_date"] = last

    members_payload["records"] = members
    save(DATA / "members.json", members_payload)
    print(f"Enriched {enriched} athlete members with sport classification.")


if __name__ == "__main__":
    main()

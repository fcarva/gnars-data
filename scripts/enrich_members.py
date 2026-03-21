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


def get_member_tags(member: dict) -> list[str]:
    tags = [str(v).lower() for v in (member.get("tags") or [])]
    domains = [str(v).lower() for v in (member.get("domains") or [])]
    return sorted(set(tags + domains))


def main() -> None:
    members_payload = load(DATA / "members.json")
    spend_payload = load(DATA / "spend_ledger.json")
    props_payload = load(DATA / "proposals_archive.json")

    members = members_payload.get("records") or []
    spend = spend_payload.get("records") or []
    props = props_payload.get("records") or []

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

    members_payload["records"] = members
    save(DATA / "members.json", members_payload)
    print(f"Enriched {enriched} athlete members with sport classification.")


if __name__ == "__main__":
    main()

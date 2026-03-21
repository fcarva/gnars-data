from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
ARCHIVE_PATH = DATA_DIR / "proposals_archive.json"
TAGS_PATH = DATA_DIR / "proposal_tags.json"


CATEGORY_RULES: list[tuple[str, list[str]]] = [
    (
        "governance_policy",
        [
            "governance",
            "resolution",
            "quorum",
            "treasury policy",
            "transfer correction",
            "autonomous agent",
            "signal",
            "proposal process",
        ],
    ),
    (
        "workstream_ops",
        [
            "operations",
            "ops",
            "reimbursement",
            "infra",
            "infrastructure",
            "ipfs",
            "fix ",
            "revamp",
            "docs",
            "documentation",
            "renderer",
        ],
    ),
    (
        "workstream_media",
        [
            "media",
            "pod",
            "podcast",
            "documentary",
            "film",
            "mag",
            "magazine",
            "news",
            "content",
            "video",
            "photo",
            "droposal",
            "drop",
        ],
    ),
    (
        "irl_events",
        [
            "festival",
            "premiere",
            "devconnect",
            "meetup",
            "event",
            "tour",
            "contest",
            "olympics",
            "house",
            "jazz",
            "session",
        ],
    ),
    (
        "workstream_products",
        [
            "noggle rail",
            "noggles rail",
            "nounstacle",
            "mini ramp",
            "ramp",
            "nogglesboard",
            "board",
            "merch",
            "sculpture",
            "park equipment",
        ],
    ),
    (
        "athletes_riders",
        [
            "athlete",
            "sponsor",
            "sponsorship",
            "skate",
            "skateboard",
            "surf",
            "wsl",
            "qs/",
            "kitesurf",
            "bodyboard",
            "rider",
            "wakeboard",
            "bmx",
            "snowboard",
            "longboard",
        ],
    ),
    (
        "public_goods",
        [
            "charity",
            "donation",
            "nonprofit",
            "public good",
            "school",
            "community aid",
            "humanitarian",
        ],
    ),
]


CAPITAL_BY_CATEGORY: dict[str, dict[str, float]] = {
    "athletes_riders": {
        "athletes": 70,
        "media": 10,
        "ops": 5,
        "dev": 0,
        "events": 15,
        "public_goods": 0,
        "other": 0,
    },
    "workstream_media": {
        "athletes": 0,
        "media": 80,
        "ops": 10,
        "dev": 0,
        "events": 10,
        "public_goods": 0,
        "other": 0,
    },
    "workstream_ops": {
        "athletes": 0,
        "media": 0,
        "ops": 70,
        "dev": 20,
        "events": 0,
        "public_goods": 0,
        "other": 10,
    },
    "workstream_products": {
        "athletes": 25,
        "media": 20,
        "ops": 10,
        "dev": 0,
        "events": 20,
        "public_goods": 0,
        "other": 25,
    },
    "irl_events": {
        "athletes": 20,
        "media": 10,
        "ops": 5,
        "dev": 0,
        "events": 65,
        "public_goods": 0,
        "other": 0,
    },
    "governance_policy": {
        "athletes": 0,
        "media": 0,
        "ops": 55,
        "dev": 25,
        "events": 0,
        "public_goods": 0,
        "other": 20,
    },
    "public_goods": {
        "athletes": 0,
        "media": 0,
        "ops": 10,
        "dev": 0,
        "events": 10,
        "public_goods": 80,
        "other": 0,
    },
    "uncategorized": {
        "athletes": 0,
        "media": 0,
        "ops": 0,
        "dev": 0,
        "events": 0,
        "public_goods": 0,
        "other": 100,
    },
}


SPORT_RULES: list[tuple[str, list[str]]] = [
    ("surf", ["surf", "wsl", "kitesurf", "bodyboard", "wave"]),
    ("snow", ["snow", "snowboard", "halfpipe"]),
    ("bmx", ["bmx", "bike", "cycling", "mtb", "mountain bike"]),
    ("sk8", ["skate", "sk8", "skateboard", "longboard", "noggle", "nounstacle"]),
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_text(*values: str | None) -> str:
    merged = " ".join(v or "" for v in values).lower()
    merged = re.sub(r"\s+", " ", merged).strip()
    return merged


def infer_category(text: str) -> tuple[str, float, list[str]]:
    hits: dict[str, list[str]] = {}
    for category, keywords in CATEGORY_RULES:
        for kw in keywords:
            if kw in text:
                hits.setdefault(category, []).append(kw)

    if not hits:
        return "uncategorized", 0.55, []

    ranked = sorted(hits.items(), key=lambda item: (-len(item[1]), item[0]))
    top_category, top_hits = ranked[0]
    confidence = min(0.95, 0.65 + len(top_hits) * 0.08)
    return top_category, round(confidence, 2), sorted(set(top_hits))


def infer_sport(text: str, category: str) -> str | None:
    found: list[str] = []
    for sport, keywords in SPORT_RULES:
        if any(kw in text for kw in keywords):
            found.append(sport)

    if not found:
        return "multi" if category == "athletes_riders" else None
    if len(set(found)) > 1:
        return "multi"
    return found[0]


def fallback_secondary(category: str) -> list[str]:
    mapping = {
        "athletes_riders": ["athletes"],
        "workstream_media": ["content"],
        "workstream_ops": ["dao-ops"],
        "workstream_products": ["products"],
        "irl_events": ["irl"],
        "governance_policy": ["governance-process"],
        "public_goods": ["community"],
        "uncategorized": ["other"],
    }
    return mapping.get(category, ["other"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Local non-API semantic classifier for proposal tags")
    parser.add_argument("--limit", type=int, default=0, help="Maximum records to update (0 = all missing)")
    parser.add_argument("--force", action="store_true", help="Recompute even when semantic_category exists")
    args = parser.parse_args()

    archive = load_json(ARCHIVE_PATH)
    tags = load_json(TAGS_PATH)
    archive_map = {str(r.get("archive_id") or ""): r for r in archive.get("records", [])}
    records = tags.get("records", [])

    updated = 0
    for record in records:
        has_semantic = bool(record.get("semantic_category"))
        needs_backfill = not record.get("sport") or not record.get("capital_breakdown")
        if has_semantic and not args.force and not needs_backfill:
            continue

        archive_id = str(record.get("archive_id") or "")
        proposal = archive_map.get(archive_id, {})
        title = str(proposal.get("title") or record.get("title") or "")
        summary = str(proposal.get("summary") or "")
        description = str(proposal.get("description") or "")
        text = normalize_text(title, summary, description)

        if has_semantic and not args.force:
            category = str(record.get("semantic_category"))
            conf = float(record.get("semantic_confidence") or record.get("confidence") or 0.75)
            matched = []
        else:
            category, conf, matched = infer_category(text)
        sport = infer_sport(text, category)

        if not has_semantic or args.force:
            record["semantic_category"] = category
            record["semantic_confidence"] = conf
            record["confidence"] = conf
            record["semantic_reasoning"] = (
                f"Local heuristic classification from title/context. Matched keywords: {', '.join(matched) if matched else 'none'}"
            )
            record["rationale"] = record.get("rationale") or record["semantic_reasoning"]
            record["model_provider"] = "copilot-local"
            record["model_name"] = "gpt-5.3-codex-heuristic"

        record["secondary_categories"] = record.get("secondary_categories") or fallback_secondary(category)
        record["capital_breakdown"] = record.get("capital_breakdown") or CAPITAL_BY_CATEGORY.get(category, CAPITAL_BY_CATEGORY["uncategorized"])
        record["sport"] = sport or "none"
        record["updated_at"] = utc_iso_now()

        updated += 1
        if args.limit and updated >= args.limit:
            break

    tags["records"] = records
    tags["as_of"] = utc_iso_now()
    write_json(TAGS_PATH, tags)

    print(f"[ok] local classification updated {updated} record(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
            "delegation strategy",
            "pause auctions",
            "collect royalties",
            "base jump",
            "test proposal",
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
            "frontend",
            "migration",
            "account management",
            "moderation proposal",
            "gas refund",
            "gas costs",
            "co-working space",
            "community platform",
            "bring that's gnarly onchain",
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
            "comic",
            "comicsdao",
            "music",
            "musician",
            "artist",
            "collab",
            "illustradora",
            "messhup",
            "greta gremplin",
            "children's book",
            "book of tricks",
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
            "ethdenver",
            "nft nyc",
            "nako",
            "wrg",
            "portugal",
            "italy",
            "japan",
            "thai",
            "uganda",
            "mexico",
            "devcon",
            "nounsiversary",
            "adventure",
            "trip",
            "travel grant",
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
            "hot sauce",
            "product",
            "line at",
            "bike park",
            "minted",
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
            "parkour",
            "breakers",
            "shredder",
            "help miguel",
            "vivência",
            "mare",
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


TITLE_OVERRIDE_RULES: list[tuple[str, str, str]] = [
    (r"\bgnars flows\b", "workstream_ops", "Flows/infra initiative interpreted as DAO operations tooling."),
    (r"\btitle pr\b", "workstream_ops", "Placeholder proposal title treated as operations/process bucket."),
    (r"pizza gnar turned into a whale", "workstream_products", "Product/meme activation interpreted as product workstream."),
    (r"desci", "irl_events", "Ecosystem collaboration interpreted as event/community activation."),
    (r"\bthe gnarving\b", "governance_policy", "Treasury/governance signaling around Nouns purchasing."),
    (r"bring that'?s gnarly onchain", "workstream_ops", "Onchain migration/infrastructure interpreted as operations."),
    (r"noun.?gnar.?versary", "irl_events", "Anniversary celebration interpreted as IRL/community event."),
    (r"breakdance", "athletes_riders", "Athlete performance proposal interpreted as athletes/riders."),
    (r"vlad'?s renew proposal", "workstream_ops", "Renewal workstream interpreted as operations funding."),
    (r"set the stage for others to shine", "public_goods", "Community-enablement framing interpreted as public goods."),
    (r"hive account managem", "workstream_ops", "Account management interpreted as DAO operations."),
    (r"celebrate.?the gnarving", "governance_policy", "Governance proposal tied to treasury action."),
    (r"start the gnars revolution", "governance_policy", "High-level DAO direction interpreted as governance signal."),
    (r"xv completion", "workstream_products", "Completion/mint artifact interpreted as product output."),
    (r"test prop", "governance_policy", "Testing/procedural proposal interpreted as governance process."),
    (r"locals only", "irl_events", "Local activation interpreted as event/community initiative."),
    (r"gnars is based", "governance_policy", "Base migration signaling interpreted as governance/policy."),
]


PRIMARY_BY_SEMANTIC: dict[str, str] = {
    "athletes_riders": "grants",
    "workstream_media": "media",
    "workstream_ops": "operations",
    "workstream_products": "product",
    "irl_events": "events",
    "governance_policy": "governance",
    "public_goods": "other",
    "uncategorized": "other",
}


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
    for pattern, category, _ in TITLE_OVERRIDE_RULES:
        if re.search(pattern, text):
            return category, 0.72, [f"override:{pattern}"]

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


def infer_funding_category(text: str, category: str) -> str:
    has_eth = " eth" in f" {text} " or "weth" in text
    has_usdc = "usdc" in text
    no_spend_markers = ["no direct spend", "zero ask", "signal", "resolution"]
    if any(marker in text for marker in no_spend_markers) and category == "governance_policy":
        return "none"
    if has_eth and has_usdc:
        return "mixed"
    if has_eth:
        return "eth"
    if has_usdc:
        return "usdc"
    if category == "governance_policy":
        return "none"
    return "mixed"


def infer_lifecycle_stage(text: str, category: str) -> str:
    if category == "governance_policy":
        return "signal"
    if any(k in text for k in ["droposal", "proof", "report", "update"]):
        return "delivery"
    if any(k in text for k in ["reimbursement", "infra", "infrastructure", "fix", "ops"]):
        return "infrastructure"
    return "funding-request"


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
        needs_backfill = any(
            [
                not record.get("sport"),
                not record.get("capital_breakdown"),
                not record.get("primary_category"),
                not record.get("funding_category"),
                not record.get("lifecycle_stage"),
                record.get("confidence") in (None, ""),
            ]
        )
        needs_reclassify = record.get("semantic_category") == "uncategorized"
        if has_semantic and not args.force and not needs_backfill and not needs_reclassify:
            continue

        archive_id = str(record.get("archive_id") or "")
        proposal = archive_map.get(archive_id, {})
        title = str(proposal.get("title") or record.get("title") or "")
        summary = str(proposal.get("summary") or "")
        description = str(proposal.get("description") or "")
        text = normalize_text(title, summary, description)

        if has_semantic and not args.force and not needs_reclassify:
            category = str(record.get("semantic_category"))
            conf = float(record.get("semantic_confidence") or record.get("confidence") or 0.75)
            matched = []
        else:
            category, conf, matched = infer_category(text)
        sport = infer_sport(text, category)

        if not has_semantic or args.force or needs_reclassify:
            record["semantic_category"] = category
            record["semantic_confidence"] = conf
            record["confidence"] = conf
            record["semantic_reasoning"] = (
                f"Local heuristic classification from title/context. Matched keywords: {', '.join(matched) if matched else 'none'}"
            )
            record["rationale"] = record.get("rationale") or record["semantic_reasoning"]
            record["model_provider"] = "copilot-local"
            record["model_name"] = "gpt-5.3-codex-heuristic"

        record["primary_category"] = record.get("primary_category") or PRIMARY_BY_SEMANTIC.get(category, "other")
        record["secondary_categories"] = record.get("secondary_categories") or fallback_secondary(category)
        record["funding_category"] = record.get("funding_category") or infer_funding_category(text, category)
        record["lifecycle_stage"] = record.get("lifecycle_stage") or infer_lifecycle_stage(text, category)
        record["capital_breakdown"] = record.get("capital_breakdown") or CAPITAL_BY_CATEGORY.get(category, CAPITAL_BY_CATEGORY["uncategorized"])
        record["sport"] = sport or "none"
        if record.get("confidence") in (None, ""):
            record["confidence"] = float(record.get("semantic_confidence") or conf)
        record["tagging_status"] = "tagged"
        record["review_state"] = "approved"
        record["requires_human_review"] = False
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

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse


PRODUCT_CATEGORIES = [
    "Operations",
    "Media",
    "Events",
    "Travel",
    "Athlete Support",
    "Software",
    "Governance",
    "Other",
]

TRIBE_ORDER = [
    "athlete",
    "filmmaker",
    "builder",
    "organizer",
    "delegate",
    "holder",
    "proposer",
    "recipient",
    "contributor",
    "member",
]

URL_PATTERN = re.compile(r"https?://[^\s<>)\]]+")

CATEGORY_ALIASES = {
    "operations": "Operations",
    "ops": "Operations",
    "governance operations": "Governance",
    "governance-operations": "Governance",
    "governance": "Governance",
    "media": "Media",
    "pod-media": "Media",
    "content": "Media",
    "events": "Events",
    "event": "Events",
    "travel": "Travel",
    "athlete support": "Athlete Support",
    "athlete-support": "Athlete Support",
    "software": "Software",
}

CATEGORY_KEYWORDS = {
    "Operations": [
        "operations",
        "archive",
        "documentation",
        "docs",
        "infra",
        "infrastructure",
        "qa",
        "community support",
    ],
    "Media": [
        "media",
        "video",
        "film",
        "filming",
        "documentary",
        "pod",
        "podcast",
        "branding",
        "book",
        "animation",
        "photo",
        "magazine",
    ],
    "Events": [
        "event",
        "contest",
        "best trick",
        "premiere",
        "meetup",
        "activation",
        "game of skate",
        "jam",
        "festival",
    ],
    "Travel": [
        "travel",
        "tour",
        "trip",
        "mission",
        "argentina",
        "africa",
        "puerto rico",
        "new mexico",
        "texas",
        "massachusetts",
    ],
    "Athlete Support": [
        "athlete",
        "gnarthlete",
        "skater",
        "filmer",
        "rider",
        "support",
        "residency",
        "filmed tricks",
    ],
    "Software": [
        "website",
        "web development",
        "app",
        "bot",
        "agent",
        "data pipeline",
        "dashboard",
        "shopify",
        "e-commerce",
        "tooling",
        "software",
        "gnars.com",
    ],
    "Governance": [
        "governance",
        "delegation",
        "delegates",
        "base migration",
        "quorum",
        "constitutional",
        "executor",
    ],
}

EDITORIAL_TOPIC_KEYWORDS = {
    "branding": ["branding", "brand", "identity", "visual"],
    "onboarding": ["onboarding", "onboard", "welcome"],
    "documentary": ["documentary", "feature film", "full-length film"],
    "tech": ["renderer", "metadata", "website", "site", "app", "bot", "agent", "dashboard", "tooling", "software"],
    "community": ["community", "member", "members", "local scene", "support system"],
    "contest": ["contest", "best trick", "competition", "game of skate", "jam"],
}

REFERENCE_CHANNEL_PATTERNS = {
    "youtube": ("youtube.com", "youtu.be"),
    "vimeo": ("vimeo.com",),
    "instagram": ("instagram.com",),
    "farcaster": ("farcaster.xyz",),
    "warpcast": ("warpcast.com",),
    "x": ("twitter.com", "x.com"),
    "paragraph": ("paragraph.com",),
    "mirror": ("mirror.xyz",),
    "github": ("github.com",),
    "zora": ("zora.co",),
    "notion": ("notion.so", "notion.site"),
    "hackmd": ("hackmd.io",),
    "ipfs": ("ipfs.", "ipfs/", "ipfs"),
}


def number_or_zero(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def normalize_address(value: Any) -> str:
    if value in (None, ""):
        return ""
    return str(value).strip().lower()


def parse_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    text = str(value).strip().replace("Z", "+00:00")
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def latest_value(*values: Any) -> str:
    parsed = [item for item in (parse_datetime(value) for value in values) if item is not None]
    if not parsed:
        return datetime.now(timezone.utc).date().isoformat()
    latest = max(parsed)
    if latest.time() == datetime.min.time().replace(tzinfo=None):
        return latest.date().isoformat()
    return latest.isoformat().replace("+00:00", "Z")


def unique_strings(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value in (None, ""):
            continue
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        output.append(text)
    return output


def unique_addresses(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        address = normalize_address(value)
        if not address or address in seen:
            continue
        seen.add(address)
        output.append(address)
    return output


def clean_text(value: Any) -> str:
    text = str(value or "")
    replacements = {
        "Â·": "·",
        "â€™": "'",
        "â€œ": '"',
        "â€\x9d": '"',
        "â€“": "-",
        "â€”": "-",
        "\xa0": " ",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return re.sub(r"\s+", " ", text).strip()


def slug_label(value: Any) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return text


def short_address(value: str) -> str:
    if len(value) < 12:
        return value
    return f"{value[:6]}...{value[-4:]}"


def label_display(value: Any) -> str:
    text = str(value or "").strip().replace("-", " ").replace("_", " ")
    if not text:
        return ""
    if text.isupper():
        return text
    if " " not in text and text.lower() in {"usdc", "eth", "gnars", "sendit"}:
        return text.upper()
    return " ".join(word.capitalize() for word in text.split())


def percent(numerator: float, denominator: float) -> float | None:
    if denominator <= 0:
        return None
    return round((numerator / denominator) * 100, 2)


def asset_totals(records: list[dict[str, Any]], symbol_key: str = "asset_symbol", amount_key: str = "amount") -> list[dict[str, Any]]:
    totals: defaultdict[str, float] = defaultdict(float)
    for record in records:
        symbol = str(record.get(symbol_key) or "").strip().upper()
        amount = number_or_zero(record.get(amount_key))
        if not symbol or amount <= 0:
            continue
        totals[symbol] += amount
    return [
        {"symbol": symbol, "amount": round(amount, 8)}
        for symbol, amount in sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    ]


def domain_from_url(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except ValueError:
        return ""


def strip_url(url: str) -> str:
    return url.rstrip(".,;:!?)]}")


def extract_urls(*texts: Any) -> list[str]:
    urls: list[str] = []
    for text in texts:
        if text in (None, ""):
            continue
        urls.extend(strip_url(match) for match in URL_PATTERN.findall(str(text)))
    return unique_strings(urls)


def reference_channel(url: str) -> str:
    normalized = url.lower()
    for channel, patterns in REFERENCE_CHANNEL_PATTERNS.items():
        if any(pattern in normalized for pattern in patterns):
            return channel
    if any(domain in normalized for domain in ("gnars.com", "gnars.center", "gnars.wtf", "thatsgnar.ly")):
        return "website"
    if any(domain in normalized for domain in ("basescan.org", "etherscan.io", "polygonscan.com")):
        return "explorer"
    if any(domain in normalized for domain in ("i.imgur.com", "images.hive.blog")):
        return "image-host"
    return "website"


def reference_channels_from_urls(urls: list[str]) -> list[str]:
    return unique_strings(reference_channel(url) for url in urls if url)


def transaction_asset_totals(
    records: list[dict[str, Any]],
    symbol_by_contract: dict[str, str],
) -> list[dict[str, Any]]:
    totals: defaultdict[str, float] = defaultdict(float)
    for record in records:
        kind = str(record.get("kind") or "").strip().lower()
        if kind == "native_transfer":
            amount = number_or_zero(record.get("amount_eth"))
            if amount > 0:
                totals["ETH"] += amount
            continue
        if kind != "erc20_transfer":
            continue
        amount = number_or_zero(record.get("amount_normalized"))
        if amount <= 0:
            continue
        contract = normalize_address(record.get("token_contract") or record.get("target"))
        symbol = symbol_by_contract.get(contract) or short_address(contract).upper()
        totals[symbol] += amount
    return [
        {"symbol": symbol, "amount": round(amount, 8)}
        for symbol, amount in sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    ]


def url_kind(url: str) -> str:
    host = domain_from_url(url)
    if any(part in host for part in ("youtube.com", "youtu.be", "vimeo.com")):
        return "video"
    if any(part in host for part in ("farcaster", "warpcast", "instagram.com", "twitter.com", "x.com")):
        return "social"
    if "github.com" in host:
        return "code"
    if any(part in host for part in ("docs.", "notion.so", "notion.site", "mirror.xyz")):
        return "doc"
    if re.search(r"\.(png|jpg|jpeg|gif|webp|svg)$", url, re.IGNORECASE):
        return "image"
    return "web"


def normalize_category(value: Any) -> str | None:
    if value in (None, ""):
        return None
    lowered = str(value).strip().lower().replace("_", " ")
    if lowered in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[lowered]
    for alias, category in CATEGORY_ALIASES.items():
        if alias in lowered:
            return category
    return None


def infer_category(title: str, summary: str, content: str, project_category: Any = None, tagged_category: Any = None) -> str:
    for candidate in (project_category, tagged_category):
        normalized = normalize_category(candidate)
        if normalized:
            return normalized
    scores: dict[str, int] = defaultdict(int)
    for haystack, weight in ((title.lower(), 4), (summary.lower(), 2), (content.lower(), 1)):
        for category, keywords in CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in haystack:
                    scores[category] += weight
    if scores:
        return sorted(scores.items(), key=lambda item: (-item[1], PRODUCT_CATEGORIES.index(item[0])))[0][0]
    return "Other"


def summarize_text(value: Any, limit: int = 160) -> str:
    text = clean_text(value)
    if not text:
        return ""
    if "| TL;DR" in text:
        text = text.split("| TL;DR", 1)[1].strip(" :|-")
    elif "TL;DR" in text:
        text = text.split("TL;DR", 1)[1].strip(" :|-")
    for separator in (". ", " | ", " · "):
        if separator in text:
            first = text.split(separator, 1)[0].strip()
            if first:
                text = first
                break
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3].rstrip()}..."


def format_amount_display(amount: float) -> str:
    rounded = round(number_or_zero(amount), 8)
    if rounded == 0:
        return "0"
    if float(int(rounded)) == rounded:
        return f"{int(rounded):,}"
    if rounded >= 100:
        text = f"{rounded:,.2f}"
    elif rounded >= 1:
        text = f"{rounded:,.4f}"
    else:
        text = f"{rounded:,.6f}"
    return text.rstrip("0").rstrip(".")


def asset_display(items: list[dict[str, Any]], empty_label: str = "No direct spend") -> str:
    filtered = [item for item in items if number_or_zero(item.get("amount")) > 0 and str(item.get("symbol") or "").strip()]
    if not filtered:
        return empty_label
    return " + ".join(f"{format_amount_display(number_or_zero(item['amount']))} {str(item['symbol']).upper()}" for item in filtered)


def transaction_kinds(records: list[dict[str, Any]]) -> list[str]:
    return unique_strings(str(record.get("kind") or "").strip().lower() for record in records if record.get("kind"))


def normalized_status(value: Any) -> str:
    return slug_label(value)


def outcome_group(record: dict[str, Any], successful: bool) -> str:
    status = normalized_status(record.get("status"))
    if status == "closed":
        return "closed-passed" if successful else "closed-not-passed"
    if status in {"active", "executed", "defeated", "cancelled", "pending"}:
        return status
    return status or "unknown"


def proposal_type(
    *,
    title: str,
    summary: str,
    content: str,
    category: str,
    requested_by_asset: list[dict[str, Any]],
    routed_by_asset: list[dict[str, Any]],
) -> str:
    haystack = " ".join([title, summary, content]).lower()
    has_budget = bool(requested_by_asset or routed_by_asset)
    if any(keyword in haystack for keyword in ("ratification", "ratify")):
        return "ratification"
    if any(keyword in haystack for keyword in ("update", "milestone", "report back", "delivery")) and not has_budget:
        return "delivery-update"
    if not has_budget:
        if "treasury" in haystack or "executor" in haystack or "policy" in haystack:
            return "treasury-policy"
        if category == "Governance":
            return "governance-change"
        return "signal-only"
    if category == "Operations":
        return "ops"
    return "funding"


def derive_editorial_labels(
    *,
    category: str,
    title: str,
    summary: str,
    content: str,
    tagged: dict[str, Any],
) -> list[str]:
    haystack = " ".join([title, summary]).lower()
    labels = [slug_label(category)]
    for topic, keywords in EDITORIAL_TOPIC_KEYWORDS.items():
        if any(keyword in haystack for keyword in keywords):
            labels.append(topic)
    normalized_secondary = [slug_label(value) for value in (tagged.get("secondary_categories") or []) if value not in (None, "")]
    labels.extend(label for label in normalized_secondary if label not in PRODUCT_CATEGORY_LABELS)
    return unique_strings(label for label in labels if label)


PRODUCT_CATEGORY_LABELS = {slug_label(value) for value in PRODUCT_CATEGORIES}


def derive_status_labels(status: str, outcome: str, closing_soon: bool) -> list[str]:
    labels = [normalized_status(status)]
    if outcome and outcome not in labels:
        labels.append(outcome)
    if closing_soon:
        labels.append("closing-soon")
    return unique_strings(labels)


def derive_funding_labels(
    *,
    title: str,
    summary: str,
    content: str,
    requested_by_asset: list[dict[str, Any]],
    routed_by_asset: list[dict[str, Any]],
    transaction_kind_values: list[str],
) -> list[str]:
    haystack = " ".join([title, summary, content]).lower()
    assets = unique_strings(
        slug_label(item.get("symbol"))
        for item in [*(requested_by_asset or []), *(routed_by_asset or [])]
        if item.get("symbol")
    )
    labels: list[str] = []
    if assets:
        labels.append("funding-request")
        labels.extend(assets)
        labels.append("multi-asset" if len(assets) > 1 else "single-asset")
    else:
        labels.append("no-direct-spend")
        if "treasury" in haystack or "policy" in haystack:
            labels.append("treasury-policy")
    if "erc721_transfer" in transaction_kind_values:
        labels.append("nft")
    return unique_strings(labels)


def derive_relationship_labels(
    *,
    category: str,
    linked_project: dict[str, Any] | None,
    recipient_count: int,
    proof_count: int,
    proposal_type_value: str,
) -> list[str]:
    labels = ["multi-recipient" if recipient_count > 1 else "single-recipient"]
    if linked_project:
        labels.append("linked-project")
    if category == "Athlete Support":
        labels.append("athlete-linked")
    if category == "Software":
        labels.append("builder-linked")
    if category == "Operations":
        labels.append("operations-linked")
    if proof_count > 0:
        labels.append("media-proof")
        if linked_project:
            labels.append("project-proof")
    if proposal_type_value == "ops":
        labels.append("operations-linked")
    return unique_strings(labels)


def derive_platform_labels(platform: str, chain: str) -> list[str]:
    return unique_strings([slug_label(platform), slug_label(chain)])


def derive_delivery_stage(
    *,
    successful: bool,
    outcome: str,
    proof_count: int,
    linked_project: dict[str, Any] | None,
) -> str:
    project_status = slug_label(linked_project.get("status")) if linked_project else ""
    if outcome in {"active", "pending", "defeated", "cancelled", "closed-not-passed"}:
        return "pre-funding"
    if project_status == "completed":
        return "delivered"
    if proof_count > 0:
        return "proof-linked"
    if successful and project_status in {"active", "in-progress", "in-progress", "planned"}:
        return "in-progress"
    if successful or outcome == "closed-passed":
        return "funded"
    return "pre-funding"


def derive_lifecycle_labels(
    *,
    proposal_type_value: str,
    delivery_stage_value: str,
    successful: bool,
    is_terminal: bool,
    proof_count: int,
) -> list[str]:
    labels = ["proposal"]
    if successful:
        labels.append("funded")
    if delivery_stage_value in {"in-progress", "delivered", "proof-linked"}:
        labels.append(delivery_stage_value)
    if proof_count > 0:
        labels.append("proof-added")
    if is_terminal:
        labels.append("archival")
    if proposal_type_value == "delivery-update":
        labels.append("in-delivery")
    return unique_strings(labels)


def derive_lineage_strength(
    *,
    archive_id: str,
    linked_project: dict[str, Any] | None,
    routed_by_asset: list[dict[str, Any]],
    proof_count: int,
) -> str:
    if not linked_project:
        return "adjacent"
    if archive_id in set(linked_project.get("origin_proposals") or []):
        return "direct-origin"
    if routed_by_asset:
        return "direct-budget"
    if proof_count > 0:
        return "proof-only"
    return "supporting"


def derive_proof_strength(proofs: list[dict[str, Any]]) -> str:
    if not proofs:
        return "none"
    if len(proofs) > 1:
        return "multi-proof"
    if any(str(record.get("proof_kind") or "").strip().lower() == "delivery" for record in proofs):
        return "delivery-proof"
    return "reference-only"


def derive_proof_labels(
    *,
    reference_channels: list[str],
    proofs: list[dict[str, Any]],
) -> list[str]:
    labels: list[str] = []
    channels = set(reference_channels)
    if channels.intersection({"youtube", "vimeo"}):
        labels.append("video")
    if channels.intersection({"instagram", "image-host"}):
        labels.append("photo")
    if channels.intersection({"paragraph", "mirror"}):
        labels.append("article")
    if channels.intersection({"farcaster", "warpcast", "x"}):
        labels.append("thread")
    if channels.intersection({"github", "hackmd", "notion"}):
        labels.append("doc")
    if channels.intersection({"zora"}):
        labels.append("drop")
    if any(str(record.get("proof_kind") or "").strip().lower() == "delivery" for record in proofs):
        labels.append("report")
    return unique_strings(labels)


def flatten_label_groups(*groups: list[str]) -> list[str]:
    flattened: list[str] = []
    for group in groups:
        flattened.extend(group or [])
    return unique_strings(flattened)


def primary_recipient_labels(routes: list[dict[str, Any]], recipient_addresses: list[str]) -> list[str]:
    labels = unique_strings(
        record.get("recipient_display_name") or short_address(normalize_address(record.get("recipient_address")))
        for record in routes
    )
    if labels:
        return labels[:6]
    return [short_address(address) for address in recipient_addresses[:6]]


def branding_tags_from_text(*texts: Any) -> list[str]:
    haystack = " ".join(str(text or "") for text in texts).lower()
    tags = []
    for label, keywords in {
        "skate": ["skate", "skateboard", "gnarthlete", "rider"],
        "media": ["media", "video", "film", "pod", "branding", "animation", "documentary"],
        "governance": ["governance", "proposal", "vote", "dao", "treasury"],
        "operations": ["ops", "operations", "infra", "documentation", "archive", "data"],
        "software": ["site", "app", "bot", "agent", "dashboard", "pipeline"],
        "events": ["event", "contest", "tour", "trip", "activation"],
    }.items():
        if any(keyword in haystack for keyword in keywords):
            tags.append(label)
    return unique_strings(tags)


def is_successful_proposal(record: dict[str, Any]) -> bool:
    platform = str(record.get("platform") or "").strip().lower()
    status = str(record.get("status") or "").strip().lower()
    if platform == "gnars.com":
        return status == "executed"
    if platform == "snapshot" and status == "closed":
        scores = [number_or_zero(value) for value in (record.get("scores_by_choice") or [])]
        return bool(scores) and scores[0] > 0 and scores[0] == max(scores) and number_or_zero(record.get("scores_total")) >= number_or_zero(record.get("quorum"))
    return status == "executed"


def proposal_date(record: dict[str, Any]) -> str:
    return str(record.get("end_at") or record.get("created_at") or record.get("start_at") or "")


def build_proposals_enriched(
    archive: dict[str, Any],
    project_rollups: dict[str, Any],
    spend_records: list[dict[str, Any]],
    timeline_events: dict[str, Any],
    proposal_tags: dict[str, Any],
    analytics_as_of: str,
) -> dict[str, Any]:
    project_by_archive: dict[str, dict[str, Any]] = {}
    symbol_by_contract = {
        normalize_address(record.get("token_contract")): str(record.get("asset_symbol") or "").strip().upper()
        for record in spend_records
        if record.get("token_contract") and record.get("asset_symbol")
    }
    for project in project_rollups["records"]:
        for summary in project.get("proposal_summaries") or []:
            archive_id = str(summary.get("archive_id") or "").strip()
            if archive_id:
                project_by_archive[archive_id] = project

    tags_by_archive = {
        str(record.get("archive_id") or "").strip(): record for record in proposal_tags.get("records") or []
    }
    routes_by_archive: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in spend_records:
        routes_by_archive[str(record.get("archive_id") or "")].append(record)

    event_counts: Counter[str] = Counter()
    for event in timeline_events.get("records") or []:
        for archive_id in unique_strings(event.get("proposal_ids") or []):
            event_counts[archive_id] += 1
        archive_id = str(event.get("archive_id") or "").strip()
        if archive_id:
            event_counts[archive_id] += 1

    analytics_dt = parse_datetime(analytics_as_of) or datetime.now(timezone.utc)
    records: list[dict[str, Any]] = []
    for proposal in archive.get("records") or []:
        archive_id = proposal["archive_id"]
        linked_project = project_by_archive.get(archive_id)
        routes = routes_by_archive.get(archive_id, [])
        tagged = tags_by_archive.get(archive_id, {})
        title = clean_text(proposal.get("title"))
        content_summary = clean_text(proposal.get("content_summary"))
        content_markdown = clean_text(proposal.get("content_markdown"))
        category = infer_category(
            title,
            content_summary,
            content_markdown,
            linked_project.get("category") if linked_project else None,
            tagged.get("primary_category"),
        )
        successful = is_successful_proposal(proposal)
        outcome = outcome_group(proposal, successful)
        end_dt = parse_datetime(proposal.get("end_at"))
        closing_soon = bool(
            str(proposal.get("status") or "").strip().lower() == "active"
            and end_dt is not None
            and timedelta(0) <= end_dt - analytics_dt <= timedelta(days=7)
        )
        reference_urls = unique_strings(
            [
                proposal.get("links", {}).get("canonical_url"),
                proposal.get("links", {}).get("source_url"),
                proposal.get("links", {}).get("discussion_url"),
                proposal.get("links", {}).get("explorer_url"),
                *(extract_urls(proposal.get("content_markdown"), proposal.get("content_summary"))[:10]),
            ]
        )
        reference_channels = reference_channels_from_urls(reference_urls)
        transaction_records = proposal.get("transactions") or []
        requested_by_asset = (
            [
                {"symbol": "ETH", "amount": number_or_zero(linked_project.get("budget", {}).get("eth"))},
                {"symbol": "USDC", "amount": number_or_zero(linked_project.get("budget", {}).get("usdc"))},
                {"symbol": "GNARS", "amount": number_or_zero(linked_project.get("budget", {}).get("gnars"))},
            ]
            if linked_project
            else transaction_asset_totals(transaction_records, symbol_by_contract)
        )
        requested_by_asset = [item for item in requested_by_asset if number_or_zero(item.get("amount")) > 0]
        routed_by_asset = asset_totals(routes)
        recipient_addresses = unique_addresses([record.get("recipient_address") for record in routes])
        transaction_kind_values = transaction_kinds(transaction_records)
        initial_proof_count = event_counts.get(archive_id, 0)
        proposal_type_value = proposal_type(
            title=title,
            summary=content_summary,
            content=content_markdown,
            category=category,
            requested_by_asset=requested_by_asset,
            routed_by_asset=routed_by_asset,
        )
        delivery_stage_value = derive_delivery_stage(
            successful=successful,
            outcome=outcome,
            proof_count=initial_proof_count,
            linked_project=linked_project,
        )
        editorial_labels = derive_editorial_labels(
            category=category,
            title=title,
            summary=content_summary,
            content=content_markdown,
            tagged=tagged,
        )
        status_labels = derive_status_labels(str(proposal.get("status") or ""), outcome, closing_soon)
        funding_labels = derive_funding_labels(
            title=title,
            summary=content_summary,
            content=content_markdown,
            requested_by_asset=requested_by_asset,
            routed_by_asset=routed_by_asset,
            transaction_kind_values=transaction_kind_values,
        )
        relationship_labels = derive_relationship_labels(
            category=category,
            linked_project=linked_project,
            recipient_count=len(recipient_addresses),
            proof_count=initial_proof_count,
            proposal_type_value=proposal_type_value,
        )
        platform_labels = derive_platform_labels(str(proposal.get("platform") or ""), str(proposal.get("chain") or ""))
        lifecycle_labels = derive_lifecycle_labels(
            proposal_type_value=proposal_type_value,
            delivery_stage_value=delivery_stage_value,
            successful=successful,
            is_terminal=outcome not in {"active", "pending"},
            proof_count=initial_proof_count,
        )
        proof_labels = derive_proof_labels(reference_channels=reference_channels, proofs=[])
        primary_recipients = primary_recipient_labels(routes, recipient_addresses)
        summary_short = summarize_text(content_summary or content_markdown or title)
        requested_total_display = asset_display(requested_by_asset)
        routed_total_display = asset_display(routed_by_asset)
        lineage_strength = derive_lineage_strength(
            archive_id=archive_id,
            linked_project=linked_project,
            routed_by_asset=routed_by_asset,
            proof_count=initial_proof_count,
        )

        records.append(
            {
                "archive_id": archive_id,
                "proposal_key": proposal["proposal_key"],
                "proposal_number": proposal.get("proposal_number"),
                "title": proposal["title"],
                "status": proposal["status"],
                "platform": proposal["platform"],
                "chain": proposal["chain"],
                "proposer": normalize_address(proposal.get("proposer")),
                "proposer_label": proposal.get("proposer_label"),
                "created_at": proposal.get("created_at"),
                "start_at": proposal.get("start_at"),
                "end_at": proposal.get("end_at"),
                "date": proposal_date(proposal),
                "successful": successful,
                "hot": closing_soon,
                "closing_soon": closing_soon,
                "is_active": outcome in {"active", "pending"},
                "is_terminal": outcome not in {"active", "pending"},
                "outcome_group": outcome,
                "category": category,
                "summary_short": summary_short,
                "requested_total_display": requested_total_display,
                "routed_total_display": routed_total_display,
                "proposal_type": proposal_type_value,
                "delivery_stage": delivery_stage_value,
                "proof_strength": "none",
                "lineage_strength": lineage_strength,
                "reference_channels": reference_channels,
                "primary_recipients": primary_recipients,
                "editorial_labels": editorial_labels,
                "status_labels": status_labels,
                "funding_labels": funding_labels,
                "relationship_labels": relationship_labels,
                "platform_labels": platform_labels,
                "lifecycle_labels": lifecycle_labels,
                "proof_labels": proof_labels,
                "project_ids": [linked_project["project_id"]] if linked_project else [],
                "recipient_addresses": recipient_addresses,
                "recipient_count": len(recipient_addresses),
                "requested_by_asset": requested_by_asset,
                "routed_by_asset": routed_by_asset,
                "transaction_kinds": transaction_kind_values,
                "transaction_count": len(transaction_records),
                "nft_transfer_count": sum(1 for record in transaction_records if str(record.get("kind") or "").strip().lower() == "erc721_transfer"),
                "vote_count": len(proposal.get("votes") or []),
                "scores_total": number_or_zero(proposal.get("scores_total")),
                "quorum": number_or_zero(proposal.get("quorum")),
                "quorum_met": number_or_zero(proposal.get("scores_total")) >= number_or_zero(proposal.get("quorum")),
                "proof_count": initial_proof_count,
                "related_proof_ids": [],
                "reference_urls": reference_urls,
                "summary": content_summary,
                "href": f"/proposals/{archive_id}/",
            }
        )

    records.sort(key=lambda record: (str(record.get("date") or ""), str(record["archive_id"])), reverse=True)
    return {
        "dataset": "proposals_enriched",
        "analytics_as_of": analytics_as_of,
        "as_of": analytics_as_of,
        "version": 1,
        "taxonomy": PRODUCT_CATEGORIES,
        "records": records,
    }


def build_media_proof(
    project_updates: dict[str, Any],
    archive: dict[str, Any],
    project_rollups: dict[str, Any],
    analytics_as_of: str,
) -> dict[str, Any]:
    proposal_by_alias: dict[str, dict[str, Any]] = {}
    for proposal in archive.get("records") or []:
        aliases = {
            str(proposal.get("archive_id") or "").strip().lower(),
            str(proposal.get("proposal_key") or "").strip().lower(),
        }
        number = proposal.get("proposal_number")
        chain = str(proposal.get("chain") or "").strip().lower()
        if number is not None and chain:
            aliases.add(f"{chain}-{number}".lower())
        for alias in aliases:
            if alias:
                proposal_by_alias[alias] = proposal

    project_by_id = {record["project_id"]: record for record in project_rollups.get("records") or []}
    project_lookup: dict[str, str] = {}
    for project in project_rollups.get("records") or []:
        for summary in project.get("proposal_summaries") or []:
            archive_id = str(summary.get("archive_id") or "").strip()
            if archive_id:
                project_lookup[archive_id] = project["project_id"]

    records: list[dict[str, Any]] = []
    for update in project_updates.get("records") or []:
        project_id = update["project_id"]
        project = project_by_id.get(project_id)
        related_proposals = [
            proposal_by_alias[alias]["archive_id"]
            for alias in (str(reference).strip().lower() for reference in update.get("related_proposals") or [])
            if alias in proposal_by_alias
        ]
        primary_url = (update.get("links") or [None])[0]
        records.append(
            {
                "proof_id": f"project-update:{update['update_id']}",
                "date": update["date"],
                "title": update["title"],
                "status": update["status"],
                "source_kind": "project_update",
                "proof_kind": "delivery"
                if str(update.get("status") or "").strip().lower() == "completed"
                or str(update.get("kind") or "").strip().lower() in {"delivery", "milestone"}
                else "update",
                "reference_kind": url_kind(primary_url) if primary_url else "internal",
                "url": primary_url or (f"/projects/{project_id}/" if project else "/projects/"),
                "domain": domain_from_url(primary_url or ""),
                "project_id": project_id,
                "archive_id": related_proposals[0] if related_proposals else None,
                "related_proposals": related_proposals,
                "people_addresses": unique_addresses(update.get("related_addresses") or []),
                "summary": update.get("summary") or "",
                "thumbnail_url": None,
            }
        )
        for index, link in enumerate(unique_strings(update.get("links") or [])):
            records.append(
                {
                    "proof_id": f"project-link:{update['update_id']}:{index}",
                    "date": update["date"],
                    "title": update["title"],
                    "status": update["status"],
                    "source_kind": "project_link",
                    "proof_kind": "reference",
                    "reference_kind": url_kind(link),
                    "url": link,
                    "domain": domain_from_url(link),
                    "project_id": project_id,
                    "archive_id": related_proposals[0] if related_proposals else None,
                    "related_proposals": related_proposals,
                    "people_addresses": unique_addresses(update.get("related_addresses") or []),
                    "summary": update.get("summary") or "",
                    "thumbnail_url": None,
                }
            )

    for proposal in archive.get("records") or []:
        urls = extract_urls(proposal.get("content_markdown"), proposal.get("content_summary"))[:8]
        for index, link in enumerate(urls):
            records.append(
                {
                    "proof_id": f"proposal-reference:{proposal['archive_id']}:{index}",
                    "date": proposal_date(proposal),
                    "title": proposal["title"],
                    "status": proposal["status"],
                    "source_kind": "proposal",
                    "proof_kind": "reference",
                    "reference_kind": url_kind(link),
                    "url": link,
                    "domain": domain_from_url(link),
                    "project_id": project_lookup.get(proposal["archive_id"]),
                    "archive_id": proposal["archive_id"],
                    "related_proposals": [proposal["archive_id"]],
                    "people_addresses": unique_addresses([proposal.get("proposer")]),
                    "summary": proposal.get("content_summary") or "",
                    "thumbnail_url": proposal.get("cover_image_url"),
                }
            )

    records.sort(key=lambda record: (str(record.get("date") or ""), str(record["proof_id"])), reverse=True)
    return {
        "dataset": "media_proof",
        "analytics_as_of": analytics_as_of,
        "as_of": analytics_as_of,
        "version": 1,
        "records": records,
    }


def hydrate_proposals_with_proof(proposals_enriched: dict[str, Any], media_proof: dict[str, Any]) -> dict[str, Any]:
    proofs_by_archive: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in media_proof.get("records") or []:
        archive_id = str(record.get("archive_id") or "").strip()
        if archive_id:
            proofs_by_archive[archive_id].append(record)

    for record in proposals_enriched.get("records") or []:
        proofs = proofs_by_archive.get(record["archive_id"], [])
        proof_ids = [proof["proof_id"] for proof in proofs]
        record["proof_count"] = len(proofs)
        record["related_proof_ids"] = proof_ids[:24]
        record["proof_strength"] = derive_proof_strength(proofs)
        merged_channels = unique_strings(
            [*(record.get("reference_channels") or []), *(reference_channel(proof.get("url") or "") for proof in proofs if proof.get("url"))]
        )
        record["reference_channels"] = merged_channels
        record["proof_labels"] = derive_proof_labels(reference_channels=merged_channels, proofs=proofs)
        record["delivery_stage"] = derive_delivery_stage(
            successful=bool(record.get("successful")),
            outcome=str(record.get("outcome_group") or ""),
            proof_count=len(proofs),
            linked_project={"status": "completed"} if record.get("project_ids") and any(str(proof.get("proof_kind") or "").strip().lower() == "delivery" for proof in proofs) else None,
        )
        record["lifecycle_labels"] = derive_lifecycle_labels(
            proposal_type_value=str(record.get("proposal_type") or ""),
            delivery_stage_value=str(record.get("delivery_stage") or ""),
            successful=bool(record.get("successful")),
            is_terminal=bool(record.get("is_terminal")),
            proof_count=len(proofs),
        )
        base_relationship_labels = [
            label
            for label in (record.get("relationship_labels") or [])
            if label not in {"media-proof", "project-proof"}
        ]
        record["relationship_labels"] = unique_strings(
            [
                *base_relationship_labels,
                "media-proof" if proofs else "",
                "project-proof" if proofs and (record.get("project_ids") or []) else "",
            ]
        )
        if not (record.get("project_ids") or []):
            record["lineage_strength"] = "adjacent"
    return proposals_enriched


def expand_project_rollups(
    project_rollups: dict[str, Any],
    project_updates: dict[str, Any],
    media_proof: dict[str, Any],
    analytics_as_of: str,
) -> dict[str, Any]:
    updates_by_project: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in project_updates.get("records") or []:
        updates_by_project[str(record.get("project_id") or "")].append(record)

    proofs_by_project: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in media_proof.get("records") or []:
        project_id = str(record.get("project_id") or "").strip()
        if project_id:
            proofs_by_project[project_id].append(record)

    for project in project_rollups.get("records") or []:
        updates = updates_by_project.get(project["project_id"], [])
        proofs = proofs_by_project.get(project["project_id"], [])
        proof_evidence = [record for record in proofs if str(record.get("proof_kind") or "").strip().lower() != "reference"]
        delivery_proofs = [record for record in proof_evidence if str(record.get("proof_kind") or "").strip().lower() == "delivery"]
        delivery_count = sum(
            1
            for update in updates
            if str(update.get("status") or "").strip().lower() == "completed"
            or str(update.get("kind") or "").strip().lower() in {"delivery", "milestone"}
        )
        contributor_addresses = unique_addresses(
            [
                *(project.get("owner_addresses") or []),
                *(recipient.get("address") for recipient in project.get("recipients") or []),
                *(address for update in updates for address in (update.get("related_addresses") or [])),
            ]
        )
        project["proposal_lineage"] = unique_strings(
            [summary.get("archive_id") for summary in project.get("proposal_summaries") or [] if summary.get("archive_id")]
        )
        project["scope_labels"] = unique_strings(
            [
                normalize_category(project.get("category")) or "Other",
                str(project.get("status") or ""),
                "workstream",
                "multi-recipient" if len(project.get("recipients") or []) > 1 else "single-recipient",
            ]
        )
        project["branding_tags"] = branding_tags_from_text(project.get("name"), project.get("objective"), *(project.get("outputs") or []))
        project["contributor_addresses"] = contributor_addresses
        project["delivery_count"] = delivery_count
        project["proof_count"] = len(proof_evidence)
        project["proof_coverage_pct"] = percent(len(delivery_proofs), delivery_count or max(1, len(updates)))
        project["related_proof_ids"] = [record["proof_id"] for record in proof_evidence[:24]]

    project_rollups["analytics_as_of"] = analytics_as_of
    project_rollups["as_of"] = analytics_as_of
    return project_rollups


def expand_people(
    people: dict[str, Any],
    archive: dict[str, Any],
    spend_records: list[dict[str, Any]],
    project_updates: dict[str, Any],
    media_proof: dict[str, Any],
    network_graph: dict[str, Any],
    proposals_enriched: dict[str, Any],
    analytics_as_of: str,
) -> dict[str, Any]:
    proposals_by_id = {record["archive_id"]: record for record in archive.get("records") or []}
    enriched_by_archive = {record["archive_id"]: record for record in proposals_enriched.get("records") or []}
    routes_by_person: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in spend_records:
        routes_by_person[normalize_address(record.get("recipient_address"))].append(record)

    updates_by_person: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in project_updates.get("records") or []:
        for address in unique_addresses(record.get("related_addresses") or []):
            updates_by_person[address].append(record)

    proofs_by_person: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in media_proof.get("records") or []:
        for address in unique_addresses(record.get("people_addresses") or []):
            proofs_by_person[address].append(record)

    network_degree: Counter[str] = Counter()
    for edge in network_graph.get("edges") or []:
        for node_id in (edge.get("source"), edge.get("target")):
            node = str(node_id or "")
            if node.startswith("person:"):
                network_degree[node.split(":", 1)[1]] += 1

    for person in people.get("records") or []:
        address = normalize_address(person.get("address"))
        authored = [enriched_by_archive[archive_id] for archive_id in person.get("relationships", {}).get("authored_proposals", []) if archive_id in enriched_by_archive]
        successful_authored = [record for record in authored if record.get("successful")]
        owned_projects = set(person.get("relationships", {}).get("owned_projects") or [])
        managed_records = [
            record
            for record in spend_records
            if record.get("archive_id") in {proposal["archive_id"] for proposal in successful_authored}
            or record.get("project_id") in owned_projects
        ]
        related_updates = updates_by_person.get(address, [])
        delivery_count = sum(
            1
            for record in related_updates
            if str(record.get("status") or "").strip().lower() == "completed"
            or str(record.get("kind") or "").strip().lower() in {"delivery", "milestone"}
        )
        proofs = proofs_by_person.get(address, [])
        dates = []
        for archive_id in person.get("relationships", {}).get("authored_proposals", []):
            proposal = proposals_by_id.get(archive_id)
            if proposal:
                dates.append(proposal_date(proposal))
        for archive_id in person.get("relationships", {}).get("voted_proposals", []):
            proposal = proposals_by_id.get(archive_id)
            if proposal:
                dates.append(proposal_date(proposal))
        for record in routes_by_person.get(address, []):
            dates.append(record.get("proposal_end_at") or record.get("proposal_created_at"))
        for record in related_updates:
            dates.append(record.get("date"))
        for record in proofs:
            dates.append(record.get("date"))
        parsed_dates = [parse_datetime(value) for value in dates if value not in (None, "")]
        parsed_dates = [value for value in parsed_dates if value is not None]

        tribes = [tag for tag in TRIBE_ORDER if tag in (person.get("tags") or [])]
        references = unique_strings(
            [
                person.get("identity", {}).get("member_url"),
                person.get("identity", {}).get("farcaster"),
                person.get("identity", {}).get("github"),
                person.get("identity", {}).get("website"),
                person.get("identity", {}).get("x"),
                person.get("identity", {}).get("instagram"),
            ]
        )
        person["tribes"] = tribes
        person["headline"] = person.get("bio") or person.get("role") or "Gnars community operator"
        person["history_short"] = person.get("bio") or person.get("role") or "Community participant in the Gnars network."
        person["history_long"] = person.get("notes") or person.get("bio") or person.get("role") or ""
        person["successful_authored_count"] = len(successful_authored)
        person["successful_authored_proposals"] = [record["archive_id"] for record in successful_authored]
        person["budget_managed_by_asset"] = asset_totals(managed_records)
        person["treasury_route_count"] = len(routes_by_person.get(address, []))
        person["delivery_count"] = delivery_count
        person["proof_count"] = len(proofs)
        person["proof_coverage_pct"] = percent(len(proofs), delivery_count or max(1, len(related_updates)))
        person["network_degree"] = network_degree.get(address, 0)
        person["first_seen_at"] = min(parsed_dates).date().isoformat() if parsed_dates else None
        person["last_seen_at"] = max(parsed_dates).date().isoformat() if parsed_dates else None
        person["references"] = [
            {"label": urlparse(url).netloc or url, "url": url, "kind": url_kind(url)} for url in references
        ]
        person["media_references"] = [
            {
                "proof_id": record["proof_id"],
                "title": record["title"],
                "url": record["url"],
                "kind": record["reference_kind"],
                "date": record["date"],
            }
            for record in proofs[:12]
        ]
        person["proposal_editorial_labels"] = unique_strings(
            [label for record in authored for label in (record.get("editorial_labels") or [])]
        )
        person["treasury_totals"] = person.get("receipts", {}).get("by_asset") or []
        person["project_count"] = len(person.get("relationships", {}).get("related_projects") or [])

    people["analytics_as_of"] = analytics_as_of
    people["as_of"] = analytics_as_of
    return people


def build_feed_stream(
    proposals_enriched: dict[str, Any],
    spend_records: list[dict[str, Any]],
    project_updates: dict[str, Any],
    media_proof: dict[str, Any],
    people: dict[str, Any],
    project_rollups: dict[str, Any],
    analytics_as_of: str,
) -> dict[str, Any]:
    people_by_address = {record["address"]: record for record in people.get("records") or []}
    projects_by_id = {record["project_id"]: record for record in project_rollups.get("records") or []}
    proposals_by_id = {record["archive_id"]: record for record in proposals_enriched.get("records") or []}
    proposal_aliases: dict[str, str] = {}
    for proposal in proposals_enriched.get("records") or []:
        archive_id = proposal["archive_id"]
        proposal_aliases[archive_id.lower()] = archive_id
        key = str(proposal.get("proposal_key") or "").strip().lower()
        if key:
            proposal_aliases[key] = archive_id
        chain = str(proposal.get("chain") or "").strip().lower()
        number = proposal.get("proposal_number")
        if chain and number is not None:
            proposal_aliases[f"{chain}-{number}".lower()] = archive_id
    items: list[dict[str, Any]] = []

    for proposal in proposals_enriched.get("records") or []:
        labels = flatten_label_groups(
            proposal.get("editorial_labels") or [],
            proposal.get("status_labels") or [],
            proposal.get("funding_labels") or [],
            proposal.get("relationship_labels") or [],
            proposal.get("platform_labels") or [],
            proposal.get("lifecycle_labels") or [],
            proposal.get("proof_labels") or [],
        )
        items.append(
            {
                "item_id": f"proposal:{proposal['archive_id']}",
                "kind": "proposal",
                "date": proposal["date"],
                "status": proposal["status"],
                "title": proposal["title"],
                "summary": proposal["summary_short"] or proposal["summary"],
                "labels": labels,
                "editorial_labels": proposal.get("editorial_labels") or [],
                "status_labels": proposal.get("status_labels") or [],
                "funding_labels": proposal.get("funding_labels") or [],
                "relationship_labels": proposal.get("relationship_labels") or [],
                "platform_labels": proposal.get("platform_labels") or [],
                "lifecycle_labels": proposal.get("lifecycle_labels") or [],
                "proof_labels": proposal.get("proof_labels") or [],
                "source_labels": [],
                "linked_people": unique_addresses([proposal.get("proposer"), *(proposal.get("recipient_addresses") or [])]),
                "linked_projects": unique_strings(proposal.get("project_ids") or []),
                "linked_proposals": [proposal["archive_id"]],
                "linked_assets": [item["symbol"] for item in proposal.get("routed_by_asset") or []],
                "primary_href": proposal["href"],
            }
        )

    for record in spend_records:
        proposal = proposals_by_id.get(record["archive_id"], {})
        linked_person = people_by_address.get(normalize_address(record.get("recipient_address")))
        editorial_labels = unique_strings(
            [*(proposal.get("editorial_labels") or []), "treasury"]
        )
        status_labels = unique_strings([normalized_status(record.get("status")), "funded"])
        funding_labels = unique_strings([slug_label(record.get("asset_symbol")), "treasury-route"])
        relationship_labels = unique_strings(
            [
                "recipient",
                "linked-project" if record.get("project_id") else "",
                "multi-recipient" if number_or_zero(proposal.get("recipient_count")) > 1 else "single-recipient",
            ]
        )
        platform_labels = unique_strings(proposal.get("platform_labels") or [slug_label(record.get("chain"))])
        lifecycle_labels = ["funded"]
        proof_labels: list[str] = []
        labels = flatten_label_groups(
            editorial_labels,
            status_labels,
            funding_labels,
            relationship_labels,
            platform_labels,
            lifecycle_labels,
            proof_labels,
        )
        items.append(
            {
                "item_id": f"payout:{record['ledger_id']}",
                "kind": "payout",
                "date": record.get("proposal_end_at") or record.get("proposal_created_at") or analytics_as_of,
                "status": record["status"],
                "title": f"{record['recipient_display_name']} received {round(number_or_zero(record['amount']), 2)} {record['asset_symbol']}",
                "summary": f"Routed through {record['title']} on {record['chain']}.",
                "labels": labels,
                "editorial_labels": editorial_labels,
                "status_labels": status_labels,
                "funding_labels": funding_labels,
                "relationship_labels": relationship_labels,
                "platform_labels": platform_labels,
                "lifecycle_labels": lifecycle_labels,
                "proof_labels": proof_labels,
                "source_labels": ["treasury"],
                "linked_people": unique_addresses([record.get("recipient_address"), record.get("proposer")]),
                "linked_projects": unique_strings([record.get("project_id")]),
                "linked_proposals": [record["archive_id"]],
                "linked_assets": [record["asset_symbol"]],
                "primary_href": f"/community/{linked_person['slug']}/" if linked_person else record["canonical_url"],
            }
        )

    for record in project_updates.get("records") or []:
        project = projects_by_id.get(record["project_id"], {})
        editorial_labels = unique_strings([slug_label(project.get("category") or "Other")])
        status_labels = unique_strings([normalized_status(record.get("status"))])
        relationship_labels = unique_strings(["linked-project", "project-proof"])
        lifecycle_labels = [
            "delivered"
            if str(record.get("status") or "").strip().lower() == "completed"
            or str(record.get("kind") or "").strip().lower() in {"delivery", "milestone"}
            else "in-delivery"
        ]
        source_labels = reference_channels_from_urls(unique_strings(record.get("links") or []))
        proof_labels = derive_proof_labels(reference_channels=source_labels, proofs=[])
        labels = flatten_label_groups(
            editorial_labels,
            status_labels,
            [],
            relationship_labels,
            [],
            lifecycle_labels,
            proof_labels,
        )
        items.append(
            {
                "item_id": f"update:{record['update_id']}",
                "kind": "delivery"
                if str(record.get("status") or "").strip().lower() == "completed" or str(record.get("kind") or "").strip().lower() in {"delivery", "milestone"}
                else "project_update",
                "date": record["date"],
                "status": record["status"],
                "title": record["title"],
                "summary": record["summary"],
                "labels": labels,
                "editorial_labels": editorial_labels,
                "status_labels": status_labels,
                "funding_labels": [],
                "relationship_labels": relationship_labels,
                "platform_labels": [],
                "lifecycle_labels": lifecycle_labels,
                "proof_labels": proof_labels,
                "source_labels": source_labels,
                "linked_people": unique_addresses(record.get("related_addresses") or []),
                "linked_projects": [record["project_id"]],
                "linked_proposals": unique_strings(
                    [
                        proposal_aliases.get(str(reference).strip().lower(), str(reference).strip())
                        for reference in (record.get("related_proposals") or [])
                    ]
                ),
                "linked_assets": [],
                "primary_href": (record.get("links") or [f"/projects/{record['project_id']}/"])[0],
            }
        )

    for record in media_proof.get("records") or []:
        linked_proposals = unique_strings(record.get("related_proposals") or ([record.get("archive_id")] if record.get("archive_id") else []))
        linked_proposal = proposals_by_id.get(linked_proposals[0], {}) if linked_proposals else {}
        source_labels = unique_strings([reference_channel(record.get("url") or "") if record.get("url") else "", slug_label(record.get("domain") or "")])
        editorial_labels = unique_strings(linked_proposal.get("editorial_labels") or [slug_label(projects_by_id.get(record.get("project_id"), {}).get("category") or "")])
        status_labels = unique_strings([normalized_status(record.get("status")), "proof"])
        relationship_labels = unique_strings(
            [
                "media-proof",
                "project-proof" if record.get("project_id") else "",
                "linked-project" if record.get("project_id") else "",
            ]
        )
        platform_labels = unique_strings(linked_proposal.get("platform_labels") or [])
        lifecycle_labels = ["proof-added"]
        proof_labels = derive_proof_labels(reference_channels=source_labels, proofs=[record])
        labels = flatten_label_groups(
            editorial_labels,
            status_labels,
            [],
            relationship_labels,
            platform_labels,
            lifecycle_labels,
            proof_labels,
        )
        items.append(
            {
                "item_id": f"proof:{record['proof_id']}",
                "kind": "media_reference",
                "date": record["date"],
                "status": record["status"],
                "title": record["title"],
                "summary": record["summary"],
                "labels": labels,
                "editorial_labels": editorial_labels,
                "status_labels": status_labels,
                "funding_labels": [],
                "relationship_labels": relationship_labels,
                "platform_labels": platform_labels,
                "lifecycle_labels": lifecycle_labels,
                "proof_labels": proof_labels,
                "source_labels": source_labels,
                "linked_people": unique_addresses(record.get("people_addresses") or []),
                "linked_projects": unique_strings([record.get("project_id")]),
                "linked_proposals": linked_proposals,
                "linked_assets": [],
                "primary_href": record["url"],
            }
        )

    for person in people.get("records") or []:
        last_seen = person.get("last_seen_at")
        if not last_seen or (
            person.get("successful_authored_count", 0) <= 0
            and person.get("proof_count", 0) <= 0
            and person.get("treasury_route_count", 0) <= 0
        ):
            continue
        editorial_labels = unique_strings([*(person.get("tribes") or []), "community"])
        status_labels = unique_strings([normalized_status(person.get("status"))])
        relationship_labels = ["community"]
        lifecycle_labels = ["archival"]
        proof_labels = ["report"] if person.get("proof_count", 0) > 0 else []
        labels = flatten_label_groups(
            editorial_labels,
            status_labels,
            [],
            relationship_labels,
            [],
            lifecycle_labels,
            proof_labels,
        )
        items.append(
            {
                "item_id": f"community:{person['slug']}",
                "kind": "community_reference",
                "date": last_seen,
                "status": person["status"],
                "title": person["display_name"],
                "summary": f"{person.get('headline') or person.get('role')}. {person.get('successful_authored_count', 0)} passed authored proposals, {person.get('treasury_route_count', 0)} treasury routes, {person.get('proof_count', 0)} proof records.",
                "labels": labels,
                "editorial_labels": editorial_labels,
                "status_labels": status_labels,
                "funding_labels": [],
                "relationship_labels": relationship_labels,
                "platform_labels": [],
                "lifecycle_labels": lifecycle_labels,
                "proof_labels": proof_labels,
                "source_labels": [],
                "linked_people": [person["address"]],
                "linked_projects": unique_strings(person.get("relationships", {}).get("related_projects") or []),
                "linked_proposals": unique_strings(person.get("relationships", {}).get("authored_proposals") or []),
                "linked_assets": [item["symbol"] for item in person.get("treasury_totals") or []],
                "primary_href": f"/community/{person['slug']}/",
            }
        )

    items.sort(key=lambda record: (str(record.get("date") or ""), str(record["item_id"])), reverse=True)
    return {
        "dataset": "feed_stream",
        "analytics_as_of": analytics_as_of,
        "as_of": analytics_as_of,
        "version": 1,
        "records": items,
    }


def build_insights(
    treasury: dict[str, Any],
    treasury_flows: dict[str, Any],
    community_signals: dict[str, Any],
    proposals_enriched: dict[str, Any],
    people: dict[str, Any],
    project_rollups: dict[str, Any],
    analytics_as_of: str,
) -> dict[str, Any]:
    proposals = proposals_enriched.get("records") or []
    all_routes = treasury_flows.get("routes") or []
    people_records = people.get("records") or []
    project_records = project_rollups.get("records") or []

    spending_by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    proposal_categories = {record["archive_id"]: record["category"] for record in proposals}
    for route in all_routes:
        spending_by_category[proposal_categories.get(route["archive_id"], "Other")].append(route)

    success_by_category = []
    for category in PRODUCT_CATEGORIES:
        selected = [record for record in proposals if record.get("category") == category]
        successful = [record for record in selected if record.get("successful")]
        success_by_category.append(
            {
                "category": category,
                "proposal_count": len(selected),
                "successful_count": len(successful),
                "success_rate_pct": percent(len(successful), len(selected)),
            }
        )

    concentration_rows = []
    for symbol in ["USDC", "ETH", "GNARS"]:
        totals = sorted(
            [
                {
                    "display_name": record["display_name"],
                    "slug": record["slug"],
                    "amount": number_or_zero(
                        next((asset["amount"] for asset in record.get("treasury_totals") or [] if asset["symbol"] == symbol), 0)
                    ),
                }
                for record in people_records
            ],
            key=lambda row: (-row["amount"], row["display_name"].lower()),
        )
        nonzero = [row for row in totals if row["amount"] > 0]
        total = sum(row["amount"] for row in nonzero)
        concentration_rows.append(
            {
                "symbol": symbol,
                "total_amount": round(total, 8),
                "top5_share_pct": percent(sum(row["amount"] for row in nonzero[:5]), total),
                "top10_share_pct": percent(sum(row["amount"] for row in nonzero[:10]), total),
                "top_recipients": nonzero[:10],
            }
        )

    workstream_performance = []
    for project in project_records:
        spent = asset_totals(
            [
                {"asset_symbol": "ETH", "amount": number_or_zero(project.get("spent", {}).get("eth"))},
                {"asset_symbol": "USDC", "amount": number_or_zero(project.get("spent", {}).get("usdc"))},
                {"asset_symbol": "GNARS", "amount": number_or_zero(project.get("spent", {}).get("gnars"))},
            ]
        )
        budget = asset_totals(
            [
                {"asset_symbol": "ETH", "amount": number_or_zero(project.get("budget", {}).get("eth"))},
                {"asset_symbol": "USDC", "amount": number_or_zero(project.get("budget", {}).get("usdc"))},
                {"asset_symbol": "GNARS", "amount": number_or_zero(project.get("budget", {}).get("gnars"))},
            ]
        )
        workstream_performance.append(
            {
                "project_id": project["project_id"],
                "name": project["name"],
                "category": normalize_category(project.get("category")) or "Other",
                "budget_by_asset": budget,
                "spent_by_asset": spent,
                "delivery_count": project.get("delivery_count", 0),
                "proof_count": project.get("proof_count", 0),
                "proof_coverage_pct": project.get("proof_coverage_pct"),
            }
        )
    workstream_performance.sort(key=lambda row: (-sum(item["amount"] for item in row["spent_by_asset"]), row["name"].lower()))

    return {
        "dataset": "insights",
        "analytics_as_of": analytics_as_of,
        "as_of": analytics_as_of,
        "version": 1,
        "treasury_breakdown": {
            "assets": [
                {
                    "symbol": record["symbol"],
                    "name": record["name"],
                    "amount": record["amount"],
                    "value_usd": record["value_usd"],
                }
                for record in sorted(treasury.get("records") or [], key=lambda row: -number_or_zero(row.get("value_usd")))
            ]
        },
        "spending_by_category": [
            {
                "category": category,
                "totals_by_asset": asset_totals(records),
                "route_count": len(records),
                "proposal_count": len({record["archive_id"] for record in records}),
            }
            for category, records in sorted(spending_by_category.items(), key=lambda item: PRODUCT_CATEGORIES.index(item[0]) if item[0] in PRODUCT_CATEGORIES else 999)
        ],
        "proposal_status_breakdown": [
            {"status": status, "count": count}
            for status, count in sorted(Counter(record["status"] for record in proposals).items())
        ],
        "proposal_success_by_category": success_by_category,
        "recipient_concentration": concentration_rows,
        "workstream_performance": workstream_performance[:24],
        "top_recipients_over_time": treasury_flows.get("windows") or [],
        "signal_windows": community_signals.get("windows") or [],
    }


def _facet_records(values: list[str]) -> list[dict[str, Any]]:
    counter = Counter(value for value in values if value not in (None, ""))
    return [
        {"value": value, "label": label_display(value), "count": count}
        for value, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    ]


def build_filter_facets(
    feed_stream: dict[str, Any],
    proposals_enriched: dict[str, Any],
    people: dict[str, Any],
    project_rollups: dict[str, Any],
    treasury_flows: dict[str, Any],
    timeline_events: dict[str, Any],
    analytics_as_of: str,
) -> dict[str, Any]:
    proposals = proposals_enriched.get("records") or []
    people_records = people.get("records") or []
    projects = project_rollups.get("records") or []
    feed_items = feed_stream.get("records") or []
    treasury_routes = treasury_flows.get("routes") or []
    timeline = timeline_events.get("records") or []

    return {
        "dataset": "filter_facets",
        "analytics_as_of": analytics_as_of,
        "as_of": analytics_as_of,
        "version": 1,
        "surfaces": {
            "home": {
                "kind": _facet_records([record.get("kind") for record in feed_items]),
                "status": _facet_records([record.get("status") for record in feed_items]),
                "category": _facet_records([label for record in feed_items for label in (record.get("editorial_labels") or []) if label in PRODUCT_CATEGORY_LABELS]),
                "asset": _facet_records([label for record in feed_items for label in (record.get("linked_assets") or [])]),
            },
            "proposals": {
                "status": _facet_records([record.get("status") for record in proposals]),
                "category": _facet_records([slug_label(record.get("category")) for record in proposals]),
                "platform": _facet_records([record.get("platform") for record in proposals]),
                "chain": _facet_records([record.get("chain") for record in proposals]),
            },
            "community": {
                "tribe": _facet_records([tribe for record in people_records for tribe in (record.get("tribes") or [])]),
                "status": _facet_records([record.get("status") for record in people_records]),
            },
            "projects": {
                "category": _facet_records([slug_label(normalize_category(record.get("category")) or "Other") for record in projects]),
                "status": _facet_records([record.get("status") for record in projects]),
            },
            "treasury": {
                "asset": _facet_records([record.get("asset_symbol") for record in treasury_routes]),
                "status": _facet_records([record.get("proposal_status") for record in treasury_routes]),
                "category": _facet_records(
                    [
                        slug_label(
                            next(
                                (proposal["category"] for proposal in proposals if proposal["archive_id"] == record["archive_id"]),
                                "Other",
                            )
                        )
                        for record in treasury_routes
                    ]
                ),
            },
            "timeline": {
                "kind": _facet_records([record.get("kind") for record in timeline]),
                "status": _facet_records([record.get("status") for record in timeline]),
            },
        },
    }


def build_treasury_snapshots(treasury: dict[str, Any], analytics_as_of: str) -> dict[str, Any]:
    return {
        "dataset": "treasury_snapshots",
        "analytics_as_of": analytics_as_of,
        "as_of": analytics_as_of,
        "version": 1,
        "records": [
            {
                "snapshot_id": analytics_as_of[:10],
                "date": analytics_as_of[:10],
                "wallet_address": treasury["wallet"]["address"],
                "wallet_label": treasury["wallet"]["label"],
                "homepage_label_usd": treasury["overview"]["homepage_treasury_label_usd"],
                "total_value_usd": treasury["overview"]["treasury_page_total_value_usd"],
                "display_widget_usd": treasury["overview"]["treasury_page_display_total_usd"],
                "assets": [
                    {
                        "symbol": record["symbol"],
                        "amount": record["amount"],
                        "value_usd": record["value_usd"],
                    }
                    for record in sorted(treasury.get("records") or [], key=lambda row: -number_or_zero(row.get("value_usd")))
                ],
                "data_quality_note": treasury["overview"].get("data_quality_note"),
            }
        ],
    }

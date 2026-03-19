from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_API_DIR = ROOT / "raw" / "api"

BASE_USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"


def load_json_path(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_json(name: str) -> Any:
    return load_json_path(DATA_DIR / f"{name}.json")


def write_json(name: str, payload: dict[str, Any]) -> None:
    path = DATA_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[ok] wrote {path.relative_to(ROOT)}")


def normalize_address(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    return text.lower()


def short_address(address: str) -> str:
    if len(address) < 12:
        return address
    return f"{address[:6]}...{address[-4:]}"


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned or "unknown"


def unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        ordered.append(text)
    return ordered


def unique_addresses(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        address = normalize_address(value)
        if not address or address in seen:
            continue
        seen.add(address)
        ordered.append(address)
    return ordered


def number_or_zero(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def integer_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def latest_members_snapshot() -> dict[str, Any]:
    candidates = sorted(RAW_API_DIR.glob("*gnars-members-api.json"))
    if not candidates:
        raise FileNotFoundError("No gnars members API snapshot found in raw/api/")
    return load_json_path(candidates[-1])


def contract_symbol(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "", value or "").upper()
    if cleaned == "GNARS":
        return "GNARS"
    return cleaned or "TOKEN"


def build_asset_indexes() -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    symbol_by_address: dict[str, str] = {}
    name_by_address: dict[str, str] = {}
    label_by_address: dict[str, str] = {}

    treasury = load_json("treasury")
    for record in treasury["records"]:
        token_address = normalize_address(record.get("token_address"))
        if not token_address:
            continue
        symbol_by_address[token_address] = str(record.get("symbol") or contract_symbol(record.get("name", "")))
        name_by_address[token_address] = str(record.get("name") or symbol_by_address[token_address])
        label_by_address[token_address] = str(record.get("name") or record.get("symbol") or token_address)

    contracts = load_json("contracts")
    for record in contracts["records"]:
        address = normalize_address(record.get("address"))
        if not address:
            continue
        label = str(record.get("label") or address)
        label_by_address.setdefault(address, label)
        name_by_address.setdefault(address, label)
        if record.get("kind") == "erc20":
            symbol_by_address.setdefault(address, contract_symbol(label))

    symbol_by_address.setdefault(BASE_USDC, "USDC")
    name_by_address.setdefault(BASE_USDC, "USD Coin")
    label_by_address.setdefault(BASE_USDC, "USD Coin")
    return symbol_by_address, name_by_address, label_by_address


def related_project_id(project_lookup: dict[str, str], proposal_record: dict[str, Any]) -> str | None:
    candidates = [
        proposal_record.get("proposal_key"),
        proposal_record.get("archive_id"),
    ]
    for candidate in candidates:
        key = str(candidate or "").strip().lower()
        if key and key in project_lookup:
            return project_lookup[key]
    return None


def transfer_recipient(transaction: dict[str, Any]) -> str:
    kind = transaction.get("kind")
    if kind == "native_transfer":
        return normalize_address(transaction.get("target") or transaction.get("recipient"))
    if kind == "erc20_transfer":
        return normalize_address(transaction.get("recipient") or transaction.get("target"))
    if kind == "erc721_transfer":
        return normalize_address(transaction.get("recipient"))
    return ""


def fungible_transfer_details(
    transaction: dict[str, Any],
    symbol_by_address: dict[str, str],
    name_by_address: dict[str, str],
) -> dict[str, Any] | None:
    kind = transaction.get("kind")
    recipient = transfer_recipient(transaction)
    if kind == "native_transfer":
        amount = number_or_zero(transaction.get("amount_eth"))
        if not recipient or amount <= 0:
            return None
        return {
            "asset_symbol": "ETH",
            "asset_name": "Ether",
            "asset_kind": "native",
            "token_contract": None,
            "recipient": recipient,
            "amount": amount,
        }

    if kind == "erc20_transfer":
        token_address = normalize_address(transaction.get("token_contract") or transaction.get("target"))
        amount = number_or_zero(transaction.get("amount_normalized") or transaction.get("amount_raw"))
        if not recipient or amount <= 0:
            return None
        return {
            "asset_symbol": symbol_by_address.get(token_address, contract_symbol(token_address[:8])),
            "asset_name": name_by_address.get(token_address, token_address or "ERC20"),
            "asset_kind": "erc20",
            "token_contract": token_address or None,
            "recipient": recipient,
            "amount": amount,
        }

    return None


def nft_transfer_details(transaction: dict[str, Any], label_by_address: dict[str, str]) -> dict[str, Any] | None:
    if transaction.get("kind") != "erc721_transfer":
        return None
    recipient = transfer_recipient(transaction)
    contract_address = normalize_address(transaction.get("token_contract") or transaction.get("target"))
    token_id = transaction.get("token_id")
    if not recipient or not contract_address:
        return None
    return {
        "recipient": recipient,
        "token_contract": contract_address,
        "contract_label": label_by_address.get(contract_address, contract_address),
        "token_id": token_id,
    }


def empty_person(address: str) -> dict[str, Any]:
    return {
        "address": address,
        "display_name": None,
        "slug": None,
        "status": "active",
        "role": None,
        "roles": set(),
        "tags": set(),
        "domains": set(),
        "bio": None,
        "links": {
            "member_url": None,
            "farcaster": None,
            "github": None,
            "avatar_url": None,
            "website": None,
            "x": None,
            "instagram": None,
        },
        "notes": [],
        "holder_token_count": 0,
        "delegated_token_count": 0,
        "active_votes": 0,
        "votes_count": 0,
        "attendance_pct": None,
        "like_pct": None,
        "proposals_authored": set(),
        "voted_proposals": set(),
        "payout_proposals": set(),
        "owned_projects": set(),
        "related_projects": set(),
        "related_updates": set(),
        "eth_received": 0.0,
        "usdc_received": 0.0,
        "gnars_received": 0.0,
        "fungible_transfer_count": 0,
        "nft_received_count": 0,
        "nft_transfer_count": 0,
        "asset_totals": defaultdict(float),
        "nft_assets": defaultdict(int),
    }


def ensure_person(people: dict[str, dict[str, Any]], address: str) -> dict[str, Any]:
    if address not in people:
        people[address] = empty_person(address)
    return people[address]


def merge_links(target: dict[str, Any], source: dict[str, Any]) -> None:
    for key, value in source.items():
        if value not in (None, ""):
            target[key] = value


def maybe_farcaster_url(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if text.startswith("http://") or text.startswith("https://"):
        return text
    return f"https://farcaster.xyz/{text.lstrip('@')}"


def authored_suggests_athlete(text: str) -> bool:
    lowered = text.lower()
    keywords = [
        "athlete",
        "gnarthlete",
        "skate",
        "snowboard",
        "ski",
        "surfer",
        "bike",
        "bmx",
        "mtb",
        "rider",
    ]
    return any(keyword in lowered for keyword in keywords)


def build_updates_index(project_updates: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    by_project: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in project_updates["records"]:
        by_project[record["project_id"]].append(record)
    for updates in by_project.values():
        updates.sort(key=lambda record: (record.get("date") or "", record.get("update_id") or ""))
    return by_project


def finalize_slugs(records: list[dict[str, Any]], key: str = "display_name") -> None:
    counts = Counter()
    for record in records:
        base = record.get("slug") or slugify(str(record.get(key) or record.get("address") or "unknown"))
        counts[base] += 1
        record["slug"] = base

    seen: Counter[str] = Counter()
    for record in records:
        base = str(record["slug"])
        seen[base] += 1
        if counts[base] == 1:
            continue
        suffix = short_address(str(record.get("address") or ""))[-4:].lower().replace(".", "")
        record["slug"] = f"{base}-{suffix or seen[base]}"


def build_people_dataset(
    members_seed: dict[str, Any],
    members_snapshot: dict[str, Any],
    archive: dict[str, Any],
    projects: dict[str, Any],
    project_updates: dict[str, Any],
    people_overrides: dict[str, Any],
    spend_ledger_records: list[dict[str, Any]],
    nft_receipts: list[dict[str, Any]],
) -> dict[str, Any]:
    people: dict[str, dict[str, Any]] = {}

    for record in members_seed["records"]:
        address = normalize_address(record["address"])
        person = ensure_person(people, address)
        person["display_name"] = record.get("display_name") or person["display_name"]
        person["role"] = record.get("role") or person["role"]
        person["roles"].add(record.get("role") or "")
        person["domains"].update(record.get("domains") or [])
        person["tags"].update({"member", "contributor"})
        person["notes"].append(record.get("notes") or "")
        merge_links(person["links"], record.get("links") or {})
        metrics = record.get("metrics") or {}
        person["holder_token_count"] = max(person["holder_token_count"], int(metrics.get("token_count") or 0))
        person["active_votes"] = max(person["active_votes"], int(metrics.get("active_votes") or 0))
        person["votes_count"] = max(person["votes_count"], int(metrics.get("votes_count") or 0))
        if metrics.get("attendance_pct") is not None:
            person["attendance_pct"] = int(metrics["attendance_pct"])
        if metrics.get("like_pct") is not None:
            person["like_pct"] = int(metrics["like_pct"])

    for record in people_overrides["records"]:
        address = normalize_address(record["address"])
        person = ensure_person(people, address)
        if record.get("display_name"):
            person["display_name"] = record["display_name"]
        if record.get("slug"):
            person["slug"] = record["slug"]
        if record.get("status"):
            person["status"] = record["status"]
        if record.get("role"):
            person["role"] = record["role"]
        person["roles"].update(record.get("roles") or [])
        person["tags"].update(record.get("tags") or [])
        if record.get("bio"):
            person["bio"] = record["bio"]
        person["notes"].append(record.get("notes") or "")
        merge_links(person["links"], record.get("links") or {})

    for record in members_snapshot.get("members", []):
        owner = normalize_address(record.get("owner"))
        delegate = normalize_address(record.get("delegate"))
        token_count = int(record.get("tokenCount") or 0)
        votes_count = int(record.get("votesCount") or 0)
        active_votes = int(record.get("activeVotes") or 0)
        attendance_pct = integer_or_none(record.get("attendancePct"))
        like_pct = integer_or_none(record.get("likePct"))

        if owner:
            owner_person = ensure_person(people, owner)
            owner_person["holder_token_count"] += token_count
            owner_person["active_votes"] = max(owner_person["active_votes"], active_votes)
            owner_person["votes_count"] = max(owner_person["votes_count"], votes_count)
            if attendance_pct is not None:
                owner_person["attendance_pct"] = attendance_pct
            if like_pct is not None:
                owner_person["like_pct"] = like_pct
            if token_count > 0:
                owner_person["tags"].add("holder")
            farcaster = maybe_farcaster_url(record.get("farcaster"))
            if farcaster and not owner_person["links"]["farcaster"]:
                owner_person["links"]["farcaster"] = farcaster
                if not owner_person["display_name"]:
                    owner_person["display_name"] = farcaster.rstrip("/").rsplit("/", 1)[-1]

        if delegate:
            delegate_person = ensure_person(people, delegate)
            delegate_person["delegated_token_count"] += token_count
            if token_count > 0:
                delegate_person["tags"].add("delegate")

    for record in archive["records"]:
        archive_id = record["archive_id"]
        proposal_title = str(record.get("title") or "")

        proposer = normalize_address(record.get("proposer"))
        if proposer:
            person = ensure_person(people, proposer)
            person["proposals_authored"].add(archive_id)
            person["tags"].update({"proposer", "contributor"})
            if record.get("proposer_label") and not person["display_name"]:
                person["display_name"] = record["proposer_label"]
            if authored_suggests_athlete(f"{proposal_title}\n{record.get('content_summary') or ''}"):
                person["tags"].add("athlete")

        for vote in record.get("votes") or []:
            voter = normalize_address(vote.get("voter"))
            if not voter:
                continue
            person = ensure_person(people, voter)
            person["voted_proposals"].add(archive_id)
            if vote.get("voterEnsName") and not person["display_name"]:
                person["display_name"] = vote["voterEnsName"]

    for record in spend_ledger_records:
        address = normalize_address(record["recipient_address"])
        if not address:
            continue
        person = ensure_person(people, address)
        symbol = record["asset_symbol"]
        amount = number_or_zero(record["amount"])
        person["payout_proposals"].add(record["archive_id"])
        person["fungible_transfer_count"] += 1
        person["asset_totals"][symbol] += amount
        person["tags"].update({"recipient", "contributor"})
        if record.get("project_id"):
            person["related_projects"].add(record["project_id"])
        if symbol == "ETH":
            person["eth_received"] += amount
        elif symbol == "USDC":
            person["usdc_received"] += amount
        elif symbol == "GNARS":
            person["gnars_received"] += amount

    for record in nft_receipts:
        address = normalize_address(record["recipient_address"])
        if not address:
            continue
        person = ensure_person(people, address)
        label = str(record.get("contract_label") or record.get("token_contract") or "NFT")
        person["nft_received_count"] += 1
        person["nft_transfer_count"] += 1
        person["nft_assets"][label] += 1
        person["tags"].update({"recipient", "contributor"})
        if record.get("project_id"):
            person["related_projects"].add(record["project_id"])

    for record in projects["records"]:
        for address in record.get("owner_addresses") or []:
            normalized = normalize_address(address)
            if not normalized:
                continue
            person = ensure_person(people, normalized)
            person["owned_projects"].add(record["project_id"])
            person["related_projects"].add(record["project_id"])
            person["tags"].update({"contributor", "builder"})

    for record in project_updates["records"]:
        for address in record.get("related_addresses") or []:
            normalized = normalize_address(address)
            if not normalized:
                continue
            person = ensure_person(people, normalized)
            person["related_updates"].add(record["update_id"])
            person["related_projects"].add(record["project_id"])

    records: list[dict[str, Any]] = []
    for address, person in people.items():
        if not person["links"]["member_url"]:
            person["links"]["member_url"] = f"https://www.gnars.com/members/{address}"

        display_name = person["display_name"] or short_address(address)
        base_role = person["role"] or ", ".join(unique_strings(list(person["roles"]))[:2]) or "community member"
        notes = " ".join(unique_strings(person["notes"]))

        active_votes = max(person["active_votes"], person["delegated_token_count"])
        authored_count = len(person["proposals_authored"])
        voted_count = len(person["voted_proposals"])

        roles = unique_strings([role for role in person["roles"] if role])
        tags = unique_strings(sorted(person["tags"]))
        domains = unique_strings(sorted(person["domains"]))
        related_projects = sorted(person["related_projects"])
        authored_proposals = sorted(person["proposals_authored"])
        voted_proposals = sorted(person["voted_proposals"])
        payout_proposals = sorted(person["payout_proposals"])

        records.append(
            {
                "person_id": display_name.lower().replace(" ", "-"),
                "slug": person["slug"] or slugify(display_name),
                "display_name": display_name,
                "address": address,
                "address_short": short_address(address),
                "status": person["status"],
                "role": base_role,
                "roles": roles,
                "tags": tags,
                "domains": domains,
                "bio": person["bio"] or "",
                "identity": {
                    "member_url": person["links"]["member_url"],
                    "farcaster": person["links"]["farcaster"],
                    "github": person["links"]["github"],
                    "avatar_url": person["links"]["avatar_url"],
                    "website": person["links"]["website"],
                    "x": person["links"]["x"],
                    "instagram": person["links"]["instagram"],
                },
                "governance": {
                    "holder_token_count": person["holder_token_count"],
                    "delegated_token_count": person["delegated_token_count"],
                    "active_votes": active_votes,
                    "votes_count": person["votes_count"],
                    "attendance_pct": person["attendance_pct"],
                    "like_pct": person["like_pct"],
                    "proposals_authored_count": authored_count,
                    "votes_cast_count": voted_count,
                },
                "receipts": {
                    "eth_received": round(person["eth_received"], 8),
                    "usdc_received": round(person["usdc_received"], 8),
                    "gnars_received": round(person["gnars_received"], 8),
                    "fungible_transfer_count": person["fungible_transfer_count"],
                    "nft_received_count": person["nft_received_count"],
                    "nft_transfer_count": person["nft_transfer_count"],
                    "by_asset": [
                        {
                            "symbol": symbol,
                            "amount": round(amount, 8),
                        }
                        for symbol, amount in sorted(person["asset_totals"].items())
                    ],
                    "nft_assets": [
                        {
                            "label": label,
                            "count": count,
                        }
                        for label, count in sorted(person["nft_assets"].items())
                    ],
                },
                "relationships": {
                    "authored_proposals": authored_proposals,
                    "voted_proposals": voted_proposals,
                    "payout_proposals": payout_proposals,
                    "owned_projects": sorted(person["owned_projects"]),
                    "related_projects": related_projects,
                    "related_updates": sorted(person["related_updates"]),
                },
                "notes": notes,
            }
        )

    finalize_slugs(records, key="display_name")
    records.sort(
        key=lambda record: (
            -record["receipts"]["usdc_received"],
            -record["receipts"]["eth_received"],
            -record["governance"]["active_votes"],
            record["display_name"].lower(),
        )
    )

    return {
        "dataset": "people",
        "as_of": archive["as_of"],
        "version": 1,
        "source_members_snapshot": str(sorted(RAW_API_DIR.glob("*gnars-members-api.json"))[-1].name),
        "records": records,
    }


def build_spend_and_nft_records(
    archive: dict[str, Any],
    project_lookup: dict[str, str],
    project_names: dict[str, str],
    people_by_address: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    symbol_by_address, name_by_address, label_by_address = build_asset_indexes()
    spend_records: list[dict[str, Any]] = []
    nft_records: list[dict[str, Any]] = []

    for proposal in archive["records"]:
        project_id = related_project_id(project_lookup, proposal)
        for transaction in proposal.get("transactions") or []:
            recipient = transfer_recipient(transaction)
            person = people_by_address.get(recipient, {})
            person_name = person.get("display_name") or short_address(recipient) if recipient else ""

            fungible = fungible_transfer_details(transaction, symbol_by_address, name_by_address)
            if fungible:
                spend_records.append(
                    {
                        "ledger_id": f"{proposal['archive_id']}:{transaction.get('index')}",
                        "archive_id": proposal["archive_id"],
                        "proposal_key": proposal["proposal_key"],
                        "proposal_number": proposal["proposal_number"],
                        "title": proposal["title"],
                        "status": proposal["status"],
                        "chain": proposal["chain"],
                        "project_id": project_id,
                        "project_name": project_names.get(project_id),
                        "proposer": normalize_address(proposal.get("proposer")),
                        "proposal_end_at": proposal.get("end_at"),
                        "proposal_created_at": proposal.get("created_at"),
                        "asset_symbol": fungible["asset_symbol"],
                        "asset_name": fungible["asset_name"],
                        "asset_kind": fungible["asset_kind"],
                        "token_contract": fungible["token_contract"],
                        "recipient_address": fungible["recipient"],
                        "recipient_display_name": person_name,
                        "amount": round(fungible["amount"], 8),
                        "source_url": proposal["links"]["source_url"],
                        "canonical_url": proposal["links"]["canonical_url"],
                    }
                )
                continue

            nft = nft_transfer_details(transaction, label_by_address)
            if not nft:
                continue
            nft_records.append(
                {
                    "receipt_id": f"{proposal['archive_id']}:{transaction.get('index')}",
                    "archive_id": proposal["archive_id"],
                    "proposal_key": proposal["proposal_key"],
                    "proposal_number": proposal["proposal_number"],
                    "title": proposal["title"],
                    "chain": proposal["chain"],
                    "project_id": project_id,
                    "project_name": project_names.get(project_id),
                    "recipient_address": nft["recipient"],
                    "recipient_display_name": person_name,
                    "token_contract": nft["token_contract"],
                    "contract_label": nft["contract_label"],
                    "token_id": str(nft["token_id"]) if nft["token_id"] not in (None, "") else None,
                    "source_url": proposal["links"]["source_url"],
                }
            )

    spend_records.sort(
        key=lambda record: (
            record.get("proposal_end_at") or "",
            record["archive_id"],
            record["ledger_id"],
        ),
        reverse=True,
    )
    nft_records.sort(key=lambda record: record["receipt_id"])
    return spend_records, nft_records


def build_project_rollups(
    projects: dict[str, Any],
    project_updates: dict[str, Any],
    spend_records: list[dict[str, Any]],
    nft_records: list[dict[str, Any]],
    people_by_address: dict[str, dict[str, Any]],
    proposals_by_key: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    updates_by_project = build_updates_index(project_updates)
    spend_by_project: dict[str, list[dict[str, Any]]] = defaultdict(list)
    nft_by_project: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in spend_records:
        if record.get("project_id"):
            spend_by_project[record["project_id"]].append(record)
    for record in nft_records:
        if record.get("project_id"):
            nft_by_project[record["project_id"]].append(record)

    rollups: list[dict[str, Any]] = []
    for project in projects["records"]:
        project_id = project["project_id"]
        rollup_spend = spend_by_project.get(project_id, [])
        rollup_nfts = nft_by_project.get(project_id, [])

        spent_eth = sum(record["amount"] for record in rollup_spend if record["asset_symbol"] == "ETH")
        spent_usdc = sum(record["amount"] for record in rollup_spend if record["asset_symbol"] == "USDC")
        spent_gnars = sum(record["amount"] for record in rollup_spend if record["asset_symbol"] == "GNARS")
        budget_eth = number_or_zero(project["budget"].get("eth"))
        budget_usdc = number_or_zero(project["budget"].get("usdc"))
        budget_gnars = 0.0

        recipient_rows: dict[str, dict[str, Any]] = {}
        for record in rollup_spend:
            address = normalize_address(record["recipient_address"])
            person = people_by_address.get(address, {})
            if address not in recipient_rows:
                recipient_rows[address] = {
                    "address": address,
                    "display_name": person.get("display_name") or short_address(address),
                    "eth_received": 0.0,
                    "usdc_received": 0.0,
                    "gnars_received": 0.0,
                    "fungible_transfer_count": 0,
                    "nft_received_count": 0,
                }
            row = recipient_rows[address]
            symbol = record["asset_symbol"]
            if symbol == "ETH":
                row["eth_received"] += record["amount"]
            elif symbol == "USDC":
                row["usdc_received"] += record["amount"]
            elif symbol == "GNARS":
                row["gnars_received"] += record["amount"]
            row["fungible_transfer_count"] += 1

        nft_rows: dict[str, dict[str, Any]] = {}
        for record in rollup_nfts:
            address = normalize_address(record["recipient_address"])
            person = people_by_address.get(address, {})
            recipient_rows.setdefault(
                address,
                {
                    "address": address,
                    "display_name": person.get("display_name") or short_address(address),
                    "eth_received": 0.0,
                    "usdc_received": 0.0,
                    "gnars_received": 0.0,
                    "fungible_transfer_count": 0,
                    "nft_received_count": 0,
                },
            )
            recipient_rows[address]["nft_received_count"] += 1

            key = f"{address}:{record['contract_label']}"
            nft_rows.setdefault(
                key,
                {
                    "address": address,
                    "display_name": person.get("display_name") or short_address(address),
                    "contract_label": record["contract_label"],
                    "token_contract": record["token_contract"],
                    "count": 0,
                },
            )
            nft_rows[key]["count"] += 1

        proposal_summaries = []
        for origin in project["origin_proposals"]:
            proposal = proposals_by_key.get(origin.lower())
            proposal_summaries.append(
                {
                    "proposal_key": origin,
                    "archive_id": proposal.get("archive_id") if proposal else None,
                    "proposal_number": proposal.get("proposal_number") if proposal else None,
                    "title": proposal.get("title") if proposal else origin,
                    "status": proposal.get("status") if proposal else "unknown",
                }
            )

        updates = updates_by_project.get(project_id, [])
        rollups.append(
            {
                "project_id": project_id,
                "slug": slugify(project["name"]),
                "name": project["name"],
                "status": project["status"],
                "category": project["category"],
                "origin_proposals": project["origin_proposals"],
                "proposal_summaries": proposal_summaries,
                "owner_addresses": unique_addresses(project.get("owner_addresses") or []),
                "budget": {
                    "eth": budget_eth,
                    "usdc": budget_usdc,
                    "gnars": budget_gnars,
                },
                "spent": {
                    "eth": round(spent_eth, 8),
                    "usdc": round(spent_usdc, 8),
                    "gnars": round(spent_gnars, 8),
                },
                "utilization_pct": {
                    "eth": round((spent_eth / budget_eth) * 100, 2) if budget_eth > 0 else None,
                    "usdc": round((spent_usdc / budget_usdc) * 100, 2) if budget_usdc > 0 else None,
                    "gnars": round((spent_gnars / budget_gnars) * 100, 2) if budget_gnars > 0 else None,
                },
                "recipients": sorted(
                    recipient_rows.values(),
                    key=lambda record: (-record["usdc_received"], -record["eth_received"], record["display_name"].lower()),
                ),
                "nft_receipts": sorted(
                    nft_rows.values(),
                    key=lambda record: (-record["count"], record["display_name"].lower()),
                ),
                "updates_count": len(updates),
                "update_ids": [record["update_id"] for record in updates],
                "last_update_date": updates[-1]["date"] if updates else None,
                "objective": project["objective"],
                "outputs": project["outputs"],
                "kpis": project["kpis"],
                "notes": project["notes"],
            }
        )

    rollups.sort(key=lambda record: (-record["spent"]["usdc"], -record["spent"]["eth"], record["name"].lower()))
    return {
        "dataset": "project_rollups",
        "as_of": projects["as_of"],
        "version": 1,
        "records": rollups,
    }


def build_dao_metrics(
    archive: dict[str, Any],
    people: dict[str, Any],
    project_rollups: dict[str, Any],
    spend_records: list[dict[str, Any]],
    nft_records: list[dict[str, Any]],
    treasury: dict[str, Any],
) -> dict[str, Any]:
    people_records = people["records"]
    proposal_status_counts = Counter(record["status"] for record in archive["records"])

    def leaderboard(
        value_getter: Any,
        *,
        minimum: float = 0,
        limit: int = 10,
        label: str,
    ) -> list[dict[str, Any]]:
        rows = []
        for record in people_records:
            value = value_getter(record)
            if value is None or value <= minimum:
                continue
            rows.append(
                {
                    "display_name": record["display_name"],
                    "address": record["address"],
                    "slug": record["slug"],
                    "value": value,
                    "label": label,
                }
            )
        rows.sort(key=lambda record: (-record["value"], record["display_name"].lower()))
        return rows[:limit]

    recent_proposals = sorted(
        archive["records"],
        key=lambda record: (record.get("end_at") or record.get("created_at") or "", record["archive_id"]),
        reverse=True,
    )[:12]
    recent_payouts = sorted(
        spend_records,
        key=lambda record: (record.get("proposal_end_at") or record.get("proposal_created_at") or "", record["ledger_id"]),
        reverse=True,
    )[:12]

    treasury_assets = sorted(treasury["records"], key=lambda record: -number_or_zero(record.get("value_usd")))[:10]
    overview = {
        "proposal_count": len(archive["records"]),
        "active_proposal_count": proposal_status_counts.get("active", 0),
        "people_count": len(people_records),
        "holders_count": sum(1 for record in people_records if "holder" in record["tags"]),
        "delegates_count": sum(1 for record in people_records if "delegate" in record["tags"]),
        "contributors_count": sum(1 for record in people_records if "contributor" in record["tags"]),
        "athletes_count": sum(1 for record in people_records if "athlete" in record["tags"]),
        "recipients_count": sum(1 for record in people_records if "recipient" in record["tags"]),
        "proposers_count": sum(1 for record in people_records if "proposer" in record["tags"]),
        "workstream_count": len(project_rollups["records"]),
        "treasury_assets_count": len(treasury["records"]),
        "treasury_total_value_usd": treasury["overview"]["treasury_page_total_value_usd"],
        "outflows_eth": round(sum(record["amount"] for record in spend_records if record["asset_symbol"] == "ETH"), 8),
        "outflows_usdc": round(sum(record["amount"] for record in spend_records if record["asset_symbol"] == "USDC"), 8),
        "outflows_gnars": round(sum(record["amount"] for record in spend_records if record["asset_symbol"] == "GNARS"), 8),
        "fungible_transfer_count": len(spend_records),
        "nft_transfer_count": len(nft_records),
        "proposal_status_counts": dict(sorted(proposal_status_counts.items())),
    }

    return {
        "dataset": "dao_metrics",
        "as_of": archive["as_of"],
        "version": 1,
        "overview": overview,
        "treasury": {
            "wallet_address": treasury["wallet"]["address"],
            "wallet_label": treasury["wallet"]["label"],
            "homepage_treasury_label_usd": treasury["overview"]["homepage_treasury_label_usd"],
            "treasury_page_total_value_usd": treasury["overview"]["treasury_page_total_value_usd"],
            "treasury_page_display_total_usd": treasury["overview"]["treasury_page_display_total_usd"],
            "assets": [
                {
                    "symbol": record["symbol"],
                    "name": record["name"],
                    "amount": record["amount"],
                    "value_usd": record["value_usd"],
                }
                for record in treasury_assets
            ],
        },
        "leaderboards": {
            "eth_received": leaderboard(lambda record: record["receipts"]["eth_received"], label="ETH received"),
            "usdc_received": leaderboard(lambda record: record["receipts"]["usdc_received"], label="USDC received"),
            "gnars_received": leaderboard(lambda record: record["receipts"]["gnars_received"], label="GNARS received"),
            "proposal_count": leaderboard(
                lambda record: record["governance"]["proposals_authored_count"],
                label="proposals authored",
            ),
            "attendance_pct": leaderboard(
                lambda record: record["governance"]["attendance_pct"],
                label="attendance %",
            ),
            "active_votes": leaderboard(
                lambda record: record["governance"]["active_votes"],
                label="active votes",
            ),
        },
        "recent": {
            "proposals": [
                {
                    "archive_id": record["archive_id"],
                    "proposal_number": record["proposal_number"],
                    "title": record["title"],
                    "status": record["status"],
                    "end_at": record["end_at"],
                }
                for record in recent_proposals
            ],
            "payouts": [
                {
                    "ledger_id": record["ledger_id"],
                    "archive_id": record["archive_id"],
                    "asset_symbol": record["asset_symbol"],
                    "amount": record["amount"],
                    "recipient_display_name": record["recipient_display_name"],
                    "recipient_address": record["recipient_address"],
                    "project_id": record["project_id"],
                    "proposal_end_at": record["proposal_end_at"],
                }
                for record in recent_payouts
            ],
            "workstreams": [
                {
                    "project_id": record["project_id"],
                    "name": record["name"],
                    "status": record["status"],
                    "last_update_date": record["last_update_date"],
                }
                for record in project_rollups["records"][:8]
            ],
        },
    }


def build_timeline_events(
    archive: dict[str, Any],
    project_updates: dict[str, Any],
    project_rollups: dict[str, Any],
    project_lookup: dict[str, str],
) -> dict[str, Any]:
    project_by_id = {record["project_id"]: record for record in project_rollups["records"]}
    proposals_by_alias: dict[str, dict[str, Any]] = {}
    for record in archive["records"]:
        aliases = {
            str(record["archive_id"]).lower(),
            str(record["proposal_key"]).lower(),
        }
        number = record.get("proposal_number")
        chain = str(record.get("chain") or "").strip().lower()
        platform = str(record.get("platform") or "").strip().lower()
        if number is not None and chain:
            aliases.add(f"{chain}-{number}".lower())
        if number is not None and platform and chain:
            aliases.add(f"{platform}-{chain}-{number}".lower())
        for alias in aliases:
            proposals_by_alias[alias] = record

    def proposal_archive_id(value: str) -> str | None:
        record = proposals_by_alias.get(str(value).strip().lower())
        if record:
            return record["archive_id"]
        return None

    def proposal_record(value: str) -> dict[str, Any] | None:
        return proposals_by_alias.get(str(value).strip().lower())

    records: list[dict[str, Any]] = []

    for update in project_updates["records"]:
        resolved_proposals = [
            archive_id
            for archive_id in (
                proposal_archive_id(reference) for reference in update["related_proposals"]
            )
            if archive_id
        ]
        project = project_by_id.get(update["project_id"])
        records.append(
            {
                "event_id": f"project-update:{update['update_id']}",
                "date": update["date"],
                "title": update["title"],
                "summary": update["summary"],
                "kind": update["kind"],
                "status": update["status"],
                "project_id": update["project_id"],
                "project_name": project["name"] if project else None,
                "archive_id": resolved_proposals[0] if resolved_proposals else None,
                "proposal_number": (
                    proposal_record(update["related_proposals"][0]).get("proposal_number")
                    if update["related_proposals"] and proposal_record(update["related_proposals"][0])
                    else None
                ),
                "people_addresses": unique_addresses(update["related_addresses"]),
                "proposal_ids": resolved_proposals,
                "links": unique_strings(update["links"]),
                "source": "project_updates",
                "thumbnail_url": None,
            }
        )

    for proposal in archive["records"]:
        canonical_url = proposal["links"].get("canonical_url")
        source_url = proposal["links"].get("source_url")
        discussion_url = proposal["links"].get("discussion_url")
        related_project = related_project_id(project_lookup, proposal)
        project = project_by_id.get(related_project or "")
        event_date = proposal.get("end_at") or proposal.get("created_at") or proposal.get("start_at") or ""
        proposal_number = proposal.get("proposal_number")
        title = (
            f"Proposal #{proposal_number}: {proposal['title']}"
            if proposal_number is not None
            else proposal["title"]
        )
        records.append(
            {
                "event_id": f"proposal:{proposal['archive_id']}",
                "date": event_date,
                "title": title,
                "summary": proposal["content_summary"],
                "kind": "proposal",
                "status": proposal["status"],
                "project_id": related_project,
                "project_name": project["name"] if project else None,
                "archive_id": proposal["archive_id"],
                "proposal_number": proposal_number,
                "people_addresses": unique_addresses([proposal["proposer"]]),
                "proposal_ids": [proposal["archive_id"]],
                "links": unique_strings(
                    [
                        canonical_url,
                        source_url,
                        discussion_url,
                    ]
                ),
                "source": proposal["platform"],
                "thumbnail_url": proposal.get("cover_image_url"),
            }
        )

    records.sort(
        key=lambda record: (
            str(record.get("date") or ""),
            str(record.get("event_id") or ""),
        ),
        reverse=True,
    )

    return {
        "dataset": "timeline_events",
        "as_of": archive["as_of"],
        "version": 1,
        "records": records,
    }


def main() -> int:
    archive = load_json("proposals_archive")
    treasury = load_json("treasury")
    projects = load_json("projects")
    members_seed = load_json("members")
    people_overrides = load_json("people_overrides")
    project_updates = load_json("project_updates")
    members_snapshot = latest_members_snapshot()

    project_lookup: dict[str, str] = {}
    project_names: dict[str, str] = {}
    for project in projects["records"]:
        project_names[project["project_id"]] = project["name"]
        for origin in project["origin_proposals"]:
            project_lookup[origin.lower()] = project["project_id"]
            project_lookup[f"gnars-{origin}".lower()] = project["project_id"]

    seed_people = build_people_dataset(
        members_seed=members_seed,
        members_snapshot=members_snapshot,
        archive=archive,
        projects=projects,
        project_updates=project_updates,
        people_overrides=people_overrides,
        spend_ledger_records=[],
        nft_receipts=[],
    )
    seed_people_by_address = {record["address"]: record for record in seed_people["records"]}

    spend_records, nft_records = build_spend_and_nft_records(
        archive=archive,
        project_lookup=project_lookup,
        project_names=project_names,
        people_by_address=seed_people_by_address,
    )

    people = build_people_dataset(
        members_seed=members_seed,
        members_snapshot=members_snapshot,
        archive=archive,
        projects=projects,
        project_updates=project_updates,
        people_overrides=people_overrides,
        spend_ledger_records=spend_records,
        nft_receipts=nft_records,
    )
    people_by_address = {record["address"]: record for record in people["records"]}
    for record in spend_records:
        record["recipient_display_name"] = people_by_address.get(record["recipient_address"], {}).get("display_name") or short_address(record["recipient_address"])
    for record in nft_records:
        record["recipient_display_name"] = people_by_address.get(record["recipient_address"], {}).get("display_name") or short_address(record["recipient_address"])

    proposals_by_key: dict[str, dict[str, Any]] = {}
    for record in archive["records"]:
        aliases = {
            str(record["proposal_key"]).lower(),
            str(record["archive_id"]).lower(),
        }
        if record.get("proposal_number") is not None and record.get("chain"):
            aliases.add(f"{record['chain']}-{record['proposal_number']}".lower())
        for alias in aliases:
            proposals_by_key[alias] = record
    project_rollups = build_project_rollups(
        projects=projects,
        project_updates=project_updates,
        spend_records=spend_records,
        nft_records=nft_records,
        people_by_address=people_by_address,
        proposals_by_key=proposals_by_key,
    )
    dao_metrics = build_dao_metrics(
        archive=archive,
        people=people,
        project_rollups=project_rollups,
        spend_records=spend_records,
        nft_records=nft_records,
        treasury=treasury,
    )
    timeline_events = build_timeline_events(
        archive=archive,
        project_updates=project_updates,
        project_rollups=project_rollups,
        project_lookup=project_lookup,
    )

    write_json("people", people)
    write_json(
        "spend_ledger",
        {
            "dataset": "spend_ledger",
            "as_of": archive["as_of"],
            "version": 1,
            "records": spend_records,
        },
    )
    write_json("project_rollups", project_rollups)
    write_json("dao_metrics", dao_metrics)
    write_json("timeline_events", timeline_events)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

from Crypto.Hash import keccak

from product_datasets import (
    build_feed_stream,
    build_filter_facets,
    build_insights,
    build_media_proof,
    build_proposals_enriched,
    build_treasury_snapshots,
    expand_people,
    expand_project_rollups,
    hydrate_proposals_with_proof,
    latest_value,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_API_DIR = ROOT / "raw" / "api"

BASE_USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
BASE_SENDIT = "0xba5b9b2d2d06a9021eb3190ea5fb0e02160839a4"
TOKEN_DECIMALS_BY_ADDRESS = {
    BASE_USDC: 6,
    BASE_SENDIT: 18,
}
ETH_MAINNET_RPC_URL = "https://ethereum-rpc.publicnode.com"
ETH_MAINNET_CHAIN_ID = "0x1"
ENS_REGISTRY = "0x00000000000c2e074ec69a0dfb2997ba6c7d2e1e"
RPC_BATCH_SIZE = 200
DISPLAY_NAME_PRIORITIES = {
    "seed": 350,
    "override": 400,
    "ens": 300,
    "farcaster": 250,
    "proposal_label": 200,
    "archive_vote_ens": 150,
}
JSON_RPC_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "gnars-data/ens-resolver",
}


def keccak256(value: bytes) -> bytes:
    digest = keccak.new(digest_bits=256)
    digest.update(value)
    return digest.digest()


def function_selector(signature: str) -> str:
    return keccak256(signature.encode("utf-8"))[:4].hex()


ENS_RESOLVER_SELECTOR = function_selector("resolver(bytes32)")
ENS_NAME_SELECTOR = function_selector("name(bytes32)")
ENS_ADDR_SELECTOR = function_selector("addr(bytes32)")


def load_json_path(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_json(name: str) -> Any:
    return load_json_path(DATA_DIR / f"{name}.json")


def load_json_optional(name: str) -> Any | None:
    path = DATA_DIR / f"{name}.json"
    if not path.exists():
        return None
    return load_json_path(path)


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


def rpc_batch(payload: list[dict[str, Any]], url: str = ETH_MAINNET_RPC_URL) -> dict[int, Any]:
    request = urllib_request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=JSON_RPC_HEADERS,
    )
    try:
        with urllib_request.urlopen(request, timeout=45) as response:
            raw = response.read().decode("utf-8")
    except urllib_error.URLError as exc:
        raise RuntimeError(f"RPC batch request failed: {exc}") from exc
    body = json.loads(raw)
    if isinstance(body, dict):
        body = [body]
    results: dict[int, Any] = {}
    for item in body:
        if "error" in item:
            results[int(item["id"])] = None
            continue
        results[int(item["id"])] = item.get("result")
    return results


def namehash(name: str) -> str:
    node = b"\x00" * 32
    if name:
        for label in reversed([part for part in name.split(".") if part]):
            node = keccak256(node + keccak256(label.encode("utf-8")))
    return node.hex()


def decode_solidity_address(result: Any) -> str | None:
    if result in (None, "", "0x", "0x0"):
        return None
    text = str(result)
    if not text.startswith("0x"):
        return None
    body = text[2:].rjust(64, "0")
    address = f"0x{body[-40:]}".lower()
    if int(address, 16) == 0:
        return None
    return address


def decode_solidity_string(result: Any) -> str | None:
    if result in (None, "", "0x", "0x0"):
        return None
    text = str(result)
    if not text.startswith("0x"):
        return None
    body = text[2:]
    if len(body) < 128:
        return None
    offset = int(body[:64], 16) * 2
    if len(body) < offset + 64:
        return None
    length = int(body[offset : offset + 64], 16)
    start = offset + 64
    end = start + (length * 2)
    if len(body) < end:
        return None
    try:
        return bytes.fromhex(body[start:end]).decode("utf-8")
    except ValueError:
        return None


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


def mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def percent(numerator: float, denominator: float) -> float | None:
    if denominator <= 0:
        return None
    return round((numerator / denominator) * 100, 2)


def parse_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso_day(value: Any) -> str | None:
    parsed = parse_datetime(value)
    if parsed is None:
        return None
    return parsed.date().isoformat()


def latest_day(*values: Any) -> str | None:
    parsed_values = [parsed for parsed in (parse_datetime(value) for value in values) if parsed is not None]
    if not parsed_values:
        return None
    return max(parsed_values).date().isoformat()


def windowed(records: list[dict[str, Any]], key: str, since: datetime | None) -> list[dict[str, Any]]:
    if since is None:
        return records
    filtered: list[dict[str, Any]] = []
    for record in records:
        parsed = parse_datetime(record.get(key))
        if parsed is not None and parsed >= since:
            filtered.append(record)
    return filtered


def build_window_specs(as_of_value: str) -> list[dict[str, Any]]:
    as_of = parse_datetime(as_of_value) or datetime.now(timezone.utc)
    return [
        {"window_id": "7d", "label": "Last 7 Days", "since": as_of - timedelta(days=7)},
        {"window_id": "30d", "label": "Last 30 Days", "since": as_of - timedelta(days=30)},
        {"window_id": "90d", "label": "Last 90 Days", "since": as_of - timedelta(days=90)},
        {"window_id": "all", "label": "All Time", "since": None},
    ]


def is_successful_proposal(record: dict[str, Any]) -> bool:
    platform = str(record.get("platform") or "").strip().lower()
    status = str(record.get("status") or "").strip().lower()
    if platform in {"gnars", "gnars.com"}:
        return status == "executed"
    if platform == "snapshot" and status == "closed":
        scores = [number_or_zero(value) for value in (record.get("scores_by_choice") or [])]
        if not scores or number_or_zero(record.get("scores_total")) < number_or_zero(record.get("quorum")):
            return False
        return scores[0] > 0 and scores[0] == max(scores)
    return False


def proposal_event_at(record: dict[str, Any]) -> Any:
    return record.get("end_at") or record.get("created_at") or record.get("start_at")


def in_window(value: Any, since: datetime | None) -> bool:
    if since is None:
        return True
    parsed = parse_datetime(value)
    return parsed is not None and parsed >= since


def asset_totals(records: list[dict[str, Any]], *, symbol_key: str = "asset_symbol", amount_key: str = "amount") -> list[dict[str, Any]]:
    totals: defaultdict[str, float] = defaultdict(float)
    for record in records:
        symbol = str(record.get(symbol_key) or "").strip().upper()
        amount = number_or_zero(record.get(amount_key))
        if not symbol or amount <= 0:
            continue
        totals[symbol] += amount
    return [
        {
            "symbol": symbol,
            "amount": round(amount, 8),
        }
        for symbol, amount in sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    ]


def primary_asset_amount(records: list[dict[str, Any]]) -> float:
    if not records:
        return 0.0
    if "amount" in records[0] and "symbol" in records[0]:
        return number_or_zero(records[0]["amount"])
    totals = asset_totals(records)
    if not totals:
        return 0.0
    return number_or_zero(totals[0]["amount"])


def latest_members_snapshot() -> dict[str, Any]:
    candidates = sorted(RAW_API_DIR.glob("*gnars-members-api.json"))
    if not candidates:
        raise FileNotFoundError("No gnars members API snapshot found in raw/api/")
    return load_json_path(candidates[-1])


def build_previous_ens_cache() -> dict[str, dict[str, Any]]:
    existing_people = load_json_optional("people") or {}
    cache: dict[str, dict[str, Any]] = {}
    for record in existing_people.get("records", []):
        address = normalize_address(record.get("address"))
        identity = record.get("identity") or {}
        ens_name = str(identity.get("ens") or "").strip().lower()
        if not address:
            continue
        cache[address] = {
            "ens": ens_name or None,
            "ens_source": identity.get("ens_source"),
            "ens_verified_at": identity.get("ens_verified_at"),
        }
    return cache


def resolve_verified_ens_profiles(
    addresses: list[str],
    *,
    analytics_as_of: str,
    previous_cache: dict[str, dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    unique = unique_addresses(addresses)
    if not unique:
        return {}

    previous = previous_cache or {}
    resolved: dict[str, dict[str, Any]] = {
        address: {
            "ens": previous.get(address, {}).get("ens"),
            "ens_source": previous.get(address, {}).get("ens_source"),
            "ens_verified_at": previous.get(address, {}).get("ens_verified_at"),
        }
        for address in unique
    }

    reverse_nodes = {
        address: namehash(f"{address[2:]}.addr.reverse")
        for address in unique
        if address.startswith("0x") and len(address) == 42
    }
    if not reverse_nodes:
        return resolved

    try:
        chain_id_response = rpc_batch(
            [{"jsonrpc": "2.0", "id": 1, "method": "eth_chainId", "params": []}],
        )
        if str(chain_id_response.get(1)) != ETH_MAINNET_CHAIN_ID:
            raise RuntimeError(f"Unexpected ENS RPC chain id: {chain_id_response.get(1)!r}")

        reverse_resolver_requests: list[dict[str, Any]] = []
        reverse_request_ids: dict[int, str] = {}
        next_id = 10
        for address, node in reverse_nodes.items():
            reverse_request_ids[next_id] = address
            reverse_resolver_requests.append(
                {
                    "jsonrpc": "2.0",
                    "id": next_id,
                    "method": "eth_call",
                    "params": [{"to": ENS_REGISTRY, "data": f"0x{ENS_RESOLVER_SELECTOR}{node}"}, "latest"],
                }
            )
            next_id += 1

        reverse_resolver_results: dict[int, Any] = {}
        for start in range(0, len(reverse_resolver_requests), RPC_BATCH_SIZE):
            reverse_resolver_results.update(rpc_batch(reverse_resolver_requests[start : start + RPC_BATCH_SIZE]))

        reverse_resolvers = {
            reverse_request_ids[request_id]: decode_solidity_address(result)
            for request_id, result in reverse_resolver_results.items()
        }

        reverse_name_requests: list[dict[str, Any]] = []
        reverse_name_request_ids: dict[int, str] = {}
        for address, resolver in reverse_resolvers.items():
            if not resolver:
                continue
            reverse_name_request_ids[next_id] = address
            reverse_name_requests.append(
                {
                    "jsonrpc": "2.0",
                    "id": next_id,
                    "method": "eth_call",
                    "params": [{"to": resolver, "data": f"0x{ENS_NAME_SELECTOR}{reverse_nodes[address]}"}, "latest"],
                }
            )
            next_id += 1

        reverse_name_results: dict[int, Any] = {}
        for start in range(0, len(reverse_name_requests), RPC_BATCH_SIZE):
            reverse_name_results.update(rpc_batch(reverse_name_requests[start : start + RPC_BATCH_SIZE]))

        reverse_names = {
            reverse_name_request_ids[request_id]: (decode_solidity_string(result) or "").strip().lower()
            for request_id, result in reverse_name_results.items()
        }
        reverse_names = {address: name for address, name in reverse_names.items() if name}

        forward_resolver_requests: list[dict[str, Any]] = []
        forward_resolver_request_ids: dict[int, tuple[str, str]] = {}
        forward_nodes: dict[str, str] = {}
        for address, ens_name in reverse_names.items():
            node = namehash(ens_name)
            forward_nodes[address] = node
            forward_resolver_request_ids[next_id] = (address, ens_name)
            forward_resolver_requests.append(
                {
                    "jsonrpc": "2.0",
                    "id": next_id,
                    "method": "eth_call",
                    "params": [{"to": ENS_REGISTRY, "data": f"0x{ENS_RESOLVER_SELECTOR}{node}"}, "latest"],
                }
            )
            next_id += 1

        forward_resolver_results: dict[int, Any] = {}
        for start in range(0, len(forward_resolver_requests), RPC_BATCH_SIZE):
            forward_resolver_results.update(rpc_batch(forward_resolver_requests[start : start + RPC_BATCH_SIZE]))

        forward_resolvers: dict[str, tuple[str, str]] = {}
        for request_id, result in forward_resolver_results.items():
            address, ens_name = forward_resolver_request_ids[request_id]
            resolver = decode_solidity_address(result)
            if resolver:
                forward_resolvers[address] = (ens_name, resolver)

        forward_address_requests: list[dict[str, Any]] = []
        forward_address_request_ids: dict[int, tuple[str, str]] = {}
        for address, (ens_name, resolver) in forward_resolvers.items():
            forward_address_request_ids[next_id] = (address, ens_name)
            forward_address_requests.append(
                {
                    "jsonrpc": "2.0",
                    "id": next_id,
                    "method": "eth_call",
                    "params": [{"to": resolver, "data": f"0x{ENS_ADDR_SELECTOR}{forward_nodes[address]}"}, "latest"],
                }
            )
            next_id += 1

        forward_address_results: dict[int, Any] = {}
        for start in range(0, len(forward_address_requests), RPC_BATCH_SIZE):
            forward_address_results.update(rpc_batch(forward_address_requests[start : start + RPC_BATCH_SIZE]))

        for request_id, result in forward_address_results.items():
            address, ens_name = forward_address_request_ids[request_id]
            if decode_solidity_address(result) == address:
                resolved[address] = {
                    "ens": ens_name,
                    "ens_source": "mainnet-reverse-forward",
                    "ens_verified_at": analytics_as_of,
                }
            else:
                resolved[address] = {
                    "ens": None,
                    "ens_source": None,
                    "ens_verified_at": None,
                }
    except Exception as exc:
        print(f"[warn] ENS resolution failed, keeping cached ENS values: {exc}")
        return resolved

    return resolved


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
        normalized_value = transaction.get("amount_normalized")
        raw_value = transaction.get("amount_raw")
        amount = number_or_zero(normalized_value if normalized_value not in (None, "") else raw_value)
        if raw_value not in (None, "") and token_address in TOKEN_DECIMALS_BY_ADDRESS:
            try:
                raw_int = int(str(raw_value))
            except ValueError:
                raw_int = 0
            normalized_text = str(normalized_value).strip() if normalized_value not in (None, "") else ""
            raw_text = str(raw_value).strip()
            if raw_int > 0 and (not normalized_text or normalized_text == raw_text):
                amount = raw_int / (10 ** TOKEN_DECIMALS_BY_ADDRESS[token_address])
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
        "display_name_priority": 0,
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
        "ens": None,
        "ens_source": None,
        "ens_verified_at": None,
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


def farcaster_handle(value: Any) -> str | None:
    url = maybe_farcaster_url(value)
    if not url:
        return None
    return url.rstrip("/").rsplit("/", 1)[-1] or None


def set_preferred_display_name(
    person: dict[str, Any],
    candidate: Any,
    source: str,
) -> None:
    text = str(candidate or "").strip()
    if not text:
        return
    priority = DISPLAY_NAME_PRIORITIES[source]
    current_priority = int(person.get("display_name_priority") or 0)
    if priority >= current_priority:
        person["display_name"] = text
        person["display_name_priority"] = priority


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
    ens_profiles: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    people: dict[str, dict[str, Any]] = {}

    for record in members_seed["records"]:
        address = normalize_address(record["address"])
        person = ensure_person(people, address)
        set_preferred_display_name(person, record.get("display_name"), "seed")
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
        set_preferred_display_name(person, record.get("display_name"), "override")
        override_ens = str(record.get("ens") or "").strip().lower()
        if override_ens:
            person["ens"] = override_ens
            person["ens_source"] = "override"
            person["ens_verified_at"] = people_overrides.get("as_of")
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
                set_preferred_display_name(owner_person, farcaster_handle(farcaster), "farcaster")

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
            set_preferred_display_name(person, record.get("proposer_label"), "proposal_label")
            if authored_suggests_athlete(f"{proposal_title}\n{record.get('content_summary') or ''}"):
                person["tags"].add("athlete")

        for vote in record.get("votes") or []:
            voter = normalize_address(vote.get("voter"))
            if not voter:
                continue
            person = ensure_person(people, voter)
            person["voted_proposals"].add(archive_id)
            set_preferred_display_name(person, vote.get("voterEnsName"), "archive_vote_ens")

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
        ens_profile = (ens_profiles or {}).get(address) or {}
        ens_name = person["ens"] or str(ens_profile.get("ens") or "").strip().lower() or None
        if ens_name and not person["ens_source"]:
            person["ens_source"] = ens_profile.get("ens_source")
            person["ens_verified_at"] = ens_profile.get("ens_verified_at")
        person["ens"] = ens_name
        if ens_name:
            set_preferred_display_name(person, ens_name, "ens")

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
                    "ens": person["ens"],
                    "ens_source": person["ens_source"],
                    "ens_verified_at": person["ens_verified_at"],
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
        if not is_successful_proposal(proposal):
            continue
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
    project_updates: dict[str, Any],
) -> dict[str, Any]:
    people_records = people["records"]
    proposal_status_counts = Counter(record["status"] for record in archive["records"])
    as_of_dt = parse_datetime(archive["as_of"]) or datetime.now(timezone.utc)
    by_30d = as_of_dt - timedelta(days=30)

    successful_proposals = [record for record in archive["records"] if is_successful_proposal(record)]
    closed_outcomes = sum(
        1
        for record in archive["records"]
        if str(record.get("status") or "").strip().lower() in {"executed", "closed", "defeated", "failed", "cancelled", "canceled", "expired"}
    )
    unique_voters = {
        normalize_address(vote.get("voter"))
        for proposal in archive["records"]
        for vote in (proposal.get("votes") or [])
        if normalize_address(vote.get("voter"))
    }
    vote_counts = [float(len(record.get("votes") or [])) for record in archive["records"]]

    proposals_with_routes = {record["archive_id"] for record in spend_records}
    payout_values_usdc = [number_or_zero(record["receipts"].get("usdc_received")) for record in people_records]
    payout_values_eth = [number_or_zero(record["receipts"].get("eth_received")) for record in people_records]
    top10_usdc = sum(sorted(payout_values_usdc, reverse=True)[:10])
    top10_eth = sum(sorted(payout_values_eth, reverse=True)[:10])

    recent_proposals_30d = [record for record in archive["records"] if in_window(proposal_event_at(record), by_30d)]
    recent_spend_30d = [record for record in spend_records if in_window(record.get("proposal_end_at") or record.get("proposal_created_at"), by_30d)]
    recent_deliveries_30d = [
        record
        for record in project_updates["records"]
        if in_window(record.get("date"), by_30d)
        and (
            str(record.get("status") or "").strip().lower() == "completed"
            or str(record.get("kind") or "").strip().lower() in {"delivery", "milestone"}
        )
    ]

    project_status_counts = Counter(str(record.get("status") or "unknown").strip().lower() for record in project_rollups["records"])

    proposal_event_days = [parse_datetime(proposal_event_at(record)) for record in archive["records"]]
    proposal_event_days = [day for day in proposal_event_days if day is not None]
    payout_event_days = [
        parse_datetime(record.get("proposal_end_at") or record.get("proposal_created_at"))
        for record in spend_records
    ]
    payout_event_days = [day for day in payout_event_days if day is not None]
    delivery_event_days = [
        parse_datetime(record.get("date"))
        for record in project_updates["records"]
        if str(record.get("status") or "").strip().lower() == "completed"
        or str(record.get("kind") or "").strip().lower() in {"delivery", "milestone"}
    ]
    delivery_event_days = [day for day in delivery_event_days if day is not None]

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
        "successful_proposal_count": len(successful_proposals),
        "closed_outcome_count": closed_outcomes,
        "proposal_success_rate_pct": percent(len(successful_proposals), closed_outcomes),
        "people_count": len(people_records),
        "holders_count": sum(1 for record in people_records if "holder" in record["tags"]),
        "delegates_count": sum(1 for record in people_records if "delegate" in record["tags"]),
        "contributors_count": sum(1 for record in people_records if "contributor" in record["tags"]),
        "athletes_count": sum(1 for record in people_records if "athlete" in record["tags"]),
        "recipients_count": sum(1 for record in people_records if "recipient" in record["tags"]),
        "proposers_count": sum(1 for record in people_records if "proposer" in record["tags"]),
        "unique_voters_count": len(unique_voters),
        "avg_votes_per_proposal": round(mean(vote_counts), 2),
        "median_votes_per_proposal": round(median(vote_counts), 2),
        "workstream_count": len(project_rollups["records"]),
        "workstream_status_counts": dict(sorted(project_status_counts.items())),
        "treasury_assets_count": len(treasury["records"]),
        "treasury_total_value_usd": treasury["overview"]["treasury_page_total_value_usd"],
        "outflows_eth": round(sum(record["amount"] for record in spend_records if record["asset_symbol"] == "ETH"), 8),
        "outflows_usdc": round(sum(record["amount"] for record in spend_records if record["asset_symbol"] == "USDC"), 8),
        "outflows_gnars": round(sum(record["amount"] for record in spend_records if record["asset_symbol"] == "GNARS"), 8),
        "fungible_transfer_count": len(spend_records),
        "nft_transfer_count": len(nft_records),
        "routed_proposal_count": len(proposals_with_routes),
        "routed_proposal_share_pct": percent(len(proposals_with_routes), len(archive["records"])),
        "top10_recipient_concentration_usdc_pct": percent(top10_usdc, sum(payout_values_usdc)),
        "top10_recipient_concentration_eth_pct": percent(top10_eth, sum(payout_values_eth)),
        "proposals_30d": len(recent_proposals_30d),
        "successful_proposals_30d": sum(1 for record in recent_proposals_30d if is_successful_proposal(record)),
        "payout_routes_30d": len(recent_spend_30d),
        "deliveries_30d": len(recent_deliveries_30d),
        "active_recipients_30d": len({record["recipient_address"] for record in recent_spend_30d}),
        "days_since_last_proposal": max(0, (as_of_dt.date() - max(proposal_event_days).date()).days) if proposal_event_days else None,
        "days_since_last_payout": max(0, (as_of_dt.date() - max(payout_event_days).date()).days) if payout_event_days else None,
        "days_since_last_delivery": max(0, (as_of_dt.date() - max(delivery_event_days).date()).days) if delivery_event_days else None,
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


def build_activity_timeseries(
    archive: dict[str, Any],
    spend_records: list[dict[str, Any]],
    project_updates: dict[str, Any],
) -> dict[str, Any]:
    activity: defaultdict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "date": "",
            "proposals_created": 0,
            "proposals_closed": 0,
            "proposals_executed": 0,
            "proposals_defeated": 0,
            "proposals_cancelled": 0,
            "proposals_active": 0,
            "payouts_count": 0,
            "payouts_eth": 0.0,
            "payouts_usdc": 0.0,
            "payouts_gnars": 0.0,
            "updates_count": 0,
            "deliveries_count": 0,
        }
    )

    min_date: datetime | None = None
    max_date = parse_datetime(archive["as_of"]) or datetime.now(timezone.utc)

    proposal_spans: list[tuple[datetime, datetime]] = []
    for proposal in archive["records"]:
        created_at = parse_datetime(proposal.get("created_at") or proposal.get("start_at") or proposal_event_at(proposal))
        ended_at = parse_datetime(proposal_event_at(proposal)) or created_at
        if created_at is None or ended_at is None:
            continue
        proposal_spans.append((created_at, ended_at))
        min_date = created_at if min_date is None else min(min_date, created_at)
        max_date = max(max_date, ended_at)

        created_day = created_at.date().isoformat()
        activity[created_day]["date"] = created_day
        activity[created_day]["proposals_created"] += 1

        ended_day = ended_at.date().isoformat()
        activity[ended_day]["date"] = ended_day
        status = str(proposal.get("status") or "").strip().lower()
        if status in {"closed", "executed", "defeated", "cancelled", "canceled", "expired"}:
            activity[ended_day]["proposals_closed"] += 1
        if status == "executed":
            activity[ended_day]["proposals_executed"] += 1
        if status in {"defeated", "failed"}:
            activity[ended_day]["proposals_defeated"] += 1
        if status in {"cancelled", "canceled", "expired"}:
            activity[ended_day]["proposals_cancelled"] += 1

    for record in spend_records:
        event_at = parse_datetime(record.get("proposal_end_at") or record.get("proposal_created_at") or archive["as_of"])
        if event_at is None:
            continue
        min_date = event_at if min_date is None else min(min_date, event_at)
        max_date = max(max_date, event_at)
        day = event_at.date().isoformat()
        activity[day]["date"] = day
        activity[day]["payouts_count"] += 1
        symbol = str(record.get("asset_symbol") or "").upper()
        amount = number_or_zero(record.get("amount"))
        if symbol == "ETH":
            activity[day]["payouts_eth"] += amount
        elif symbol == "USDC":
            activity[day]["payouts_usdc"] += amount
        elif symbol == "GNARS":
            activity[day]["payouts_gnars"] += amount

    for update in project_updates["records"]:
        update_at = parse_datetime(update.get("date"))
        if update_at is None:
            continue
        min_date = update_at if min_date is None else min(min_date, update_at)
        max_date = max(max_date, update_at)
        day = update_at.date().isoformat()
        activity[day]["date"] = day
        activity[day]["updates_count"] += 1
        if str(update.get("status") or "").strip().lower() == "completed" or str(update.get("kind") or "").strip().lower() in {"delivery", "milestone"}:
            activity[day]["deliveries_count"] += 1

    if min_date is None:
        min_date = max_date

    records: list[dict[str, Any]] = []
    cursor = min_date.date()
    last_day = max_date.date()
    while cursor <= last_day:
        day = cursor.isoformat()
        row = activity[day]
        row["date"] = day
        active_count = 0
        for start_at, end_at in proposal_spans:
            if start_at.date() <= cursor <= end_at.date():
                active_count += 1
        row["proposals_active"] = active_count
        records.append(
            {
                "date": day,
                "proposals_created": row["proposals_created"],
                "proposals_closed": row["proposals_closed"],
                "proposals_executed": row["proposals_executed"],
                "proposals_defeated": row["proposals_defeated"],
                "proposals_cancelled": row["proposals_cancelled"],
                "proposals_active": row["proposals_active"],
                "payouts_count": row["payouts_count"],
                "payouts_eth": round(row["payouts_eth"], 8),
                "payouts_usdc": round(row["payouts_usdc"], 8),
                "payouts_gnars": round(row["payouts_gnars"], 8),
                "updates_count": row["updates_count"],
                "deliveries_count": row["deliveries_count"],
            }
        )
        cursor += timedelta(days=1)

    return {
        "dataset": "activity_timeseries",
        "as_of": max_date.isoformat(),
        "version": 1,
        "granularity": "day",
        "records": records,
    }


def build_treasury_flows(
    archive: dict[str, Any],
    spend_records: list[dict[str, Any]],
) -> dict[str, Any]:
    proposals_by_id = {record["archive_id"]: record for record in archive["records"]}
    routes: list[dict[str, Any]] = []

    for record in spend_records:
        proposal = proposals_by_id.get(record["archive_id"], {})
        event_at = parse_datetime(record.get("proposal_end_at") or record.get("proposal_created_at") or archive["as_of"])
        routes.append(
            {
                "route_id": record["ledger_id"],
                "event_at": event_at.isoformat() if event_at else archive["as_of"],
                "archive_id": record["archive_id"],
                "proposal_key": record["proposal_key"],
                "proposal_number": record["proposal_number"],
                "proposal_title": record["title"],
                "proposal_status": record["status"],
                "proposal_chain": record["chain"],
                "project_id": record["project_id"],
                "project_name": record["project_name"],
                "proposer_address": record["proposer"],
                "recipient_address": record["recipient_address"],
                "recipient_display_name": record["recipient_display_name"],
                "asset_symbol": record["asset_symbol"],
                "amount": round(number_or_zero(record["amount"]), 8),
                "asset_kind": record["asset_kind"],
                "token_contract": record["token_contract"],
                "proposal_href": proposal.get("links", {}).get("canonical_url") or record["canonical_url"],
            }
        )

    routes.sort(key=lambda record: (str(record["event_at"]), str(record["route_id"])), reverse=True)
    as_of = latest_day(*(route["event_at"] for route in routes), archive["as_of"]) or str(archive["as_of"])
    window_specs = build_window_specs(as_of)

    windows: list[dict[str, Any]] = []
    for spec in window_specs:
        selected = [route for route in routes if in_window(route["event_at"], spec["since"])]
        recipient_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        project_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for route in selected:
            recipient_groups[route["recipient_address"]].append(route)
            if route.get("project_id"):
                project_groups[str(route["project_id"])].append(route)

        recipient_rows = [
            {
                "address": address,
                "display_name": rows[0]["recipient_display_name"],
                "totals": asset_totals(rows),
            }
            for address, rows in recipient_groups.items()
        ]
        project_rows = [
            {
                "project_id": project_id,
                "project_name": rows[0]["project_name"],
                "totals": asset_totals(rows),
            }
            for project_id, rows in project_groups.items()
        ]

        windows.append(
            {
                "window_id": spec["window_id"],
                "label": spec["label"],
                "since": spec["since"].isoformat() if spec["since"] is not None else None,
                "route_count": len(selected),
                "proposal_count": len({route["archive_id"] for route in selected}),
                "recipient_count": len(recipient_rows),
                "project_count": len(project_rows),
                "totals_by_asset": asset_totals(selected),
                "top_recipients": sorted(
                    recipient_rows,
                    key=lambda row: (-primary_asset_amount(row["totals"]), str(row["display_name"]).lower()),
                )[:8],
                "top_projects": sorted(
                    project_rows,
                    key=lambda row: (-primary_asset_amount(row["totals"]), str(row["project_name"]).lower()),
                )[:8],
            }
        )

    proposal_routes: list[dict[str, Any]] = []
    for proposal in archive["records"]:
        related = [route for route in routes if route["archive_id"] == proposal["archive_id"]]
        recipient_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for route in related:
            recipient_groups[route["recipient_address"]].append(route)
        proposal_routes.append(
            {
                "archive_id": proposal["archive_id"],
                "proposal_number": proposal["proposal_number"],
                "proposal_title": proposal["title"],
                "proposal_status": proposal["status"],
                "proposal_chain": proposal["chain"],
                "project_id": related[0]["project_id"] if related else None,
                "project_name": related[0]["project_name"] if related else None,
                "totals_by_asset": asset_totals(related),
                "route_count": len(related),
                "recipients": [
                    {
                        "address": address,
                        "display_name": rows[0]["recipient_display_name"],
                        "totals_by_asset": asset_totals(rows),
                    }
                    for address, rows in sorted(recipient_groups.items(), key=lambda item: item[0])
                ],
            }
        )

    proposal_routes.sort(
        key=lambda record: (
            -(record["proposal_number"] if record["proposal_number"] is not None else -1),
            str(record["archive_id"]),
        )
    )

    return {
        "dataset": "treasury_flows",
        "as_of": as_of,
        "version": 1,
        "routes": routes,
        "windows": windows,
        "proposal_routes": proposal_routes,
    }


def build_community_signals(
    archive: dict[str, Any],
    people: dict[str, Any],
    project_rollups: dict[str, Any],
    timeline_events: dict[str, Any],
    treasury_flows: dict[str, Any],
) -> dict[str, Any]:
    people_by_address = {record["address"]: record for record in people["records"]}
    proposals_by_id = {record["archive_id"]: record for record in archive["records"]}
    projects_by_id = {record["project_id"]: record for record in project_rollups["records"]}
    routes = treasury_flows["routes"]
    as_of = treasury_flows["as_of"]

    def proposal_rows_for_window(since: datetime | None) -> list[dict[str, Any]]:
        return [
            proposal
            for proposal in archive["records"]
            if in_window(proposal_event_at(proposal), since)
        ]

    def update_rows_for_window(since: datetime | None) -> list[dict[str, Any]]:
        return [
            event
            for event in timeline_events["records"]
            if event.get("kind") != "proposal" and in_window(event.get("date"), since)
        ]

    windows: list[dict[str, Any]] = []
    for spec in build_window_specs(as_of):
        selected_routes = [route for route in routes if in_window(route["event_at"], spec["since"])]
        selected_proposals = proposal_rows_for_window(spec["since"])
        selected_updates = update_rows_for_window(spec["since"])

        recipient_scores: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
        project_scores: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
        proposal_scores: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
        activity_scores: defaultdict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "address": "",
                "display_name": "",
                "received_routes": [],
                "authored_count": 0,
                "delivery_count": 0,
            }
        )

        for route in selected_routes:
            recipient_scores[route["recipient_address"]].append(route)
            proposal_scores[route["archive_id"]].append(route)
            if route.get("project_id"):
                project_scores[str(route["project_id"])].append(route)

            address = route["recipient_address"]
            person = people_by_address.get(address, {})
            row = activity_scores[address]
            row["address"] = address
            row["display_name"] = person.get("display_name") or route["recipient_display_name"]
            row["received_routes"].append(route)

        for proposal in selected_proposals:
            proposer = normalize_address(proposal.get("proposer"))
            if not proposer:
                continue
            person = people_by_address.get(proposer, {})
            row = activity_scores[proposer]
            row["address"] = proposer
            row["display_name"] = person.get("display_name") or proposal.get("proposer_label") or short_address(proposer)
            row["authored_count"] += 1

        for event in selected_updates:
            for address in unique_addresses(event.get("people_addresses") or []):
                person = people_by_address.get(address, {})
                row = activity_scores[address]
                row["address"] = address
                row["display_name"] = person.get("display_name") or short_address(address)
                row["delivery_count"] += 1

        top_recipients = sorted(
            [
                {
                    "address": address,
                    "display_name": rows[0]["recipient_display_name"],
                    "totals_by_asset": asset_totals(rows),
                }
                for address, rows in recipient_scores.items()
            ],
            key=lambda row: (-primary_asset_amount(row["totals_by_asset"]), str(row["display_name"]).lower()),
        )[:8]

        top_projects = sorted(
            [
                {
                    "project_id": project_id,
                    "project_name": (projects_by_id.get(project_id) or {}).get("name") or rows[0]["project_name"] or project_id,
                    "status": (projects_by_id.get(project_id) or {}).get("status") or "unknown",
                    "totals_by_asset": asset_totals(rows),
                }
                for project_id, rows in project_scores.items()
            ],
            key=lambda row: (-primary_asset_amount(row["totals_by_asset"]), str(row["project_name"]).lower()),
        )[:8]

        top_proposals = sorted(
            [
                {
                    "archive_id": archive_id,
                    "proposal_number": (proposals_by_id.get(archive_id) or {}).get("proposal_number"),
                    "title": (proposals_by_id.get(archive_id) or {}).get("title") or archive_id,
                    "status": (proposals_by_id.get(archive_id) or {}).get("status") or "unknown",
                    "totals_by_asset": asset_totals(rows),
                }
                for archive_id, rows in proposal_scores.items()
            ],
            key=lambda row: (-primary_asset_amount(row["totals_by_asset"]), str(row["title"]).lower()),
        )[:8]

        top_people = sorted(
            [
                {
                    "address": row["address"],
                    "display_name": row["display_name"],
                    "received_totals": asset_totals(row["received_routes"]),
                    "authored_count": row["authored_count"],
                    "delivery_count": row["delivery_count"],
                    "score": round(
                        primary_asset_amount(asset_totals(row["received_routes"])) + row["authored_count"] * 2 + row["delivery_count"] * 1.5,
                        4,
                    ),
                    "tribes": (people_by_address.get(row["address"]) or {}).get("tags") or [],
                }
                for row in activity_scores.values()
                if row["address"]
            ],
            key=lambda row: (-number_or_zero(row["score"]), str(row["display_name"]).lower()),
        )[:10]

        unique_voters = {
            normalize_address(vote.get("voter"))
            for proposal in selected_proposals
            for vote in (proposal.get("votes") or [])
            if normalize_address(vote.get("voter"))
        }
        vote_counts = [float(len(proposal.get("votes") or [])) for proposal in selected_proposals]
        successful_count = sum(1 for proposal in selected_proposals if is_successful_proposal(proposal))

        windows.append(
            {
                "window_id": spec["window_id"],
                "label": spec["label"],
                "since": spec["since"].isoformat() if spec["since"] is not None else None,
                "metrics": {
                    "active_proposals_now": sum(1 for proposal in archive["records"] if str(proposal.get("status") or "").lower() == "active"),
                    "proposal_count": len(selected_proposals),
                    "successful_proposal_count": successful_count,
                    "payout_count": len(selected_routes),
                    "delivery_count": len(selected_updates),
                    "recipient_count": len(recipient_scores),
                    "project_count": len(project_scores),
                    "unique_voters_count": len(unique_voters),
                    "avg_votes_per_proposal": round(mean(vote_counts), 2),
                    "median_votes_per_proposal": round(median(vote_counts), 2),
                    "proposal_success_rate_pct": percent(successful_count, len(selected_proposals)),
                    "payouts_per_proposal": round(len(selected_routes) / len(selected_proposals), 3) if selected_proposals else 0.0,
                    "deliveries_per_proposal": round(len(selected_updates) / len(selected_proposals), 3) if selected_proposals else 0.0,
                    "payouts_by_asset": asset_totals(selected_routes),
                },
                "top_recipients": top_recipients,
                "top_projects": top_projects,
                "top_proposals": top_proposals,
                "top_people": top_people,
            }
        )

    leading_window = next((window for window in windows if window["window_id"] == "30d"), windows[0] if windows else None)
    leading_asset = (leading_window or {}).get("metrics", {}).get("payouts_by_asset", [])
    leading_asset_label = leading_asset[0]["symbol"] if leading_asset else "capital"
    leading_recipient = ((leading_window or {}).get("top_recipients") or [{}])[0]
    leading_project = ((leading_window or {}).get("top_projects") or [{}])[0]

    field_notes = [
        {
            "note_id": "field-note-capital",
            "window_id": leading_window["window_id"] if leading_window else "30d",
            "kind": "treasury",
            "title": "Capital flows concentrate around visible operators.",
            "summary": (
                f"In the latest active window, routed value is dominated by {leading_asset_label} flows, "
                f"with {leading_recipient.get('display_name') or 'core contributors'} appearing as the top recipient cluster."
            ),
        },
        {
            "note_id": "field-note-delivery",
            "window_id": leading_window["window_id"] if leading_window else "30d",
            "kind": "delivery",
            "title": "Workstreams are legible when treasury and proof sit together.",
            "summary": (
                f"{leading_project.get('project_name') or 'Current workstreams'} surfaces as a leading delivery node when treasury routes, proposals, and public updates are read as one chain of evidence."
            ),
        },
        {
            "note_id": "field-note-governance",
            "window_id": "all",
            "kind": "governance",
            "title": "Governance acts as editorial infrastructure.",
            "summary": "Proposal history is most useful when it is read alongside recipients, workstreams, and public proof, rather than as an isolated voting log.",
        },
    ]

    return {
        "dataset": "community_signals",
        "as_of": as_of,
        "version": 1,
        "windows": windows,
        "field_notes": field_notes,
    }


def build_network_graph(
    archive: dict[str, Any],
    people: dict[str, Any],
    project_rollups: dict[str, Any],
    timeline_events: dict[str, Any],
    treasury_flows: dict[str, Any],
) -> dict[str, Any]:
    proposals_by_id = {record["archive_id"]: record for record in archive["records"]}
    people_by_address = {record["address"]: record for record in people["records"]}
    project_by_id = {record["project_id"]: record for record in project_rollups["records"]}
    routes = treasury_flows["routes"]

    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[str, dict[str, Any]] = {}

    def upsert_node(node_id: str, payload: dict[str, Any]) -> None:
        existing = nodes.get(node_id)
        if existing is None:
            nodes[node_id] = {"node_id": node_id, **payload}
            return
        merged = {**existing, **payload}
        nodes[node_id] = merged

    def add_edge(
        source: str,
        target: str,
        kind: str,
        *,
        weight: float = 1.0,
        count: int = 1,
        asset_symbol: str | None = None,
        href: str | None = None,
    ) -> None:
        edge_id = f"{kind}:{source}:{target}:{asset_symbol or 'all'}"
        if edge_id not in edges:
            edges[edge_id] = {
                "edge_id": edge_id,
                "source": source,
                "target": target,
                "kind": kind,
                "weight": 0.0,
                "count": 0,
                "asset_symbol": asset_symbol,
                "href": href,
            }
        edges[edge_id]["weight"] = round(number_or_zero(edges[edge_id]["weight"]) + weight, 8)
        edges[edge_id]["count"] = int(edges[edge_id]["count"]) + count

    treasury_node_id = "treasury:gnars"
    upsert_node(
        treasury_node_id,
        {
            "kind": "treasury",
            "label": "Gnars Treasury",
            "href": "/treasury/",
            "status": "active",
            "tags": ["treasury"],
            "size": 48.0,
            "metrics": {
                "route_count": len(routes),
                "proposal_count": len({route["archive_id"] for route in routes}),
            },
        },
    )

    for person in people["records"]:
        total_received = person["receipts"]["eth_received"] + person["receipts"]["usdc_received"] + person["receipts"]["gnars_received"]
        size = 14 + math.log1p(total_received + person["governance"]["active_votes"] + person["governance"]["proposals_authored_count"] * 4) * 10
        upsert_node(
            f"person:{person['address']}",
            {
                "kind": "person",
                "label": person["display_name"],
                "href": f"/community/{person['slug']}/",
                "status": person["status"],
                "tags": person["tags"],
                "address": person["address"],
                "size": round(size, 2),
                "metrics": {
                    "eth_received": person["receipts"]["eth_received"],
                    "usdc_received": person["receipts"]["usdc_received"],
                    "gnars_received": person["receipts"]["gnars_received"],
                    "active_votes": person["governance"]["active_votes"],
                    "proposals_authored": person["governance"]["proposals_authored_count"],
                },
            },
        )

    for proposal in archive["records"]:
        routed_total = sum(
            number_or_zero(route["amount"])
            for route in routes
            if route["archive_id"] == proposal["archive_id"]
        )
        size = 16 + math.log1p(routed_total + number_or_zero(proposal.get("scores_total")) / 100) * 9
        upsert_node(
            f"proposal:{proposal['archive_id']}",
            {
                "kind": "proposal",
                "label": proposal["title"],
                "href": f"/proposals/{proposal['archive_id']}/",
                "status": proposal["status"],
                "chain": proposal["chain"],
                "proposal_number": proposal["proposal_number"],
                "tags": [proposal["platform"], proposal["chain"]],
                "size": round(size, 2),
                "metrics": {
                    "scores_total": proposal["scores_total"],
                    "vote_count": len(proposal.get("votes") or []),
                    "routed_total": round(routed_total, 8),
                    "successful": is_successful_proposal(proposal),
                },
            },
        )

    for project in project_rollups["records"]:
        total_spent = project["spent"]["eth"] + project["spent"]["usdc"] + project["spent"]["gnars"]
        size = 18 + math.log1p(total_spent + project["updates_count"] * 2 + len(project["proposal_summaries"])) * 10
        upsert_node(
            f"project:{project['project_id']}",
            {
                "kind": "project",
                "label": project["name"],
                "href": f"/projects/{project['project_id']}/",
                "status": project["status"],
                "tags": [project["category"]],
                "size": round(size, 2),
                "metrics": {
                    "spent_eth": project["spent"]["eth"],
                    "spent_usdc": project["spent"]["usdc"],
                    "spent_gnars": project["spent"]["gnars"],
                    "updates_count": project["updates_count"],
                },
            },
        )

    for proposal in archive["records"]:
        proposal_id = f"proposal:{proposal['archive_id']}"
        proposer = normalize_address(proposal.get("proposer"))
        if proposer and proposer in people_by_address:
            person_id = f"person:{proposer}"
            add_edge(person_id, proposal_id, "authored", href=f"/proposals/{proposal['archive_id']}/")
            if is_successful_proposal(proposal):
                add_edge(person_id, proposal_id, "managed", weight=2.0, href=f"/proposals/{proposal['archive_id']}/")

        vote_counter: Counter[str] = Counter(
            normalize_address(vote.get("voter"))
            for vote in (proposal.get("votes") or [])
            if normalize_address(vote.get("voter"))
        )
        for voter, count in vote_counter.items():
            if voter in people_by_address:
                add_edge(f"person:{voter}", proposal_id, "voted", weight=float(count), count=count, href=f"/proposals/{proposal['archive_id']}/")

    for route in routes:
        proposal_id = f"proposal:{route['archive_id']}"
        add_edge(
            treasury_node_id,
            proposal_id,
            "funded",
            weight=number_or_zero(route["amount"]),
            asset_symbol=route["asset_symbol"],
            href=f"/proposals/{route['archive_id']}/",
        )
        if route.get("project_id") and route["project_id"] in project_by_id:
            add_edge(
                proposal_id,
                f"project:{route['project_id']}",
                "funded",
                weight=number_or_zero(route["amount"]),
                asset_symbol=route["asset_symbol"],
                href=f"/projects/{route['project_id']}/",
            )
        if route["recipient_address"] in people_by_address:
            add_edge(
                proposal_id,
                f"person:{route['recipient_address']}",
                "funded",
                weight=number_or_zero(route["amount"]),
                asset_symbol=route["asset_symbol"],
                href=f"/community/{people_by_address[route['recipient_address']]['slug']}/",
            )

    for project in project_rollups["records"]:
        project_id = f"project:{project['project_id']}"
        for address in unique_addresses(project.get("owner_addresses") or []):
            if address in people_by_address:
                add_edge(f"person:{address}", project_id, "owned", href=f"/projects/{project['project_id']}/")

    for event in timeline_events["records"]:
        project_id = event.get("project_id")
        if not project_id or project_id not in project_by_id:
            continue
        for address in unique_addresses(event.get("people_addresses") or []):
            if address not in people_by_address:
                continue
            kind = "delivered" if str(event.get("status") or "").lower() == "completed" else "referenced"
            add_edge(
                f"person:{address}",
                f"project:{project_id}",
                kind,
                href=f"/projects/{project_id}/",
            )

    node_list = sorted(nodes.values(), key=lambda record: (record["kind"], str(record["label"]).lower(), record["node_id"]))
    edge_list = sorted(edges.values(), key=lambda record: (record["kind"], record["source"], record["target"], str(record.get("asset_symbol") or "")))

    top_people = sorted(
        [record for record in node_list if record["kind"] == "person"],
        key=lambda record: (-number_or_zero(record["size"]), str(record["label"]).lower()),
    )[:18]
    top_projects = sorted(
        [record for record in node_list if record["kind"] == "project"],
        key=lambda record: (-number_or_zero(record["size"]), str(record["label"]).lower()),
    )[:10]
    top_proposals = sorted(
        [record for record in node_list if record["kind"] == "proposal" and (record.get("status") == "active" or number_or_zero(record["metrics"].get("routed_total")) > 0)],
        key=lambda record: (-number_or_zero(record["size"]), str(record["label"]).lower()),
    )[:12]

    homepage_node_ids = {treasury_node_id, *(record["node_id"] for record in top_people), *(record["node_id"] for record in top_projects), *(record["node_id"] for record in top_proposals)}
    homepage_edge_ids = [
        record["edge_id"]
        for record in edge_list
        if record["source"] in homepage_node_ids and record["target"] in homepage_node_ids
    ]

    return {
        "dataset": "network_graph",
        "as_of": treasury_flows["as_of"],
        "version": 1,
        "nodes": node_list,
        "edges": edge_list,
        "views": {
            "homepage": {
                "node_ids": sorted(homepage_node_ids),
                "edge_ids": homepage_edge_ids,
            },
        },
    }


def main() -> int:
    archive = load_json("proposals_archive")
    treasury = load_json("treasury")
    projects = load_json("projects")
    members_seed = load_json("members")
    people_overrides = load_json("people_overrides")
    project_updates = load_json("project_updates")
    proposal_tags = load_json("proposal_tags")
    members_snapshot = latest_members_snapshot()
    analytics_as_of = latest_value(
        archive.get("as_of"),
        treasury.get("as_of"),
        projects.get("as_of"),
        members_seed.get("as_of"),
        project_updates.get("as_of"),
    )

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
    ens_profiles = resolve_verified_ens_profiles(
        addresses=[
            *[record["address"] for record in seed_people["records"]],
            *[record["recipient_address"] for record in spend_records],
            *[record["recipient_address"] for record in nft_records],
        ],
        analytics_as_of=analytics_as_of,
        previous_cache=build_previous_ens_cache(),
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
        ens_profiles=ens_profiles,
    )
    people_by_address = {record["address"]: record for record in people["records"]}
    for record in spend_records:
        record["recipient_display_name"] = people_by_address.get(record["recipient_address"], {}).get("display_name") or short_address(record["recipient_address"])
    for record in nft_records:
        record["recipient_display_name"] = people_by_address.get(record["recipient_address"], {}).get("display_name") or short_address(record["recipient_address"])
    for record in archive["records"]:
        proposer = normalize_address(record.get("proposer"))
        if proposer:
            record["proposer_label"] = (
                people_by_address.get(proposer, {}).get("display_name")
                or record.get("proposer_label")
                or short_address(proposer)
            )

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
        project_updates=project_updates,
    )
    timeline_events = build_timeline_events(
        archive=archive,
        project_updates=project_updates,
        project_rollups=project_rollups,
        project_lookup=project_lookup,
    )
    activity_timeseries = build_activity_timeseries(
        archive=archive,
        spend_records=spend_records,
        project_updates=project_updates,
    )
    treasury_flows = build_treasury_flows(
        archive=archive,
        spend_records=spend_records,
    )
    community_signals = build_community_signals(
        archive=archive,
        people=people,
        project_rollups=project_rollups,
        timeline_events=timeline_events,
        treasury_flows=treasury_flows,
    )
    network_graph = build_network_graph(
        archive=archive,
        people=people,
        project_rollups=project_rollups,
        timeline_events=timeline_events,
        treasury_flows=treasury_flows,
    )
    proposals_enriched = build_proposals_enriched(
        archive=archive,
        project_rollups=project_rollups,
        spend_records=spend_records,
        timeline_events=timeline_events,
        proposal_tags=proposal_tags,
        analytics_as_of=analytics_as_of,
    )
    media_proof = build_media_proof(
        project_updates=project_updates,
        archive=archive,
        project_rollups=project_rollups,
        analytics_as_of=analytics_as_of,
    )
    proposals_enriched = hydrate_proposals_with_proof(proposals_enriched, media_proof)
    project_rollups = expand_project_rollups(
        project_rollups=project_rollups,
        project_updates=project_updates,
        media_proof=media_proof,
        analytics_as_of=analytics_as_of,
    )
    people = expand_people(
        people=people,
        archive=archive,
        spend_records=spend_records,
        project_updates=project_updates,
        media_proof=media_proof,
        network_graph=network_graph,
        proposals_enriched=proposals_enriched,
        analytics_as_of=analytics_as_of,
    )
    feed_stream = build_feed_stream(
        proposals_enriched=proposals_enriched,
        spend_records=spend_records,
        project_updates=project_updates,
        media_proof=media_proof,
        people=people,
        project_rollups=project_rollups,
        analytics_as_of=analytics_as_of,
    )
    insights = build_insights(
        treasury=treasury,
        treasury_flows=treasury_flows,
        community_signals=community_signals,
        proposals_enriched=proposals_enriched,
        people=people,
        project_rollups=project_rollups,
        analytics_as_of=analytics_as_of,
    )
    filter_facets = build_filter_facets(
        feed_stream=feed_stream,
        proposals_enriched=proposals_enriched,
        people=people,
        project_rollups=project_rollups,
        treasury_flows=treasury_flows,
        timeline_events=timeline_events,
        analytics_as_of=analytics_as_of,
    )
    treasury_snapshots = build_treasury_snapshots(treasury=treasury, analytics_as_of=analytics_as_of)

    for payload in (
        people,
        project_rollups,
        dao_metrics,
        timeline_events,
        activity_timeseries,
        treasury_flows,
        community_signals,
        network_graph,
    ):
        payload["analytics_as_of"] = analytics_as_of
        payload["as_of"] = analytics_as_of

    write_json("people", people)
    write_json(
        "spend_ledger",
        {
            "dataset": "spend_ledger",
            "analytics_as_of": analytics_as_of,
            "as_of": analytics_as_of,
            "version": 1,
            "records": spend_records,
        },
    )
    write_json("project_rollups", project_rollups)
    write_json("dao_metrics", dao_metrics)
    write_json("timeline_events", timeline_events)
    write_json("activity_timeseries", activity_timeseries)
    write_json("treasury_flows", treasury_flows)
    write_json("community_signals", community_signals)
    write_json("network_graph", network_graph)
    write_json("proposals_enriched", proposals_enriched)
    write_json("media_proof", media_proof)
    write_json("feed_stream", feed_stream)
    write_json("insights", insights)
    write_json("filter_facets", filter_facets)
    write_json("treasury_snapshots", treasury_snapshots)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

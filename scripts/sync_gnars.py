from __future__ import annotations

import argparse
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GRAPH_HEADERS = {
        "User-Agent": "gnars-data-sync/1.0",
        "Accept": "application/json",
        "Content-Type": "application/json",
}

NETWORK_PRIORITY = ["base", "ethereum", "polygon"]
AUCTION_QUERY = """
query GnarsAuctions($first: Int!, $skip: Int!) {
    auctions(first: $first, skip: $skip, orderBy: id, orderDirection: desc) {
        id
        amount
        amountWei
        bidder
        bidderAddress
        tokenId
        token_id
        settled
        timestamp
        blockTimestamp
        txHash
        transactionHash
    }
}
"""


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "raw"
CONFIG_PATH = ROOT / "config" / "source_catalog.json"
CONTRACTS_PATH = ROOT / "data" / "contracts.json"


def load_sources() -> list[dict]:
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload["sources"]


def load_contracts() -> list[dict[str, Any]]:
    with CONTRACTS_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload.get("records", [])


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def fetch_url(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "gnars-data-sync/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
        return response.read()


def fetch_json_url(url: str) -> Any:
    request = urllib.request.Request(url, headers=GRAPH_HEADERS)
    with urllib.request.urlopen(request, timeout=45) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def post_graphql(url: str, query: str, variables: dict[str, Any]) -> dict[str, Any]:
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request = urllib.request.Request(url, data=payload, headers=GRAPH_HEADERS, method="POST")
    with urllib.request.urlopen(request, timeout=45) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def extension_for(source_format: str) -> str:
    if source_format == "json":
        return "json"
    if source_format == "html":
        return "html"
    return "txt"


def sync_source(source: dict, stamp: str) -> Path:
    bucket_dir = RAW_DIR / source["bucket"]
    bucket_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{stamp}-{slugify(source['source_id'])}.{extension_for(source['format'])}"
    path = bucket_dir / filename
    path.write_bytes(fetch_url(source["url"]))
    return path


def auction_subgraph_url(network: str) -> str | None:
    # Preferred naming matches .env.example. Keep legacy key support for compatibility.
    preferred_key = f"GNARS_AUCTION_SUBGRAPH_{network.upper()}_URL"
    legacy_key = f"GNARS_AUCTIONS_{network.upper()}_SUBGRAPH_URL"
    value = os.getenv(preferred_key, "").strip() or os.getenv(legacy_key, "").strip()
    return value or None


def select_auction_contract(contracts: list[dict[str, Any]], network: str) -> dict[str, Any] | None:
    matches = [
        record
        for record in contracts
        if str(record.get("ecosystem") or "").strip().lower() == "gnars"
        and str(record.get("kind") or "").strip().lower() == "auction_house"
        and str(record.get("network") or "").strip().lower() == network
    ]
    if not matches:
        return None
    preferred = [
        record
        for record in matches
        if str(record.get("status") or "").strip().lower() == "active"
    ]
    return preferred[0] if preferred else matches[0]


def auction_networks_from_contracts(contracts: list[dict[str, Any]]) -> list[str]:
    discovered: set[str] = set()
    for record in contracts:
        if str(record.get("ecosystem") or "").strip().lower() != "gnars":
            continue
        if str(record.get("kind") or "").strip().lower() != "auction_house":
            continue
        network = str(record.get("network") or "").strip().lower()
        if network:
            discovered.add(network)
    ordered = [network for network in NETWORK_PRIORITY if network in discovered]
    remaining = sorted(network for network in discovered if network not in NETWORK_PRIORITY)
    return [*ordered, *remaining]


def safe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_auction_record(network: str, contract: str, row: dict[str, Any]) -> dict[str, Any]:
    amount_wei = row.get("amountWei")
    if amount_wei in (None, ""):
        amount_wei = row.get("amount")
    amount_eth = None
    if amount_wei not in (None, ""):
        try:
            amount_eth = int(str(amount_wei)) / 10**18
        except ValueError:
            amount_eth = safe_float(amount_wei)

    auction_id = row.get("id") or row.get("auctionId") or row.get("tokenId") or row.get("token_id")
    bidder = row.get("bidder") or row.get("bidderAddress")
    timestamp = row.get("timestamp") or row.get("blockTimestamp")
    tx_hash = row.get("transactionHash") or row.get("txHash")
    token_id = row.get("tokenId") if row.get("tokenId") not in (None, "") else row.get("token_id")

    return {
        "network": network,
        "contract": contract,
        "auction_id": str(auction_id) if auction_id not in (None, "") else None,
        "token_id": str(token_id) if token_id not in (None, "") else None,
        "bidder": str(bidder).lower() if bidder not in (None, "") else None,
        "amount_wei": str(amount_wei) if amount_wei not in (None, "") else None,
        "amount_eth": round(amount_eth, 8) if amount_eth is not None else None,
        "settled": bool(row.get("settled")) if row.get("settled") is not None else None,
        "timestamp": str(timestamp) if timestamp not in (None, "") else None,
        "tx_hash": str(tx_hash) if tx_hash not in (None, "") else None,
    }


def sync_auctions_for_network(network: str, contracts: list[dict[str, Any]], stamp: str) -> tuple[Path, dict[str, Any]]:
    output_path = RAW_DIR / f"auctions_{network}.json"
    contract_record = select_auction_contract(contracts, network)
    contract_address = str(contract_record.get("address") or "").lower() if contract_record else None
    source_url = auction_subgraph_url(network)

    warnings: list[str] = []
    records: list[dict[str, Any]] = []
    status = "ok"
    page_size = 250

    if not contract_address:
        status = "skipped"
        warnings.append(f"Missing auction_house contract for network '{network}' in data/contracts.json")
    elif not source_url:
        status = "skipped"
        warnings.append(
            (
                f"Missing subgraph URL for {network}. Set "
                f"GNARS_AUCTION_SUBGRAPH_{network.upper()}_URL "
                f"(or legacy GNARS_AUCTIONS_{network.upper()}_SUBGRAPH_URL) to enable auction sync."
            )
        )
    else:
        skip = 0
        seen_ids: set[str] = set()
        while True:
            body = post_graphql(source_url, AUCTION_QUERY, {"first": page_size, "skip": skip})
            errors = body.get("errors") or []
            if errors:
                status = "error"
                warnings.append(f"GraphQL error on {network}: {errors[0].get('message', 'unknown error')}")
                break
            payload = body.get("data") or {}
            rows = payload.get("auctions") or []
            if not rows:
                break
            for row in rows:
                normalized = normalize_auction_record(network, contract_address, row)
                auction_id = normalized.get("auction_id")
                if auction_id:
                    key = f"{network}:{auction_id}"
                    if key in seen_ids:
                        continue
                    seen_ids.add(key)
                records.append(normalized)
            if len(rows) < page_size:
                break
            skip += page_size

    payload = {
        "dataset": "auctions",
        "as_of": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "version": 1,
        "network": network,
        "sync_stamp": stamp,
        "contract": contract_address,
        "source": source_url,
        "status": status,
        "warnings": warnings,
        "records": records,
    }
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output_path, payload


def merge_auction_payloads(payloads: list[dict[str, Any]], stamp: str) -> tuple[Path, dict[str, Any]]:
    merged_records: list[dict[str, Any]] = []
    warnings: list[str] = []
    seen: set[str] = set()

    for payload in payloads:
        warnings.extend(payload.get("warnings") or [])
        for row in payload.get("records") or []:
            network = str(row.get("network") or "unknown")
            auction_id = str(row.get("auction_id") or "")
            key = f"{network}:{auction_id}"
            if auction_id and key in seen:
                continue
            if auction_id:
                seen.add(key)
            merged_records.append(row)

    merged_records.sort(
        key=lambda row: (
            str(row.get("network") or ""),
            str(row.get("auction_id") or ""),
            str(row.get("tx_hash") or ""),
        )
    )

    by_network: dict[str, int] = {}
    for row in merged_records:
        network = str(row.get("network") or "unknown")
        by_network[network] = by_network.get(network, 0) + 1

    merged_payload = {
        "dataset": "auctions_all",
        "as_of": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "version": 1,
        "sync_stamp": stamp,
        "networks": by_network,
        "warnings": warnings,
        "records": merged_records,
    }
    output_path = RAW_DIR / "auctions_all.json"
    output_path.write_text(json.dumps(merged_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output_path, merged_payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture raw Gnars source snapshots.")
    parser.add_argument("--source", help="Only sync a single source_id", default=None)
    args = parser.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sources = [source for source in load_sources() if source.get("enabled", False)]
    if args.source:
        sources = [source for source in sources if source["source_id"] == args.source]

    if not sources:
        print("No enabled sources matched the requested filter.")
        return 1

    contracts = load_contracts()

    for source in sources:
        path = sync_source(source, stamp)
        print(f"[ok] {source['source_id']} -> {path.relative_to(ROOT)}")

    auction_payloads: list[dict[str, Any]] = []
    auction_networks = auction_networks_from_contracts(contracts)
    if not auction_networks:
        print("[warn] No gnars auction_house contracts found in data/contracts.json; skipping auction sync.")
    for network in auction_networks:
        path, payload = sync_auctions_for_network(network, contracts, stamp)
        auction_payloads.append(payload)
        print(
            f"[ok] auctions:{network} -> {path.relative_to(ROOT)} "
            f"(status={payload['status']}, rows={len(payload.get('records') or [])})"
        )
        for warning in payload.get("warnings") or []:
            print(f"[warn] {warning}")

    if auction_payloads:
        merged_path, merged_payload = merge_auction_payloads(auction_payloads, stamp)
        print(
            f"[ok] auctions:merged -> {merged_path.relative_to(ROOT)} "
            f"(rows={len(merged_payload.get('records') or [])})"
        )
        for warning in merged_payload.get("warnings") or []:
            print(f"[warn] {warning}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

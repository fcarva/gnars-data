from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = ROOT / "raw" / "nouns.build"
CONTRACTS_PATH = DATA_DIR / "contracts.json"
TREASURY_PATH = DATA_DIR / "treasury.json"
OUTPUT_PATH = DATA_DIR / "nouns_activity_events.json"

DAO_SOURCE_URL = "https://nouns.build/dao/base/0x880Fb3Cf5c6Cc2d7DFC13a993E839a9411200C17/7008"
BASE_CHAIN_ID = 8453
BASE_RPC_URL = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")

# Topic name mapping is intentionally conservative; unknown signatures stay as generic logs.
GOVERNOR_TOPIC_NAMES: dict[str, str] = {}

# Transfer(address,address,uint256)
TRANSFER_TOPIC0 = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55aeb3ef"

KNOWN_DECIMALS = {
    "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913": 6,  # USDC
    "0x4200000000000000000000000000000000000006": 18,  # WETH
    "0x0cf0c3b75d522290d7d12c74d7f1f0cc47ccb23b": 18,  # GNARS
    "0xba5b9b2d2d06a9021eb3190ea5fb0e02160839a4": 18,  # SENDIT
}

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "gnars-data/nouns-activity-sync",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def isoformat_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def is_stale(path: Path, max_age_hours: int = 6) -> bool:
    if not path.exists():
        return True
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    return age > timedelta(hours=max_age_hours)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def rpc_call(method: str, params: list[Any]) -> Any:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode("utf-8")
    last_error: Exception | None = None
    for attempt in range(5):
        try:
            request = urllib.request.Request(BASE_RPC_URL, data=body, headers=HEADERS, method="POST")
            with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310
                payload = json.loads(response.read().decode("utf-8"))
            if "error" in payload:
                raise RuntimeError(f"RPC error ({method}): {payload['error']}")
            return payload.get("result")
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt == 4:
                break
            time.sleep(1.5 * (attempt + 1))

    raise RuntimeError(f"RPC request failed after retries ({method}): {last_error}")


def hex_to_int(value: str | None) -> int:
    if not value:
        return 0
    return int(value, 16)


def int_to_hex(value: int) -> str:
    return hex(value)


def topic_address(value: str) -> str:
    return "0x" + value.lower().replace("0x", "").rjust(64, "0")


def topic_to_address(value: str | None) -> str | None:
    if not value:
        return None
    compact = value.lower().replace("0x", "")
    if len(compact) < 40:
        return None
    return "0x" + compact[-40:]


def chunk_data_words(data_hex: str | None) -> list[str]:
    if not data_hex or data_hex == "0x":
        return []
    compact = data_hex[2:] if data_hex.startswith("0x") else data_hex
    if len(compact) % 64 != 0:
        return []
    return [compact[idx : idx + 64] for idx in range(0, len(compact), 64)]


def word_to_int(word: str | None) -> int | None:
    if not word:
        return None
    try:
        return int(word, 16)
    except ValueError:
        return None


def word_to_address(word: str | None) -> str | None:
    if not word or len(word) < 40:
        return None
    return "0x" + word[-40:].lower()


def get_latest_block() -> int:
    return hex_to_int(rpc_call("eth_blockNumber", []))


def contract_exists_at(address: str, block_number: int) -> bool:
    code = rpc_call("eth_getCode", [address, int_to_hex(block_number)])
    return isinstance(code, str) and code != "0x"


def first_deployed_block(address: str, latest_block: int) -> int:
    if not contract_exists_at(address, latest_block):
        raise RuntimeError(f"Contract not deployed on current chain: {address}")

    low = 0
    high = latest_block
    while low < high:
        mid = (low + high) // 2
        if contract_exists_at(address, mid):
            high = mid
        else:
            low = mid + 1
    return low


def fetch_logs_chunked(
    *,
    address: str,
    from_block: int,
    to_block: int,
    topics: list[Any] | None = None,
    chunk_size: int = 20000,
) -> list[dict[str, Any]]:
    logs: list[dict[str, Any]] = []
    cursor = from_block
    current_chunk = chunk_size
    while cursor <= to_block:
        end_block = min(cursor + current_chunk - 1, to_block)
        params: dict[str, Any] = {
            "address": address,
            "fromBlock": int_to_hex(cursor),
            "toBlock": int_to_hex(end_block),
        }
        if topics is not None:
            params["topics"] = topics

        try:
            rows = rpc_call("eth_getLogs", [params]) or []
            logs.extend(rows)
            cursor = end_block + 1
            if current_chunk < chunk_size:
                current_chunk = min(chunk_size, current_chunk * 2)
        except RuntimeError as exc:
            message = str(exc).lower()
            if ("413" in message or "payload too large" in message) and current_chunk > 1000:
                current_chunk = max(1000, current_chunk // 2)
                continue
            raise
    return logs


def block_timestamps(logs: list[dict[str, Any]]) -> dict[int, str]:
    unique_blocks = sorted({hex_to_int(row.get("blockNumber")) for row in logs if row.get("blockNumber")})
    out: dict[int, str] = {}
    for block_number in unique_blocks:
        block = rpc_call("eth_getBlockByNumber", [int_to_hex(block_number), False])
        ts = hex_to_int((block or {}).get("timestamp"))
        out[block_number] = isoformat_utc(datetime.fromtimestamp(ts, tz=timezone.utc))
    return out


def load_contract_map() -> dict[str, dict[str, Any]]:
    payload = load_json(CONTRACTS_PATH)
    records = payload.get("records", [])
    targets: dict[str, dict[str, Any]] = {}
    for record in records:
        if str(record.get("ecosystem") or "").lower() != "gnars":
            continue
        if str(record.get("network") or "").lower() != "base":
            continue
        kind = str(record.get("kind") or "").lower()
        if kind in {"governor", "auction_house", "treasury"}:
            targets[kind] = record
    return targets


def treasury_token_registry() -> tuple[list[str], dict[str, str], dict[str, int]]:
    payload = load_json(TREASURY_PATH)
    tokens: set[str] = set()
    symbols: dict[str, str] = {}
    decimals: dict[str, int] = {}

    for record in payload.get("records", []):
        token_address = str(record.get("token_address") or "").lower()
        if not token_address.startswith("0x"):
            continue
        tokens.add(token_address)
        symbol = str(record.get("symbol") or "").strip().upper()
        if symbol:
            symbols[token_address] = symbol
        decimals[token_address] = KNOWN_DECIMALS.get(token_address, 18)

    return sorted(tokens), symbols, decimals


def normalize_governor_logs(
    logs: list[dict[str, Any]],
    ts_map: dict[int, str],
    governor_address: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in logs:
        topics = row.get("topics") or []
        topic0 = str(topics[0]).lower() if topics else None
        block_number = hex_to_int(row.get("blockNumber"))
        proposal_id = None
        if len(topics) > 1:
            try:
                proposal_id = int(str(topics[1]), 16)
            except ValueError:
                proposal_id = None

        records.append(
            {
                "event_id": f"governor:{row.get('transactionHash')}:{hex_to_int(row.get('logIndex'))}",
                "trail": "governor",
                "event_kind": GOVERNOR_TOPIC_NAMES.get(topic0 or "", "governor_log"),
                "network": "base",
                "chain_id": BASE_CHAIN_ID,
                "dao_source_url": DAO_SOURCE_URL,
                "contract_address": governor_address,
                "topic0": topic0,
                "proposal_id": proposal_id,
                "tx_hash": row.get("transactionHash"),
                "tx_index": hex_to_int(row.get("transactionIndex")),
                "log_index": hex_to_int(row.get("logIndex")),
                "block_number": block_number,
                "block_timestamp": ts_map.get(block_number),
                "removed": bool(row.get("removed")),
                "topics": topics,
                "data": row.get("data"),
            }
        )
    return records


def normalize_auction_logs(
    logs: list[dict[str, Any]],
    ts_map: dict[int, str],
    auction_address: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in logs:
        topics = row.get("topics") or []
        topic0 = str(topics[0]).lower() if topics else None
        token_id = None
        if len(topics) > 1:
            try:
                token_id = int(str(topics[1]), 16)
            except ValueError:
                token_id = None

        data_words = chunk_data_words(str(row.get("data") or ""))
        event_kind = "auction_log"
        bidder = None
        winner = None
        amount_wei = None
        extended = None

        # Nouns-like auction house contracts typically encode bids with 3 words and settles with 2 words.
        if len(data_words) == 3:
            event_kind = "auction_bid"
            bidder = word_to_address(data_words[0])
            amount_wei = word_to_int(data_words[1])
            extended_raw = word_to_int(data_words[2])
            extended = bool(extended_raw) if extended_raw is not None else None
        elif len(data_words) == 2:
            event_kind = "auction_settled"
            winner = word_to_address(data_words[0])
            amount_wei = word_to_int(data_words[1])

        block_number = hex_to_int(row.get("blockNumber"))
        records.append(
            {
                "event_id": f"auction:{row.get('transactionHash')}:{hex_to_int(row.get('logIndex'))}",
                "trail": "auction",
                "event_kind": event_kind,
                "network": "base",
                "chain_id": BASE_CHAIN_ID,
                "dao_source_url": DAO_SOURCE_URL,
                "contract_address": auction_address,
                "topic0": topic0,
                "token_id": token_id,
                "bidder": bidder,
                "winner": winner,
                "amount_wei": str(amount_wei) if amount_wei is not None else None,
                "extended": extended,
                "tx_hash": row.get("transactionHash"),
                "tx_index": hex_to_int(row.get("transactionIndex")),
                "log_index": hex_to_int(row.get("logIndex")),
                "block_number": block_number,
                "block_timestamp": ts_map.get(block_number),
                "removed": bool(row.get("removed")),
                "topics": topics,
                "data": row.get("data"),
            }
        )
    return records


def normalize_transfer_logs(
    logs: list[dict[str, Any]],
    ts_map: dict[int, str],
    treasury_address: str,
    symbols: dict[str, str],
    decimals: dict[str, int],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    treasury = treasury_address.lower()

    for row in logs:
        topics = row.get("topics") or []
        if len(topics) < 3:
            continue

        token = str(row.get("address") or "").lower()
        from_address = topic_to_address(topics[1])
        to_address = topic_to_address(topics[2])
        if not from_address or not to_address:
            continue

        value_raw = hex_to_int(row.get("data"))
        token_decimals = decimals.get(token, 18)
        value_normalized = value_raw / (10 ** token_decimals)

        direction = "self"
        if from_address.lower() == treasury and to_address.lower() != treasury:
            direction = "outbound"
        elif to_address.lower() == treasury and from_address.lower() != treasury:
            direction = "inbound"

        block_number = hex_to_int(row.get("blockNumber"))
        records.append(
            {
                "event_id": f"treasury_transfer:{row.get('transactionHash')}:{hex_to_int(row.get('logIndex'))}",
                "trail": "treasury_transfer",
                "event_kind": "erc20_transfer",
                "network": "base",
                "chain_id": BASE_CHAIN_ID,
                "dao_source_url": DAO_SOURCE_URL,
                "contract_address": token,
                "topic0": str(topics[0]).lower(),
                "treasury_address": treasury,
                "direction": direction,
                "from_address": from_address,
                "to_address": to_address,
                "token_address": token,
                "token_symbol": symbols.get(token),
                "token_decimals": token_decimals,
                "value_raw": str(value_raw),
                "value_normalized": round(value_normalized, 12),
                "tx_hash": row.get("transactionHash"),
                "tx_index": hex_to_int(row.get("transactionIndex")),
                "log_index": hex_to_int(row.get("logIndex")),
                "block_number": block_number,
                "block_timestamp": ts_map.get(block_number),
                "removed": bool(row.get("removed")),
                "topics": topics,
                "data": row.get("data"),
            }
        )

    return records


def dedupe_by_event_id(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        by_id[record["event_id"]] = record
    return sorted(by_id.values(), key=lambda row: (row["block_number"], row["log_index"], row["event_id"]))


def main() -> int:
    force = "--force" in sys.argv

    if not force and not is_stale(OUTPUT_PATH, max_age_hours=6):
        print("[skip] nouns activity events fresh")
        return 0

    contracts = load_contract_map()
    governor = str((contracts.get("governor") or {}).get("address") or "").lower()
    auction = str((contracts.get("auction_house") or {}).get("address") or "").lower()
    treasury = str((contracts.get("treasury") or {}).get("address") or "").lower()

    if not governor or not auction or not treasury:
        raise RuntimeError("Missing required Base contracts (governor/auction_house/treasury) in data/contracts.json")

    latest_block = get_latest_block()
    print(f"[nouns] latest base block: {latest_block}")

    governor_from = first_deployed_block(governor, latest_block)
    auction_from = first_deployed_block(auction, latest_block)
    treasury_from = first_deployed_block(treasury, latest_block)

    print(f"[nouns] governor from block: {governor_from}")
    print(f"[nouns] auction from block: {auction_from}")
    print(f"[nouns] treasury from block: {treasury_from}")

    governor_logs = fetch_logs_chunked(address=governor, from_block=governor_from, to_block=latest_block)
    auction_logs = fetch_logs_chunked(address=auction, from_block=auction_from, to_block=latest_block)

    token_addresses, symbols, decimals = treasury_token_registry()
    treasury_logs: list[dict[str, Any]] = []
    treasury_topic = topic_address(treasury)
    for token_address in token_addresses:
        outbound = fetch_logs_chunked(
            address=token_address,
            from_block=treasury_from,
            to_block=latest_block,
            topics=[TRANSFER_TOPIC0, treasury_topic],
        )
        inbound = fetch_logs_chunked(
            address=token_address,
            from_block=treasury_from,
            to_block=latest_block,
            topics=[TRANSFER_TOPIC0, None, treasury_topic],
        )
        treasury_logs.extend(outbound)
        treasury_logs.extend(inbound)

    all_logs = [*governor_logs, *auction_logs, *treasury_logs]
    ts_map = block_timestamps(all_logs)

    governor_records = normalize_governor_logs(governor_logs, ts_map, governor)
    auction_records = normalize_auction_logs(auction_logs, ts_map, auction)
    treasury_records = normalize_transfer_logs(treasury_logs, ts_map, treasury, symbols, decimals)
    records = dedupe_by_event_id([*governor_records, *auction_records, *treasury_records])

    fetched_at = isoformat_utc(utc_now())
    write_json(
        RAW_DIR / "governor_logs.json",
        {
            "fetched_at": fetched_at,
            "network": "base",
            "chain_id": BASE_CHAIN_ID,
            "contract_address": governor,
            "from_block": governor_from,
            "to_block": latest_block,
            "records": governor_logs,
        },
    )
    write_json(
        RAW_DIR / "auction_logs.json",
        {
            "fetched_at": fetched_at,
            "network": "base",
            "chain_id": BASE_CHAIN_ID,
            "contract_address": auction,
            "from_block": auction_from,
            "to_block": latest_block,
            "records": auction_logs,
        },
    )
    write_json(
        RAW_DIR / "treasury_transfer_logs.json",
        {
            "fetched_at": fetched_at,
            "network": "base",
            "chain_id": BASE_CHAIN_ID,
            "treasury_address": treasury,
            "token_addresses": token_addresses,
            "from_block": treasury_from,
            "to_block": latest_block,
            "records": treasury_logs,
        },
    )

    write_json(
        OUTPUT_PATH,
        {
            "dataset": "nouns_activity_events",
            "as_of": fetched_at,
            "version": 1,
            "network": "base",
            "chain_id": BASE_CHAIN_ID,
            "dao_source_url": DAO_SOURCE_URL,
            "records": records,
        },
    )

    print(f"[nouns] governor logs: {len(governor_logs)}")
    print(f"[nouns] auction logs: {len(auction_logs)}")
    print(f"[nouns] treasury transfer logs: {len(treasury_logs)}")
    print(f"[nouns] normalized events: {len(records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

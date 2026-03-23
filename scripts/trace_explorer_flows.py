from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "raw" / "explorer"

ETHERSCAN_V2_BASE = "https://api.etherscan.io/v2/api"
BASESCAN_V1_BASE = "https://api.basescan.org/api"
CHAIN_ID_ETHEREUM = 1
CHAIN_ID_BASE = 8453

GNARS_EXECUTOR_ETH = "0xa1b74d2280966a89ac7e0f3a8bc5f0867c776d98"
GNARS_TREASURY_BASE = "0x72ad986ebac0246d2b3c565ab2a1ce3a14ce6f88"
BASE_USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"


def _load_env_file_value(name: str) -> str:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return ""
    for line in env_path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        if key.strip() == name:
            return value.strip().strip('"').strip("'")
    return ""


def _api_key(name: str) -> str:
    raw = os.environ.get(name, "").strip() or _load_env_file_value(name)
    # Some terminals append artifacts like "|54"; keep only the token-like prefix.
    raw = raw.split("|")[0].strip()
    return "".join(ch for ch in raw if ch.isalnum() or ch in {"_", "-"})


def _fetch_v1(api_base: str, api_key: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    merged = {
        "apikey": api_key,
        **params,
    }
    resp = requests.get(api_base, params=merged, timeout=45)
    resp.raise_for_status()
    payload = resp.json()
    if not isinstance(payload, dict):
        return []
    status = str(payload.get("status", "")).strip()
    result = payload.get("result", [])
    if status == "0" and isinstance(result, str):
        if "No transactions" in result or "No records" in result:
            return []
        raise RuntimeError(result)
    return result if isinstance(result, list) else []


def _fetch(chain_id: int, api_key: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    merged = {
        "chainid": str(chain_id),
        "apikey": api_key,
        **params,
    }
    max_attempts = 4
    for attempt in range(1, max_attempts + 1):
        resp = requests.get(ETHERSCAN_V2_BASE, params=merged, timeout=45)
        resp.raise_for_status()
        payload = resp.json()
        if not isinstance(payload, dict):
            return []

        status = str(payload.get("status", "")).strip()
        result = payload.get("result", [])
        message = str(result) if isinstance(result, str) else ""

        if status == "0" and isinstance(result, str):
            # Etherscan returns status=0 with a text message when there are no txs.
            if "No transactions" in message or "No records" in message:
                return []
            # Respect free tier burst limits with backoff retry.
            if "rate limit" in message.lower() and attempt < max_attempts:
                time.sleep(0.6 * attempt)
                continue
            raise RuntimeError(message)

        parsed = payload.get("result", [])
        if isinstance(parsed, list):
            # Keep requests comfortably under free tier threshold.
            time.sleep(0.22)
            return parsed
        return []

    return []


def fetch_eth_executor_transactions(address: str, api_key: str) -> dict[str, Any]:
    txs = _fetch(
        CHAIN_ID_ETHEREUM,
        api_key,
        {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "sort": "asc",
        },
    )
    internals = _fetch(
        CHAIN_ID_ETHEREUM,
        api_key,
        {
            "module": "account",
            "action": "txlistinternal",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "sort": "asc",
        },
    )
    erc20 = _fetch(
        CHAIN_ID_ETHEREUM,
        api_key,
        {
            "module": "account",
            "action": "tokentx",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "sort": "asc",
        },
    )
    return {"txlist": txs, "internal": internals, "tokentx": erc20}


def fetch_base_treasury_transactions(address: str, api_key: str) -> dict[str, Any]:
    txs = _fetch(
        CHAIN_ID_BASE,
        api_key,
        {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "sort": "asc",
        },
    )
    internals = _fetch(
        CHAIN_ID_BASE,
        api_key,
        {
            "module": "account",
            "action": "txlistinternal",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "sort": "asc",
        },
    )
    usdc = _fetch(
        CHAIN_ID_BASE,
        api_key,
        {
            "module": "account",
            "action": "tokentx",
            "address": address,
            "contractaddress": BASE_USDC,
            "startblock": 0,
            "endblock": 99999999,
            "sort": "asc",
        },
    )
    return {"txlist": txs, "internal": internals, "tokentx_usdc": usdc}


def fetch_base_treasury_transactions_basescan_v1(address: str, api_key: str) -> dict[str, Any]:
    txs = _fetch_v1(
        BASESCAN_V1_BASE,
        api_key,
        {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "sort": "asc",
        },
    )
    internals = _fetch_v1(
        BASESCAN_V1_BASE,
        api_key,
        {
            "module": "account",
            "action": "txlistinternal",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "sort": "asc",
        },
    )
    usdc = _fetch_v1(
        BASESCAN_V1_BASE,
        api_key,
        {
            "module": "account",
            "action": "tokentx",
            "address": address,
            "contractaddress": BASE_USDC,
            "startblock": 0,
            "endblock": 99999999,
            "sort": "asc",
        },
    )
    return {"txlist": txs, "internal": internals, "tokentx_usdc": usdc}


def main() -> int:
    parser = argparse.ArgumentParser(description="Trace gnars treasury/executor flows via Etherscan API V2")
    parser.add_argument("--eth-address", default=GNARS_EXECUTOR_ETH)
    parser.add_argument("--base-address", default=GNARS_TREASURY_BASE)
    args = parser.parse_args()

    etherscan_key = _api_key("ETHERSCAN_API_KEY")
    basescan_key = _api_key("BASESCAN_API_KEY") or etherscan_key

    if not etherscan_key:
        print("[warn] Missing ETHERSCAN_API_KEY in env/.env")
        print("[hint] add ETHERSCAN_API_KEY to run explorer tracing")
        return 0

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()

    payload: dict[str, Any] = {
        "generated_at": now,
        "eth_address": args.eth_address.lower(),
        "base_address": args.base_address.lower(),
        "sources": {},
    }

    try:
        payload["sources"]["etherscan_v2_ethereum"] = fetch_eth_executor_transactions(args.eth_address, etherscan_key)
        print("[ok] fetched etherscan v2 ethereum transactions")
    except Exception as exc:  # noqa: BLE001
        payload["sources"]["etherscan_v2_ethereum_error"] = str(exc)
        print(f"[warn] etherscan v2 ethereum failed: {exc}")

    try:
        payload["sources"]["etherscan_v2_base"] = fetch_base_treasury_transactions(args.base_address, etherscan_key)
        print("[ok] fetched etherscan v2 base transactions")
    except Exception as exc:  # noqa: BLE001
        payload["sources"]["etherscan_v2_base_error"] = str(exc)
        print(f"[warn] etherscan v2 base failed: {exc}")
        if basescan_key:
            try:
                payload["sources"]["basescan_v1_base"] = fetch_base_treasury_transactions_basescan_v1(
                    args.base_address,
                    basescan_key,
                )
                print("[ok] fetched basescan v1 base transactions (fallback)")
            except Exception as inner_exc:  # noqa: BLE001
                payload["sources"]["basescan_v1_base_error"] = str(inner_exc)
                print(f"[warn] basescan v1 fallback failed: {inner_exc}")

    out_path = RAW_DIR / "gnars_treasury_trace.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[ok] wrote {out_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

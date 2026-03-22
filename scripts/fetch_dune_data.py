from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = ROOT / "raw"


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


DUNE_API_KEY = (os.environ.get("DUNE_API_KEY", "").strip() or _load_env_file_value("DUNE_API_KEY"))
BASE_URL = "https://api.dune.com/api/v1"
HEADERS = {"X-Dune-API-Key": DUNE_API_KEY}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _read_query_ids_from_sources() -> dict[str, int | None]:
    source_path = DATA_DIR / "sources.json"
    if not source_path.exists():
        return {}
    payload = load_json(source_path)
    dune = payload.get("dune_queries") or {}
    out: dict[str, int | None] = {}
    for key, value in dune.items():
        try:
            out[key] = int(value) if value not in (None, "") else None
        except (TypeError, ValueError):
            out[key] = None
    return out


def _read_query_ids_from_env() -> dict[str, int | None]:
    env_keys = {
        "gnars_auctions_base": "DUNE_QUERY_GNARS_AUCTIONS_BASE",
        "gnars_auctions_ethereum": "DUNE_QUERY_GNARS_AUCTIONS_ETHEREUM",
        "treasury_outflows_base": "DUNE_QUERY_GNARS_TREASURY_OUTFLOWS_BASE",
        "eth_price_history": "DUNE_QUERY_ETH_PRICE_HISTORY",
    }
    out: dict[str, int | None] = {}
    for key, env_name in env_keys.items():
        raw = os.environ.get(env_name, "").strip()
        try:
            out[key] = int(raw) if raw else None
        except ValueError:
            out[key] = None
    return out


def _query_ids() -> dict[str, int | None]:
    merged = _read_query_ids_from_sources()
    merged.update({k: v for k, v in _read_query_ids_from_env().items() if v})
    return {
        "gnars_auctions_base": merged.get("gnars_auctions_base"),
        "gnars_auctions_ethereum": merged.get("gnars_auctions_ethereum"),
        "treasury_outflows_base": merged.get("treasury_outflows_base"),
        "eth_price_history": merged.get("eth_price_history"),
    }


def get_latest_result(query_id: int) -> list[dict[str, Any]]:
    url = f"{BASE_URL}/query/{query_id}/results"
    resp = requests.get(url, headers=HEADERS, timeout=45)
    resp.raise_for_status()
    data = resp.json()
    return data.get("result", {}).get("rows", [])


def execute_query(query_id: int, wait: bool = True) -> list[dict[str, Any]]:
    trigger = requests.post(f"{BASE_URL}/query/{query_id}/execute", headers=HEADERS, json={}, timeout=45)
    trigger.raise_for_status()
    execution_id = trigger.json().get("execution_id")
    if not execution_id or not wait:
        return []

    status_url = f"{BASE_URL}/execution/{execution_id}/status"
    for _ in range(60):
        status = requests.get(status_url, headers=HEADERS, timeout=45)
        status.raise_for_status()
        state = status.json().get("state", "")
        if state == "QUERY_STATE_COMPLETED":
            break
        if state in {"QUERY_STATE_FAILED", "QUERY_STATE_CANCELLED"}:
            raise RuntimeError(f"Query {query_id} failed with state {state}")
        time.sleep(5)

    results = requests.get(f"{BASE_URL}/execution/{execution_id}/results", headers=HEADERS, timeout=45)
    results.raise_for_status()
    return results.json().get("result", {}).get("rows", [])


def fetch_eth_price_on_date(date_str: str) -> float | None:
    try:
        from datetime import datetime

        dt = datetime.fromisoformat(date_str[:10])
        cg_date = dt.strftime("%d-%m-%Y")
        url = f"https://api.coingecko.com/api/v3/coins/ethereum/history?date={cg_date}"
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        price = data.get("market_data", {}).get("current_price", {}).get("usd")
        return float(price) if price else None
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] CoinGecko fallback failed for {date_str}: {exc}")
        return None


def build_eth_price_cache(dates: list[str]) -> dict[str, float]:
    cache_path = RAW_DIR / "eth_prices.json"
    cache: dict[str, float] = {}
    if cache_path.exists():
        payload = load_json(cache_path)
        if isinstance(payload, dict):
            for key, value in payload.items():
                try:
                    cache[str(key)] = float(value)
                except (TypeError, ValueError):
                    continue

    missing = [date for date in dates if date[:10] not in cache]
    for date in missing:
        price = fetch_eth_price_on_date(date)
        if price:
            cache[date[:10]] = price
            print(f"  ETH price {date[:10]}: ${price:,.2f}")
        time.sleep(1.2)

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    save_json(cache_path, cache)
    return cache


def _record_date(row: dict[str, Any]) -> str:
    return (
        str(
            row.get("proposal_executed_at")
            or row.get("valuation_reference_at")
            or row.get("proposal_end_at")
            or row.get("proposal_created_at")
            or row.get("date")
            or ""
        )
        .strip()
    )


def _asset_symbol(row: dict[str, Any]) -> str:
    return str(row.get("asset") or row.get("asset_symbol") or "").strip().upper()


def _amount(row: dict[str, Any]) -> float:
    try:
        return float(row.get("amount") or 0)
    except (TypeError, ValueError):
        return 0.0


def enrich_spend_ledger_with_prices() -> int:
    spend_path = DATA_DIR / "spend_ledger.json"
    payload = load_json(spend_path)
    is_wrapped = isinstance(payload, dict)
    records = payload.get("records", []) if is_wrapped else payload
    if not isinstance(records, list):
        print("[warn] spend_ledger records malformed; skipping")
        return 0

    dates = sorted({_record_date(row)[:10] for row in records if _asset_symbol(row) == "ETH" and _record_date(row)})
    if dates:
        print(f"Fetching ETH prices for {len(dates)} dates...")
    cache = build_eth_price_cache(dates)
    print(f"Price cache size: {len(cache)} dates")

    enriched = 0
    for row in records:
        asset = _asset_symbol(row)
        if asset == "USDC":
            row["usd_value_at_execution"] = _amount(row)
            continue
        if asset != "ETH":
            continue
        date = _record_date(row)
        if not date:
            continue
        price = cache.get(date[:10])
        if price is None:
            continue
        row["eth_price_usd"] = price
        row["usd_value_at_execution"] = round(_amount(row) * price, 2)
        enriched += 1

    if is_wrapped:
        payload["records"] = records
        save_json(spend_path, payload)
    else:
        save_json(spend_path, records)

    print(f"Enriched {enriched} ETH records with historical USD values")
    return enriched


def _save_dune_result(name: str, rows: list[dict[str, Any]]) -> None:
    out = RAW_DIR / "dune"
    out.mkdir(parents=True, exist_ok=True)
    save_json(
        out / f"{name}.json",
        {
            "dataset": name,
            "as_of": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "version": 1,
            "rows": rows,
        },
    )
    print(f"[ok] wrote raw/dune/{name}.json ({len(rows)} rows)")


def fetch_dune_results() -> None:
    if not DUNE_API_KEY:
        print("[skip] DUNE_API_KEY not set")
        return

    ids = _query_ids()
    for name, query_id in ids.items():
        if not query_id:
            print(f"[skip] {name}: query id not configured")
            continue
        try:
            rows = get_latest_result(query_id)
            _save_dune_result(name, rows)
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] {name}: latest result failed ({exc}); trying execute_query")
            try:
                rows = execute_query(query_id, wait=True)
                _save_dune_result(name, rows)
            except Exception as inner_exc:  # noqa: BLE001
                print(f"[warn] {name}: execute_query failed ({inner_exc})")


def run() -> None:
    fetch_dune_results()
    enrich_spend_ledger_with_prices()


if __name__ == "__main__":
    run()

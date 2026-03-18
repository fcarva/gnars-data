from __future__ import annotations

import argparse
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "raw"
DATA_DIR = ROOT / "data"
TREASURY_PATH = DATA_DIR / "treasury.json"

GNARS_DASHBOARD_URL = "https://www.gnars.com"
GNARS_TREASURY_URL = "https://www.gnars.com/treasury"
USER_AGENT = "gnars-data-sync/1.0 (+https://github.com/fcarva/gnars-data)"
DEFAULT_WALLET = {
    "label": "Gnars DAO Treasury",
    "chain": "base",
    "address": "0x72ad986ebac0246d2b3c565ab2a1ce3a14ce6f88",
}


class SyncError(RuntimeError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def isoformat_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        return response.read()


def fetch_and_store(url: str, *, stamp: str, slug: str) -> str:
    payload = fetch_bytes(url)
    path = RAW_DIR / "gnars.com" / f"{stamp}-{slug}.html"
    write_bytes(path, payload)
    print(f"[ok] fetched {url} -> {path.relative_to(ROOT)}")
    return payload.decode("utf-8")


def extract_balanced(text: str, start: int, open_char: str, close_char: str) -> str:
    depth = 0
    in_string = False
    escape = False

    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue

        if char == open_char:
            depth += 1
        elif char == close_char:
            depth -= 1
            if depth == 0:
                return text[start : index + 1]

    raise SyncError(f"Could not find balanced {open_char}{close_char} block")


def safe_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def parse_money(value: str) -> float:
    cleaned = value.replace("$", "").replace(",", "").strip()
    return float(cleaned)


def parse_compact_number(value: str) -> float:
    cleaned = value.replace(",", "").replace("$", "").strip().upper()
    if cleaned.endswith("K"):
        return float(cleaned[:-1]) * 1_000
    if cleaned.endswith("M"):
        return float(cleaned[:-1]) * 1_000_000
    if cleaned.endswith("B"):
        return float(cleaned[:-1]) * 1_000_000_000
    return float(cleaned)


def extract_homepage_label_usd(dashboard_html: str) -> float | None:
    patterns = [
        r'href="/treasury".{0,1500}?\$([0-9]+(?:\.[0-9]+)?[kmb])',
        r'>Treasury<.{0,1500}?\$([0-9]+(?:\.[0-9]+)?[kmb])',
    ]
    for pattern in patterns:
        match = re.search(pattern, dashboard_html, flags=re.I | re.S)
        if match:
            return parse_compact_number(match.group(1))
    return None


def extract_metric_total_usd(treasury_html: str) -> float:
    patterns = [
        r'"metric":"total","value":([0-9]+(?:\.[0-9]+)?)',
        r'\\"metric\\":\\"total\\",\\"value\\":([0-9]+(?:\.[0-9]+)?)',
    ]
    for pattern in patterns:
        match = re.search(pattern, treasury_html)
        if match:
            return float(match.group(1))
    raise SyncError("Could not parse treasury metric total value")


def extract_display_total_usd(treasury_html: str) -> float | None:
    match = re.search(
        r'<div class="text-2xl font-semibold text-foreground">\$(?:<span[^>]*>)?([0-9][0-9,]*\.[0-9]+)',
        treasury_html,
    )
    if not match:
        return None
    return parse_money(match.group(1))


def extract_token_payload(treasury_html: str) -> list[dict[str, Any]]:
    patterns = [
        r'{"tokens":\[(.*?)\]}',
        r'{\\"tokens\\":\[(.*?)\]\}',
    ]

    for pattern in patterns:
        match = re.search(pattern, treasury_html, flags=re.S)
        if not match:
            continue
        inner = match.group(1)
        payload = '{"tokens":[' + inner + ']}'
        if '\\"' in payload:
            payload = payload.replace('\\"', '"')
        return json.loads(payload)["tokens"]

    raise SyncError("Could not locate token holdings payload")


def build_existing_record_maps(existing_payload: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    by_token_address: dict[str, dict[str, Any]] = {}
    by_symbol: dict[str, dict[str, Any]] = {}
    for record in existing_payload.get("records", []):
        token_address = record.get("token_address")
        if token_address:
            by_token_address[token_address.lower()] = record
        by_symbol[record["symbol"].lower()] = record
    return by_token_address, by_symbol


def build_erc20_records(tokens: list[dict[str, Any]], existing_payload: dict[str, Any]) -> list[dict[str, Any]]:
    by_token_address, by_symbol = build_existing_record_maps(existing_payload)
    records = []
    for token in tokens:
        contract_address = token.get("contractAddress")
        symbol = (token.get("symbol") or token.get("name") or "unknown").strip()
        key = contract_address.lower() if contract_address else symbol.lower()
        existing = by_token_address.get(key) if contract_address else by_symbol.get(symbol.lower())
        existing = existing or by_symbol.get(symbol.lower())
        normalized_symbol = existing["symbol"] if existing else symbol.upper()
        normalized_name = existing["name"] if existing else (token.get("name") or symbol)
        asset_id = existing["asset_id"] if existing else f"base-{safe_slug(normalized_symbol)}"
        notes = existing["notes"] if existing else "Live treasury holdings table snapshot."

        records.append(
            {
                "asset_id": asset_id,
                "asset_type": "erc20",
                "symbol": normalized_symbol,
                "name": normalized_name,
                "token_address": contract_address.lower() if contract_address else None,
                "amount": float(token["balance"]),
                "value_usd": float(token["usdValue"]),
                "source_url": GNARS_TREASURY_URL,
                "notes": notes,
            }
        )
    return records


def extract_zora_records(treasury_html: str, existing_payload: dict[str, Any]) -> list[dict[str, Any]]:
    by_token_address, by_symbol = build_existing_record_maps(existing_payload)
    pattern = re.compile(
        r'<tr[^>]*>.*?<div class="font-medium">([^<]+)</div><div class="text-sm text-muted-foreground">([^<]+)</div>'
        r'.*?<td[^>]*text-right font-mono">([^<]+)</td>'
        r'.*?<td[^>]*text-right font-medium">\$(.*?)</td>'
        r'.*?<a href="https://zora\.co/collect/base:(0x[0-9a-fA-F]+)"',
        flags=re.S,
    )

    records = []
    for match in pattern.finditer(treasury_html):
        display_name = match.group(1).strip()
        symbol_hint = match.group(2).strip()
        amount = parse_compact_number(match.group(3))
        value_usd = parse_money(match.group(4))
        token_address = match.group(5).lower()

        existing = by_token_address.get(token_address) or by_symbol.get(symbol_hint.lower()) or by_symbol.get(display_name.lower())
        asset_id = existing["asset_id"] if existing else f"zora-{safe_slug(symbol_hint)}"
        symbol = existing["symbol"] if existing else symbol_hint.upper()
        name = existing["name"] if existing else display_name
        notes = existing["notes"] if existing else "Zora coin balance listed on the Gnars treasury page."

        records.append(
            {
                "asset_id": asset_id,
                "asset_type": "zora-coin",
                "symbol": symbol,
                "name": name,
                "token_address": token_address,
                "amount": amount,
                "value_usd": value_usd,
                "source_url": f"https://zora.co/collect/base:{token_address}",
                "notes": notes,
            }
        )

    return records


def build_overview(
    dashboard_html: str,
    treasury_html: str,
    existing_payload: dict[str, Any],
) -> dict[str, Any]:
    existing_overview = existing_payload.get("overview", {})
    homepage_label = extract_homepage_label_usd(dashboard_html)
    if homepage_label is None:
        homepage_label = existing_overview.get("homepage_treasury_label_usd")

    metric_total = extract_metric_total_usd(treasury_html)
    display_total = extract_display_total_usd(treasury_html)

    note = (
        f"Homepage treasury label: {homepage_label if homepage_label is not None else 'unavailable'}; "
        f"treasury metric payload: {metric_total:.2f}; "
        f"visible treasury widget: {display_total if display_total is not None else 'unavailable'}. "
        "Use row-level holdings plus the metric payload as the reliable balance layer."
    )
    return {
        "homepage_treasury_label_usd": homepage_label,
        "treasury_page_total_value_usd": metric_total,
        "treasury_page_display_total_usd": display_total,
        "data_quality_note": note,
    }


def build_payload(
    dashboard_html: str,
    treasury_html: str,
    existing_payload: dict[str, Any],
) -> dict[str, Any]:
    erc20_records = build_erc20_records(extract_token_payload(treasury_html), existing_payload)
    zora_records = extract_zora_records(treasury_html, existing_payload)

    payload = {
        "dataset": "treasury",
        "as_of": utc_now().date().isoformat(),
        "version": existing_payload.get("version", 1),
        "wallet": existing_payload.get("wallet", DEFAULT_WALLET),
        "overview": build_overview(dashboard_html, treasury_html, existing_payload),
        "records": sorted(erc20_records + zora_records, key=lambda record: (record["asset_type"], record["asset_id"])),
    }
    return payload


def load_html_or_fetch(path_value: str | None, *, live_url: str, stamp: str, slug: str) -> str:
    if path_value:
        return Path(path_value).read_text(encoding="utf-8")
    return fetch_and_store(live_url, stamp=stamp, slug=slug)


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect and normalize Gnars treasury holdings.")
    parser.add_argument("--dashboard-html", help="Use an existing dashboard HTML file instead of fetching live.")
    parser.add_argument("--treasury-html", help="Use an existing treasury HTML file instead of fetching live.")
    args = parser.parse_args()

    stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    existing_payload = load_json(TREASURY_PATH)
    dashboard_html = load_html_or_fetch(args.dashboard_html, live_url=GNARS_DASHBOARD_URL, stamp=stamp, slug="gnars-dashboard")
    treasury_html = load_html_or_fetch(args.treasury_html, live_url=GNARS_TREASURY_URL, stamp=stamp, slug="gnars-treasury")

    payload = build_payload(dashboard_html, treasury_html, existing_payload)
    write_json(TREASURY_PATH, payload)
    print(f"[ok] wrote {TREASURY_PATH.relative_to(ROOT)} ({len(payload['records'])} assets)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

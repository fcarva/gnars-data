from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ETH_PRICE = 2800.0
ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def _load_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _load_rows(path: Path) -> list[dict[str, Any]]:
    payload = _load_payload(path)
    rows = payload.get("rows")
    return rows if isinstance(rows, list) else []


def _round(value: float | int | None) -> float:
    return round(float(value or 0), 2)


def _load_eth_prices() -> dict[str, float]:
    prices = _load_payload(ROOT / "raw" / "eth_prices.json")
    out: dict[str, float] = {}
    for key, value in prices.items():
        try:
            out[str(key)[:10]] = float(value)
        except (TypeError, ValueError):
            continue
    return out


def _load_bridge_whitelist() -> dict[str, dict[str, str]]:
    payload = _load_payload(ROOT / "config" / "bridge_custody_whitelist.json")
    rows = payload.get("bridge_custody")
    if not isinstance(rows, list):
        return {}

    out: dict[str, dict[str, str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        address = str(row.get("address") or "").strip().lower()
        if not address:
            continue
        out[address] = {
            "label": str(row.get("label") or "bridge-custody"),
            "notes": str(row.get("notes") or ""),
        }
    return out


def _load_internal_contracts() -> dict[str, dict[str, str]]:
    payload = _load_payload(ROOT / "data" / "contracts.json")
    rows = payload.get("records")
    if not isinstance(rows, list):
        return {}

    out: dict[str, dict[str, str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        ecosystem = str(row.get("ecosystem") or "").strip().lower()
        if ecosystem != "gnars":
            continue
        address = str(row.get("address") or "").strip().lower()
        if not address:
            continue
        out[address] = {
            "label": str(row.get("label") or row.get("contract_id") or "gnars-contract"),
            "kind": str(row.get("kind") or "unknown"),
            "network": str(row.get("network") or "unknown"),
        }
    return out


def _build_entry(row: dict[str, Any], eth_prices: dict[str, float]) -> dict[str, Any] | None:
    direction = str(row.get("direction") or "").strip().lower()
    if direction not in {"inflow", "outflow"}:
        return None

    asset = str(row.get("asset") or "").strip().upper()
    if asset not in {"USDC", "ETH"}:
        return None

    try:
        amount = float(row.get("amount") or 0)
    except (TypeError, ValueError):
        amount = 0.0
    if amount <= 0:
        return None

    block_time = str(row.get("block_time") or "").strip()
    date_key = block_time[:10] if block_time else ""

    if asset == "USDC":
        eth_price = None
        usd_value = amount
    else:
        eth_price = float(eth_prices.get(date_key, ETH_PRICE))
        usd_value = amount * eth_price

    return {
        "chain": str(row.get("chain") or "").strip().lower() or "other",
        "block_time": block_time,
        "tx_hash": str(row.get("tx_hash") or "").strip().lower(),
        "direction": direction,
        "asset": asset,
        "amount": amount,
        "eth_price_usd": eth_price,
        "usd_value": usd_value,
        "counterparty": str(row.get("counterparty") or "").strip().lower(),
    }


def _mark_noise(
    entries: list[dict[str, Any]],
    bridge_whitelist: dict[str, dict[str, str]],
    internal_contracts: dict[str, dict[str, str]],
) -> dict[str, dict[str, Any]]:
    by_tx: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        tx_hash = str(entry.get("tx_hash") or "")
        if tx_hash:
            by_tx[tx_hash].append(entry)

    tx_flags: dict[str, dict[str, Any]] = {}
    for tx_hash, tx_entries in by_tx.items():
        inflow_usd = sum(float(e.get("usd_value") or 0) for e in tx_entries if e.get("direction") == "inflow")
        outflow_usd = sum(float(e.get("usd_value") or 0) for e in tx_entries if e.get("direction") == "outflow")
        has_both_dirs = inflow_usd > 0 and outflow_usd > 0
        ratio = 0.0
        if has_both_dirs:
            ratio = abs(inflow_usd - outflow_usd) / max(inflow_usd, outflow_usd)

        counterparties = {str(e.get("counterparty") or "") for e in tx_entries}
        has_bridge_counterparty = any(cp in bridge_whitelist for cp in counterparties)
        has_internal_counterparty = any(cp in internal_contracts for cp in counterparties)

        is_self_transfer = has_both_dirs and ratio <= 0.02
        is_bridge_noise = has_both_dirs and has_bridge_counterparty and ratio <= 0.15
        is_internal_routing = has_both_dirs and has_internal_counterparty and ratio <= 0.15

        reasons = []
        if is_self_transfer:
            reasons.append("self-transfer-mirrored")
        if is_bridge_noise:
            reasons.append("bridge-custody-routing")
        if is_internal_routing:
            reasons.append("internal-contract-routing")

        tx_flags[tx_hash] = {
            "tx_hash": tx_hash,
            "inflow_usd": _round(inflow_usd),
            "outflow_usd": _round(outflow_usd),
            "delta_usd": _round(inflow_usd - outflow_usd),
            "mirror_ratio": round(ratio, 6),
            "counterparties": sorted(counterparties),
            "is_self_transfer": is_self_transfer,
            "is_bridge_noise": is_bridge_noise,
            "is_internal_routing": is_internal_routing,
            "is_noise": bool(reasons),
            "noise_reasons": reasons,
        }

    return tx_flags


def _counterparty_rollup(
    entries: list[dict[str, Any]],
    bridge_whitelist: dict[str, dict[str, str]],
    internal_contracts: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = {}

    for entry in entries:
        cp = str(entry.get("counterparty") or "")
        if not cp:
            cp = "unknown"
        bucket = stats.setdefault(
            cp,
            {
                "counterparty": cp,
                "inflow_usd": 0.0,
                "outflow_usd": 0.0,
                "inflow_count": 0,
                "outflow_count": 0,
                "chains": set(),
            },
        )

        direction = str(entry.get("direction") or "")
        usd_value = float(entry.get("usd_value") or 0)
        if direction == "inflow":
            bucket["inflow_usd"] += usd_value
            bucket["inflow_count"] += 1
        elif direction == "outflow":
            bucket["outflow_usd"] += usd_value
            bucket["outflow_count"] += 1

        bucket["chains"].add(str(entry.get("chain") or "other"))

    rows: list[dict[str, Any]] = []
    for cp, bucket in stats.items():
        inflow_usd = float(bucket["inflow_usd"])
        outflow_usd = float(bucket["outflow_usd"])
        net_inflow_usd = inflow_usd - outflow_usd

        bridge_meta = bridge_whitelist.get(cp)
        internal_meta = internal_contracts.get(cp)

        rows.append(
            {
                "counterparty": cp,
                "inflow_usd": _round(inflow_usd),
                "outflow_usd": _round(outflow_usd),
                "net_inflow_usd": _round(net_inflow_usd),
                "inflow_count": int(bucket["inflow_count"]),
                "outflow_count": int(bucket["outflow_count"]),
                "chains": sorted(bucket["chains"]),
                "is_bridge_custody_whitelisted": bool(bridge_meta),
                "bridge_custody_label": (bridge_meta or {}).get("label"),
                "is_internal_gnars_contract": bool(internal_meta),
                "internal_contract_label": (internal_meta or {}).get("label"),
                "internal_contract_kind": (internal_meta or {}).get("kind"),
            }
        )

    rows.sort(key=lambda item: float(item.get("inflow_usd") or 0), reverse=True)
    return rows


def build_report() -> dict[str, Any]:
    reconcile = _load_payload(REPORTS / "reconciliation.json")
    ledger_rows = _load_rows(ROOT / "raw" / "dune" / "treasury_full_flows_ledger.json")

    eth_prices = _load_eth_prices()
    bridge_whitelist = _load_bridge_whitelist()
    internal_contracts = _load_internal_contracts()

    entries: list[dict[str, Any]] = []
    for row in ledger_rows:
        entry = _build_entry(row, eth_prices)
        if entry:
            entries.append(entry)

    tx_flags = _mark_noise(entries, bridge_whitelist, internal_contracts)
    counterparties = _counterparty_rollup(entries, bridge_whitelist, internal_contracts)

    filtered_entries = []
    flagged_entries = []
    for entry in entries:
        tx_hash = str(entry.get("tx_hash") or "")
        flag = tx_flags.get(tx_hash, {})
        is_noise = bool(flag.get("is_noise"))

        row = {
            "tx_hash": tx_hash,
            "block_time": entry.get("block_time"),
            "chain": entry.get("chain"),
            "direction": entry.get("direction"),
            "asset": entry.get("asset"),
            "amount": round(float(entry.get("amount") or 0), 8),
            "usd_value": _round(entry.get("usd_value")),
            "counterparty": entry.get("counterparty"),
            "is_noise": is_noise,
            "noise_reasons": flag.get("noise_reasons") or [],
        }

        if is_noise:
            flagged_entries.append(row)
        else:
            filtered_entries.append(row)

    def totals(values: list[dict[str, Any]]) -> dict[str, float]:
        inflow = sum(float(v.get("usd_value") or 0) for v in values if v.get("direction") == "inflow")
        outflow = sum(float(v.get("usd_value") or 0) for v in values if v.get("direction") == "outflow")
        return {
            "inflow_usd": _round(inflow),
            "outflow_usd": _round(outflow),
            "net_usd": _round(inflow - outflow),
        }

    raw_totals = totals(
        [
            {
                "direction": e.get("direction"),
                "usd_value": _round(e.get("usd_value"),),
            }
            for e in entries
        ]
    )
    filtered_totals = totals(filtered_entries)

    funding_total = float(reconcile.get("funding_total_usd") or 0)
    actual_balance = float(reconcile.get("actual_balance_usd") or 0)

    expected_raw = funding_total - raw_totals["outflow_usd"]
    expected_filtered = funding_total - filtered_totals["outflow_usd"]

    gap_raw_signed = actual_balance - expected_raw
    gap_filtered_signed = actual_balance - expected_filtered

    initial_adjustment_raw = actual_balance - raw_totals["net_usd"]
    initial_adjustment_filtered = actual_balance - filtered_totals["net_usd"]

    top_whitelist_candidates = [
        row
        for row in counterparties
        if row.get("is_bridge_custody_whitelisted") and float(row.get("inflow_usd") or 0) > 0
    ]
    top_missing_candidates = [
        row
        for row in counterparties
        if float(row.get("net_inflow_usd") or 0) > 0 and not row.get("is_internal_gnars_contract")
    ]

    top_whitelist_candidates.sort(key=lambda item: float(item.get("inflow_usd") or 0), reverse=True)
    top_missing_candidates.sort(key=lambda item: float(item.get("net_inflow_usd") or 0), reverse=True)
    flagged_entries.sort(key=lambda item: float(item.get("usd_value") or 0), reverse=True)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "reconciliation": "reports/reconciliation.json",
            "full_flows_ledger": "raw/dune/treasury_full_flows_ledger.json",
            "eth_prices": "raw/eth_prices.json",
            "bridge_whitelist": "config/bridge_custody_whitelist.json",
            "contracts": "data/contracts.json",
        },
        "inputs": {
            "funding_total_usd": _round(funding_total),
            "actual_balance_usd": _round(actual_balance),
            "ledger_rows": len(ledger_rows),
            "flow_entries_used": len(entries),
        },
        "whitelist_bridge_custody": [
            {
                "address": address,
                "label": meta.get("label"),
                "notes": meta.get("notes"),
            }
            for address, meta in bridge_whitelist.items()
        ],
        "noise_detection": {
            "rules": [
                "self-transfer-mirrored: tx has inflow and outflow with <= 2% USD delta",
                "bridge-custody-routing: tx has both directions, contains bridge/custody whitelist address, and <= 15% USD delta",
                "internal-contract-routing: tx has both directions, contains gnars contract address, and <= 15% USD delta",
            ],
            "tx_total": len(tx_flags),
            "tx_noise": sum(1 for value in tx_flags.values() if value.get("is_noise")),
            "entries_noise": len(flagged_entries),
        },
        "totals_raw_usd": raw_totals,
        "totals_filtered_usd": filtered_totals,
        "gap_recompute": {
            "expected_balance_raw_usd": _round(expected_raw),
            "expected_balance_filtered_usd": _round(expected_filtered),
            "signed_gap_raw_actual_minus_expected_usd": _round(gap_raw_signed),
            "signed_gap_filtered_actual_minus_expected_usd": _round(gap_filtered_signed),
            "abs_gap_raw_usd": _round(abs(gap_raw_signed)),
            "abs_gap_filtered_usd": _round(abs(gap_filtered_signed)),
            "initial_balance_adjustment_raw_usd": _round(initial_adjustment_raw),
            "initial_balance_adjustment_filtered_usd": _round(initial_adjustment_filtered),
        },
        "top_inflow_counterparties": counterparties[:30],
        "top_inflow_missing_candidates": top_missing_candidates[:20],
        "top_whitelist_bridge_custody_counterparties": top_whitelist_candidates[:20],
        "flagged_noise_transactions": sorted(
            [
                flag
                for flag in tx_flags.values()
                if flag.get("is_noise")
            ],
            key=lambda item: max(float(item.get("inflow_usd") or 0), float(item.get("outflow_usd") or 0)),
            reverse=True,
        )[:200],
        "flagged_noise_entries_top": flagged_entries[:200],
    }

    return report


def write_outputs(report: dict[str, Any]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)

    json_path = REPORTS / "inflow_counterparty_filters.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    gap = report.get("gap_recompute") or {}
    noise = report.get("noise_detection") or {}
    top = report.get("top_whitelist_bridge_custody_counterparties") or []

    lines = [
        "# Inflow Counterparty Filters",
        "",
        "## Gap Recompute",
        f"- abs_gap_raw_usd: {float(gap.get('abs_gap_raw_usd') or 0):,.2f}",
        f"- abs_gap_filtered_usd: {float(gap.get('abs_gap_filtered_usd') or 0):,.2f}",
        f"- signed_gap_raw_actual_minus_expected_usd: {float(gap.get('signed_gap_raw_actual_minus_expected_usd') or 0):,.2f}",
        f"- signed_gap_filtered_actual_minus_expected_usd: {float(gap.get('signed_gap_filtered_actual_minus_expected_usd') or 0):,.2f}",
        f"- initial_balance_adjustment_raw_usd: {float(gap.get('initial_balance_adjustment_raw_usd') or 0):,.2f}",
        f"- initial_balance_adjustment_filtered_usd: {float(gap.get('initial_balance_adjustment_filtered_usd') or 0):,.2f}",
        "",
        "## Noise Detection",
        f"- tx_total: {int(noise.get('tx_total') or 0)}",
        f"- tx_noise: {int(noise.get('tx_noise') or 0)}",
        f"- entries_noise: {int(noise.get('entries_noise') or 0)}",
        "",
        "## Top Whitelist Bridge/Custody Counterparties",
    ]

    for row in top[:10]:
        lines.append(
            "- {counterparty} | inflow={inflow:,.2f} | outflow={outflow:,.2f} | net={net:,.2f} | label={label}".format(
                counterparty=str(row.get("counterparty") or "unknown"),
                inflow=float(row.get("inflow_usd") or 0),
                outflow=float(row.get("outflow_usd") or 0),
                net=float(row.get("net_inflow_usd") or 0),
                label=str(row.get("bridge_custody_label") or "n/a"),
            )
        )

    md_path = REPORTS / "inflow_counterparty_filters.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[ok] wrote {json_path.relative_to(ROOT)}")
    print(f"[ok] wrote {md_path.relative_to(ROOT)}")


if __name__ == "__main__":
    write_outputs(build_report())
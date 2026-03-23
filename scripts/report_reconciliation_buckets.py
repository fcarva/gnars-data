from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _round(value: float | int | None) -> float:
    return round(float(value or 0), 2)


def _top(entries: list[dict[str, Any]], direction: str, n: int = 10) -> list[dict[str, Any]]:
    filtered = [e for e in entries if str(e.get("direction") or "").lower() == direction]
    filtered.sort(key=lambda x: float(x.get("usd_value") or 0), reverse=True)
    top = []
    for item in filtered[:n]:
        top.append(
            {
                "block_time": item.get("block_time"),
                "chain": item.get("chain"),
                "asset": item.get("asset"),
                "usd_value": _round(item.get("usd_value")),
                "counterparty": item.get("counterparty"),
                "tx_hash": item.get("tx_hash"),
                "tx_url": item.get("tx_url"),
            }
        )
    return top


def build_report() -> dict[str, Any]:
    rec = _load(REPORTS / "reconciliation.json")
    ledger = _load(REPORTS / "onchain_outflow_ledger.json")

    funding_total_raw = float(rec.get("funding_total_usd") or 0)
    auction_raw = float(rec.get("auction_revenue_usd") or 0)
    external_raw = float(rec.get("external_funding_usd") or 0)
    actual_raw = float(rec.get("actual_balance_usd") or 0)
    expected_funding_model_raw = float(rec.get("expected_balance_usd") or 0)
    gap_funding_model_raw = float(rec.get("gap_usd") or 0)

    onchain_inflow_raw = float(ledger.get("inflow_usd") or 0)
    onchain_outflow_raw = float(ledger.get("outflow_usd") or rec.get("spend_total_usd_onchain") or 0)
    onchain_net_raw = float(ledger.get("net_usd") if ledger.get("net_usd") is not None else (onchain_inflow_raw - onchain_outflow_raw))

    funding_total = _round(funding_total_raw)
    auction = _round(auction_raw)
    external = _round(external_raw)
    actual = _round(actual_raw)
    expected_funding_model = _round(expected_funding_model_raw)
    gap_funding_model = _round(gap_funding_model_raw)
    onchain_inflow = _round(onchain_inflow_raw)
    onchain_outflow = _round(onchain_outflow_raw)
    onchain_net = _round(onchain_net_raw)

    # Bucket decomposition
    inflow_missing_raw = funding_total_raw - onchain_inflow_raw
    initial_balance_adjustment_raw = actual_raw - onchain_net_raw
    inflow_missing_vs_reference = _round(inflow_missing_raw)
    initial_balance_adjustment = _round(initial_balance_adjustment_raw)

    # Signed funding model difference: actual - expected
    signed_gap_raw = actual_raw - expected_funding_model_raw
    signed_gap = _round(signed_gap_raw)
    # Identity check: signed_gap = initial_balance_adjustment - inflow_missing_vs_reference
    identity_rhs_raw = initial_balance_adjustment_raw - inflow_missing_raw
    identity_rhs = _round(identity_rhs_raw)

    entries = ledger.get("entries") if isinstance(ledger.get("entries"), list) else []

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "auction_revenue_usd": auction,
            "external_funding_usd": external,
            "funding_total_usd": funding_total,
            "actual_balance_usd": actual,
            "expected_balance_funding_model_usd": expected_funding_model,
            "gap_funding_model_usd": gap_funding_model,
            "onchain_inflow_usd": onchain_inflow,
            "onchain_outflow_usd": onchain_outflow,
            "onchain_net_usd": onchain_net,
        },
        "bucket_decomposition": {
            "inflow_missing_usd": inflow_missing_vs_reference,
            "outflow_explained_onchain_usd": onchain_outflow,
            "initial_balance_adjustment_usd": initial_balance_adjustment,
            "signed_gap_actual_minus_expected_usd": signed_gap,
            "signed_gap_identity_rhs_usd": identity_rhs,
            "identity_holds": abs(signed_gap_raw - identity_rhs_raw) < 1.0,
        },
        "interpretation": {
            "summary": (
                "Residual gap is decomposed into missing inflow vs reference funding and "
                "an initial-balance adjustment implied by onchain net flows."
            ),
            "notes": [
                "inflow_missing_usd > 0 means reference funding exceeds tracked onchain inflows for treasury addresses.",
                "initial_balance_adjustment_usd > 0 means current treasury balance is above the simple net-flow baseline.",
                "outflow_explained_onchain_usd is fully traceable from transaction-level records.",
            ],
        },
        "top_inflows": _top(entries, "inflow", n=10),
        "top_outflows": _top(entries, "outflow", n=10),
    }
    return report


def write_outputs(report: dict[str, Any]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)

    json_path = REPORTS / "reconciliation_buckets.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    b = report["bucket_decomposition"]
    i = report["inputs"]
    md = []
    md.append("# Reconciliation Buckets")
    md.append("")
    md.append("## Inputs")
    md.append(f"- funding_total_usd: {i['funding_total_usd']:,.2f}")
    md.append(f"- onchain_inflow_usd: {i['onchain_inflow_usd']:,.2f}")
    md.append(f"- onchain_outflow_usd: {i['onchain_outflow_usd']:,.2f}")
    md.append(f"- onchain_net_usd: {i['onchain_net_usd']:,.2f}")
    md.append(f"- expected_balance_funding_model_usd: {i['expected_balance_funding_model_usd']:,.2f}")
    md.append(f"- actual_balance_usd: {i['actual_balance_usd']:,.2f}")
    md.append("")
    md.append("## Buckets")
    md.append(f"- inflow_missing_usd: {b['inflow_missing_usd']:,.2f}")
    md.append(f"- outflow_explained_onchain_usd: {b['outflow_explained_onchain_usd']:,.2f}")
    md.append(f"- initial_balance_adjustment_usd: {b['initial_balance_adjustment_usd']:,.2f}")
    md.append(f"- signed_gap_actual_minus_expected_usd: {b['signed_gap_actual_minus_expected_usd']:,.2f}")
    md.append(f"- signed_gap_identity_rhs_usd: {b['signed_gap_identity_rhs_usd']:,.2f}")
    md.append(f"- identity_holds: {b['identity_holds']}")
    md.append("")
    md.append("## Identity")
    md.append("- actual - expected = initial_balance_adjustment - inflow_missing")

    md_path = REPORTS / "reconciliation_buckets.md"
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"[ok] wrote {json_path.relative_to(ROOT)}")
    print(f"[ok] wrote {md_path.relative_to(ROOT)}")


if __name__ == "__main__":
    report_data = build_report()
    write_outputs(report_data)

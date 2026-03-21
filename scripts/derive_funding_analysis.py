from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"
USER_AGENT = "gnars-data-funding-analysis/1.0 (+https://github.com/fcarva/gnars-data)"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(name: str) -> dict[str, Any]:
    path = DATA_DIR / f"{name}.json"
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(name: str, payload: dict[str, Any]) -> None:
    path = DATA_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[ok] wrote {path.relative_to(ROOT)}")


def fetch_eth_price_usd(date_iso: str) -> tuple[float | None, str | None]:
    dt = datetime.fromisoformat(date_iso)
    date_for_api = dt.strftime("%d-%m-%Y")
    url = f"{COINGECKO_API_BASE}/coins/ethereum/history?date={date_for_api}&localization=false"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as exc:
        return None, f"coingecko fetch failed for {date_iso}: {exc}"

    market_data = payload.get("market_data") or {}
    current_price = market_data.get("current_price") or {}
    value = current_price.get("usd")
    if value is None:
        return None, f"coingecko missing usd price for {date_iso}"
    return float(value), None


def month_bucket(value: str | None) -> str:
    if not value:
        return "unknown"
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        dt = datetime.fromisoformat(value)
        return dt.strftime("%Y-%m")
    except ValueError:
        return "unknown"


def main() -> int:
    funding = load_json("funding_origins")
    spend = load_json("spend_ledger")
    proposals_archive = load_json("proposals_archive")

    proposal_by_archive_id: dict[str, dict[str, Any]] = {
        record["archive_id"]: record for record in proposals_archive.get("records", [])
    }

    warnings: list[str] = []

    approved_funding_usd = 0.0
    potential_funding_usd = 0.0
    funding_sources_enriched: list[dict[str, Any]] = []

    for source in funding.get("records", []):
        amount = float(source.get("requested_amount", {}).get("amount", 0.0))
        currency = str(source.get("requested_amount", {}).get("currency", "")).upper()
        usd_hint = source.get("requested_amount", {}).get("usd_estimate_hint")

        source_dates = [
            item.get("proposed_at")
            for item in source.get("proposal_chain", [])
            if item.get("proposed_at")
        ]
        source_date = min(source_dates) if source_dates else None

        usd_estimate = None
        fx_label = None
        if currency == "USDC":
            usd_estimate = amount
            fx_label = "stablecoin-parity"
        elif currency == "ETH" and source_date:
            eth_price, warning = fetch_eth_price_usd(source_date)
            if warning:
                warnings.append(warning)
            if eth_price is not None:
                usd_estimate = amount * eth_price
                fx_label = f"coingecko:ethereum:{source_date}"
            elif isinstance(usd_hint, (int, float)):
                usd_estimate = float(usd_hint)
                fx_label = "source-usd-hint"

        status = str(source.get("status", ""))
        if status in {"approved", "executed", "received"} and usd_estimate is not None:
            approved_funding_usd += usd_estimate
        if usd_estimate is not None:
            potential_funding_usd += usd_estimate

        funding_sources_enriched.append(
            {
                "funding_source_id": source.get("funding_source_id"),
                "title": source.get("title"),
                "status": status,
                "source_date": source_date,
                "requested_amount": source.get("requested_amount"),
                "usd_estimate_at_source": usd_estimate,
                "usd_estimate_fx": fx_label,
                "proposal_chain": source.get("proposal_chain", []),
            }
        )

    spend_by_archive_id: dict[str, float] = defaultdict(float)
    monthly: dict[str, dict[str, Any]] = {}

    total_spend_usd = 0.0
    for row in spend.get("records", []):
        value = row.get("usd_value_at_execution")
        if value is None:
            continue
        usd = float(value)
        total_spend_usd += usd

        archive_id = row.get("archive_id")
        if archive_id:
            spend_by_archive_id[str(archive_id)] += usd

        bucket = month_bucket(row.get("proposal_executed_at") or row.get("valuation_reference_at"))
        entry = monthly.setdefault(
            bucket,
            {
                "month": bucket,
                "executed_spend_usd": 0.0,
                "proposal_count": 0,
                "vote_count": 0,
                "voting_power": 0.0,
                "cost_per_vote_usd": None,
                "cost_per_voting_power_usd": None,
            },
        )
        entry["executed_spend_usd"] += usd

    proposal_rows: list[dict[str, Any]] = []
    seen_month_proposal: set[tuple[str, str]] = set()

    for archive_id, spend_usd in sorted(spend_by_archive_id.items()):
        proposal = proposal_by_archive_id.get(archive_id)
        if proposal is None:
            continue
        vote_count = len(proposal.get("votes", []))
        voting_power = float(proposal.get("scores_total") or 0.0)

        created_at = proposal.get("created_at")
        month = month_bucket(created_at)
        monthly_entry = monthly.setdefault(
            month,
            {
                "month": month,
                "executed_spend_usd": 0.0,
                "proposal_count": 0,
                "vote_count": 0,
                "voting_power": 0.0,
                "cost_per_vote_usd": None,
                "cost_per_voting_power_usd": None,
            },
        )
        key = (month, archive_id)
        if key not in seen_month_proposal:
            monthly_entry["proposal_count"] += 1
            monthly_entry["vote_count"] += vote_count
            monthly_entry["voting_power"] += voting_power
            seen_month_proposal.add(key)

        proposal_rows.append(
            {
                "archive_id": archive_id,
                "proposal_number": proposal.get("proposal_number"),
                "title": proposal.get("title"),
                "status": proposal.get("status"),
                "chain": proposal.get("chain"),
                "created_at": created_at,
                "executed_spend_usd": round(spend_usd, 2),
                "vote_count": vote_count,
                "voting_power": round(voting_power, 3),
                "cost_per_vote_usd": round(spend_usd / vote_count, 2) if vote_count > 0 else None,
                "cost_per_voting_power_usd": round(spend_usd / voting_power, 6) if voting_power > 0 else None,
                "source_url": proposal.get("links", {}).get("source_url"),
            }
        )

    monthly_rows = sorted(monthly.values(), key=lambda item: item["month"])
    for row in monthly_rows:
        votes = int(row.get("vote_count") or 0)
        vp = float(row.get("voting_power") or 0.0)
        spend_usd = float(row.get("executed_spend_usd") or 0.0)
        row["executed_spend_usd"] = round(spend_usd, 2)
        row["voting_power"] = round(vp, 3)
        row["cost_per_vote_usd"] = round(spend_usd / votes, 2) if votes > 0 else None
        row["cost_per_voting_power_usd"] = round(spend_usd / vp, 6) if vp > 0 else None

    coverage_approved = (total_spend_usd / approved_funding_usd) if approved_funding_usd > 0 else None
    coverage_potential = (total_spend_usd / potential_funding_usd) if potential_funding_usd > 0 else None

    payload = {
        "dataset": "funding_analysis",
        "as_of": utc_now_iso(),
        "version": 1,
        "summary": {
            "funding_sources": len(funding_sources_enriched),
            "approved_funding_usd_estimate": round(approved_funding_usd, 2),
            "potential_funding_usd_estimate": round(potential_funding_usd, 2),
            "executed_spend_usd": round(total_spend_usd, 2),
            "coverage_ratio_approved": round(coverage_approved, 6) if coverage_approved is not None else None,
            "coverage_ratio_potential": round(coverage_potential, 6) if coverage_potential is not None else None,
        },
        "funding_sources": funding_sources_enriched,
        "allocation_by_proposal": proposal_rows,
        "voting_power_timeseries": monthly_rows,
        "method_notes": [
            "Cost per vote = executed_spend_usd / vote_count for each proposal.",
            "Cost per voting power = executed_spend_usd / scores_total.",
            "coverage_ratio_approved compares spend vs only approved/received funding sources.",
            "coverage_ratio_potential compares spend vs all known funding source asks.",
        ],
        "context_sources": [
            "https://nounsagora.com/proposals/51",
            "https://www.nouns.camp/proposals/51",
            "https://nouns.wtf/vote/363",
            "https://www.nouns.camp/proposals/382",
        ],
        "warnings": warnings,
    }

    write_json("funding_analysis", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

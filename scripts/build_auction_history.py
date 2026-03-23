#!/usr/bin/env python3
"""
build_auction_history.py

Constrói histórico de auctions a partir de dados Dune.

Dois modos:
1. Agregado por mês (dados atuais disponíveis)
2. Detalhado por transação (quando Dune query IDs forem preenchidos)

Objetivo: Criar data/auctions.json com auctions detalhadas para BI dashboards.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = ROOT / "raw" / "dune"


def load_json(path: Path) -> dict:
    """Load JSON file."""
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    """Save JSON file."""
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def build_auction_history_monthly() -> dict:
    """
    Build auction history from monthly aggregates.
    
    Returns structure suitable for Sankey/charts:
    {
      "records": [
        {
          "month": "2024-03",
          "chain": "base+ethereum",
          "total_eth": 3.126,
          "total_usd": 10988.93,
          "auction_count": 219,
          "avg_eth_price": 3518.16
        }
      ]
    }
    """
    
    auction_data = load_json(RAW_DIR / "auction_revenue_all_time.json")
    rows = auction_data.get("rows", [])
    
    records = []
    for row in rows:
        # Parse month from "2024-03-01 00:00:00.000 UTC"
        month_str = row.get("month", "").split(" ")[0]  # "2024-03-01" → "2024-03"
        
        record = {
            "month": month_str,
            "chain": "base+ethereum",  # Combined until individual query IDs available
            "auction_count": row.get("auction_count", 0),
            "total_eth": row.get("total_eth", 0),
            "avg_eth_price": row.get("avg_eth_price", 0),
            "total_usd": row.get("total_usd", 0),
        }
        records.append(record)
    
    return {
        "dataset": "auctions",
        "as_of": auction_data.get("as_of"),
        "version": 1,
        "schema_notes": "Aggregated by month. Individual transaction records pending Dune query IDs (gnars_auctions_base, gnars_auctions_ethereum)",
        "records": records,
    }


def build_auction_timeseries() -> dict:
    """
    Build daily auction timeseries for treasury charting.
    
    Interpolates monthly data to daily granularity (approximation).
    """
    
    auction_data = load_json(RAW_DIR / "auction_revenue_all_time.json")
    monthly_rows = auction_data.get("rows", [])
    
    daily_records = []
    for row in monthly_rows:
        month_str = row.get("month", "").split(" ")[0]  # "2024-03-01"
        month_date = datetime.strptime(month_str, "%Y-%m-%d")
        
        total_eth = row.get("total_eth", 0)
        total_usd = row.get("total_usd", 0)
        auction_count = row.get("auction_count", 0)
        
        # Approximate daily average for month
        days_in_month = 30  # Simplified assumptions
        daily_eth = total_eth / days_in_month if days_in_month > 0 else 0
        daily_usd = total_usd / days_in_month if days_in_month > 0 else 0
        daily_auctions = max(1, auction_count // days_in_month)
        
        # Create entries for each day of the month
        for day in range(1, min(32, days_in_month + 1)):
            try:
                date = month_date.replace(day=day)
                daily_records.append({
                    "date": date.isoformat(),
                    "chain": "base+ethereum",
                    "daily_eth": round(daily_eth, 8),
                    "daily_usd": round(daily_usd, 2),
                    "daily_auction_count": daily_auctions,
                    "source": "interpolated_from_monthly_dune",
                })
            except ValueError:
                continue  # Day doesn't exist in month
    
    return {
        "dataset": "auction_timeseries",
        "as_of": auction_data.get("as_of"),
        "version": 1,
        "schema_notes": "Daily interpolation from monthly Dune aggregates. Rough estimate for charting.",
        "records": daily_records,
    }


def build_auction_summary() -> dict:
    """
    Summary statistics for onchain revenue tracking.
    """
    
    auction_data = load_json(RAW_DIR / "auction_revenue_all_time.json")
    rows = auction_data.get("rows", [])
    
    total_eth = sum(r.get("total_eth", 0) for r in rows)
    total_usd = sum(r.get("total_usd", 0) for r in rows)
    total_count = sum(r.get("auction_count", 0) for r in rows)
    
    # Date range
    if rows:
        first_month_str = rows[0].get("month", "").split(" ")[0]
        last_month_str = rows[-1].get("month", "").split(" ")[0]
    else:
        first_month_str = last_month_str = "unknown"
    
    return {
        "dataset": "auction_summary",
        "as_of": auction_data.get("as_of"),
        "version": 1,
        "summary": {
            "total_eth_all_time": round(total_eth, 8),
            "total_usd_all_time": round(total_usd, 2),
            "auction_count_all_time": total_count,
            "avg_eth_per_auction": round(total_eth / total_count, 8) if total_count > 0 else 0,
            "date_range": {
                "first_month": first_month_str,
                "last_month": last_month_str,
            },
            "data_source": "Dune query 'auction_revenue_all_time' (monthly aggregated)",
            "note": "Individual auction transactions require Dune query IDs: gnars_auctions_base, gnars_auctions_ethereum",
        }
    }


def main():
    print("\n" + "="*60)
    print("AUCTION HISTORY BUILDER")
    print("="*60)
    
    # Build datasets
    print("\n📊 Building monthly auction history...")
    monthly_history = build_auction_history_monthly()
    save_json(DATA_DIR / "auctions_monthly.json", monthly_history)
    print(f"   ✓ Saved {len(monthly_history['records'])} months to auctions_monthly.json")
    
    print("\n📊 Building daily auction timeseries...")
    daily_timeseries = build_auction_timeseries()
    save_json(DATA_DIR / "auctions_daily.json", daily_timeseries)
    print(f"   ✓ Saved {len(daily_timeseries['records'])} days to auctions_daily.json")
    
    print("\n📊 Building auction summary...")
    summary = build_auction_summary()
    save_json(DATA_DIR / "auctions_summary.json", summary)
    print(f"   ✓ Saved summary to auctions_summary.json")
    
    # Print summary stats
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    summary_data = summary.get("summary", {})
    print(f"Total revenue all-time: {summary_data.get('total_usd_all_time', 0):,.2f} USD")
    print(f"Total ETH: {summary_data.get('total_eth_all_time', 0):.8f} ETH")
    print(f"Total auctions: {summary_data.get('auction_count_all_time', 0)}")
    print(f"Date range: {summary_data.get('date_range', {}).get('first_month')} to {summary_data.get('date_range', {}).get('last_month')}")
    
    print("\n⚠️  To complete auction indexing:")
    print("   1. Configure Dune query IDs in data/sources.json:")
    print("      - gnars_auctions_base: <query_id>")
    print("      - gnars_auctions_ethereum: <query_id>")
    print("   2. Update fetch_dune_data.py to fetch individual records")
    print("   3. Run: python scripts/refresh_all.py --derive-only")


if __name__ == "__main__":
    main()

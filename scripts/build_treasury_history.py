#!/usr/bin/env python3
"""
build_treasury_history.py

Constrói histórico diário do treasury balance a partir de:
1. Auction revenue diário (auctions_daily.json)
2. Spend ledger com datas de execução
3. Transações já passadas

Objetivo: Criar data/treasury_history.json com serie temporal para gráficos.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def load_json(name: str) -> dict:
    """Load JSON file."""
    path = DATA_DIR / f"{name}.json"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(name: str, data: dict) -> None:
    """Save JSON file."""
    path = DATA_DIR / f"{name}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def parse_iso_date(date_str: str) -> datetime:
    """Parse ISO format date string."""
    try:
        # Handle various ISO formats
        date_str = date_str.replace("Z", "+00:00")
        return datetime.fromisoformat(date_str)
    except Exception:
        return None


def build_treasury_history() -> dict:
    """
    Build daily treasury balance history.
    
    Starts from 2024-03-01 (first auction).
    For each day: balance += inflows - outflows
    """
    
    print("📊 Loading data...")
    auctions_daily = load_json("auctions_daily")
    spend_ledger = load_json("spend_ledger")
    current_treasury = load_json("treasury")
    dao_metrics = load_json("dao_metrics")
    
    current_balance = current_treasury.get("balance_usd", dao_metrics.get("treasury_balance_usd", 44737))
    
    print(f"   Current balance: ${current_balance:,.2f}")
    
    # Build daily inflows/outflows
    daily_flows = defaultdict(lambda: {"inflow": 0.0, "outflow": 0.0})
    
    # Process auction inflows
    print("📊 Processing auction inflows...")
    for record in auctions_daily.get("records", []):
        date = record.get("date", "")[:10]  # YYYY-MM-DD
        daily_flows[date]["inflow"] += record.get("daily_usd", 0)
    
    # Process spend ledger outflows
    print("📊 Processing spend outflows...")
    for record in spend_ledger.get("records", []):
        exec_date_str = record.get("proposal_executed_at", "")
        if not exec_date_str:
            continue
        
        exec_date = parse_iso_date(exec_date_str)
        if not exec_date:
            continue
        
        date = exec_date.strftime("%Y-%m-%d")
        amount = record.get("usd_value_at_execution", 0)
        daily_flows[date]["outflow"] += amount
    
    # Build cumulative balance from start date
    print("📊 Building cumulative balance...")
    
    start_date = datetime(2024, 3, 1)
    end_date = datetime.now()
    
    # Infer opening balance (working backwards from current)
    # total_inflows - total_outflows + opening_balance = current_balance
    total_inflows = sum(f["inflow"] for f in daily_flows.values())
    total_outflows = sum(f["outflow"] for f in daily_flows.values())
    opening_balance = current_balance - (total_inflows - total_outflows)
    
    print(f"   Inferred opening balance: ${opening_balance:,.2f}")
    print(f"   Total inflows (calculated): ${total_inflows:,.2f}")
    print(f"   Total outflows (calculated): ${total_outflows:,.2f}")
    
    records = []
    balance = opening_balance
    current_date = start_date
    
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        flows = daily_flows.get(date_str, {"inflow": 0.0, "outflow": 0.0})
        
        inflow = flows["inflow"]
        outflow = flows["outflow"]
        balance += inflow - outflow
        
        # Only include non-zero days + monthly endpoints
        if inflow > 0 or outflow > 0 or current_date.day == 1:
            records.append({
                "date": date_str,
                "inflow_usd": round(inflow, 2),
                "outflow_usd": round(outflow, 2),
                "balance_usd": round(balance, 2),
                "has_activity": inflow > 0 or outflow > 0,
            })
        
        current_date += timedelta(days=1)
    
    return {
        "dataset": "treasury_history",
        "as_of": datetime.now().isoformat(),
        "version": 1,
        "summary": {
            "start_date": (start_date).isoformat(),
            "end_date": end_date.isoformat(),
            "opening_balance_usd": round(opening_balance, 2),
            "current_balance_usd": round(balance, 2),
            "total_inflows_usd": round(total_inflows, 2),
            "total_outflows_usd": round(total_outflows, 2),
            "note": "Opening balance inferred from current balance and net flows. May not match blockchain genesis.",
        },
        "records": records,
    }


def main():
    print("\n" + "="*60)
    print("TREASURY HISTORY BUILDER")
    print("="*60)
    
    history = build_treasury_history()
    
    save_json("treasury_history", history)
    
    summary = history.get("summary", {})
    records = history.get("records", [])
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Date range: {summary.get('start_date')} to {summary.get('end_date')}")
    print(f"Records: {len(records)} days")
    print(f"Opening balance: ${summary.get('opening_balance_usd', 0):,.2f}")
    print(f"Current balance: ${summary.get('current_balance_usd', 0):,.2f}")
    print(f"Total inflows: ${summary.get('total_inflows_usd', 0):,.2f}")
    print(f"Total outflows: ${summary.get('total_outflows_usd', 0):,.2f}")
    print(f"Net: ${summary.get('total_inflows_usd', 0) - summary.get('total_outflows_usd', 0):,.2f}")
    
    print(f"\n✅ Saved to data/treasury_history.json")


if __name__ == "__main__":
    main()

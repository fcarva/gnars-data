#!/usr/bin/env python3
"""
enrich_spend_tx_hash.py

Enriquece spend_ledger com tx_hash completo via:
1. Uso de dune_tx_hash como fallback
2. Lookup em BaseScan usando recipient + amount + timestamp
3. Busca em raw/dune para records já indexados

Objetivo: Melhorar cobertura de 50% → 90%+
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = ROOT / "raw"

TREASURY_ADDRESS_BASE = "0x72ad986ebac0246d2b3c565ab2a1ce3a14ce6f88"
BASESCAN_API_URL = "https://api.basescan.org/api"


def load_json(name: str) -> dict:
    """Load JSON file by name from data directory."""
    path = DATA_DIR / f"{name}.json"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(name: str, data: dict) -> None:
    """Save JSON file to data directory."""
    path = DATA_DIR / f"{name}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def fetch_treasury_transactions_from_basescan() -> list[dict]:
    """
    Fetch all transactions from Gnars treasury on Base via BaseScan API.
    
    Returns list of transaction dicts with fields: hash, from, to, value, input, timeStamp, ...
    """
    api_key = os.getenv("BASESCAN_API_KEY", "")
    if not api_key:
        print("⚠️  BASESCAN_API_KEY not set - skipping BaseScan lookup")
        return []
    
    try:
        import urllib.request
        import urllib.parse
        
        params = {
            "module": "account",
            "action": "txlist",
            "address": TREASURY_ADDRESS_BASE,
            "startblock": 0,
            "endblock": 99999999,
            "sort": "asc",
            "apikey": api_key,
        }
        
        url = BASESCAN_API_URL + "?" + urllib.parse.urlencode(params)
        print(f"🔍 Fetching treasury transactions from BaseScan...")
        
        with urllib.request.urlopen(url, timeout=30) as response:
            result = json.loads(response.read())
            
        if result.get("status") != "1":
            print(f"⚠️  BaseScan API error: {result.get('message')}")
            return []
            
        txs = result.get("result", [])
        print(f"✓ Fetched {len(txs)} transactions from BaseScan")
        return txs
        
    except Exception as e:
        print(f"❌ Error fetching from BaseScan: {e}")
        return []


def get_tx_hash_from_dune(record: Dict[str, Any]) -> Optional[str]:
    """
    Try to get tx_hash from dune_tx_hash field.
    """
    dune_hash = record.get("dune_tx_hash")
    if dune_hash and dune_hash.startswith("0x"):
        return dune_hash
    return None


def match_tx_to_record(
    tx: dict,
    record: Dict[str, Any],
    tolerance_hours: int = 2
) -> bool:
    """
    Try to match a BaseScan transaction to a spend record.
    
    Criteria:
    - Recipient address matches
    - Amount matches (with tolerance for stablecoins)
    - Timestamp within tolerance
    """
    try:
        # Get record details
        recipient = record.get("recipient_address", "").lower()
        amount_usd = record.get("usd_value_at_execution", 0)
        asset_symbol = record.get("asset_symbol", "").upper()
        executed_at = record.get("proposal_executed_at", "")
        
        if not recipient or not executed_at or amount_usd == 0:
            return False
        
        # Parse record timestamp
        try:
            record_time = datetime.fromisoformat(executed_at.replace("Z", "+00:00"))
        except Exception:
            return False
        
        # Get transaction details
        tx_to = tx.get("to", "").lower()
        tx_time_str = tx.get("timeStamp", "0")
        tx_func = tx.get("input", "")
        
        if not tx_to:
            return False
        
        # Parse tx timestamp
        try:
            tx_time = datetime.fromtimestamp(int(tx_time_str))
        except Exception:
            return False
        
        # Check recipient match
        if tx_to != recipient:
            return False
        
        # Check timestamp proximity (within tolerance_hours)
        time_diff = abs((record_time - tx_time).total_seconds()) / 3600
        if time_diff > tolerance_hours:
            return False
        
        # For USDC transfers, check amount in calldata
        if asset_symbol == "USDC":
            # ERC20 transfer calldata format: 0xa9059cbb + recipient (32) + amount (32)
            if tx_func.startswith("0xa9059cbb"):
                try:
                    # Extract amount from calldata (last 64 hex chars = 32 bytes)
                    amount_hex = "0x" + tx_func[-64:]
                    amount_raw = int(amount_hex, 16)
                    # USDC has 6 decimals
                    amount_usdc = amount_raw / 1e6
                    # Match if within 1% tolerance
                    if abs(amount_usdc - amount_usd) / amount_usd < 0.01:
                        return True
                except Exception:
                    pass
        
        # For ETH transfers, check value field
        elif asset_symbol == "ETH":
            try:
                value_eth = int(tx.get("value", "0")) / 1e18
                # Match if within 1% tolerance
                if abs(value_eth - amount_usd / 2800) / (amount_usd / 2800) < 0.01:
                    return True
            except Exception:
                pass
        
        return False
        
    except Exception as e:
        print(f"⚠️  Error matching tx: {e}")
        return False


def enrich_spend_ledger() -> None:
    """Main enrichment function."""
    
    print("\n" + "="*60)
    print("SPEND LEDGER TX_HASH ENRICHMENT")
    print("="*60)
    
    # Load data
    ledger = load_json("spend_ledger")
    records = ledger.get("records", [])
    
    print(f"\n📊 Starting state: {len(records)} records")
    has_tx_hash_before = sum(1 for r in records if r.get("tx_hash"))
    print(f"   - With tx_hash: {has_tx_hash_before} ({100*has_tx_hash_before/len(records):.1f}%)")
    
    # Strategy 0: Check proposal_explorer_url for embedded tx_hash
    print("\n🔗 Strategy 0: Extracting from proposal_explorer_url...")
    filled_from_explorer_url = 0
    for record in records:
        if not record.get("tx_hash"):
            explorer_url = record.get("proposal_explorer_url") or ""
            if explorer_url and "/tx/" in explorer_url:
                tx_hash = explorer_url.split("/tx/")[-1]
                if tx_hash.startswith("0x") and len(tx_hash) == 66:
                    record["tx_hash"] = tx_hash
                    record["tx_hash_source"] = "explorer_url"
                    filled_from_explorer_url += 1
    
    print(f"   ✓ Filled {filled_from_explorer_url} records from explorer_url")
    
    # Strategy 1: Use dune_tx_hash as fallback
    print("\n🔗 Strategy 1: Using dune_tx_hash as fallback...")
    filled_from_dune = 0
    for record in records:
        if not record.get("tx_hash"):
            dune_hash = get_tx_hash_from_dune(record)
            if dune_hash:
                record["tx_hash"] = dune_hash
                record["tx_hash_source"] = "dune"
                filled_from_dune += 1
    
    print(f"   ✓ Filled {filled_from_dune} records from dune_tx_hash")
    
    # Strategy 2: Fetch from BaseScan and match
    print("\n🔗 Strategy 2: Fetching BaseScan transactions...")
    basescan_txs = fetch_treasury_transactions_from_basescan()
    
    filled_from_basescan = 0
    if basescan_txs:
        for record in records:
            if record.get("tx_hash"):
                continue  # Already has tx_hash
            
            # Try to find matching transaction
            for tx in basescan_txs:
                if match_tx_to_record(tx, record):
                    record["tx_hash"] = tx.get("hash")
                    record["tx_hash_source"] = "basescan"
                    filled_from_basescan += 1
                    break
        
        print(f"   ✓ Filled {filled_from_basescan} records from BaseScan matching")
    
    # Summary
    has_tx_hash_after = sum(1 for r in records if r.get("tx_hash"))
    improvement = has_tx_hash_after - has_tx_hash_before
    coverage_pct = 100 * has_tx_hash_after / len(records)
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"Records with tx_hash: {has_tx_hash_before} → {has_tx_hash_after}")
    print(f"Coverage: {100*has_tx_hash_before/len(records):.1f}% → {coverage_pct:.1f}%")
    print(f"Improvement: +{improvement} records (+{100*improvement/len(records):.1f}%)")
    
    # Count by source
    source_counts = {}
    for r in records:
        if r.get("tx_hash"):
            source = r.get("tx_hash_source", "unknown")
            source_counts[source] = source_counts.get(source, 0) + 1
    
    print("\nBreakdown by source:")
    for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        print(f"  {source}: {count}")
    
    # Save
    ledger["records"] = records
    save_json("spend_ledger", ledger)
    print(f"\n✅ Saved updated spend_ledger.json")


if __name__ == "__main__":
    enrich_spend_ledger()

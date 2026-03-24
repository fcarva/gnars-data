#!/usr/bin/env python3
import json
import pprint

print("=== SPEND LEDGER ANALYSIS ===")
ledger = json.load(open('data/spend_ledger.json', encoding='utf-8'))
records = ledger['records']

print(f'Total records: {len(records)}')
print(f'TX Hash coverage: {sum(1 for r in records if r.get("tx_hash"))} / {len(records)}')
print(f'Records with project_id: {sum(1 for r in records if r.get("project_id"))}')
print(f'Records with category: {sum(1 for r in records if r.get("category"))}')
print()

print("Sample record:")
pprint.pprint(records[0], width=120)
print()

print("=== DAO METRICS ANALYSIS ===")
try:
    dao = json.load(open('data/dao_metrics.json', encoding='utf-8'))
    print(f'Funding in: {dao.get("funding_in_usd")}')
    print(f'Total spend: {dao.get("total_spend_usd")}')
    print(f'Balance: {dao.get("treasury_balance_usd")}')
    print()
    print("Keys in dao_metrics:")
    pprint.pprint(list(dao.keys()), width=120)
except Exception as e:
    print(f"Error: {e}")

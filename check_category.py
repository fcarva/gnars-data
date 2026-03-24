#!/usr/bin/env python3
"""Check category status after enrich"""
import json

spend = json.load(open('data/spend_ledger.json', encoding='utf-8'))
records = spend.get('records', [])

cat_count = {}
for r in records:
    cat = r.get('category', 'MISSING')
    cat_count[cat] = cat_count.get(cat, 0) + 1

print('SPEND_LEDGER CATEGORY STATUS:')
for cat, count in sorted(cat_count.items()):
    pct = 100*count/len(records)
    print(f'{cat}: {count} ({pct:.1f}%)')

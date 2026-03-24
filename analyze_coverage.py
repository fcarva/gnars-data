#!/usr/bin/env python3
import json

ledger = json.load(open('data/spend_ledger.json', encoding='utf-8'))

# Count by proposal type
snapshot_records = [r for r in ledger['records'] if 'snapshot-' in r.get('archive_id', '')]
base_records = [r for r in ledger['records'] if 'gnars-base-' in r.get('archive_id', '')]

print(f'Total records: {len(ledger["records"])}')
print(f'  Snapshot (offchain): {len(snapshot_records)}')
print(f'  Base onchain: {len(base_records)}')
print()

# Check tx_hash coverage per type
snapshot_with_tx = sum(1 for r in snapshot_records if r.get('tx_hash'))
base_with_tx = sum(1 for r in base_records if r.get('tx_hash'))

print(f'TX Hash coverage:')
if snapshot_records:
    print(f'  Snapshot: {snapshot_with_tx}/{len(snapshot_records)} ({100*snapshot_with_tx/len(snapshot_records):.1f}%)')
if base_records:
    print(f'  Base: {base_with_tx}/{len(base_records)} ({100*base_with_tx/len(base_records):.1f}%)')
print()

# Check category coverage
snapshot_categorized = sum(1 for r in snapshot_records if r.get('category'))
base_categorized = sum(1 for r in base_records if r.get('category'))

print(f'Category coverage:')
if snapshot_records:
    print(f'  Snapshot: {snapshot_categorized}/{len(snapshot_records)} ({100*snapshot_categorized/len(snapshot_records):.1f}%)')
if base_records:
    print(f'  Base: {base_categorized}/{len(base_records)} ({100*base_categorized/len(base_records):.1f}%)')

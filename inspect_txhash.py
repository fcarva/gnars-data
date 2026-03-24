#!/usr/bin/env python3
import json

ledger = json.load(open('data/spend_ledger.json', encoding='utf-8'))
records = ledger['records']

# Check records without tx_hash
no_tx = [r for r in records if not r.get('tx_hash')]
print(f'Total records without tx_hash: {len(no_tx)}')
if no_tx:
    r = no_tx[0]
    print(f'\nFirst record without tx_hash:')
    print(f'  archive_id: {r.get("archive_id")}')
    print(f'  proposal_explorer_url: {r.get("proposal_explorer_url")}')
    print(f'  dune_tx_hash: {r.get("dune_tx_hash")}')
    print(f'  dune_match_source: {r.get("dune_match_source")}')
    
# Check a record WITH tx_hash
with_tx = [r for r in records if r.get('tx_hash')]
if with_tx:
    r = with_tx[0]
    print(f'\nFirst record WITH tx_hash:')
    print(f'  archive_id: {r.get("archive_id")}')
    print(f'  tx_hash: {r.get("tx_hash")}')
    print(f'  dune_tx_hash: {r.get("dune_tx_hash")}')
    print(f'  proposal_explorer_url: {r.get("proposal_explorer_url")}')
    print(f'  dune_match_source: {r.get("dune_match_source")}')

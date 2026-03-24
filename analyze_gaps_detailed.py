#!/usr/bin/env python3
"""
Análise detalhada dos gaps encontrados na auditoria
"""

import json

print('█ ANÁLISE DETALHADA DOS GAPS ENCONTRADOS')
print('='*60)
print()

# 1. TREASURY GAP
print('❌ PROBLEMA 1: TREASURY DATA ZEROED OUT')
print('-'*60)
treasury = json.load(open('data/treasury.json', encoding='utf-8'))
spend_ledger = json.load(open('data/spend_ledger.json', encoding='utf-8'))

print(f'treasury.json:')
print(f'  - balance_usd: ${treasury.get("balance_usd", 0):,.2f} (SHOULD BE ~$44,737)')
print(f'  - Keys present: {list(treasury.keys())}')
print()

print(f'spend_ledger.json - Sample first 3 records:')
for i, record in enumerate(spend_ledger.get('records', [])[:3]):
    print(f'  Record {i}:')
    print(f'    category: {record.get("category", "MISSING")}')
    print(f'    usd_value: {record.get("usd_value_at_execution", 0)}')
    print()

# Check category field
category_check = {}
for r in spend_ledger.get('records', []):
    cat = r.get('category', 'MISSING')
    category_check[cat] = category_check.get(cat, 0) + 1

print(f'Category distribution in spend_ledger:')
for cat, count in sorted(category_check.items()):
    print(f'  {cat}: {count}')
print()

# 2. MILESTONES GAP  
print('❌ PROBLEMA 2: MILESTONES FILE COMPLETELY EMPTY')
print('-'*60)
milestones = json.load(open('data/milestones.json', encoding='utf-8'))
print(f'milestones.json total records: {len(milestones.get("records", []))}')
print(f'File size: {len(json.dumps(milestones))} bytes')
print(f'Keys in file: {list(milestones.keys())}')
print()

# 3. MEMBERS SPORT GAP
print('❌ PROBLEMA 3: MEMBERS SPORT DATA NEARLY EMPTY')
print('-'*60)
members = json.load(open('data/members.json', encoding='utf-8'))
sport_counts = {}
for m in members.get('records', []):
    sport = m.get('sport', 'MISSING')
    sport_counts[sport] = sport_counts.get(sport, 0) + 1

print(f'Total members: {len(members.get("records", []))}')
print(f'Sport distribution:')
for sport, count in sorted(sport_counts.items(), key=lambda x: -x[1])[:10]:
    pct = 100*count/len(members.get('records', []))
    print(f'  {sport}: {count} ({pct:.1f}%)')
print()

# 4. VOTES GAP
print('❌ PROBLEMA 4: 26 PROPOSALS MISSING VOTE DATA')
print('-'*60)
proposals = json.load(open('data/proposals_archive.json', encoding='utf-8'))
no_vote_props = [p for p in proposals['records'] if not p.get('votes') or len(p.get('votes', [])) == 0]

print(f'Proposals without vote data: {len(no_vote_props)}/{len(proposals["records"])}')
print(f'Examples:')
for p in no_vote_props[:5]:
    title = p.get('title', 'Unknown')[:50]
    chain = p.get('chain', 'unknown')
    print(f'  - {p.get("archive_id")}: {title}... (chain: {chain})')

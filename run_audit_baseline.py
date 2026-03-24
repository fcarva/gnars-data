#!/usr/bin/env python3
"""
GNARS-DATA AUDIT BASELINE REPORT
Diagnóstico automático dos 4 tabs: Votes, Treasury, Milestones, Analytics
"""

import json
from datetime import datetime
from pathlib import Path

print('='*60)
print('GNARS-DATA AUDIT REPORT - DIAGNÓSTICO AUTOMÁTICO')
print('='*60)
print(f'Data: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print()

# 1. VOTES ANALYSIS
print('█ FASE 1: VOTES TAB ANALYSIS')
print('-' * 60)
proposals = json.load(open('data/proposals_archive.json', encoding='utf-8'))
base_props = [p for p in proposals['records'] if p.get('chain') == 'base']
eth_props = [p for p in proposals['records'] if p.get('chain') == 'ethereum']
snapshot_props = [p for p in proposals['records'] if p.get('chain') == 'snapshot']
props_with_votes = [p for p in proposals['records'] if p.get('votes') and len(p['votes']) > 0]

print(f'Total proposals: {len(proposals["records"])}')
print(f'  ├─ Base: {len(base_props)} ({100*len(base_props)/len(proposals["records"]):.1f}%)')
print(f'  ├─ Ethereum: {len(eth_props)} ({100*len(eth_props)/len(proposals["records"]):.1f}%)')
print(f'  └─ Snapshot: {len(snapshot_props)} ({100*len(snapshot_props)/len(proposals["records"]):.1f}%)')
print()

votes_coverage = 100*len(props_with_votes)/len(proposals["records"]) if proposals["records"] else 0
print(f'Proposals with vote data: {len(props_with_votes)}/{len(proposals["records"])} ({votes_coverage:.1f}%)')
votes_status = "✅ PASS" if votes_coverage > 95 else "⚠️  NEEDS WORK"
print(f'Target: >95% ▶ Status: {votes_status}')
print()

# 2. TREASURY ANALYSIS
print('█ FASE 2: TREASURY TAB ANALYSIS')
print('-' * 60)
treasury = json.load(open('data/treasury.json', encoding='utf-8'))
treasury_flows = json.load(open('data/treasury_flows.json', encoding='utf-8'))
spend_ledger = json.load(open('data/spend_ledger.json', encoding='utf-8'))

print(f'Current balance: ${treasury.get("balance_usd", 0):,.2f}')

records = spend_ledger.get('records', [])
print(f'Spend ledger records: {len(records)}')
tx_hash_pct = 100*sum(1 for r in records if r.get('tx_hash'))/len(records) if records else 0
project_id_pct = 100*sum(1 for r in records if r.get('project_id'))/len(records) if records else 0
category_pct = 100*sum(1 for r in records if r.get('category'))/len(records) if records else 0
recipient_pct = 100*sum(1 for r in records if r.get('recipient_address'))/len(records) if records else 0

print(f'  ├─ tx_hash: {tx_hash_pct:.1f}% (target: >90%)')
print(f'  ├─ project_id: {project_id_pct:.1f}% (target: 100%)')
print(f'  ├─ category: {category_pct:.1f}% (target: 100%)')
print(f'  └─ recipient: {recipient_pct:.1f}% (target: 100%)')

if tx_hash_pct > 90 and project_id_pct == 100 and category_pct == 100:
    treasury_status = "✅ EXCELLENT"
elif min(tx_hash_pct, project_id_pct, category_pct) >= 80:
    treasury_status = "⚠️  GOOD - Minor gaps"
else:
    treasury_status = "❌ NEEDS WORK"
print(f'Status: {treasury_status}')
print()

# 3. MILESTONES ANALYSIS
print('█ FASE 3: MILESTONES TAB ANALYSIS')
print('-' * 60)
milestones = json.load(open('data/milestones.json', encoding='utf-8'))
milestone_records = milestones.get('records', [])

phases = {}
for m in milestone_records:
    phase = m.get('phase', 'uncategorized')
    phases[phase] = phases.get(phase, 0) + 1

print(f'Total milestones: {len(milestone_records)}')
for phase, count in sorted(phases.items()):
    print(f'  ├─ {phase}: {count}')

props_with_milestones = len(set(m.get('proposal_id') for m in milestone_records if m.get('proposal_id')))
milestone_coverage = 100*props_with_milestones/len(proposals['records']) if proposals['records'] else 0

print()
print(f'Proposals with deliverables: {props_with_milestones}/{len(proposals["records"])} ({milestone_coverage:.1f}%)')
milestone_status = "✅ PASS" if milestone_coverage > 95 else "⚠️  NEEDS WORK"
print(f'Target: 100% ▶ Status: {milestone_status}')
print()

# 4. ANALYTICS ANALYSIS
print('█ FASE 4: ANALYTICS TAB ANALYSIS')
print('-' * 60)
members = json.load(open('data/members.json', encoding='utf-8'))
proposal_tags = json.load(open('data/proposal_tags.json', encoding='utf-8'))

member_records = members.get('records', [])
sport_pct = 100*sum(1 for m in member_records if m.get('sport'))/len(member_records) if member_records else 0
display_pct = 100*sum(1 for m in member_records if m.get('display_name'))/len(member_records) if member_records else 0

print(f'Total members: {len(member_records)}')
print(f'  ├─ with sport: {sport_pct:.1f}% (target: >95%)')
print(f'  └─ with display_name: {display_pct:.1f}% (target: >90%)')

recipients = set(r.get('recipient_address') for r in records if r.get('recipient_address'))
recipients_in_members = sum(1 for addr in recipients if any(m.get('address', '').lower() == addr.lower() for m in member_records))
recipient_coverage_pct = 100*recipients_in_members/len(recipients) if recipients else 0

print()
print(f'Recipient coverage: {recipients_in_members}/{len(recipients)} ({recipient_coverage_pct:.1f}%)')
recipient_status = "✅ EXCELLENT" if recipient_coverage_pct > 95 else "⚠️  NEEDS WORK"
print(f'Target: 100% ▶ Status: {recipient_status}')

# Category tags
tag_records = proposal_tags.get('records', [])
low_confidence = sum(1 for t in tag_records if t.get('semantic_confidence', 1.0) < 0.6)
tag_confidence_pct = 100*(len(tag_records) - low_confidence)/len(tag_records) if tag_records else 100

print()
print(f'Tagged proposals: {len(tag_records)}')
print(f'  └─ high confidence: {tag_confidence_pct:.1f}% (target: >90%)')
print()

# SUMMARY
print('='*60)
print('📊 OVERALL SCORE')
print('='*60)
scores = [
    ('Votes', votes_coverage),
    ('Treasury', min(tx_hash_pct, project_id_pct, category_pct)),
    ('Milestones', milestone_coverage),
    ('Analytics', min(sport_pct, display_pct, recipient_coverage_pct, tag_confidence_pct))
]

for name, score in scores:
    bar = '█' * int(score/10) + '░' * (10 - int(score/10))
    print(f'{name:15} [{bar}] {score:.1f}%')

overall = sum(s for _, s in scores) / len(scores)
print()
print(f'OVERALL: {overall:.1f}%')
if overall >= 95:
    print('Status: 🟢 EXCELENTE')
elif overall >= 80:
    print('Status: 🟡 BOM - Pequenas lacunas')
else:
    print('Status: 🔴 PRECISA DE TRABALHO')

# Save to file
report_data = {
    'timestamp': datetime.now().isoformat(),
    'votes': {'coverage': votes_coverage, 'status': votes_status},
    'treasury': {
        'balance': treasury.get('balance_usd'),
        'tx_hash_pct': tx_hash_pct,
        'project_id_pct': project_id_pct,
        'category_pct': category_pct,
        'status': treasury_status
    },
    'milestones': {'coverage': milestone_coverage, 'status': milestone_status},
    'analytics': {
        'members_count': len(member_records),
        'sport_pct': sport_pct,
        'display_pct': display_pct,
        'recipient_coverage_pct': recipient_coverage_pct,
        'tag_confidence_pct': tag_confidence_pct
    },
    'overall_score': overall
}

with open('reports/audit_baseline.json', 'w', encoding='utf-8') as f:
    json.dump(report_data, f, indent=2, ensure_ascii=False)

print()
print('='*60)
print(f'✅ Relatório salvo em: reports/audit_baseline.json')
print('='*60)

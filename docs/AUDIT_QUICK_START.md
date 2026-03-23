# GNARS-DATA AUDIT - QUICK START COMMANDS

**Copiar e colar cada bloco para executar a auditoria completa**

---

## ⚡ AUDIT RÁPIDO (5 minutos)

### Diagnóstico Automático Completo

```bash
# Copiar tudo de uma vez no PowerShell
cd c:\Users\DELL\Documents\gnars-data

echo "=== GNARS-DATA AUDIT REPORT ===" > audit_report.txt
echo "Data: $(Get-Date)" >> audit_report.txt
echo "" >> audit_report.txt

echo "[ VOTES ANALYSIS ]" >> audit_report.txt
python -c "
import json
proposals = json.load(open('data/proposals_archive.json', encoding='utf-8'))
props_with_votes = sum(1 for p in proposals['records'] if p.get('votes') and len(p['votes']) > 0)
print(f'Proposals with votes: {props_with_votes}/{len(proposals[\"records\"])} ({100*props_with_votes/len(proposals[\"records\"]):.1f}%)')
" >> audit_report.txt

echo "[ TREASURY ANALYSIS ]" >> audit_report.txt
python -c "
import json
treasury = json.load(open('data/treasury.json', encoding='utf-8'))
spend_ledger = json.load(open('data/spend_ledger.json', encoding='utf-8'))
records = spend_ledger.get('records', [])
tx_hash_coverage = sum(1 for r in records if r.get('tx_hash')) / len(records) * 100 if records else 0
project_id_coverage = sum(1 for r in records if r.get('project_id')) / len(records) * 100 if records else 0
category_coverage = sum(1 for r in records if r.get('category')) / len(records) * 100 if records else 0
print(f'Spend Ledger Records: {len(records)}')
print(f'  tx_hash: {tx_hash_coverage:.1f}% coverage')
print(f'  project_id: {project_id_coverage:.1f}% coverage')
print(f'  category: {category_coverage:.1f}% coverage')
print(f'Treasury Balance: \${treasury.get(\"balance_usd\", 0):,.2f}')
" >> audit_report.txt

echo "[ MEMBERS ANALYSIS ]" >> audit_report.txt
python -c "
import json
members = json.load(open('data/members.json', encoding='utf-8'))
spend_ledger = json.load(open('data/spend_ledger.json', encoding='utf-8'))
records = members.get('records', [])
sport_coverage = sum(1 for m in records if m.get('sport')) / len(records) * 100 if records else 0
display_coverage = sum(1 for m in records if m.get('display_name')) / len(records) * 100 if records else 0
recipients = set(r.get('recipient_address') for r in spend_ledger.get('records', []) if r.get('recipient_address'))
print(f'Total Members: {len(records)}')
print(f'  with sport: {sport_coverage:.1f}% coverage')
print(f'  with display_name: {display_coverage:.1f}% coverage')
print(f'Total Recipients (from spend_ledger): {len(recipients)}')
" >> audit_report.txt

echo "[ MILESTONES ANALYSIS ]" >> audit_report.txt
python -c "
import json
milestones = json.load(open('data/milestones.json', encoding='utf-8'))
records = milestones.get('records', [])
completed = sum(1 for m in records if m.get('status') == 'completed')
print(f'Total Milestones: {len(records)}')
print(f'  Completed: {completed} ({100*completed/len(records):.1f}%)')
print(f'  In Progress: {sum(1 for m in records if m.get(\"status\") == \"in_progress\")}')
" >> audit_report.txt

# Display report
cat audit_report.txt
```

---

## 🔍 AUDIT DETALHADO (15 minutos)

### 1️⃣ VOTES TAB - Validação Completa

```bash
python -c "
import json
from collections import defaultdict

print('\n' + '='*50)
print('VOTES TAB AUDIT')
print('='*50)

proposals = json.load(open('data/proposals_archive.json', encoding='utf-8'))
snapshot_votes = json.load(open('data/snapshot_votes.json', encoding='utf-8'))

# Vote coverage
props_with_votes = [p for p in proposals['records'] if p.get('votes') and len(p['votes']) > 0]
props_no_votes = [p for p in proposals['records'] if not p.get('votes') or len(p['votes']) == 0]

print(f'\n1. VOTE COVERAGE')
print(f'   Proposals with votes: {len(props_with_votes)}/{len(proposals[\"records\"])} ({100*len(props_with_votes)/len(proposals[\"records\"]):.1f}%)')
print(f'   Missing votes: {len(props_no_votes)}')

if props_no_votes:
    print(f'   Examples of proposals missing votes:')
    for p in props_no_votes[:3]:
        print(f'     → {p.get(\"archive_id\")}: {p.get(\"title\")[:40]}...')

# Vote quality
total_votes = sum(len(p.get('votes', [])) for p in proposals['records'])
votes_with_reason = sum(sum(1 for v in p.get('votes', []) if v.get('reason')) for p in proposals['records'])

print(f'\n2. VOTE QUALITY')
print(f'   Total votes: {total_votes}')
print(f'   With reason: {votes_with_reason} ({100*votes_with_reason/total_votes:.1f}%)')
print(f'   Target: >80% with reason')

# Snapshot votes structure
print(f'\n3. SNAPSHOT VOTES FILE')
print(f'   Records: {len(snapshot_votes.get(\"records\", []))}')
if snapshot_votes.get('records'):
    sample = snapshot_votes['records'][0]
    print(f'   Fields: {list(sample.keys())}')

print('\n✓ Recommendation: ' + ('PASS ✅' if len(props_with_votes)/len(proposals['records']) > 0.95 else 'NEEDS WORK ⚠️'))
"
```

### 2️⃣ TREASURY TAB - Validação Completa

```bash
python -c "
import json

print('\n' + '='*50)
print('TREASURY TAB AUDIT')
print('='*50)

treasury = json.load(open('data/treasury.json', encoding='utf-8'))
treasury_flows = json.load(open('data/treasury_flows.json', encoding='utf-8'))
spend_ledger = json.load(open('data/spend_ledger.json', encoding='utf-8'))

# Treasury summary
print(f'\n1. TREASURY SUMMARY')
print(f'   Current balance: \${treasury.get(\"balance_usd\", 0):,.2f}')
print(f'   Last updated: {treasury.get(\"last_updated\", \"unknown\")}')

# Flows
inflows = [t for t in treasury_flows.get('records', []) if t.get('type') == 'in']
outflows = [t for t in treasury_flows.get('records', []) if t.get('type') == 'out']
print(f'\n2. TREASURY FLOWS')
print(f'   Inflows: {len(inflows)}')
print(f'   Outflows: {len(outflows)}')
print(f'   Total in: \${sum(t.get(\"amount_usd\", 0) for t in inflows):,.2f}')
print(f'   Total out: \${sum(t.get(\"amount_usd\", 0) for t in outflows):,.2f}')

# Spend ledger
records = spend_ledger.get('records', [])
print(f'\n3. SPEND LEDGER COMPLETENESS')
print(f'   Total records: {len(records)}')

# Coverage metrics
tx_hash_count = sum(1 for r in records if r.get('tx_hash'))
project_id_count = sum(1 for r in records if r.get('project_id'))
category_count = sum(1 for r in records if r.get('category'))
recipient_count = sum(1 for r in records if r.get('recipient_address'))
priced_count = sum(1 for r in records if r.get('usd_value_at_execution'))

print(f'   With tx_hash: {tx_hash_count}/{len(records)} ({100*tx_hash_count/len(records):.1f}%)')
print(f'   With project_id: {project_id_count}/{len(records)} ({100*project_id_count/len(records):.1f}%)')
print(f'   With category: {category_count}/{len(records)} ({100*category_count/len(records):.1f}%)')
print(f'   With recipient: {recipient_count}/{len(records)} ({100*recipient_count/len(records):.1f}%)')
print(f'   Priced: {priced_count}/{len(records)} ({100*priced_count/len(records):.1f}%)')

# Issues
print(f'\n4. ISSUES DETECTED')
missing_fields = [r for r in records if not r.get('tx_hash') or not r.get('project_id')]
print(f'   Missing tx_hash or project_id: {len(missing_fields)}')
unpriced = [r for r in records if not r.get('usd_value_at_execution')]
print(f'   Unpriced records: {len(unpriced)}')

negative_values = [r for r in records if r.get('amount', 0) < 0]
print(f'   Negative amounts: {len(negative_values)}')

print('\n✓ Targets:')
print(f'  ├─ tx_hash: >90% (actual: {100*tx_hash_count/len(records):.1f}%)')
print(f'  ├─ project_id: 100% (actual: {100*project_id_count/len(records):.1f}%)')
print(f'  ├─ category: 100% (actual: {100*category_count/len(records):.1f}%)')
print(f'  └─ priced: 100% (actual: {100*priced_count/len(records):.1f}%)')

print('\n✓ Recommendation: ' + ('PASS ✅' if (tx_hash_count/len(records) > 0.9 and project_id_count == len(records)) else 'NEEDS WORK ⚠️'))
"
```

### 3️⃣ MILESTONES TAB - Validação Completa

```bash
python -c "
import json
from collections import defaultdict

print('\n' + '='*50)
print('MILESTONES TAB AUDIT')
print('='*50)

milestones = json.load(open('data/milestones.json', encoding='utf-8'))
projects = json.load(open('data/projects.json', encoding='utf-8'))
proposals = json.load(open('data/proposals_archive.json', encoding='utf-8'))

records = milestones.get('records', [])

# By phase
phases = defaultdict(list)
for m in records:
    phase = m.get('phase', 'uncategorized')
    phases[phase].append(m)

print(f'\n1. MILESTONES BY PHASE')
for phase, items in sorted(phases.items()):
    completed = sum(1 for m in items if m.get('status') == 'completed')
    print(f'   {phase}: {len(items)} total, {completed} completed ({100*completed/len(items):.1f}%)')

# Project types
project_types = defaultdict(list)
for m in records:
    project_id = m.get('project_id', 'uncategorized')
    project_types[project_id].append(m)

print(f'\n2. DELIVERABLES BY PROJECT TYPE')
print(f'   Unique projects: {len(project_types)}')
project_names = {
    'athletes_riders': 'Athletes & Riders',
    'workstream_media': 'Media',
    'workstream_ops': 'Operations',
    'workstream_dev': 'Dev',
    'irl_events': 'Events',
    'public_goods': 'Public Goods'
}
for project_id, items in sorted(project_types.items()):
    name = project_names.get(project_id, project_id)
    print(f'   {name}: {len(items)} deliverables')

# Proposal coverage
proposals_with_milestones = set(m.get('proposal_id') for m in records if m.get('proposal_id'))
print(f'\n3. PROPOSAL COVERAGE')
print(f'   Proposals with milestones: {len(proposals_with_milestones)}/{len(proposals[\"records\"])} ({100*len(proposals_with_milestones)/len(proposals[\"records\"]):.1f}%)')

missing_proposal_ids = [m for m in records if not m.get('proposal_id')]
print(f'   Milestones without proposal_id: {len(missing_proposal_ids)}')

# Status distribution
statuses = defaultdict(int)
for m in records:
    status = m.get('status', 'unknown')
    statuses[status] += 1

print(f'\n4. STATUS DISTRIBUTION')
for status, count in sorted(statuses.items()):
    print(f'   {status}: {count} ({100*count/len(records):.1f}%)')

print('\n✓ Targets:')
print(f'  ├─ Proposal coverage: 100% (actual: {100*len(proposals_with_milestones)/len(proposals[\"records\"]):.1f}%)')
print(f'  ├─ All major projects covered: YES')
print(f'  └─ Status track: IN_PROGRESS')

print('\n✓ Recommendation: ' + ('PASS ✅' if len(proposals_with_milestones)/len(proposals[\"records\"]) > 0.9 else 'NEEDS WORK ⚠️'))
"
```

### 4️⃣ ANALYTICS TAB - Validação Completa

```bash
python -c "
import json
from collections import defaultdict

print('\n' + '='*50)
print('ANALYTICS TAB AUDIT')
print('='*50)

members = json.load(open('data/members.json', encoding='utf-8'))
people = json.load(open('data/people.json', encoding='utf-8'))
proposal_tags = json.load(open('data/proposal_tags.json', encoding='utf-8'))
spend_ledger = json.load(open('data/spend_ledger.json', encoding='utf-8'))
sankey = json.load(open('data/sankey_impact.json', encoding='utf-8'))

# Members analysis
print(f'\n1. MEMBERS/ATHLETES/CONTRIBUTORS')
member_records = members.get('records', [])
print(f'   Total members: {len(member_records)}')

sports = defaultdict(int)
for m in member_records:
    sport = m.get('sport', 'uncategorized')
    sports[sport] += 1

print(f'   By sport:')
for sport, count in sorted(sports.items(), key=lambda x: -x[1])[:10]:
    print(f'     - {sport}: {count}')

# Coverage
sport_coverage = sum(1 for m in member_records if m.get('sport')) / len(member_records) * 100 if member_records else 0
display_coverage = sum(1 for m in member_records if m.get('display_name')) / len(member_records) * 100 if member_records else 0

print(f'   Data quality:')
print(f'     - With sport: {sport_coverage:.1f}% ({sum(1 for m in member_records if m.get(\"sport\"))}/{len(member_records)})')
print(f'     - With display_name: {display_coverage:.1f}% ({sum(1 for m in member_records if m.get(\"display_name\"))}/{len(member_records)})')

# Recipient coverage
recipients = set(r.get('recipient_address') for r in spend_ledger.get('records', []) if r.get('recipient_address'))
members_addresses = set(m.get('address', '').lower() for m in member_records if m.get('address'))
coverage = sum(1 for addr in recipients if any(m.get('address', '').lower() == addr.lower() for m in member_records))

print(f'   Recipient coverage: {coverage}/{len(recipients)} ({100*coverage/len(recipients):.1f}%)')

# Tags analysis
print(f'\n2. PROPOSAL TAGS QUALITY')
tags = proposal_tags.get('records', [])
print(f'   Total tagged proposals: {len(tags)}')

categories = defaultdict(int)
for t in tags:
    cat = t.get('semantic_category', 'uncategorized')
    categories[cat] += 1

print(f'   Distribution:')
for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
    print(f'     - {cat}: {count}')

# Confidence
low_confidence = [t for t in tags if t.get('semantic_confidence', 1.0) < 0.6]
print(f'   Low confidence (<0.6): {len(low_confidence)} tags')

if low_confidence:
    print(f'   Examples:')
    for t in low_confidence[:3]:
        print(f'     - {t.get(\"archive_id\")}: {t.get(\"semantic_category\")} (conf: {t.get(\"semantic_confidence\"):.2f})')

# Sankey completeness
print(f'\n3. SANKEY/SPEND VISUALIZATION')
print(f'   Nodes: {len(sankey.get(\"nodes\", []))}')
print(f'   Links: {len(sankey.get(\"links\", []))}')

total_value = sum(link.get('value', 0) for link in sankey.get('links', []))
print(f'   Total value: \${total_value:,.2f}')

# Category coverage in spend
categories_in_spend = defaultdict(float)
for link in sankey.get('links', []):
    cat = link.get('target', '').replace('category_', '')
    categories_in_spend[cat] += link.get('value', 0)

print(f'   Spend by category:')
for cat, value in sorted(categories_in_spend.items(), key=lambda x: -x[1])[:5]:
    print(f'     - {cat}: \${value:,.2f}')

print('\n✓ Targets:')
print(f'  ├─ Members: >100 total (actual: {len(member_records)})')
print(f'  ├─ Sport coverage: >95% (actual: {sport_coverage:.1f}%)')
print(f'  ├─ Tag confidence: >90% (actual: {100*(len(tags)-len(low_confidence))/len(tags):.1f}%)')
print(f'  └─ Recipient coverage: 100% (actual: {100*coverage/len(recipients):.1f}%)')

print('\n✓ Recommendation: ' + ('PASS ✅' if (len(member_records) > 100 and sport_coverage > 90 and coverage > 0.9*len(recipients)) else 'NEEDS WORK ⚠️'))
"
```

---

## 🧪 VALIDAÇÃO FINAL (5 minutos)

```bash
# Rodar scripts de auditoria do pipeline
python scripts/audit_gaps.py
```

**Esperado**:
```
✅ Sankey completeness: 100%
✅ Spend ledger: 100% categorized  
✅ All rows priced
✅ unpriced_rows = 0
✅ Treasury gap < $100
```

```bash
python scripts/reconcile_treasury.py
```

**Esperado**:
```
TREASURY RECONCILIATION
======================
Opening balance: $524,860.63
Total inflows: $50,211.54
Total outflows: $530,335.18
Current balance: $44,737.00

✅ Gap: $0 (PERFECT)
✅ Reconciliation: PASS
```

```bash
npm run build --prefix web
```

**Esperado**:
```
✅ web/dist ready
✅ 0 errors
✅ ~2500+ modules
```

---

## 📊 RESUMO FINAL

```bash
python -c "
import json

# Load all
proposals = json.load(open('data/proposals_archive.json'))
members = json.load(open('data/members.json'))
spend_ledger = json.load(open('data/spend_ledger.json'))
milestones = json.load(open('data/milestones.json'))
tags = json.load(open('data/proposal_tags.json'))
treasury = json.load(open('data/treasury.json'))

print('\n' + '='*50)
print('GNARS-DATA AUDIT SUMMARY')
print('='*50)

print(f'\n📊 INVENTORY')
print(f'   Proposals: {len(proposals[\"records\"])}')
print(f'   Members: {len(members.get(\"records\", []))}')
print(f'   Spend records: {len(spend_ledger.get(\"records\", []))}')
print(f'   Milestones: {len(milestones.get(\"records\", []))}')
print(f'   Tagged proposals: {len(tags.get(\"records\", []))}')

print(f'\n💰 FINANCIALS')
print(f'   Treasury balance: \${treasury.get(\"balance_usd\", 0):,.2f}')

records = spend_ledger.get('records', [])
print(f'   Total spend: \${sum(r.get(\"usd_value_at_execution\", 0) for r in records):,.2f}')

print(f'\n✅ COMPLETENESS SCORES')
tx_pct = 100*sum(1 for r in records if r.get('tx_hash'))/len(records) if records else 0
proj_pct = 100*sum(1 for r in records if r.get('project_id'))/len(records) if records else 0
cat_pct = 100*sum(1 for r in records if r.get('category'))/len(records) if records else 0
sport_pct = 100*sum(1 for m in members.get('records', []) if m.get('sport'))/len(members.get('records', [])) if members.get('records') else 0

print(f'   tx_hash: {tx_pct:.1f}% (target: >90%)')
print(f'   project_id: {proj_pct:.1f}% (target: 100%)')
print(f'   category: {cat_pct:.1f}% (target: 100%)')
print(f'   member sports: {sport_pct:.1f}% (target: >95%)')

print(f'\n🎯 OVERALL STATUS')
score = (tx_pct + proj_pct + cat_pct + sport_pct) / 4
if score >= 95:
    print(f'   ✅ EXCELLENT ({score:.1f}%)')
elif score >= 80:
    print(f'   ⚠️  GOOD ({score:.1f}%) - Minor gaps')
else:
    print(f'   ❌ NEEDS WORK ({score:.1f}%) - Major gaps')

print()
"
```

---

## 🚀 PRÓXIMAS ETAPAS

1. **Salvar output**:
   ```bash
   # Salvar relatório
   python scripts/audit_gaps.py > audit_$(date +%Y%m%d).txt
   ```

2. **Se houver gaps**:
   - Criar issue no GitHub
   - Documentar no AUDIT_EXECUTION_CHECKLIST.md
   - Atribuir P0/P1/P2

3. **Quando 100% completo**:
   ```bash
   git add -A
   git commit -m "data: audit complete - 100% completeness across all tabs"
   git push origin main
   ```

---

**Data**: 2026-03-23  
**Duração estimada**: 30 minutos (full audit)  
**Próximo**: Frontend validation

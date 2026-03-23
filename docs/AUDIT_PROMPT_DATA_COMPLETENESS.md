# GNARS-DATA AUDIT PROMPT - Data Completeness & Quality

## Objetivo
Auditoria completa de dados para garantir que 100% dos gráficos, tabs e listas estejam completos, precisos e refletindo a realidade do DAO Gnars.

**Escopo**: Apenas dados/JSON - SEM alterações de front-end/React

---

## 1. VOTES TAB AUDIT

### 1.1 Verificar Cobertura de Votação

**Executar**:
```bash
python -c "
import json

# Load data
proposals = json.load(open('data/proposals_archive.json', encoding='utf-8'))
snapshot_votes = json.load(open('data/snapshot_votes.json', encoding='utf-8'))

# Count proposals by chain
base_props = [p for p in proposals['records'] if p.get('chain') == 'base']
eth_props = [p for p in proposals['records'] if p.get('chain') == 'ethereum']
snapshot_props = [p for p in proposals['records'] if p.get('chain') == 'snapshot']

# Check vote coverage
props_with_votes = [p for p in proposals['records'] if p.get('votes') and len(p['votes']) > 0]

print(f'VOTE COVERAGE ANALYSIS')
print(f'===================')
print(f'Total proposals: {len(proposals[\"records\"])}')
print(f'  - Base: {len(base_props)} ({100*len(base_props)/len(proposals[\"records\"]):.1f}%)')
print(f'  - Ethereum: {len(eth_props)} ({100*len(eth_props)/len(proposals[\"records\"]):.1f}%)')
print(f'  - Snapshot: {len(snapshot_props)} ({100*len(snapshot_props)/len(proposals[\"records\"]):.1f}%)')
print()
print(f'Proposals with vote data: {len(props_with_votes)}/{len(proposals[\"records\"])} ({100*len(props_with_votes)/len(proposals[\"records\"]):.1f}%)')
print()

# Check vote quality
vote_data_issues = []
for p in proposals['records']:
    votes = p.get('votes', [])
    if votes:
        has_voter = sum(1 for v in votes if v.get('voter'))
        has_reason = sum(1 for v in votes if v.get('reason'))
        vote_data_issues.append({
            'proposal_id': p.get('archive_id'),
            'total_votes': len(votes),
            'with_voter': has_voter,
            'with_reason': has_reason
        })

if vote_data_issues:
    print('Sample vote quality:')
    for issue in vote_data_issues[:3]:
        print(f'  {issue[\"proposal_id\"]}: {issue[\"total_votes\"]} votes, {issue[\"with_voter\"]}/{issue[\"total_votes\"]} have voter, {issue[\"with_reason\"]}/{issue[\"total_votes\"]} have reason')
"
```

### 1.2 Validar Vote Reasons & Sentiment

**Checklist**:
- [ ] Vote reasons preenchidos para >80% de votos?
- [ ] Sentiment detectado (support/against/abstain)?
- [ ] Voting power registrado por voto?
- [ ] Timestamps de cada voto presentes?

**Ação Necessária**:
```json
// Esperado em data/snapshot_votes.json
{
  "voter": "0x...",
  "proposal_id": "snapshot-0x...",
  "choice": "For|Against|Abstain",
  "voting_power": 1.5,
  "reason": "community funding is critical",
  "timestamp": "2026-03-20T15:30:00Z",
  "chain": "snapshot"
}
```

### 1.3 Proposal Vote Mismatch

**Validar**:
```bash
# Proposals sem votos quando esperado
jq '[.records[] | select(.status=="active" or .status=="executed") | select(.votes | length == 0)]' data/proposals_archive.json
```

---

## 2. TREASURY TAB AUDIT

### 2.1 Completude de Transações

**Executar**:
```bash
python -c "
import json

treasury = json.load(open('data/treasury.json', encoding='utf-8'))
treasury_flows = json.load(open('data/treasury_flows.json', encoding='utf-8'))
spend_ledger = json.load(open('data/spend_ledger.json', encoding='utf-8'))

print('TREASURY COMPLETENESS')
print('===================')
print(f'Current balance: \${treasury.get(\"balance_usd\", 0):,.2f}')
print(f'Historical inflows: {len([t for t in treasury_flows.get(\"records\", []) if t.get(\"type\") == \"in\"  ])}')
print(f'Historical outflows: {len([t for t in treasury_flows.get(\"records\", []) if t.get(\"type\") == \"out\"])}')
print()

# Spend ledger validation
print('SPEND LEDGER VALIDATION')
print('===================')
records = spend_ledger.get('records', [])
print(f'Total records: {len(records)}')
print(f'  - With tx_hash: {sum(1 for r in records if r.get(\"tx_hash\"))} ({100*sum(1 for r in records if r.get(\"tx_hash\"))/len(records):.1f}%)')
print(f'  - With project_id: {sum(1 for r in records if r.get(\"project_id\"))} ({100*sum(1 for r in records if r.get(\"project_id\"))/len(records):.1f}%)')
print(f'  - With category: {sum(1 for r in records if r.get(\"category\"))} ({100*sum(1 for r in records if r.get(\"category\"))/len(records):.1f}%)')
print(f'  - With recipient: {sum(1 for r in records if r.get(\"recipient_address\"))} ({100*sum(1 for r in records if r.get(\"recipient_address\"))/len(records):.1f}%)')
print()

# Missing fields (Critical)
critical_missing = [r for r in records if not r.get('tx_hash') or not r.get('project_id')]
print(f'⚠️  Critical gaps: {len(critical_missing)} records missing tx_hash or project_id')
"
```

### 2.2 Treasury Reconciliation Status

**Validar**:
```bash
cat reports/reconciliation.json | jq '.'
```

**Esperado**:
```json
{
  "reconciled": true,
  "gap_usd": 0,
  "treasury_balance_usd": 44737,
  "funding_in_usd": 50223,
  "spend_out_usd": 530335
}
```

### 2.3 Verificar Saldos por Token

**Checklist**:
- [ ] Base USDC balance validado em BaseScan?
- [ ] ETH balance atual?
- [ ] Outros tokens/NFTs contabilizados?
- [ ] Histórico de balances para cada mês?

---

## 3. MILESTONES TAB AUDIT

### 3.1 Fases de Delivery

**Executar**:
```bash
python -c "
import json

timeline = json.load(open('data/timeline_events.json', encoding='utf-8'))
milestones = json.load(open('data/milestones.json', encoding='utf-8'))

print('MILESTONES COMPLETENESS')
print('====================')

# Count by phase
phases = {}
for m in milestones.get('records', []):
    phase = m.get('phase', 'unknown')
    phases[phase] = phases.get(phase, 0) + 1

print(f'Total milestones: {len(milestones.get(\"records\", []))}')
print('By phase:')
for phase, count in sorted(phases.items()):
    print(f'  - {phase}: {count}')
print()

# Missing deliverables
incomplete = [m for m in milestones.get('records', []) if m.get('status') != 'completed']
print(f'Incomplete/In-progress: {len(incomplete)}')
print()

# Timeline events
print(f'Timeline events: {len(timeline.get(\"records\", []))}')
"
```

### 3.2 Deliverables Mapeados

**Validar por Proposta**:
```bash
python -c "
import json

proposals = json.load(open('data/proposals_archive.json', encoding='utf-8'))
milestones = json.load(open('data/milestones.json', encoding='utf-8'))

# Map proposals to deliverables
print('PROPOSAL → DELIVERABLE MAPPING')
print('============================')

proposal_deliverables = {}
for m in milestones.get('records', []):
    prop_id = m.get('proposal_id', m.get('project_id'))
    if prop_id:
        if prop_id not in proposal_deliverables:
            proposal_deliverables[prop_id] = []
        proposal_deliverables[prop_id].append(m.get('deliverable', m.get('title')))

props_with_deliverables = len([p for p in proposals['records'] if p.get('archive_id') in proposal_deliverables])
print(f'Proposals with deliverables mapped: {props_with_deliverables}/{len(proposals[\"records\"])} ({100*props_with_deliverables/len(proposals[\"records\"]):.1f}%)')
print()

# Show examples
print('Sample mappings:')
for prop_id, deliverables in list(proposal_deliverables.items())[:5]:
    print(f'  {prop_id}:')
    for d in deliverables:
        print(f'    → {d}')
"
```

### 3.3 Projetos Executados

**CRÍTICO**: Validar cada entrada em `data/projects.json`:

```bash
python -c "
import json

projects = json.load(open('data/projects.json', encoding='utf-8'))

print('PROJECTS EXECUTION AUDIT')
print('========================')

for project in projects.get('records', [])[:10]:  # Primeiros 10
    print(f'\n📌 {project.get(\"name\")}')
    print(f'   Project ID: {project.get(\"id\")}')
    print(f'   Status: {project.get(\"status\")}')
    print(f'   Funding: \${project.get(\"total_funding_usd\", 0):,.2f}')
    print(f'   Proposal: {project.get(\"proposal_id\")}')
    print(f'   Deliverables: {len(project.get(\"deliverables\", []))}')
    print(f'   Execution %: {project.get(\"execution_percentage\", 0):.0f}%')
"
```

**Espera-se**:
- [ ] NogglesRails (Skate park infrastructure)
- [ ] Onboarding (Community education)
- [ ] Media (Content creation)
- [ ] Dev (Infrastructure/tooling)
- [ ] Events (IRL competitions)
- [ ] Public Goods (Ecosystem support)

---

## 4. ANALYTICS TAB - COMPLETENESS

### 4.1 Members/Athletes/Contributors List

**Executa**:
```bash
python -c "
import json

members = json.load(open('data/members.json', encoding='utf-8'))
people = json.load(open('data/people.json', encoding='utf-8'))
spend_ledger = json.load(open('data/spend_ledger.json', encoding='utf-8'))

print('MEMBERS & CONTRIBUTORS AUDIT')
print('===========================')
print(f'Total members: {len(members.get(\"records\", []))}')

# By sport
sports = {}
for m in members.get('records', []):
    sport = m.get('sport', 'uncategorized')
    sports[sport] = sports.get(sport, 0) + 1

print('\nBreakdown by sport:')
for sport, count in sorted(sports.items(), key=lambda x: -x[1]):
    print(f'  {sport}: {count}')

# Active recipients (received funding)
recipients = set(r.get('recipient_address') for r in spend_ledger.get('records', []))
print(f'\nActive recipients (with spending): {len(recipients)}')

# Coverage
recipients_in_members = sum(1 for addr in recipients if any(m.get('address', '').lower() == addr.lower() for m in members.get('records', [])))
print(f'Coverage: {recipients_in_members}/{len(recipients)} ({100*recipients_in_members/len(recipients):.1f}% have member records)')

# Missing data checks
print('\nDATA QUALITY ISSUES:')
missing_sport = sum(1 for m in members.get('records', []) if not m.get('sport'))
missing_display = sum(1 for m in members.get('records', []) if not m.get('display_name'))
missing_address = sum(1 for m in members.get('records', []) if not m.get('address'))

print(f'  - Members without sport: {missing_sport}')
print(f'  - Members without display_name: {missing_display}')
print(f'  - Members without address: {missing_address}')
"
```

**Ações**:
- [ ] Completar `members.json` com todos os recipients
- [ ] Adicionar sport/categoria para cada um
- [ ] Validar display_name (use ENS ou wallet_name)
- [ ] Link com social profiles (Twitter, Instagram, etc)

### 4.2 Category Tags Validation

**Executar**:
```bash
python -c "
import json

tags = json.load(open('data/proposal_tags.json', encoding='utf-8'))
spend_ledger = json.load(open('data/spend_ledger.json', encoding='utf-8'))

print('CATEGORY TAGS VALIDATION')
print('=======================')

# Distribution
categories = {}
for t in tags.get('records', []):
    cat = t.get('semantic_category', 'uncategorized')
    categories[cat] = categories.get(cat, 0) + 1

print('Category distribution:')
for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
    print(f'  {cat}: {count}')

print()

# Spot check errors
print('POTENTIAL TAG ISSUES:')
issues = [t for t in tags.get('records', []) if t.get('semantic_confidence', 1.0) < 0.6]
print(f'  Low confidence tags (<0.6): {len(issues)}')
if issues:
    print('    Examples:')
    for issue in issues[:3]:
        print(f'      - {issue.get(\"archive_id\")}: {issue.get(\"semantic_category\")} (confidence: {issue.get(\"semantic_confidence\", 0):.2f})')
"
```

### 4.3 Spend by Category Completeness

**Validar**:
```bash
python -c "
import json

sankey = json.load(open('data/sankey_impact.json', encoding='utf-8'))
spend_ledger = json.load(open('data/spend_ledger.json', encoding='utf-8'))

print('SPEND DISTRIBUTION')
print('==================')

# Total spend by category in Sankey
if 'nodes' in sankey and 'links' in sankey:
    print(f'Sankey nodes: {len(sankey[\"nodes\"])}')
    print(f'Sankey links (flows): {len(sankey[\"links\"])}')
    
    # Link values
    total_value = sum(link.get('value', 0) for link in sankey['links'])
    print(f'Total value: \${total_value:,.2f}')

# Validation
ledger_total = sum(r.get('usd_value_at_execution', 0) for r in spend_ledger.get('records', []))
print(f'Spend ledger total: \${ledger_total:,.2f}')
"
```

---

## 5. COMPREHENSIVE DATA QUALITY CHECKLIST

### 5.1 Proposals
- [ ] Todos os 222 proposals têm `archive_id` único
- [ ] Todos têm `chain` (base/ethereum/snapshot)
- [ ] Todos têm `status` (active/executed/defeated/cancelled)
- [ ] Timestamps válidos (created_at, end_at, executed_at)
- [ ] Proposer address válida
- [ ] Título sem caracteres corrompidos
- [ ] Links (source_url, explorer_url) funcionais

### 5.2 Votes
- [ ] >90% de proposals têm vote data
- [ ] Cada voto tem (voter, choice, timestamp)
- [ ] Voting power registrado
- [ ] Vote reasons para >70% de votos
- [ ] Sem duplicatas de voto

### 5.3 Spend Ledger
- [ ] 100% com `amount` válido
- [ ] 100% com `usd_value_at_execution`
- [ ] >90% com `tx_hash` verificável
- [ ] 100% com `project_id`
- [ ] 100% com `category` (athletes_riders, media, ops, dev, events)
- [ ] 100% com `recipient_address`
- [ ] Sem valores negativos/corrompidos

### 5.4 Members
- [ ] Cobertura: Todos os recipients têm entry
- [ ] >95% com `sport` preenchido
- [ ] >90% com `display_name`
- [ ] Sem endereços duplicados
- [ ] Links ENS para profiles públicos

### 5.5 Milestones/Deliverables
- [ ] Cada proposal com deliverables mapeados
- [ ] Status (not_started/in_progress/completed)
- [ ] Completion % para cada um
- [ ] Entregáveis mapeados ao projeto (NogglesRails, etc)

### 5.6 Treasury
- [ ] Balance reconciliado (ledger = current)
- [ ] 100% de transações com tx_hash
- [ ] Histórico de balances (daily snapshots)
- [ ] Inflows e outflows balanceados

---

## 6. RELATÓRIO DE SAÍDA

**Executar ao final**:
```bash
python scripts/audit_gaps.py
python scripts/reconcile_treasury.py
```

**Esperado**: 
- ✅ Sankey coverage = 100%
- ✅ Reconciliation gap < $100
- ✅ All records priced
- ✅ Category coverage = 100%

---

## 7. AÇÕES PRIORITÁRIAS

### P0 (CRÍTICO - Hoje)
- [ ] Validar todas as tags são semântica correta
- [ ] Completar list de todos recipients em members.json
- [ ] Verificar spend ledger para valores corrompidos

### P1 (Alto - Esta semana)
- [ ] Preencher missing sports em members.json
- [ ] Validar vote data em proposals >80%
- [ ] Mapear todos deliverables por proposal

### P2 (Médio - Próxima semana)
- [ ] Enriquecer member profiles (Twitter, Instagram)
- [ ] Adicionar descriptions para cada milestone
- [ ] Validar tx_hash em 90%+ de spend records

### P3 (Baixo - Próximo mês)
- [ ] Add proposal execution timeline (delay analysis)
- [ ] Historical contributor retention metrics
- [ ] Impact scoring para cada deliverable

---

## 8. COMO USAR ESTE PROMPT

1. **Copiar blocos de código** do audit (seções 1-5)
2. **Executar cada script** para identificar gaps
3. **Documentar achados** em spreadsheet/Notion
4. **Priorizar fixes** por P0/P1/P2
5. **Fazer PRs** com correções de dados
6. **Re-rodar audit_gaps.py** para validar

---

## EXEMPLO: Estrutura de PR para Fix

```
Title: data: complete members list + fix category tags

## Changes
- Added 15 missing members from spend_ledger recipients
- Fixed 8 incorrect semantic_category tags
- Validated all member sports assignments
- Updated members.json display_names with ENS resolution

## Validation
- audit_gaps.py: PASS (0 gaps)
- reconcile_treasury.py: gap = $0
- Spend coverage: 100%
- Category coverage: 100%

## Files Changed
- data/members.json (+15 records)
- data/proposal_tags.json (8 corrections)
```

---

**Última atualização**: 2026-03-23  
**Status**: Pronto para auditoria completa

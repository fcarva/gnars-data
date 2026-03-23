# GNARS-DATA AUDIT EXECUTION CHECKLIST

**Objetivo**: 100% completude de dados para Votes, Treasury, Milestones e Analytics  
**Data Início**: 2026-03-23  
**Target**: 2026-03-30

---

## 📋 FASE 1: DIAGNÓSTICO (Dia 1-2)

### 1.1 VOTES TAB Diagnosis
- [ ] Executar vote coverage script (seção 1.1)
  - Target: >95% proposals com vote data
  - Atual: ____%
  - Gap: ___ proposals
  
- [ ] Validar vote quality (seção 1.2)
  - [ ] Vote reasons: ___/total (alvo: >80%)
  - [ ] Voting power: ___/total (alvo: 100%)
  - [ ] Timestamps: ___/total (alvo: 100%)
  
- [ ] Documentar achados
  - Issue: ___
  - Raiz: ___
  - Fix: ___

### 1.2 TREASURY TAB Diagnosis
- [ ] Executar spend ledger validation (seção 2.1)
  - tx_hash: ___/total (alvo: >90%)
  - project_id: ___/total (alvo: 100%)
  - category: ___/total (alvo: 100%)
  - recipient: ___/total (alvo: 100%)
  
- [ ] Validar reconciliação (seção 2.2)
  - Gap: $_____ (alvo: <$100)
  - Status: ✅/⚠️
  
- [ ] Documentar achados

### 1.3 MILESTONES TAB Diagnosis
- [ ] Executar fases de delivery (seção 3.1)
  - Total milestones: ____
  - Fase mais vazia: _____ (___projetos)
  - Completude: ___%
  
- [ ] Validar projeto executados (seção 3.3)
  - [ ] NogglesRails: ____ deliverables
  - [ ] Onboarding: ____ deliverables
  - [ ] Media: ____ deliverables
  - [ ] Dev: ____ deliverables
  - [ ] Events: ____ deliverables
  - [ ] Public Goods: ____ deliverables
  
- [ ] Documentar achados

### 1.4 ANALYTICS TAB Diagnosis
- [ ] Executar members audit (seção 4.1)
  - Total members: ____
  - Com sport: __% (alvo: >95%)
  - Com display_name: __% (alvo: >90%)
  - Cobertura de recipients: __% (alvo: 100%)
  
- [ ] Validar tags (seção 4.2)
  - Low confidence tags: ____
  - Inconsistências detectadas: ____
  
- [ ] Documentar achados

---

## 🔧 FASE 2: CORREÇÕES (Dia 3-6)

### P0 - CRÍTICO (Hoje)

#### Correção 1: Members List Completeness
```
Issue: ___ recipients sem entry em members.json
Status: [ ] Not Started [ ] In Progress [ ] Complete
Fix:
  - [ ] Identificar missing recipients
  - [ ] Extrair dados públicos (ENS, Twitter)
  - [ ] Adicionar a members.json
  - [ ] Validar coverage = 100%
  
PR: ____ (link)
Validation: audit_gaps.py = ✅
```

#### Correção 2: Category Tags Validation
```
Issue: ___ tags com confidence <0.6
Status: [ ] Not Started [ ] In Progress [ ] Complete
Fix:
  - [ ] Revisar cada low-confidence tag
  - [ ] Corrigir semantic_category
  - [ ] Re-treinar se necessário
  
PR: ____ (link)
Validation: category coverage = 100% ✅
```

#### Correção 3: Spend Ledger Gaps
```
Issue: ___ records sem tx_hash ou project_id
Status: [ ] Not Started [ ] In Progress [ ] Complete
Fix:
  - [ ] Validar tx_hash em BaseScan
  - [ ] Preencher project_id faltando
  - [ ] Resolver 2+ valores corrompidos
  
PR: ____ (link)
Validation: exec% >90%, project%=100% ✅
```

---

### P1 - ALTO (Esta semana)

#### Correção 4: Vote Data Quality
```
Issue: ___ proposals sem vote reasons
Status: [ ] Not Started [ ] In Progress [ ] Complete
Fix:
  - [ ] Extrair de Snapshot/forum
  - [ ] Parsing de reasons automatizado
  - [ ] Manual review para > 70%
  
PR: ____ (link)
Validation: reason coverage = __% ✅
```

#### Correção 5: Milestones/Deliverables Mapping
```
Issue: ___ proposals sem deliverables mapeados
Status: [ ] Not Started [ ] In Progress [ ] Complete
Fix:
  - [ ] Mapear cada proposal → projeto
  - [ ] Preencher milestone data
  - [ ] Validar completion % em cada um
  
PR: ____ (link)
Validation: ALL proposals have milestones ✅
```

#### Correção 6: Member Sports/Categories
```
Issue: ___ members sem sport preenchido
Status: [ ] Not Started [ ] In Progress [ ] Complete
Fix:
  - [ ] Validar via social profiles
  - [ ] Classificar por visual (fotos)
  - [ ] Research community discord
  
PR: ____ (link)
Validation: sport coverage = >95% ✅
```

---

### P2 - MÉDIO (Próxima semana)

#### Correção 7: Treasury tx_hash Enrichment
```
Issue: ___ tx_hash missing em spend_ledger
Status: [ ] Not Started [ ] In Progress [ ] Complete
Fix:
  - [ ] Query BaseScan para USDC transfers
  - [ ] Correlate com recipient + amount
  - [ ] Fallback: Dune query archives
  
PR: ____ (link)
Validation: tx_hash coverage = >90% ✅
```

#### Correção 8: Member Profile Enrichment
```
Issue: Missing Twitter, Instagram, ENS profiles
Status: [ ] Not Started [ ] In Progress [ ] Complete
Fix:
  - [ ] Resolver ENS names
  - [ ] Scrape Twitter profiles
  - [ ] Manual verification
  
PR: ____ (link)
Validation: >80% members have social links ✅
```

---

## ✅ FASE 3: VALIDAÇÃO (Dia 6+)

### Full Audit Suite
```bash
python scripts/audit_gaps.py
→ Expected: 
  ✅ Sankey coverage = 100%
  ✅ spend_ledger = 100% categorized
  ✅ All rows priced
  ✅ unpriced_rows = 0

python scripts/reconcile_treasury.py
→ Expected:
  ✅ gap_usd < $100
  ✅ adjusted_gap = 0
  ✅ All transactions linked
```

### Data Quality Scorecard
```
VOTES
  ├─ Coverage: ___% (target: >95%)
  ├─ Vote quality: ___% (target: >80%)
  └─ Status: [ ] Pass [ ] Needs Work

TREASURY
  ├─ tx_hash: ___% (target: >90%)
  ├─ project_id: ___% (target: 100%)
  ├─ category: ___% (target: 100%)
  └─ Status: [ ] Pass [ ] Needs Work

MILESTONES
  ├─ Proposals covered: ___% (target: 100%)
  ├─ Deliverables mapped: ___% (target: 100%)
  └─ Status: [ ] Pass [ ] Needs Work

ANALYTICS
  ├─ Members: ___/total (target: +100% recipients)
  ├─ Sports assigned: ___% (target: >95%)
  ├─ Tags confidence: ___% (target: >90%)
  └─ Status: [ ] Pass [ ] Needs Work

Overall Compliance: __% (target: 100%)
```

### Frontend Readiness
```
[ ] npm run build --prefix web → PASS
[ ] All /data/*.json endpoints valid
[ ] Sankey loads w/ 100% data
[ ] Members list renders >100 items
[ ] Vote analysis complete
[ ] Treasury reconciled
```

---

## 📊 MÉTRICAS DE SUCESSO

| Métrica | Baseline | Target | Status |
|---------|----------|--------|--------|
| Proposals com votes | __% | >95% | ⏳ |
| Vote quality (reasons) | __% | >80% | ⏳ |
| Spend ledger completude | __% | 100% | ⏳ |
| tx_hash coverage | __% | >90% | ⏳ |
| Treasury reconciliation | $____ gap | <$100 | ⏳ |
| Members cobertura | __% | 100% | ⏳ |
| Members com sport | __% | >95% | ⏳ |
| Category tags | __% | 100% | ⏳ |
| Milestones mapeados | __% | 100% | ⏳ |
| **Overall** | __% | **100%** | ⏳ |

---

## 📝 NOTAS & BLOCKERS

```
Blocker 1:
  Descrição: ___
  Impact: ___
  Fix: ___
  Status: [ ] Open [ ] Resolved
  
Blocker 2:
  ...
```

---

## 🎯 PRÓXIMOS PASSOS

**Após 100% completude de dados:**
1. Deploy pipeline com dados corretos
2. Frontend validar todos gráficos renderizam
3. QA checklist: Votes, Treasury, Milestones, Analytics
4. Publicar relatório final de compliance

**Timeline**:
- [ ] Dia 1-2: Diagnóstico completo
- [ ] Dia 3-5: P0 + P1 fixes
- [ ] Dia 6: Validação full suite
- [ ] Dia 7: Deploy + QA
- [ ] **Dia 8**: 🚀 Release

---

**Status Geral**: ⏳ Em progresso  
**Última atualização**: 2026-03-23  
**Owner**: @fcarva

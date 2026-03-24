# GNARS-DATA AUDIT BASELINE REPORT
**Data**: 2026-03-23  
**Status**: 🔴 CRÍTICO - 22.6% geral

---

## 📊 Diagnóstico Automático

| Métrica | Atual | Target | Status | Gap |
|---------|-------|--------|--------|-----|
| **Votes** | 88.3% | >95% | ⚠️ | -6.7% |
| **Treasury** | 0.0% | 100% | ❌ | -100% |
| **Milestones** | 0.0% | 100% | ❌ | -100% |
| **Analytics** | 2.0% | >95% | ❌ | -93% |
| **OVERALL** | **22.6%** | **100%** | 🔴 | -77.4% |

---

## 🔍 PROBLEMA 1: TREASURY DATA ZEROED OUT (CRÍTICO)

### Achados
- `treasury.json` balance_usd = $0 (deveria ser ~$44,737)
- `spend_ledger.json` tem 129 records MAS **100% sem categoria**
- Todos os 129 registros têm categoria = MISSING

### Impacto
- Treasury Tab quebrada (sem saldo, sem gráficos)
- Sankey não renderiza
- Dashboards vazios

### Fix Necessário - P0 (HOJE)
```
[ ] Verificar se enrich_spend.py está sendo executado
[ ] Rodar: python scripts/enrich_spend.py --force
[ ] Validar: todas categorias preenchidas em spend_ledger
[ ] Re-gerar: treasury.json com balance correto
```

---

## 🔍 PROBLEMA 2: MILESTONES COMPLETELY EMPTY (CRÍTICO)

### Achados
- `milestones.json` tem 0 records (arquivo vazio)
- Nenhuma proposta tem deliverables mapeados
- Milestone coverage = 0/222 proposals

### Impacto
- Aba Milestones não funciona
- Sem tracking de fases de projeto
- Sem delivery timeline

### Fix Necessário - P0 (HOJE)
```
[ ] Criar script: build_milestones_from_proposals.py
[ ] Mapear proposals → milestones/deliverables
[ ] Preencher data/milestones.json
[ ] Validar coverage = 100%
```

---

## 🔍 PROBLEMA 3: MEMBERS SPORT DATA NEARLY EMPTY (CRÍTICO)

### Achados
- 1,180 membros total
- 98% com sport = None (vazio)
- Apenas 24 membros com sport preenchido:
  - sk8: 15
  - surf: 8
  - snow: 1

### Impacto
- Analytics lista incompleta
- Gráficos de esportes vazios
- Filter por sport não funciona

### Fix Necessário - P0 (HOJE)
```
[ ] Criar script: enrich_members_sport.py
[ ] Usar social profiles para classificar
[ ] Validar via visual (fotos em gnars.com)
[ ] Target: >95% com sport preenchido
```

---

## 🔍 PROBLEMA 4: VOTES DATA MISSING (ALTO)

### Achados
- 196/222 proposals com vote data (88.3%)
- 26 proposals faltando votes
- Principalmente em Base chain proposals

### Impacto
- Votes Tab - 11.7% incompleto
- Análise não pode ser feita

### Fix Necessário - P1 (ESTA SEMANA)
```
[ ] Query Snapshot GraphQL para proposals faltando
[ ] Validar BaseScan voting events (se houver)
[ ] Preencher vote_data em proposals_archive.json
[ ] Target: >95% coverage
```

---

## 📋 Próximos Passos (Prioritizados)

### P0 - HOJE (Crítico - Bloqueia Frontend)
- [ ] Fix Treasury (categoria = MISSING em 100%)
- [ ] Build Milestones (0 records em arquivo vazio)
- [ ] Populate Members Sport (98% vazio)

### P1 - ESTA SEMANA (Alto)
- [ ] Complete Votes Data (26 proposals faltando)
- [ ] Validar todas correções

### P2 - PRÓXIMO MÊS (Médio)
- [ ] Enriquecer profiles (Twitter, Instagram)
- [ ] Validar tags com confiança (alguns low-confidence)
- [ ] Reconciliar treasury

---

## 🎯 Conclusão

A auditoria identificou **4 problemas críticos** que precisam de fix imediato:

1. **Category field zerado** em spend_ledger (impede Treasury rendering)
2. **Milestones inexistente** (aba não funciona)
3. **Members sport vazio** (Analytics incompleta)
4. **Votes data missing** em 26 proposals (88.3% coverage)

**Score geral: 22.6%** → Precisa de trabalho urgente

---

**Arquivo de dados baseline**: `reports/audit_baseline.json`

**Próximo comando**: Rodar pipeline com força total para regenerar dados

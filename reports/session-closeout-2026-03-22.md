# GNARS.DATA - Encerramento de Sessao (2026-03-22)

## Resumo da sessao

### Antes desta sessao
- Site ao vivo com dados estaticos
- Pipeline sem reconciliacao onchain completa
- Leaderboard com 3 membros
- Treasury chart com escala quebrada
- Categorias exibindo keys internas

### Depois desta sessao
- Pipeline com dados onchain reais via Dune
- Leaderboard com 41 atletas
- Treasury chart com dual Y-axis
- 5 queries Dune integradas no fluxo
- AGENTS.md consolidado como playbook operacional

## Commits da sessao

| Commit | O que fez |
|---|---|
| 6563d29 | Sprint 7 - category labels, treasury chart fix, proof_record_count, reconcile datetime |
| b25de1a | Leaderboard - 41 atletas via pipeline, filtros null-safe, sport fallback |
| 789ac36 | Auction inflow series no chart, spend categories fix, FundingBreakdown |
| eb2ad8b | Dune integration - auction revenue, treasury history, vote participation onchain |

## Estado de reconciliacao

Auction revenue (Dune): 15.46 ETH = $50,223 USD  
Proposal spend (Dune): $191,981 USDC (37 proposals)  
Current treasury balance: $44,737  
Gap: -$186,495

Status: DISCREPANCY

### Causa principal do gap
- O dataset de auction revenue veio truncado (25 linhas)
- Historico esperado: 200+ auctions desde 2022
- Acao: remover limite/paginacao no fetch de resultados Dune

## Pendente nao commitado

- [ ] scripts/derive_funding_analysis.py modificado e nao commitado

Proxima acao sugerida:
1. git add scripts/derive_funding_analysis.py
2. git commit -m "fix: funding analysis auction integration"
3. git push origin main

## Sprint 8 - plano de execucao

### 0) Housekeeping
- Commitar pendencia em derive_funding_analysis.py
- Confirmar working tree limpo

### 1) Corrigir retorno completo nas 5 queries Dune
- IDs: 6881668, 6881718, 6881723, 6881732, 6881740
- Garantir historico completo (sem truncamento de 25 linhas)
- Reexecutar queries e rodar scripts/fetch_dune_data.py

### 2) Reconciliacao apos dados completos
- Rodar scripts/reconcile_treasury.py
- Meta: gap menor que $5,000

### 3) Preco historico de ETH no pipeline
- Ativar enrich de preco por transacao
- Rodar scripts/fetch_dune_data.py --with-prices

### 4) Criar e testar sync_snapshot.py
- Teste inicial rapido sem votos
- Validar data/snapshot_proposals.json e data/snapshot_votes.json

### 5) Deploy/check final
- Rodar scripts/refresh_all.py --derive-only
- Rodar npm run build --prefix web
- Revisar staging antes de push

## Checklist de inicio da proxima sessao

1. git status --short && git log --oneline -5
2. python scripts/audit_gaps.py
3. python scripts/reconcile_treasury.py
4. npm run build --prefix web
5. Conferir tamanhos em web/public/data/*.json
6. Conferir row counts em raw/dune/*.json
7. Commitar pendencia em scripts/derive_funding_analysis.py primeiro

## Arquitetura em funcionamento

### Pipeline Python
- sync_gnars.py
- sync_proposals.py
- sync_treasury.py
- fetch_dune_data.py (5 queries)
- classify_proposals_local.py
- enrich_members.py
- enrich_spend.py
- reconcile_treasury.py
- derive_analytics.py
- derive_funding_analysis.py

### Frontend React/Vite
- TreasuryChart (dual Y-axis, auction inflow)
- AnalyticsSankey (impact/workstream)
- AthletesLeaderboard (41 atletas)
- SportFundingTable
- FundingBreakdown
- VotesTable
- MilestonesTable
- ProposalsPage

### Dune queries
- 6881668 treasury_balance_over_time
- 6881718 auction_revenue_all_time (incompleto no momento)
- 6881723 proposal_spend_by_category
- 6881732 holders_over_time
- 6881740 vote_participation

Sessao encerrada em 2026-03-22.

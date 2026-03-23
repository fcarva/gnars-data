# AGENTS.md
**GNARS.DATA — Agent Instructions**
*Manter atualizado apos cada sprint. Lido automaticamente pelo Copilot ao abrir o workspace.*

---

## 1. Repositorio e produto

```
Repo:   github.com/fcarva/gnars-data
Site:   gnars-data.vercel.app (Vercel — auto-deploy em push para main)
Vault:  fcarva.github.io/gnars-data (GitHub Pages — CI daily-sync.yml)
Stack:  Python pipeline + React/Vite (web/)
```

### Fontes canonicas de dados (nao substituir sem decisao explicita)

| Arquivo | Responsabilidade |
|---|---|
| `data/contracts.json` | Registry de contratos verificados |
| `data/proposals_archive.json` | Archive completo de proposals |
| `data/sources.json` | Registry de fontes externas |
| `data/proposal_tags.json` | Classificacoes semanticas |
| `data/members.json` | Diretorio de membros enriquecido |
| `data/spend_ledger.json` | Todos os payouts |
| `data/treasury.json` | Holdings do treasury |
| `data/timeline_events.json` | Eventos cronologicos |

---

## 2. Contexto do projeto

**Gnars DAO** e um fork do Nouns DAO que financia atletas de action sports (skate, surf, BMX, snowboard) via leiloes de NFT e votacao onchain.

- **Era 1 — Ethereum** (~2022–2023): auctions e governance no mainnet
- **Era 2 — Base** (~Aug 2023–presente): migracao para Base L2
- **Voting offchain**: Snapshot space `gnars.eth` (ambas as eras)
- **Treasury atual**: ~$44k USDC · Peak: ~$312k (Jun 2024)

**Dois frontends:**
1. `web/` -> Vercel (produto principal — sempre priorizar)
2. `_site/` -> GitHub Pages (vault estatico — CI cuida, nao buildar manualmente)

**Deploy correto:**
```bash
npm run build --prefix web   # verificar
git push origin main          # Vercel deploya automaticamente
# NAO rodar build_site.py manualmente
```

**vercel.json** configura:
- Build: `cd web && npm run build` · Output: `web/dist`
- SPA rewrite: todas as rotas para `index.html`
- Cache: `index.html` sem cache · JS/CSS imutavel · `/data/*` sempre fresco

---

## 3. Pesquisa onchain

### Hierarquia de fontes

**Base e Ethereum (nesta ordem):**
1. Herd MCP ou Herd Explorer (se disponivel)
2. BaseScan / Etherscan
3. Sites e repositorios oficiais do projeto

**Polygon:**
1. PolygonScan + repositorios oficiais
2. Analytics de fallback (Herd pode ser insuficiente)

### Referencias de skill Ethereum

Consultar para trabalho orientado a Ethereum (mental models, nao dados especificos da Gnars):
```
https://ethskills.com/SKILL.md
https://ethskills.com/indexing/SKILL.md
https://ethskills.com/addresses/SKILL.md
https://ethskills.com/l2s/SKILL.md
https://ethskills.com/tools/SKILL.md
```

### Variaveis de ambiente necessarias

Ver `.env.example`. Nunca commitar valores reais.

```
GNARS_AUCTIONS_BASE_SUBGRAPH_URL
GNARS_AUCTIONS_ETHEREUM_SUBGRAPH_URL
GNARS_AUCTIONS_POLYGON_SUBGRAPH_URL
BASE_RPC_URL
DUNE_API_KEY
```

### Dune MCP (onchain analytics)

Usar quando precisar de dados onchain verificados (auctions, treasury transfers, precos historicos de ETH).

Setup:
- DUNE_API_KEY em `.env` (obter em dune.com/settings/api)
- MCP recomendado: `mcp-web3-stats` (Node)

Queries relevantes para Gnars:
- Gnars auctions Base: configurar ID em `data/sources.json` > `dune_queries`
- Gnars auctions Ethereum: configurar ID em `data/sources.json` > `dune_queries`
- Treasury USDC outflows Base: configurar ID em `data/sources.json` > `dune_queries`
- ETH prices historical: usar CoinGecko como fallback sem auth

Quando usar Dune MCP vs REST pipeline:
- MCP (interativo): explorar dados, criar queries, diagnosticar gaps
- REST API (`scripts/fetch_dune_data.py`): pipeline automatizado/CI

Hierarquia de confianca para valores USD:
1. Dune query com `prices.usd_daily`
2. CoinGecko history endpoint
3. ETH_PRICE constante (ultimo recurso)

---

## 4. Estrutura do repositorio

```
gnars-data/
|- config/                  # Catalogo de fontes e sync targets
|- data/                    # Dados normalizados (fonte de verdade)
|- docs/                    # Documentacao e archives de governance
|- exports/                 # CSVs gerados para BI
|- media/                   # Assets de marca
|- raw/                     # Snapshots brutos das APIs [NAO editar]
|  `- snapshot/
|     |- proposals.json
|     `- votes/
|- reports/                 # Relatorios gerados pelo pipeline
|  |- data_gaps.md
|  `- reconciliation.json
|- scripts/                 # Pipeline Python
|  |- sync_gnars.py
|  |- sync_proposals.py
|  |- sync_treasury.py
|  |- sync_snapshot.py      # [novo] Snapshot votes + proposals
|  |- classify_proposals_local.py
|  |- enrich_members.py
|  |- enrich_spend.py
|  |- reconcile_treasury.py # [novo]
|  |- derive_analytics.py
|  |- derive_funding_analysis.py
|  |- audit_gaps.py
|  |- export_csv.py
|  `- refresh_all.py        # [novo] Pipeline completo com DAG
|- web/                     # Frontend React/Vite -> Vercel
|  |- src/
|  |  |- components/
|  |  |- lib/format.ts      # fmtUSD fmtDate fmtRelative fmtETH
|  |  `- lib/gnars-data.ts  # Fetchers e tipos
|  |- public/data/          # JSONs servidos ao frontend
|  `- scripts/prepare-data.mjs
|- _site/                   # GitHub Pages [gerado pelo CI, nao editar]
|- AGENTS.md                # Este arquivo
|- gnars-data.agent.md      # Agent config para VS Code Copilot
|- .env.example
|- vercel.json
`- .github/workflows/
	 |- daily-sync.yml
	 `- weekly-votes-sync.yml # [novo]
```

**Ignorado pelo git:** `__pycache__/`, `.venv/`, `_site/`, `web/node_modules/`, `web/dist/`, `.vercel`

---

## 5. Invariantes do pipeline

1. **Nunca editar `raw/` manualmente** — gerado por scripts
2. **`data/` e fonte de verdade** — derivar sempre de `data/`, nunca de `raw/` direto
3. **Ordem obrigatoria:** `sync -> classify -> enrich -> reconcile -> derive -> export`
4. **Incremental por padrao** — so processar o que mudou
5. **Staleness check** — sync scripts pulam se arquivo < 6h. `--force` para bypass
6. **Reconciliar antes de derivar** — `reconcile_treasury.py` antes de `derive_analytics.py`
7. **Snapshot tem duas eras** — `created >= 1690000000` -> Base, senao -> Ethereum

### Modos de execucao

```bash
python scripts/refresh_all.py --derive-only   # ~30s
python scripts/refresh_all.py --incremental   # ~2-3 min
python scripts/refresh_all.py --force         # ~5-8 min
```

---

## 6. Invariantes do frontend

1. **Nunca hardcodar dados** — consumir de `/public/data/*.json`
2. **Formatacao via helpers** — `fmtUSD`, `fmtDate`, `fmtRelative`, `fmtETH` de `format.ts`
3. **Null safety** — todo fetch tem `.catch(() => [])` ou `.catch(() => null)`
4. **Build antes de commit** — `npm run build --prefix web` deve passar
5. **Deploy = push para main** — Vercel cuida do resto

---

## 7. Design — Flexoki Light

```
--pp:   #FFFEF8   background (paper white)
--b50:  #F9F8F2   superficies
--b100: #F4F2EC   KPI bar, headers
--b150: #E6E4D9   bordas padrao
--b500: #6F6E69   texto secundario
--b700: #403E3C   texto escuro
--b950: #1C1B1A   texto principal
```

Cores por categoria:
```
Athletes & Riders  cyan   #3AA99F / bg #DFF3F1
Media              purple #8B7EC8 / bg #EDE9FA
Operations         orange #DA702C / bg #FEF0E4
Dev                blue   #4385BE / bg #E8F4FF
Events             green  #879A39 / bg #EEF3D4
Danger/Against     red    #D14D41 / bg #FBE8E6
Warning/BMX        yellow #D0A215 / bg #FEF8D0
```

Tipografia:
```
Valores numericos:  'Courier New', monospace
Pills/badges:       font-size 7px, padding 2px 6px, border-radius 2px
Filter buttons:     font-size 7.5px, padding 3px 8px, border-radius 2px
Search bar:         border-radius 16px, input font-family system-ui
Cards:              border 1px solid var(--b150), background var(--pp)
```

---

## 8. Labels semanticas de categoria

Sempre usar labels legiveis — nunca expor keys internas:

```python
CATEGORY_LABELS = {
		"athletes_riders":   "Athletes & Riders",
		"workstream_media":  "Media",
		"workstream_ops":    "Operations",
		"workstream_dev":    "Dev",
		"irl_events":        "Events",
		"public_goods":      "Public Goods",
		"governance_policy": "Governance",
		"uncategorized":     "Other",
}
```

Aplicar em: `derive_analytics.py`, componentes React, tooltips, legends, CSV exports.

---

## 9. Checklist de auditoria (rodar ao iniciar sessao)

```bash
git status --short && git log --oneline -5

python scripts/audit_gaps.py
python scripts/reconcile_treasury.py

npm run build --prefix web 2>&1 | tail -20

python -c "
from pathlib import Path
files = [
	'web/public/data/dao_metrics.json',
	'web/public/data/sankey_impact.json',
	'web/public/data/sport_funding.json',
	'web/public/data/milestones.json',
	'web/public/data/members.json',
]
for f in files:
		p = Path(f)
		size = p.stat().st_size if p.exists() else 0
		ok = 'ok' if size > 100 else 'MISSING'
		print(f'[{ok}] {f} ({size:,} bytes)')
"
```

---

## 10. Resolucao de ambiguidade

| Pedido | Acao |
|---|---|
| "Melhora o grafico" | Perguntar qual grafico e qual problema |
| "Os dados estao errados" | Rodar audit + reconcile antes de qualquer mudanca |
| "Esta lento" | Medir tempo por script antes de otimizar |
| "Faz o deploy" | Build primeiro. Push so se build passou |
| Mudanca de dados | Rodar pipeline e verificar `web/public/data/` atualizado |

---

## 11. Sprint 7-10 — status

### Sprint 7 — concluidos

```
[x] 0. Category labels globais em derive_analytics.py + React
[x] 1A. Remover ledger do TreasuryChart
[x] 1B. Dual YAxis (balance $0-500k / spend $0-25k separados)
[x] 1C. Mover ledger para aba Treasury
[x] 2. Corrigir proof_record_count em enrich_members.py
[x] 3. Criar reconcile_treasury.py
[x] Leaderboard com dados reais (41 atletas)
[x] Dune MCP integrado (5 queries)
[x] AGENTS.md criado e commitado
```

### Sprint 8/9 — consolidado

```
[x] scripts/derive_funding_analysis.py integrado no pipeline
[x] sync_snapshot.py no pipeline (refresh_all)
[x] refresh_all.py com flags --incremental e --derive-only
[x] Sankey completeness check em audit_gaps.py
[x] Exploracao de precos Dune (scripts/explore_dune_prices.py + resultados)
[ ] Queries Dune sem LIMIT para historico completo (validar IDs/SQL em data/sources.json)
[ ] ETH historico por transacao no pipeline (hoje com fallback parcial)
[ ] Reconciliacao com gap < $5k
[ ] Sankey tooltip enriquecido (val_usdc + val_eth + top_recipients)
```

### Sprint 10 — foco atual

Baseline validado em 2026-03-23:
- `audit_gaps.py`: drift Sankey = $35, cobertura = 100%, `unpriced_rows = 0`
- `reconcile_treasury.py`: gap estrutural = $253,879, `adjusted_gap = 0` (opening balance inferido)
- `spend_ledger`: tx_hash 57/65 (88% geral), tx_hash 55/56 (98% trackable USDC/ETH), project_id 65/65
- `npm run build --prefix web`: OK

```bash
P0 - Confiabilidade financeira
[x] Corrigir audit_gaps.py para usar usd_value_at_execution + fallback seguro
[x] Corrigir reconcile_treasury.py para usar funding_in de dao_metrics + cobertura por proposal_tags
[x] Fechar reconciliacao operacional com `adjusted_gap < $5k` usando opening balance inferido
[ ] Fechar reconciliacao estrutural com `gap < $5k` via inflows historicos observados (sem ajuste inferido)

P1 - Qualidade do ledger
[ ] Preencher tx_hash em spend_ledger (meta >90% geral; atual 88%, trackable 98%)
[x] Preencher project_id em spend_ledger (meta >90%)
[x] Resolver 3 linhas unpriced com estrategia explicita (exclusao non-canonical com USD=0)

P2 - Dune / historico
[ ] Remover LIMIT das queries historicas e fazer backfill completo
[ ] Garantir trilha de source/fx por linha no funding_analysis

P3 - Produto
[ ] Enriquecer tooltip do Sankey (val_usdc + val_eth + top_recipients)
[ ] Gate de release: audit_gaps + reconcile_treasury + web build antes do push
```

---

## 12. Politica de ferramentas e mudancas

- Manter acesso completo incluindo `run_in_terminal`
- Preferir menor mudanca viavel que resolve o problema
- Nao quebrar schemas de JSON publicos sem plano de migracao
- Se mudanca conflita com invariantes: explicar e propor alternativa segura
- Rodar checagens impactadas apos cada edicao

---

*Atualizar apos cada sprint — marcar itens concluidos, adicionar novos pendentes.*

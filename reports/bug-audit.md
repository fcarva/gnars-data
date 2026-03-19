# Bug Audit

Scope: final technical risk audit focused on `web/scripts/prerender.tsx`, `web/src/types.ts`, and the coupling to derived datasets before commit/push.

Checks run:
- `npm run typecheck` in `web`
- `npm run build` in `web`

## Low-risk fixes applied

- `web/scripts/prerender.tsx`
  - Added hard failure guards for missing primary scenes/windows used during prerender.
  - Added a duplicate pathname check before writing static routes.
  - Added a lightweight integrity check for `network_view.json` so edges cannot silently point at missing or mismatched nodes during prerender.
- `web/src/types.ts`
  - Replaced `ProposalArchiveRecord.transactions` / `votes` generic object arrays with explicit minimum record types.

## Findings

### Medium
- `web/scripts/prerender.tsx` still acts as both route registry and page-view assembler. It loads all major datasets, performs joins, computes page-level view models, and writes every route in one pass. That coupling is currently build-safe, but it increases regression risk when changing any of:
  - route shape
  - derived dataset contracts
  - page prop structure

### Medium
- `web/src/types.ts` is still a monolithic contract file mixing:
  - canonical record types
  - derived analytics payloads
  - chart/view payloads
  - page props
  This is manageable now, but future refactors can easily blur the boundary between source data and UI-specific view models.

### Medium
- Prerender depends on several precomputed datasets staying internally aligned:
  - `people.json`
  - `project_rollups.json`
  - `proposals_archive.json`
  - `proposals_enriched.json`
  - `timeline_events.json`
  - `community_signals.json`
  - `feed_stream.json`
  - `insights.json`
  - `filter_facets.json`
  - `activity_view.json`
  - `treasury_view.json`
  - `network_view.json`
  The new guards catch some hard failures, but they do not yet validate all cross-dataset referential assumptions, such as proposal-to-project lineage completeness or surface facet completeness.

## Residual risk

- No route-level snapshot tests exist for `/network/`, `/treasury/`, or the denser entity pages.
- The build now fails earlier on missing scenes, duplicate paths, and broken network edges, which is good for safety, but broader semantic validation still lives outside the prerender layer.
- Any future refactor that changes `communityHref`, `projectHref`, `proposalHref`, or the derived JSON contracts should be treated as high-sensitivity because route generation and page composition are still centrally coupled.

## Current status

- `npm run typecheck`: passed
- `npm run build`: passed
- Prerender output: `1375` static routes

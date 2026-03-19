# Vercel Deployment

The public-facing `Gnars Camp` frontend now lives in `web/` as a static `React + Vite + TypeScript` app.
Current public URL: `https://gnars-data.vercel.app`

## Vercel project settings

Use these settings in the Vercel dashboard:

- Framework preset: `Vite`
- Root directory: `web`
- Production branch: `main`
- Build command: `npm run build`
- Output directory: `dist`

## Important operating rule

Vercel is only the presentation layer.

Do not move sync, treasury derivation, proposal indexing, or onchain enrichment into the Vercel runtime.

Those remain in the root Python pipeline:

- `scripts/sync_proposals.py`
- `scripts/sync_treasury.py`
- `scripts/derive_analytics.py`
- `scripts/validate_data.py`

The frontend build consumes committed JSON from `data/` and prepared public payloads under `web/public/data/`.

## Local build

```powershell
cd web
npm install
npm run build
```

## Data contract used by the frontend

The React app is currently built against:

- `people.json`
- `spend_ledger.json`
- `project_rollups.json`
- `timeline_events.json`
- `dao_metrics.json`
- `proposals_archive.json`
- `project_updates.json`

## Relationship to GitHub Pages

GitHub Pages remains the technical fallback while the React frontend is validated on Vercel.

Pages still publishes the legacy static vault from `_site/`.
Vercel is intended to become the primary public surface once the React rollout is approved.

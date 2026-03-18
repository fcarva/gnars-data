# Operations

## Core operating principle

Treat this repository as a long-lived operational system, not just a folder of files.

## Update cadence

- `gnars.com` dashboard and treasury: daily
- proposal pages and governance metadata: daily while active, weekly otherwise
- members API: daily or hourly if used for live analytics
- `gnars.center` and `gnars.wtf`: weekly
- Discord / Dune / manual exports: batch updates as data becomes available

## Stewardship rules

- Preserve raw snapshots before manual normalization
- Document data quality issues in commit messages or docs
- Prefer append-only snapshots in `raw/`
- Keep schemas aligned with dataset changes
- Regenerate CSV exports after structured data changes
- Rebuild `_site/` before publishing Pages artifacts

## Supplemental onchain tooling

- Herd Explorer and Herd MCP are tracked as supplemental context tools, not canonical data stores
- Verified against Herd docs on 2026-03-18, Herd currently supports `Ethereum` and `Base`
- `Polygon` is not currently listed as supported by Herd, so Polygon work still needs a different explorer or analytics source
- Herd is useful for contract relationships, proxy history, deployment context, and transaction decoding
- Herd is not intended for Dune-style aggregate analytics; use Dune or structured exports for rollups and KPIs
- The official MCP endpoint is `https://mcp.herd.eco/v1` and requires client-side OAuth authentication

See `docs/operations/herd-mcp.md` for the focused Herd integration note.

## Supplemental Ethereum knowledge

- ETHSkills is tracked as a playbook for Ethereum workflows and current tooling judgment
- It is especially relevant for indexing design, address hygiene, L2 tradeoffs, and tool selection
- It is not a Gnars-specific factual source and should not override explorer or repository evidence

See `docs/operations/ethskills.md` for the focused ETHSkills note.

## Immediate data quality issue observed

On 2026-03-18, the live Gnars treasury pages showed inconsistent aggregate values:

- Homepage dashboard label: `$46.5k`
- Treasury overview widget: `$0.00`
- Token holdings tables: non-zero balances

This repository stores the row-level holdings and explicitly records the discrepancy.

## GitHub Pages and automation

- `scripts/build_site.py` generates a Quartz-style static vault into `_site/`
- `.github/workflows/deploy-pages.yml` publishes `_site/` to GitHub Pages
- `.github/workflows/daily-sync.yml` refreshes proposals, treasury, exports, and the pilot tagging queue every day

See `docs/operations/github-pages.md` for the one-time repository setting that must be enabled.

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

## Immediate data quality issue observed

On 2026-03-18, the live Gnars treasury pages showed inconsistent aggregate values:

- Homepage dashboard label: `$46.5k`
- Treasury overview widget: `$0.00`
- Token holdings tables: non-zero balances

This repository stores the row-level holdings and explicitly records the discrepancy.


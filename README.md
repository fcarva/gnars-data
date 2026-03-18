# gnars-data

Canonical data repository for Gnars DAO across `gnars.com`, `gnars.wtf`, `gnars.center`, governance archives, and legacy community sources.

## Why this repo exists

This repository is designed to become the DAO's data backbone:

- Source of truth for analytics and reporting
- Base layer for an RFP Hub and proposal intelligence
- Member directory for contributors, delegates, and operators
- Impact tracking for delivered work versus proposed work
- Treasury accountability for budget, spend, and asset visibility

## Repository map

```text
gnars-data/
├── config/                 # Source catalog and sync targets
├── data/                   # Structured JSON datasets and schemas
├── docs/                   # Governance, operations, architecture, proposal archives
├── exports/                # Generated CSVs for BI / spreadsheets
├── media/                  # Photos, videos, and brand assets
├── raw/                    # Raw snapshots pulled from web sources / APIs
├── reports/                # Weekly digests and narrative outputs
└── scripts/                # Validation, export, and sync automation
```

## Current seeded datasets

- `data/proposals.json`
- `data/members.json`
- `data/treasury.json`
- `data/projects.json`
- `data/sources.json`

Each dataset is paired with a JSON Schema under `data/schemas/`.

## Quick start

Run the local validation:

```powershell
python scripts\validate_data.py
```

Generate CSV exports:

```powershell
python scripts\export_csv.py
```

Capture fresh raw snapshots from the live sources:

```powershell
python scripts\sync_gnars.py
```

## Data model conventions

- `raw/` stores untouched source snapshots.
- `data/` stores cleaned, normalized records ready for analytics.
- `exports/` stores flat CSVs generated from `data/`.
- `docs/` stores the narrative and operational context needed by humans and agents.

## Initial scope

This first commit seeds the repository with:

- Proposal archive entries for `111` and `118`
- Contributor directory seeds for the operations workstream
- Treasury asset snapshot fields aligned with the live treasury page
- Source registry for current, legacy, and external Gnars data surfaces
- Scripts for validation, exports, and raw snapshot capture


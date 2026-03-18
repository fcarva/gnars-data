# gnars-data

Canonical data repository for Gnars DAO across `gnars.com`, `gnars.wtf`, `gnars.center`, governance archives, and legacy community sources.

Supplementary operator tooling tracked in this repo includes Dune for aggregate analytics, Herd for Base/Ethereum contract intelligence, and ETHSkills for Ethereum workflow guidance.

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

- `data/contracts.json`
- `data/proposals.json`
- `data/proposals_archive.json`
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

Collect the full governance archive from `gnars.com/proposals` and `Snapshot`:

```powershell
python scripts\sync_proposals.py
```

## Data model conventions

- `raw/` stores untouched source snapshots.
- `data/` stores cleaned, normalized records ready for analytics.
- `exports/` stores flat CSVs generated from `data/`.
- `docs/` stores the narrative and operational context needed by humans and agents.

## Initial scope

This first commit seeds the repository with:

- Verified onchain contract registry for Gnars and That's Gnarly
- Proposal archive entries for `111` and `118`
- Full cross-platform proposal archive in `data/proposals_archive.json`
- Contributor directory seeds for the operations workstream
- Treasury asset snapshot fields aligned with the live treasury page
- Source registry for current, legacy, and external Gnars data surfaces
- Herd Explorer / Herd MCP as a documented supplemental layer for onchain context on Base and Ethereum
- ETHSkills as a documented supplemental knowledge layer for indexing, addresses, L2s, and tooling decisions
- Scripts for validation, exports, raw snapshot capture, and proposal-archive sync

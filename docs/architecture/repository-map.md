# Repository Architecture

## Layers

### 1. Raw capture

`raw/` stores untouched snapshots from public websites and APIs. This is the archival layer.

### 2. Structured data

`data/` stores normalized JSON records with stable fields for analytics, agents, and dashboards.

### 3. Derived exports

`exports/` stores flat CSV extracts generated from structured JSON for spreadsheets and BI tools.

### 4. Human context

`docs/` stores process notes, governance summaries, proposal archives, and operating assumptions.

## Expected workflow

1. Pull raw snapshots from live sources with `scripts/sync_gnars.py`
2. Normalize or enrich those snapshots into `data/*.json`
3. Validate contracts with `scripts/validate_data.py`
4. Generate CSV outputs with `scripts/export_csv.py`
5. Use `reports/` for weekly digests and accountability reporting

## Repository additions beyond the initial user sketch

The repo includes `config/`, `raw/`, and `reports/` on purpose:

- `config/` keeps the source registry and sync settings versioned
- `raw/` preserves the immutable evidence layer behind each dataset
- `reports/` gives the DAO a home for weekly digests, funding memos, and ROI tracking


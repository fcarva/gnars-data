# Scripts

- `validate_data.py`: validate JSON datasets against lightweight JSON Schema support
- `export_csv.py`: generate flat CSV exports from the structured JSON datasets
- `derive_analytics.py`: build `people`, `spend_ledger`, `project_rollups`, and `dao_metrics` from archive + treasury + projects + member snapshots
- `sync_gnars.py`: pull raw snapshots from live Gnars sources listed in `config/source_catalog.json`
- `sync_proposals.py`: collect the full governance archive from `gnars.com/proposals` and `Snapshot`
- `sync_treasury.py`: collect live treasury holdings and normalize the treasury dataset
- `tag_proposals.py`: seed and maintain the proposal-tagging review queue
- `build_site.py`: generate the `_site/` GitHub Pages artifact
- `refresh_all.ps1`: run full local MVP refresh (sync, derive, validate, export, and web build)

External operator tooling such as Herd MCP is documented in `docs/operations/` and `data/sources.json`, but is not yet automated by a local sync script.

Typical analytics/site refresh sequence:

```powershell
python scripts\derive_analytics.py
python scripts\validate_data.py
python scripts\export_csv.py
python scripts\build_site.py
```

Full local MVP refresh in one command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\refresh_all.ps1
```

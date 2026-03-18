# Scripts

- `validate_data.py`: validate JSON datasets against lightweight JSON Schema support
- `export_csv.py`: generate flat CSV exports from the structured JSON datasets
- `sync_gnars.py`: pull raw snapshots from live Gnars sources listed in `config/source_catalog.json`
- `sync_proposals.py`: collect the full governance archive from `gnars.com/proposals` and `Snapshot`

External operator tooling such as Herd MCP is documented in `docs/operations/` and `data/sources.json`, but is not yet automated by a local sync script.

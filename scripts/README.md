# Scripts

- `validate_data.py`: validate JSON datasets against lightweight JSON Schema support
- `export_csv.py`: generate flat CSV exports from the structured JSON datasets
- `sync_gnars.py`: pull raw snapshots from live Gnars sources listed in `config/source_catalog.json`
- `sync_proposals.py`: collect the full governance archive from `gnars.com/proposals` and `Snapshot`
- `sync_treasury.py`: collect live treasury holdings and normalize the treasury dataset
- `tag_proposals.py`: seed and maintain the proposal-tagging review queue
- `build_site.py`: generate the `_site/` GitHub Pages artifact

External operator tooling such as Herd MCP is documented in `docs/operations/` and `data/sources.json`, but is not yet automated by a local sync script.

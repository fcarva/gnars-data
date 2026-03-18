# Data Layer

`data/` holds normalized datasets meant to be consumed by analytics tools, APIs, agents, dashboards, and manual reporting.

## Key datasets

- `contracts.json`: verified smart contract registry for Gnars and That's Gnarly
- `proposals.json`: curated high-signal proposal layer
- `proposals_archive.json`: full governance archive from `gnars.com` and `Snapshot`, including raw properties, votes, and decoded transactions
- `proposal_tags.json`: proposal categorization queue and future LLM tagging layer
- `members.json`: contributor and member directory seeds
- `treasury.json`: treasury asset snapshots
- `projects.json`: executed and active workstreams
- `sources.json`: source registry and sync metadata

## Rules

- Keep raw source material in `raw/`
- Keep curated narrative context in `docs/`
- Keep machine-consumable outputs in `data/`
- Update the paired schema when the data contract changes

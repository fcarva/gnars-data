# Data Layer

`data/` holds normalized datasets meant to be consumed by analytics tools, APIs, agents, dashboards, and manual reporting.

## Key datasets

- `contracts.json`: verified smart contract registry for Gnars and That's Gnarly
- `proposals.json`: curated high-signal proposal layer
- `proposals_archive.json`: full governance archive from `gnars.com` and `Snapshot`, including raw properties, votes, and decoded transactions
- `proposal_tags.json`: proposal categorization queue and future LLM tagging layer
- `members.json`: contributor and member directory seeds
- `people_overrides.json`: editorial identity/tag layer for known people
- `people.json`: unified holder/delegate/contributor/recipient directory
- `treasury.json`: treasury asset snapshots
- `projects.json`: executed and active workstreams
- `project_updates.json`: manual milestones and status updates by workstream
- `project_rollups.json`: budget vs spent by workstream, plus recipients and linked proposals
- `spend_ledger.json`: fungible governance payout ledger derived from decoded proposal transactions
- `dao_metrics.json`: high-level DAO metrics and leaderboards for the public site
- `timeline_events.json`: merged chronology of proposals, workstream updates, and public proof links
- `sources.json`: source registry and sync metadata

## Rules

- Keep raw source material in `raw/`
- Keep curated narrative context in `docs/`
- Keep machine-consumable outputs in `data/`
- Update the paired schema when the data contract changes

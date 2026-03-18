# Exports

This directory stores CSVs generated from `data/*.json`.

Generated files are intentionally flat so they can be used in:

- spreadsheets
- BI dashboards
- governance reviews
- weekly reports

Current exports include:

- `contracts.csv`
- `proposals.csv`
- `proposals_archive.csv`
- `proposal_transactions.csv`
- `proposal_votes.csv`
- `members.csv`
- `projects.csv`
- `treasury.csv`
- `sources.csv`

Regenerate with:

```powershell
python scripts\export_csv.py
```

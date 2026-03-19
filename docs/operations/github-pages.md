# GitHub Pages Publishing

This repository publishes the legacy static vault fallback built from repository markdown, JSON datasets, and CSV exports.

The new public frontend for `Gnars Camp` is documented separately in `docs/operations/vercel.md`.

## Expected fallback public paths

- `/`
- `/notes/`
- `/datasets/`
- `/exports/proposals.csv`
- `/exports/proposals_archive.csv`

For the `fcarva/gnars-data` repository, the expected base URL is:

`https://fcarva.github.io/gnars-data/`

## What must be enabled on GitHub

In repository settings:

1. Open `Settings -> Pages`
2. Under `Build and deployment`, set `Source` to `GitHub Actions`
3. Save once

After that, `.github/workflows/deploy-pages.yml` handles fallback publication on every push to `main`.

## Local build

```powershell
python scripts\build_site.py
```

The fallback site output is generated into `_site/` and is intentionally gitignored.

## Daily automation

`.github/workflows/daily-sync.yml` runs:

- `sync_proposals.py`
- `sync_treasury.py`
- `validate_data.py`
- `export_csv.py`
- `build_site.py`

If structured data changed, the workflow commits the refreshed repository artifacts back to `main`.

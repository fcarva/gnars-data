from __future__ import annotations

import argparse
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "raw"
CONFIG_PATH = ROOT / "config" / "source_catalog.json"


def load_sources() -> list[dict]:
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload["sources"]


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def fetch_url(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "gnars-data-sync/1.0"
        }
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
        return response.read()


def extension_for(source_format: str) -> str:
    if source_format == "json":
        return "json"
    if source_format == "html":
        return "html"
    return "txt"


def sync_source(source: dict, stamp: str) -> Path:
    bucket_dir = RAW_DIR / source["bucket"]
    bucket_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{stamp}-{slugify(source['source_id'])}.{extension_for(source['format'])}"
    path = bucket_dir / filename
    path.write_bytes(fetch_url(source["url"]))
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture raw Gnars source snapshots.")
    parser.add_argument("--source", help="Only sync a single source_id", default=None)
    args = parser.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sources = [source for source in load_sources() if source.get("enabled", False)]
    if args.source:
        sources = [source for source in sources if source["source_id"] == args.source]

    if not sources:
        print("No enabled sources matched the requested filter.")
        return 1

    for source in sources:
        path = sync_source(source, stamp)
        print(f"[ok] {source['source_id']} -> {path.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

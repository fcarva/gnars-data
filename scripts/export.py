from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(name: str) -> dict[str, Any]:
    path = DATA_DIR / f"{name}.json"
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(name: str, payload: dict[str, Any]) -> None:
    path = DATA_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[ok] wrote {path.relative_to(ROOT)}")


def main() -> int:
    sections = [
        "treasury",
        "governance",
        "growth",
        "efficiency",
        "culture",
        "sankey",
        "delegation_graph",
        "runway_scenarios",
        "fork_risk",
    ]
    payload = {
        "dataset": "analytics_bundle",
        "as_of": utc_now_iso(),
        "version": 1,
        "sections": {name: load_json(name) for name in sections},
    }
    write_json("analytics_bundle", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

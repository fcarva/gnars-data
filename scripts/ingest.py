from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_script(name: str) -> None:
    script = ROOT / "scripts" / name
    cmd = [sys.executable, str(script)]
    print(f"[run] {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Orchestrate gnars ingestion sources.")
    parser.add_argument("--skip-gnars", action="store_true", help="Skip sync_gnars.py")
    parser.add_argument("--skip-proposals", action="store_true", help="Skip sync_proposals.py")
    parser.add_argument("--skip-treasury", action="store_true", help="Skip sync_treasury.py")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.skip_gnars:
        run_script("sync_gnars.py")
    if not args.skip_proposals:
        run_script("sync_proposals.py")
    if not args.skip_treasury:
        run_script("sync_treasury.py")

    print("[ok] ingestion complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

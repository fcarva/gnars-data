from __future__ import annotations

import json
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SNAPSHOT_API = "https://hub.snapshot.org/graphql"
SPACE_ID = "gnars.eth"
BASE_MIGRATION_TIMESTAMP = 1690000000
PAGE_SIZE = 1000
VOTE_PAGE_SIZE = 1000

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "raw" / "snapshot"
RAW_VOTES_DIR = RAW_DIR / "votes"
DATA_DIR = ROOT / "data"
RAW_PROPOSALS_FILE = RAW_DIR / "proposals.json"
DATA_PROPOSALS_FILE = DATA_DIR / "snapshot_proposals.json"
DATA_VOTES_FILE = DATA_DIR / "snapshot_votes.json"

IMAGE_URL_RE = re.compile(
    r"https?://[^\s\)\]>\"']+\.(?:png|jpe?g|gif|webp|svg)(?:\?[^\s\)\]>\"']*)?",
    flags=re.IGNORECASE,
)

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "gnars-data/snapshot-sync",
}

PROPOSALS_QUERY = """
query Proposals($space: String!, $first: Int!, $skip: Int!) {
  proposals(
    first: $first,
    skip: $skip,
    where: { space_in: [$space] },
    orderBy: "created",
    orderDirection: desc
  ) {
    id
    title
    body
    author
    state
    choices
    scores
    scores_total
    votes
    start
    end
    created
  }
}
"""

VOTES_QUERY = """
query Votes($proposal: String!, $first: Int!, $skip: Int!) {
  votes(
    first: $first,
    skip: $skip,
    where: { proposal: $proposal },
    orderBy: "created",
    orderDirection: desc
  ) {
    id
    proposal {
      id
    }
    voter
    created
    choice
    vp
    reason
  }
}
"""


def is_stale(filepath: Path, max_age_hours: int = 6) -> bool:
    if not filepath.exists():
        return True
    age = datetime.now() - datetime.fromtimestamp(filepath.stat().st_mtime)
    return age > timedelta(hours=max_age_hours)


def post_graphql(query: str, variables: dict[str, Any]) -> dict[str, Any]:
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request = urllib.request.Request(SNAPSHOT_API, data=payload, headers=HEADERS, method="POST")
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def fetch_all_proposals() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    skip = 0
    while True:
        body = post_graphql(PROPOSALS_QUERY, {"space": SPACE_ID, "first": PAGE_SIZE, "skip": skip})
        errors = body.get("errors") or []
        if errors:
            raise RuntimeError(f"Snapshot proposals query failed: {errors[0]}")
        rows = (body.get("data") or {}).get("proposals") or []
        if not rows:
            break
        records.extend(rows)
        if len(rows) < PAGE_SIZE:
            break
        skip += PAGE_SIZE
    return records


def fetch_votes_for_proposal(proposal_id: str) -> list[dict[str, Any]]:
    rows_all: list[dict[str, Any]] = []
    skip = 0
    while True:
        body = post_graphql(VOTES_QUERY, {"proposal": proposal_id, "first": VOTE_PAGE_SIZE, "skip": skip})
        errors = body.get("errors") or []
        if errors:
            raise RuntimeError(f"Snapshot votes query failed for {proposal_id}: {errors[0]}")
        rows = (body.get("data") or {}).get("votes") or []
        if not rows:
            break
        rows_all.extend(rows)
        if len(rows) < VOTE_PAGE_SIZE:
            break
        skip += VOTE_PAGE_SIZE
    return rows_all


def extract_images(body: str) -> list[str]:
    if not body:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for match in IMAGE_URL_RE.findall(body):
        if match in seen:
            continue
        seen.add(match)
        out.append(match)
    return out


def detect_network(created: int | None) -> str:
    if (created or 0) >= BASE_MIGRATION_TIMESTAMP:
        return "base"
    return "ethereum"


def choose_winner(choices: list[Any], scores: list[Any]) -> str | None:
    if not choices or not scores:
        return None
    best_idx = None
    best_score = float("-inf")
    for idx, score in enumerate(scores):
        try:
            numeric = float(score)
        except (TypeError, ValueError):
            continue
        if numeric > best_score:
            best_score = numeric
            best_idx = idx
    if best_idx is None or best_idx >= len(choices):
        return None
    winner = choices[best_idx]
    return str(winner) if winner is not None else None


def normalize_proposals(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for proposal in records:
        body = str(proposal.get("body") or "")
        images = extract_images(body)
        created = int(proposal.get("created") or 0)
        choices = proposal.get("choices") or []
        scores = proposal.get("scores") or []
        normalized.append(
            {
                "id": proposal.get("id"),
                "title": proposal.get("title"),
                "body": body,
                "author": proposal.get("author"),
                "state": proposal.get("state"),
                "choices": choices,
                "scores": scores,
                "scores_total": proposal.get("scores_total"),
                "votes_count": int(proposal.get("votes") or 0),
                "start": proposal.get("start"),
                "end": proposal.get("end"),
                "created": created,
                "network": detect_network(created),
                "images": images,
                "image_primary": images[0] if images else None,
                "winner": choose_winner(choices, scores),
            }
        )
    return normalized


def normalize_choice(choice: Any) -> int | None:
    if isinstance(choice, int):
        return choice
    if isinstance(choice, float):
        return int(choice)
    if isinstance(choice, list) and choice:
        first = choice[0]
        if isinstance(first, int):
            return first
        if isinstance(first, str) and first.isdigit():
            return int(first)
    if isinstance(choice, dict) and choice:
        top_key = None
        top_value = float("-inf")
        for key, value in choice.items():
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                continue
            if numeric > top_value:
                top_value = numeric
                top_key = key
        if top_key is not None:
            try:
                return int(top_key)
            except (TypeError, ValueError):
                return None
    if isinstance(choice, str) and choice.isdigit():
        return int(choice)
    return None


def normalize_votes(votes: list[dict[str, Any]], proposal_network: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for vote in votes:
        proposal_obj = vote.get("proposal") or {}
        out.append(
            {
                "id": vote.get("id"),
                "proposal_id": proposal_obj.get("id"),
                "voter": vote.get("voter"),
                "created": vote.get("created"),
                "choice": normalize_choice(vote.get("choice")),
                "vp": vote.get("vp"),
                "reason": vote.get("reason"),
                "network": proposal_network,
            }
        )
    return out


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    force = "--force" in sys.argv
    no_votes = "--no-votes" in sys.argv

    if not force and not is_stale(RAW_PROPOSALS_FILE, max_age_hours=6):
        print("[skip] snapshot proposals fresh")
        return 0

    print("[snapshot] fetching proposals from gnars.eth")
    proposals_raw = fetch_all_proposals()
    write_json(
        RAW_PROPOSALS_FILE,
        {
            "fetched_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "space": SPACE_ID,
            "records": proposals_raw,
        },
    )

    proposals_norm = normalize_proposals(proposals_raw)
    write_json(DATA_PROPOSALS_FILE, proposals_norm)
    print(f"[snapshot] proposals: {len(proposals_norm)}")

    all_votes_norm: list[dict[str, Any]] = []

    if no_votes:
        if not DATA_VOTES_FILE.exists():
            write_json(DATA_VOTES_FILE, [])
        print("[snapshot] votes skipped (--no-votes)")
        return 0

    print("[snapshot] fetching votes by proposal")
    network_by_proposal = {row["id"]: row["network"] for row in proposals_norm}

    for idx, proposal in enumerate(proposals_norm, start=1):
        proposal_id = str(proposal.get("id") or "")
        if not proposal_id:
            continue
        votes_raw = fetch_votes_for_proposal(proposal_id)
        write_json(
            RAW_VOTES_DIR / f"{proposal_id[:16]}.json",
            {
                "fetched_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "proposal_id": proposal_id,
                "records": votes_raw,
            },
        )
        all_votes_norm.extend(normalize_votes(votes_raw, network_by_proposal.get(proposal_id, "ethereum")))
        if idx % 25 == 0:
            print(f"[snapshot] votes progress: {idx}/{len(proposals_norm)} proposals")

    write_json(DATA_VOTES_FILE, all_votes_norm)
    print(f"[snapshot] votes: {len(all_votes_norm)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

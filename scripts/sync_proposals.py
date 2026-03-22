from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "raw"
DATA_DIR = ROOT / "data"
GNARS_RAW_PROPOSALS_DIR = RAW_DIR / "gnars.com" / "proposals"

GNARS_ROOT = "https://www.gnars.com"
GNARS_PROPOSALS_URL = f"{GNARS_ROOT}/proposals"
SNAPSHOT_GRAPHQL_URL = "https://hub.snapshot.org/graphql"
SNAPSHOT_SPACE = "gnars.eth"

USER_AGENT = "gnars-data-sync/1.0 (+https://github.com/fcarva/gnars-data)"
KNOWN_ERC20_DECIMALS = {
    "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913": 6,
    "0xba5b9b2d2d06a9021eb3190ea5fb0e02160839a4": 18,
}
KNOWN_GNARS_NOT_FOUND_LENGTHS = {65419, 65422}

SNAPSHOT_PROPOSALS_QUERY = """
query Proposals($space: String!, $first: Int!, $skip: Int!) {
  proposals(
    first: $first
    skip: $skip
    where: {space_in: [$space]}
    orderBy: "created"
    orderDirection: desc
  ) {
    id
    title
    body
    choices
    start
    end
    state
    author
    type
    scores
    scores_total
    scores_by_strategy
    created
    network
    symbol
    quorum
    discussion
    plugins
    privacy
    snapshot
    validation { name params }
    strategies { name params network }
    space { id name }
  }
}
""".strip()

SNAPSHOT_VOTES_QUERY = """
query Votes($proposal: String!, $first: Int!, $skip: Int!) {
  votes(
    first: $first
    skip: $skip
    where: {proposal: $proposal}
    orderBy: "created"
    orderDirection: desc
  ) {
    voter
    choice
    vp
    vp_by_strategy
    reason
    created
    ipfs
  }
}
""".strip()


class SyncError(RuntimeError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def isoformat_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def unix_to_iso(value: int | float | None) -> str | None:
    if value is None:
        return None
    return isoformat_utc(datetime.fromtimestamp(value, tz=timezone.utc))


def normalize_status(value: str | None) -> str:
    if value is None:
        return "unknown"
    return value.strip().lower().replace(" ", "_")


def is_not_found_gnars_html(html: str) -> bool:
    return "NEXT_HTTP_ERROR_FALLBACK;404" in html or "<title>Proposal Not Found | Gnars DAO</title>" in html


def raw_gnars_path_is_not_found(path: Path) -> bool:
    if path.stat().st_size in KNOWN_GNARS_NOT_FOUND_LENGTHS:
        return True
    with path.open("r", encoding="utf-8") as handle:
        head = handle.read(8192)
    return "Proposal Not Found | Gnars DAO" in head or "NEXT_HTTP_ERROR_FALLBACK;404" in head


def fetch_bytes(
    url: str,
    *,
    method: str = "GET",
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> bytes:
    request_headers = {"User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)

    request = urllib.request.Request(url, data=body, headers=request_headers, method=method)
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        return response.read()


def fetch_text(url: str) -> str:
    return fetch_bytes(url).decode("utf-8")


def post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    response = fetch_bytes(
        url,
        method="POST",
        body=body,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    data = json.loads(response.decode("utf-8"))
    if "errors" in data:
        raise SyncError(f"GraphQL error from {url}: {data['errors']!r}")
    return data


def write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def is_stale(filepath: str, max_age_hours: int = 6) -> bool:
    path = ROOT / filepath
    if not path.exists():
        return True
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    return age > timedelta(hours=max_age_hours)


def safe_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def absolute_url(url_or_path: str) -> str:
    return urllib.parse.urljoin(f"{GNARS_ROOT}/", url_or_path)


def infer_gnars_path(chain: str, number: int | str) -> str:
    return f"/proposals/{chain}/{number}"


def parse_gnars_snapshot_filename(path: Path) -> tuple[str, int] | None:
    match = re.fullmatch(r"\d{8}T\d{6}Z-([a-z]+)-(\d+)\.html", path.name)
    if not match:
        return None
    return match.group(1), int(match.group(2))


def latest_raw_gnars_snapshot_paths(*, valid_only: bool = False) -> list[Path]:
    latest: dict[tuple[str, int], Path] = {}
    if not GNARS_RAW_PROPOSALS_DIR.exists():
        return []

    for path in sorted(GNARS_RAW_PROPOSALS_DIR.glob("*.html"), reverse=True):
        parsed = parse_gnars_snapshot_filename(path)
        if parsed is None:
            continue
        if parsed in latest:
            continue
        if valid_only and raw_gnars_path_is_not_found(path):
            continue
        latest[parsed] = path

    return sorted(latest.values())


def known_gnars_paths_from_raw() -> set[str]:
    paths = set()
    for path in latest_raw_gnars_snapshot_paths(valid_only=True):
        parsed = parse_gnars_snapshot_filename(path)
        if parsed is None:
            continue
        chain, number = parsed
        paths.add(infer_gnars_path(chain, number))
    return paths


def known_gnars_paths_from_archive() -> set[str]:
    archive_path = DATA_DIR / "proposals_archive.json"
    if not archive_path.exists():
        return set()

    try:
        payload = json.loads(archive_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()

    return {
        infer_gnars_path(record["chain"], record["proposal_number"])
        for record in payload.get("records", [])
        if record.get("platform") == "gnars.com" and record.get("proposal_number") is not None
    }


def extract_balanced(text: str, start: int, open_char: str, close_char: str) -> str:
    depth = 0
    in_string = False
    escape = False

    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue

        if char == open_char:
            depth += 1
        elif char == close_char:
            depth -= 1
            if depth == 0:
                return text[start : index + 1]

    raise SyncError(f"Could not find balanced {open_char}{close_char} block")


def decode_next_flight_payload(html: str) -> str:
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)</script>', html, flags=re.S)
    if not chunks:
        raise SyncError("Could not find Next.js flight payload chunks")
    return "".join(json.loads(f'"{chunk}"') for chunk in chunks)


def parse_flight_records(flight: str) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    index = 0
    decoder = json.JSONDecoder()

    while index < len(flight):
        if flight[index] == "\n":
            index += 1
            continue

        if flight[index] == ":":
            next_newline = flight.find("\n", index)
            if next_newline == -1:
                break
            index = next_newline + 1
            continue

        key_start = index
        while index < len(flight) and flight[index] != ":":
            index += 1
        if index >= len(flight):
            break

        key = flight[key_start:index]
        index += 1
        if index >= len(flight):
            records[key] = {"kind": "empty", "value": ""}
            break

        marker = flight[index]

        if marker == "T":
            length_end = flight.find(",", index)
            if length_end == -1:
                raise SyncError(f"Malformed text record for key {key}")
            length = int(flight[index + 1 : length_end], 16)
            value_start = length_end + 1
            value_end = value_start + length
            records[key] = {"kind": "text", "value": flight[value_start:value_end]}
            index = value_end
        elif marker == '"':
            value, consumed = decoder.raw_decode(flight[index:])
            records[key] = {"kind": "json_string", "value": value}
            index += consumed
        else:
            next_newline = flight.find("\n", index)
            if next_newline == -1:
                raw_value = flight[index:]
                index = len(flight)
            else:
                raw_value = flight[index:next_newline]
                index = next_newline
            records[key] = {"kind": "raw", "value": raw_value}

        if index < len(flight) and flight[index] == "\n":
            index += 1

    return records


def resolve_flight_references(value: Any, records: dict[str, dict[str, Any]]) -> Any:
    if isinstance(value, dict):
        return {key: resolve_flight_references(item, records) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve_flight_references(item, records) for item in value]
    if not isinstance(value, str):
        return value

    if value == "$undefined":
        return None
    if value.startswith("$D"):
        return value[2:]
    if value.startswith("$"):
        record_key = value[1:]
        record = records.get(record_key)
        if record is None:
            return value
        return record["value"]
    return value


def extract_canonical_url(html: str, fallback_url: str) -> str:
    match = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    return match.group(1) if match else fallback_url


def extract_meta_description(document: str) -> str:
    match = re.search(r'<meta name="description" content="([^"]*)"', document)
    return html_lib.unescape(match.group(1)) if match else ""


def extract_proposal_object(flight: str) -> dict[str, Any]:
    marker = '"proposal":'
    start = flight.find(marker)
    if start == -1:
        raise SyncError("Could not locate proposal object in flight payload")
    object_start = flight.find("{", start)
    if object_start == -1:
        raise SyncError("Malformed proposal object in flight payload")
    raw_object = extract_balanced(flight, object_start, "{", "}")
    return json.loads(raw_object)


def extract_first_markdown_image(markdown: str | None) -> str | None:
    if not markdown:
        return None
    match = re.search(r"!\[[^\]]*]\(([^)]+)\)", markdown)
    return match.group(1) if match else None


def normalize_native_value(wei_value: str) -> float:
    return int(wei_value) / 10**18


def normalize_erc20_amount(contract: str, raw_amount: str) -> float | str:
    decimals = KNOWN_ERC20_DECIMALS.get(contract.lower())
    if decimals is None:
        return raw_amount
    return int(raw_amount) / 10**decimals


def decode_calldata_transaction(index: int, target: str, value: str, calldata: str) -> dict[str, Any]:
    if calldata == "0x":
        return {
            "index": index,
            "kind": "native_transfer",
            "target": target,
            "value_wei": value,
            "amount_eth": normalize_native_value(value),
            "calldata": calldata,
        }

    if not calldata.startswith("0x") or len(calldata) < 10:
        return {
            "index": index,
            "kind": "contract_call",
            "target": target,
            "value_wei": value,
            "selector": None,
            "calldata": calldata,
        }

    selector = calldata[2:10]
    payload = calldata[10:]

    if selector == "a9059cbb" and len(payload) >= 128:
        recipient = f"0x{payload[24:64]}"
        amount_raw = str(int(payload[64:128], 16))
        return {
            "index": index,
            "kind": "erc20_transfer",
            "target": target,
            "token_contract": target,
            "recipient": recipient,
            "amount_raw": amount_raw,
            "amount_normalized": normalize_erc20_amount(target, amount_raw),
            "value_wei": value,
            "selector": selector,
            "calldata": calldata,
        }

    if selector == "23b872dd" and len(payload) >= 192:
        sender = f"0x{payload[24:64]}"
        recipient = f"0x{payload[88:128]}"
        token_id = str(int(payload[128:192], 16))
        return {
            "index": index,
            "kind": "erc721_transfer",
            "target": target,
            "token_contract": target,
            "sender": sender,
            "recipient": recipient,
            "token_id": token_id,
            "value_wei": value,
            "selector": selector,
            "calldata": calldata,
        }

    return {
        "index": index,
        "kind": "contract_call",
        "target": target,
        "value_wei": value,
        "selector": selector,
        "calldata": calldata,
    }


def build_transaction_records(properties: dict[str, Any]) -> list[dict[str, Any]]:
    targets = properties.get("targets") or []
    values = properties.get("values") or []
    calldatas = properties.get("calldatas") or []
    transactions = []

    for index, (target, value, calldata) in enumerate(zip(targets, values, calldatas), start=1):
        transactions.append(decode_calldata_transaction(index, target, value, calldata))

    return transactions


def explorer_url_for_gnars(chain: str, tx_hash: str | None) -> str | None:
    if not tx_hash:
        return None
    if chain == "base":
        return f"https://basescan.org/tx/{tx_hash}"
    if chain == "ethereum":
        return f"https://etherscan.io/tx/{tx_hash}"
    return None


def parse_gnars_proposal_html(html: str, fetched_url: str) -> dict[str, Any]:
    flight = decode_next_flight_payload(html)
    records = parse_flight_records(flight)
    proposal = resolve_flight_references(extract_proposal_object(flight), records)

    description_markdown = proposal.get("description")
    chain = proposal.get("source") or "base"
    tx_hash = proposal.get("transactionHash")
    total_votes = int(proposal.get("forVotes") or 0) + int(proposal.get("againstVotes") or 0) + int(proposal.get("abstainVotes") or 0)

    return {
        "archive_id": f"gnars-{chain}-{proposal['proposalNumber']}",
        "platform": "gnars.com",
        "space": "gnars-dao",
        "chain": chain,
        "proposal_key": proposal["proposalId"],
        "proposal_number": proposal["proposalNumber"],
        "title": proposal["title"],
        "status": normalize_status(proposal.get("status")),
        "status_display": proposal.get("status"),
        "proposer": proposal.get("proposer"),
        "proposer_label": proposal.get("proposerEnsName"),
        "created_at": unix_to_iso((proposal.get("createdAt") or 0) / 1000 if proposal.get("createdAt") else None),
        "start_at": proposal.get("voteStart"),
        "end_at": proposal.get("voteEnd") or proposal.get("endDate"),
        "snapshot_block": proposal.get("snapshotBlock"),
        "quorum": proposal.get("quorumVotes"),
        "choices": ["FOR", "AGAINST", "ABSTAIN"],
        "scores_by_choice": [
            int(proposal.get("forVotes") or 0),
            int(proposal.get("againstVotes") or 0),
            int(proposal.get("abstainVotes") or 0),
        ],
        "scores_total": total_votes,
        "content_markdown": description_markdown,
        "content_summary": extract_meta_description(html),
        "cover_image_url": extract_first_markdown_image(description_markdown),
        "transactions": build_transaction_records(proposal),
        "votes": proposal.get("votes") or [],
        "links": {
            "source_url": fetched_url,
            "canonical_url": extract_canonical_url(html, fetched_url),
            "discussion_url": None,
            "explorer_url": explorer_url_for_gnars(chain, tx_hash),
        },
        "properties": proposal,
    }


def fetch_snapshot_proposals(space: str) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    first = 100
    skip = 0

    while True:
        payload = post_json(
            SNAPSHOT_GRAPHQL_URL,
            {
                "query": SNAPSHOT_PROPOSALS_QUERY,
                "variables": {"space": space, "first": first, "skip": skip},
            },
        )
        batch = payload["data"]["proposals"]
        if not batch:
            break
        proposals.extend(batch)
        if len(batch) < first:
            break
        skip += first

    return proposals


def fetch_snapshot_votes(proposal_id: str) -> list[dict[str, Any]]:
    votes: list[dict[str, Any]] = []
    first = 100
    skip = 0

    while True:
        payload = post_json(
            SNAPSHOT_GRAPHQL_URL,
            {
                "query": SNAPSHOT_VOTES_QUERY,
                "variables": {"proposal": proposal_id, "first": first, "skip": skip},
            },
        )
        batch = payload["data"]["votes"]
        if not batch:
            break
        votes.extend(batch)
        if len(batch) < first:
            break
        skip += first

    return votes


def snapshot_proposal_url(space: str, proposal_id: str) -> str:
    return f"https://v1.snapshot.box/#/{space}/proposal/{proposal_id}"


def normalize_snapshot_record(proposal: dict[str, Any], votes: list[dict[str, Any]]) -> dict[str, Any]:
    created_at = unix_to_iso(proposal.get("created"))
    start_at = unix_to_iso(proposal.get("start"))
    end_at = unix_to_iso(proposal.get("end"))
    status_display = proposal.get("state")

    raw_properties = dict(proposal)
    raw_properties["votes"] = votes

    return {
        "archive_id": f"snapshot-{proposal['id']}",
        "platform": "snapshot",
        "space": proposal["space"]["id"],
        "chain": "snapshot",
        "proposal_key": proposal["id"],
        "proposal_number": None,
        "title": proposal["title"],
        "status": normalize_status(status_display),
        "status_display": status_display,
        "proposer": proposal.get("author"),
        "proposer_label": None,
        "created_at": created_at,
        "start_at": start_at,
        "end_at": end_at,
        "snapshot_block": int(proposal["snapshot"]) if proposal.get("snapshot") else None,
        "quorum": proposal.get("quorum"),
        "choices": proposal.get("choices"),
        "scores_by_choice": proposal.get("scores"),
        "scores_total": proposal.get("scores_total"),
        "content_markdown": proposal.get("body"),
        "content_summary": html_lib.unescape((proposal.get("body") or "").strip().splitlines()[0][:280]),
        "cover_image_url": extract_first_markdown_image(proposal.get("body")),
        "transactions": [],
        "votes": votes,
        "links": {
            "source_url": snapshot_proposal_url(proposal["space"]["id"], proposal["id"]),
            "canonical_url": snapshot_proposal_url(proposal["space"]["id"], proposal["id"]),
            "discussion_url": proposal.get("discussion"),
            "explorer_url": None,
        },
        "properties": raw_properties,
    }


def extract_gnars_proposal_paths(index_html: str) -> set[str]:
    discovered = {
        match.group(0)
        for match in re.finditer(r"/proposals(?:/[a-z]+)?/\d+", index_html)
    }

    normalized: set[str] = set()
    base_numbers: set[int] = set()

    for path in discovered:
        plain_match = re.fullmatch(r"/proposals/(\d+)", path)
        if plain_match:
            number = int(plain_match.group(1))
            normalized.add(f"/proposals/base/{number}")
            base_numbers.add(number)
            continue

        chain_match = re.fullmatch(r"/proposals/([a-z]+)/(\d+)", path)
        if chain_match:
            chain = chain_match.group(1)
            number = int(chain_match.group(2))
            normalized.add(f"/proposals/{chain}/{number}")
            if chain == "base":
                base_numbers.add(number)

    if base_numbers:
        for number in range(min(base_numbers), max(base_numbers) + 1):
            normalized.add(f"/proposals/base/{number}")

    return normalized


def fetch_gnars_index(stamp: str) -> tuple[str, Path]:
    payload = fetch_bytes(GNARS_PROPOSALS_URL)
    path = RAW_DIR / "gnars.com" / f"{stamp}-gnars-proposals-index.html"
    write_bytes(path, payload)
    return payload.decode("utf-8"), path


def fetch_gnars_proposals(paths: set[str], stamp: str) -> list[dict[str, Any]]:
    records = []
    target_dir = GNARS_RAW_PROPOSALS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    for path in sorted(paths):
        url = absolute_url(path)
        try:
            payload = fetch_bytes(url)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                print(f"[skip] {path} -> 404")
                continue
            raise

        number_match = re.search(r"/(\d+)$", path)
        number_label = number_match.group(1) if number_match else safe_slug(path)
        chain_match = re.search(r"/proposals/([a-z]+)/", path)
        chain_label = chain_match.group(1) if chain_match else "base"
        raw_path = target_dir / f"{stamp}-{chain_label}-{number_label}.html"
        write_bytes(raw_path, payload)

        html = payload.decode("utf-8")
        if is_not_found_gnars_html(html):
            print(f"[skip] {path} -> proposal not found")
            continue
        try:
            record = parse_gnars_proposal_html(html, url)
        except SyncError as exc:
            print(f"[skip] {path} -> {exc}")
            continue

        record["raw_snapshot"] = raw_path.relative_to(ROOT).as_posix()
        records.append(record)
        print(f"[ok] gnars {path} -> {raw_path.relative_to(ROOT)}")

    return records


def load_local_gnars_archive(paths_filter: set[str] | None = None) -> list[dict[str, Any]]:
    records = []
    for raw_path in latest_raw_gnars_snapshot_paths(valid_only=True):
        parsed = parse_gnars_snapshot_filename(raw_path)
        if parsed is None:
            continue

        chain, number = parsed
        path = infer_gnars_path(chain, number)
        if paths_filter is not None and path not in paths_filter:
            continue

        url = absolute_url(path)
        html = raw_path.read_text(encoding="utf-8")

        try:
            record = parse_gnars_proposal_html(html, url)
        except SyncError:
            continue

        record["raw_snapshot"] = raw_path.relative_to(ROOT).as_posix()
        records.append(record)

    return records


def fetch_snapshot_archive(space: str, stamp: str) -> list[dict[str, Any]]:
    proposals = fetch_snapshot_proposals(space)
    records = []
    raw_path = RAW_DIR / "api" / f"{stamp}-snapshot-{safe_slug(space)}-proposals.json"
    snapshot_dump: dict[str, Any] = {"space": space, "proposals": []}

    for proposal in proposals:
        votes = fetch_snapshot_votes(proposal["id"])
        record = normalize_snapshot_record(proposal, votes)
        records.append(record)
        snapshot_dump["proposals"].append(record["properties"])
        print(f"[ok] snapshot {proposal['id']} -> {len(votes)} votes")

    write_json(raw_path, snapshot_dump)
    return records


def deduplicate_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for record in records:
        deduped[record["archive_id"]] = record
    return sorted(
        deduped.values(),
        key=lambda item: (
            item.get("created_at") or "",
            item["platform"],
            item["proposal_number"] or 0,
            item["title"],
        ),
        reverse=True,
    )


def build_archive(records: list[dict[str, Any]], generated_at: str) -> dict[str, Any]:
    return {
        "dataset": "proposals_archive",
        "as_of": generated_at,
        "version": 1,
        "records": deduplicate_records(records),
    }


def main() -> int:
    OUTPUT_FILE = "data/proposals_archive.json"
    if not is_stale(OUTPUT_FILE, max_age_hours=6) and "--force" not in sys.argv:
        print(f"[skip] {OUTPUT_FILE} is fresh (< 6h old). Use --force to re-sync.")
        sys.exit(0)

    parser = argparse.ArgumentParser(description="Collect Gnars proposals from gnars.com and Snapshot.")
    parser.add_argument("--skip-gnars", action="store_true", help="Skip gnars.com proposal collection.")
    parser.add_argument("--skip-snapshot", action="store_true", help="Skip Snapshot proposal collection.")
    parser.add_argument("--space", default=SNAPSHOT_SPACE, help="Snapshot space id to collect.")
    parser.add_argument("--force", action="store_true", help="Bypass freshness check and force re-sync.")
    args = parser.parse_args()

    stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    records: list[dict[str, Any]] = []

    if not args.skip_gnars:
        index_html, index_path = fetch_gnars_index(stamp)
        known_valid_paths = known_gnars_paths_from_archive() | known_gnars_paths_from_raw()
        gnars_paths = extract_gnars_proposal_paths(index_html) | known_valid_paths
        print(f"[ok] gnars index -> {index_path.relative_to(ROOT)} ({len(gnars_paths)} candidate paths)")
        live_gnars_records = fetch_gnars_proposals(gnars_paths, stamp)
        records.extend(live_gnars_records)

        live_gnars_paths = {
            infer_gnars_path(record["chain"], record["proposal_number"])
            for record in live_gnars_records
            if record.get("proposal_number") is not None
        }
        missing_cached_paths = known_valid_paths - live_gnars_paths
        if missing_cached_paths:
            fallback_gnars_records = load_local_gnars_archive(missing_cached_paths)
            records.extend(fallback_gnars_records)
            print(f"[ok] loaded {len(fallback_gnars_records)} gnars fallback records from raw snapshots")

    if not args.skip_snapshot:
        records.extend(fetch_snapshot_archive(args.space, stamp))

    archive = build_archive(records, isoformat_utc(utc_now()))
    output_path = DATA_DIR / "proposals_archive.json"
    write_json(output_path, archive)
    print(f"[ok] wrote {output_path.relative_to(ROOT)} ({len(archive['records'])} records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

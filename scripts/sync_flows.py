from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = ROOT / "raw"
FLOW_INTELLIGENCE_PATH = DATA_DIR / "flow_intelligence.json"

FLOWS_URL = "https://flows.wtf/gnars"
GITHUB_API_BASE = "https://api.github.com/repos"
USER_AGENT = "gnars-data-flow-sync/1.0 (+https://github.com/fcarva/gnars-data)"

HREF_PATTERN = re.compile(r'href=["\']([^"\']+)["\']', flags=re.IGNORECASE)
ADDRESS_PATTERN = re.compile(r"0x[a-fA-F0-9]{40}")
REPO_PATTERN = re.compile(r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def isoformat_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        return response.read().decode("utf-8", errors="ignore")


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def snapshot_text(bucket: str, stamp: str, slug: str, content: str) -> str:
    target = RAW_DIR / bucket / f"{stamp}-{slug}.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return str(target.relative_to(ROOT)).replace("\\", "/")


def extract_links(html: str, base_url: str) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()
    for match in HREF_PATTERN.finditer(html):
        href = match.group(1).strip()
        if not href or href.startswith("#"):
            continue
        absolute = urljoin(base_url, href)
        if absolute in seen:
            continue
        seen.add(absolute)
        links.append(absolute)
    return links


def normalize_repo(owner: str, name: str) -> str:
    cleaned_name = name.removesuffix(".git")
    return f"{owner.lower()}/{cleaned_name.lower()}"


def extract_repo_names(values: list[str]) -> list[str]:
    repositories: list[str] = []
    seen: set[str] = set()
    for value in values:
        for owner, name in REPO_PATTERN.findall(value):
            repository = normalize_repo(owner, name)
            if repository in seen:
                continue
            seen.add(repository)
            repositories.append(repository)
    return repositories


def extract_addresses(values: list[str]) -> list[str]:
    addresses: list[str] = []
    seen: set[str] = set()
    for value in values:
        for address in ADDRESS_PATTERN.findall(value):
            normalized = address.lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            addresses.append(normalized)
    return addresses


def safe_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    return 0


def short_address(address: str) -> str:
    if len(address) < 12:
        return address
    return f"{address[:6]}...{address[-4:]}"


def load_contract_index() -> dict[str, dict[str, Any]]:
    contracts_path = DATA_DIR / "contracts.json"
    if not contracts_path.exists():
        return {}
    contracts = load_json(contracts_path).get("records", [])
    index: dict[str, dict[str, Any]] = {}
    for record in contracts:
        address = str(record.get("address") or "").lower()
        if not address:
            continue
        index[address] = record
    return index


def count_treasury_touches(addresses: set[str]) -> tuple[dict[str, int], dict[str, int]]:
    flows_path = DATA_DIR / "treasury_flows.json"
    route_counts = {address: 0 for address in addresses}
    proposal_counts = {address: 0 for address in addresses}
    if not flows_path.exists():
        return route_counts, proposal_counts

    routes = load_json(flows_path).get("routes", [])
    for route in routes:
        candidate_addresses = {
            str(route.get("recipient_address") or "").lower(),
            str(route.get("proposer_address") or "").lower(),
            str(route.get("token_contract") or "").lower(),
        }
        archive_id = str(route.get("archive_id") or "")
        for address in addresses:
            if address in candidate_addresses:
                route_counts[address] += 1
                if archive_id:
                    proposal_counts[address] += 1

    return route_counts, proposal_counts


def count_proposal_touches(addresses: set[str]) -> tuple[dict[str, int], dict[str, int]]:
    archive_path = DATA_DIR / "proposals_archive.json"
    tx_counts = {address: 0 for address in addresses}
    proposal_counts = {address: 0 for address in addresses}
    if not archive_path.exists():
        return tx_counts, proposal_counts

    records = load_json(archive_path).get("records", [])
    for record in records:
        archive_id = str(record.get("archive_id") or "")
        seen_this_proposal: set[str] = set()
        for tx in record.get("transactions", []):
            touched = {
                str(tx.get("target") or "").lower(),
                str(tx.get("recipient") or "").lower(),
                str(tx.get("sender") or "").lower(),
                str(tx.get("token_contract") or "").lower(),
            }
            for address in addresses:
                if address in touched:
                    tx_counts[address] += 1
                    if archive_id:
                        seen_this_proposal.add(address)
        for address in seen_this_proposal:
            proposal_counts[address] += 1

    return tx_counts, proposal_counts


def collect_github_repo(repository: str) -> tuple[dict[str, Any] | None, str | None]:
    url = f"{GITHUB_API_BASE}/{repository}"
    try:
        payload = fetch_json(url)
    except urllib.error.HTTPError as exc:
        return None, f"{repository}: github http {exc.code}"
    except urllib.error.URLError as exc:
        return None, f"{repository}: github unreachable ({exc.reason})"
    except TimeoutError:
        return None, f"{repository}: github timeout"

    record = {
        "repo_id": repository,
        "name": payload.get("name"),
        "full_name": payload.get("full_name") or repository,
        "description": payload.get("description"),
        "html_url": payload.get("html_url") or f"https://github.com/{repository}",
        "default_branch": payload.get("default_branch"),
        "language": payload.get("language"),
        "stargazers_count": safe_int(payload.get("stargazers_count")),
        "forks_count": safe_int(payload.get("forks_count")),
        "open_issues_count": safe_int(payload.get("open_issues_count")),
        "archived": bool(payload.get("archived")),
        "updated_at": payload.get("updated_at"),
        "api_url": payload.get("url") or url,
    }
    return record, None


def build_payload(existing: dict[str, Any], flows_html: str, snapshot_path: str) -> dict[str, Any]:
    links = extract_links(flows_html, FLOWS_URL)
    repositories = extract_repo_names(links + [flows_html])
    addresses = extract_addresses(links + [flows_html])
    contract_index = load_contract_index()

    github_records: list[dict[str, Any]] = []
    warnings: list[str] = []
    for repository in repositories:
        record, warning = collect_github_repo(repository)
        if warning:
            warnings.append(warning)
            continue
        if record:
            github_records.append(record)

    address_set = set(addresses)
    treasury_route_counts, treasury_proposal_counts = count_treasury_touches(address_set)
    tx_counts, tx_proposal_counts = count_proposal_touches(address_set)

    entity_records: list[dict[str, Any]] = []
    for address in addresses:
        contract = contract_index.get(address)
        entity_records.append(
            {
                "entity_id": f"address:{address}",
                "kind": "address",
                "label": contract.get("label") if contract else short_address(address),
                "value": address,
                "source_url": contract.get("explorer_url") if contract else "",
                "confidence": "high" if contract else "medium",
                "signals": {
                    "in_contract_registry": contract is not None,
                    "contract_id": contract.get("contract_id") if contract else "",
                    "network": contract.get("network") if contract else "",
                    "treasury_route_count": treasury_route_counts.get(address, 0),
                    "treasury_proposal_touch_count": treasury_proposal_counts.get(address, 0),
                    "proposal_transaction_touch_count": tx_counts.get(address, 0),
                    "proposal_archive_touch_count": tx_proposal_counts.get(address, 0),
                },
            }
        )

    for repository in github_records:
        entity_records.append(
            {
                "entity_id": f"repository:{repository['repo_id']}",
                "kind": "repository",
                "label": repository["full_name"],
                "value": repository["repo_id"],
                "source_url": repository["html_url"],
                "confidence": "high",
                "signals": {
                    "default_branch": repository.get("default_branch") or "",
                    "language": repository.get("language") or "",
                    "stargazers_count": repository.get("stargazers_count", 0),
                    "forks_count": repository.get("forks_count", 0),
                    "open_issues_count": repository.get("open_issues_count", 0),
                    "updated_at": repository.get("updated_at") or "",
                    "archived": bool(repository.get("archived")),
                },
            }
        )

    payload = {
        "dataset": "flow_intelligence",
        "as_of": isoformat_utc(utc_now()),
        "version": int(existing.get("version", 1)),
        "origin": {
            "flows_url": FLOWS_URL,
            "flows_snapshot": snapshot_path,
            "github_api_base": GITHUB_API_BASE,
            "onchain_inputs": [
                "data/contracts.json",
                "data/treasury_flows.json",
                "data/proposals_archive.json",
            ],
        },
        "stats": {
            "flows_links_count": len(links),
            "github_repository_count": len(repositories),
            "github_repository_enriched_count": len(github_records),
            "address_count": len(addresses),
            "entity_count": len(entity_records),
        },
        "repositories": github_records,
        "addresses": addresses,
        "records": entity_records,
        "notes": warnings,
    }
    return payload


def main() -> int:
    stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    existing: dict[str, Any] = {
        "dataset": "flow_intelligence",
        "version": 1,
    }
    if FLOW_INTELLIGENCE_PATH.exists():
        existing = load_json(FLOW_INTELLIGENCE_PATH)

    try:
        html = fetch_text(FLOWS_URL)
        snapshot_path = snapshot_text("external", stamp, "flows-wtf-gnars", html)
        print(f"[ok] fetched {FLOWS_URL} -> {snapshot_path}")
    except urllib.error.URLError as exc:
        if FLOW_INTELLIGENCE_PATH.exists():
            print(f"[warn] failed to fetch {FLOWS_URL}: {exc}; keeping existing dataset")
            return 0
        raise RuntimeError(f"Failed to fetch {FLOWS_URL}: {exc}") from exc

    payload = build_payload(existing, html, snapshot_path)
    write_json(FLOW_INTELLIGENCE_PATH, payload)
    print(f"[ok] wrote {FLOW_INTELLIGENCE_PATH.relative_to(ROOT)} ({len(payload['records'])} entities)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

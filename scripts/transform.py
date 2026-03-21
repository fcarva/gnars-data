from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import networkx as nx


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def month_bucket(value: str | None) -> str:
    dt = parse_datetime(value)
    if dt is None:
        return "unknown"
    return dt.strftime("%Y-%m")


def add_months(month: str, offset: int) -> str:
    year, mon = month.split("-")
    y = int(year)
    m = int(mon)
    total = y * 12 + (m - 1) + offset
    new_y = total // 12
    new_m = (total % 12) + 1
    return f"{new_y:04d}-{new_m:02d}"


def to_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def load_json(name: str) -> dict[str, Any]:
    path = DATA_DIR / f"{name}.json"
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(name: str, payload: dict[str, Any]) -> None:
    path = DATA_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[ok] wrote {path.relative_to(ROOT)}")


def gini(values: list[float]) -> float | None:
    clean = [v for v in values if v >= 0]
    if not clean:
        return None
    sorted_vals = sorted(clean)
    n = len(sorted_vals)
    total = sum(sorted_vals)
    if total == 0:
        return 0.0
    weighted_sum = 0.0
    for idx, value in enumerate(sorted_vals, start=1):
        weighted_sum += idx * value
    return (2.0 * weighted_sum) / (n * total) - (n + 1.0) / n


def infer_proposal_type(title: str) -> str:
    text = title.lower()
    if any(k in text for k in ["media", "news", "pod", "content", "video"]):
        return "Media"
    if any(k in text for k in ["event", "devconnect", "tour", "trip", "session"]):
        return "Events"
    if any(k in text for k in ["dev", "tool", "build", "product", "app", "site"]):
        return "Development"
    if any(k in text for k in ["art", "artist", "design", "nft", "zora"]):
        return "Art"
    if any(k in text for k in ["athlete", "skate", "sponsor", "surf", "shred"]):
        return "Athlete"
    if any(k in text for k in ["ops", "operations", "onboarding", "community", "coordination"]):
        return "Operations"
    return "Other"


def infer_recipient_cluster(recipient_name: str, title: str) -> str:
    r = recipient_name.lower()
    t = title.lower()
    if any(k in r or k in t for k in ["pod", "media", "news", "agency", "studio"]):
        return "Media Collective"
    if any(k in r or k in t for k in ["athlete", "skate", "surf", "sponsor", "tour"]):
        return "Athletes"
    if any(k in r or k in t for k in ["dev", "builder", "product", "app", "tool"]):
        return "Builders"
    return "Community Recipients"


def infer_funding_source(proposal_number: int | None) -> str:
    if proposal_number is None:
        return "Treasury Revenue"
    if proposal_number <= 60:
        return "Nouns Bootstrap"
    if proposal_number <= 95:
        return "Nouns Growth Track"
    return "Ongoing Treasury Revenue"


SELECTOR_METHOD_MAP = {
    "a9059cbb": "ERC20 transfer",
    "23b872dd": "ERC721 transferFrom",
    "": "Native transfer",
}


def selector_to_method(selector: str | None) -> str:
    if selector is None:
        return "Unknown"
    key = str(selector).lower().replace("0x", "")
    if key in SELECTOR_METHOD_MAP:
        return SELECTOR_METHOD_MAP[key]
    return f"method:{key[:8]}" if key else "Native transfer"


def normalize_address(value: Any) -> str:
    text = str(value or "").strip().lower()
    return text if text.startswith("0x") else ""


def build_proposal_tx_index(proposals: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for proposal in proposals.get("records", []):
        archive_id = str(proposal.get("archive_id") or "")
        if not archive_id:
            continue
        for tx in proposal.get("transactions", []):
            selector = str(tx.get("selector") or "").lower().replace("0x", "")
            kind = str(tx.get("kind") or "unknown")
            index[archive_id].append(
                {
                    "kind": kind,
                    "selector": selector,
                    "method": selector_to_method(selector),
                    "recipient": normalize_address(tx.get("recipient")),
                    "target": normalize_address(tx.get("target")),
                    "token_contract": normalize_address(tx.get("token_contract")),
                }
            )
    return index


def classify_treasury_route(asset_symbol: str, tx: dict[str, Any] | None) -> str:
    symbol = str(asset_symbol or "OTHER").upper()
    if tx is None:
        return f"{symbol} route (unmatched)"
    kind = str(tx.get("kind") or "")
    method = str(tx.get("method") or "Unknown")
    if kind == "native_transfer":
        return "Native transfer"
    if kind == "erc20_transfer":
        return f"ERC20 transfer ({symbol})"
    if kind == "erc721_transfer":
        return "ERC721 transfer"
    return method


def match_tx_for_spend_row(
    proposal_txs: list[dict[str, Any]],
    recipient_address: str,
    asset_symbol: str,
) -> dict[str, Any] | None:
    recipient = normalize_address(recipient_address)
    symbol = str(asset_symbol or "").upper()

    preferred_kind = None
    if symbol in {"ETH", "WETH"}:
        preferred_kind = "native_transfer"
    elif symbol:
        preferred_kind = "erc20_transfer"

    if preferred_kind is not None:
        for tx in proposal_txs:
            if tx.get("kind") == preferred_kind and tx.get("recipient") == recipient:
                return tx

    for tx in proposal_txs:
        if tx.get("recipient") == recipient:
            return tx
    return None


def build_governance(
    proposals: dict[str, Any],
    dao_metrics: dict[str, Any],
) -> dict[str, Any]:
    holders = int(dao_metrics.get("overview", {}).get("holders_count") or 0)
    monthly_votes: dict[str, set[str]] = defaultdict(set)
    monthly_vote_power: dict[str, list[float]] = defaultdict(list)
    monthly_proposals: Counter[str] = Counter()

    for proposal in proposals.get("records", []):
        month = month_bucket(proposal.get("created_at"))
        monthly_proposals[month] += 1
        for vote in proposal.get("votes", []):
            voter = str(vote.get("voter") or "").lower()
            if voter:
                monthly_votes[month].add(voter)
            monthly_vote_power[month].append(to_float(vote.get("votes")))

    timeseries: list[dict[str, Any]] = []
    for month in sorted(set(monthly_proposals.keys()) | set(monthly_votes.keys())):
        unique_voters = len(monthly_votes.get(month, set()))
        turnout = (100.0 * unique_voters / holders) if holders > 0 else None
        month_gini = gini(monthly_vote_power.get(month, []))
        timeseries.append(
            {
                "month": month,
                "proposal_count": int(monthly_proposals.get(month, 0)),
                "unique_voters": unique_voters,
                "turnout_pct": round(turnout, 4) if turnout is not None else None,
                "voting_power_gini": round(month_gini, 6) if month_gini is not None else None,
            }
        )

    return {
        "dataset": "governance",
        "as_of": utc_now_iso(),
        "version": 1,
        "overview": {
            "holders_count": holders,
            "proposals_total": int(dao_metrics.get("overview", {}).get("proposal_count") or 0),
            "active_proposals": int(dao_metrics.get("overview", {}).get("active_proposal_count") or 0),
            "proposal_success_rate_pct": to_float(dao_metrics.get("overview", {}).get("proposal_success_rate_pct")),
            "unique_voters_total": int(dao_metrics.get("overview", {}).get("unique_voters_count") or 0),
        },
        "timeseries": timeseries,
    }


def build_growth(
    proposals: dict[str, Any],
    dao_metrics: dict[str, Any],
) -> dict[str, Any]:
    monthly_voters: dict[str, set[str]] = defaultdict(set)
    monthly_proposers: dict[str, set[str]] = defaultdict(set)

    for proposal in proposals.get("records", []):
        month = month_bucket(proposal.get("created_at"))
        proposer = str(proposal.get("proposer") or "").lower()
        if proposer:
            monthly_proposers[month].add(proposer)
        for vote in proposal.get("votes", []):
            voter = str(vote.get("voter") or "").lower()
            if voter:
                monthly_voters[month].add(voter)

    months = sorted(set(monthly_voters.keys()) | set(monthly_proposers.keys()))
    previous_voters: set[str] = set()
    timeseries: list[dict[str, Any]] = []
    cohort_rows: list[dict[str, Any]] = []

    for month in months:
        voters = monthly_voters.get(month, set())
        retained = len(voters & previous_voters)
        retention = (100.0 * retained / len(previous_voters)) if previous_voters else None
        timeseries.append(
            {
                "month": month,
                "active_voters": len(voters),
                "new_voters": len(voters - previous_voters),
                "retained_voters": retained,
                "retention_pct": round(retention, 4) if retention is not None else None,
                "unique_proposers": len(monthly_proposers.get(month, set())),
            }
        )
        previous_voters = set(voters)

    for month in months:
        cohort = monthly_voters.get(month, set())
        if not cohort:
            continue
        row: dict[str, Any] = {
            "cohort_month": month,
            "cohort_size": len(cohort),
        }
        for offset in (1, 3, 6, 12):
            target_month = add_months(month, offset)
            target = monthly_voters.get(target_month)
            if target is None:
                row[f"m_plus_{offset}"] = None
                continue
            row[f"m_plus_{offset}"] = round((100.0 * len(cohort & target) / len(cohort)), 4)
        cohort_rows.append(row)

    holders = int(dao_metrics.get("overview", {}).get("holders_count") or 0)
    unique_voters_total = int(dao_metrics.get("overview", {}).get("unique_voters_count") or 0)
    active_pct = (100.0 * unique_voters_total / holders) if holders else None

    return {
        "dataset": "growth",
        "as_of": utc_now_iso(),
        "version": 1,
        "overview": {
            "holders_count": holders,
            "unique_voters_total": unique_voters_total,
            "active_voter_pct": round(active_pct, 4) if active_pct is not None else None,
            "proposers_total": int(dao_metrics.get("overview", {}).get("proposers_count") or 0),
        },
        "timeseries": timeseries,
        "cohort_retention": cohort_rows,
    }


def build_efficiency(
    spend_ledger: dict[str, Any],
    proposals: dict[str, Any],
) -> dict[str, Any]:
    proposal_by_id = {str(item.get("archive_id")): item for item in proposals.get("records", [])}
    by_month: dict[str, dict[str, Any]] = {}
    by_proposal_spend: defaultdict[str, float] = defaultdict(float)

    for row in spend_ledger.get("records", []):
        usd = row.get("usd_value_at_execution")
        if usd is None:
            continue
        archive_id = str(row.get("archive_id") or "")
        if archive_id:
            by_proposal_spend[archive_id] += to_float(usd)

    proposal_rows: list[dict[str, Any]] = []
    for archive_id, spend_usd in sorted(by_proposal_spend.items()):
        proposal = proposal_by_id.get(archive_id)
        if not proposal:
            continue
        votes = proposal.get("votes", [])
        vote_count = len(votes)
        vp = to_float(proposal.get("scores_total"))
        month = month_bucket(proposal.get("created_at"))
        entry = by_month.setdefault(
            month,
            {
                "month": month,
                "executed_spend_usd": 0.0,
                "vote_count": 0,
                "voting_power": 0.0,
                "proposal_count": 0,
            },
        )
        entry["executed_spend_usd"] += spend_usd
        entry["vote_count"] += vote_count
        entry["voting_power"] += vp
        entry["proposal_count"] += 1

        proposal_rows.append(
            {
                "archive_id": archive_id,
                "proposal_number": proposal.get("proposal_number"),
                "title": proposal.get("title"),
                "executed_spend_usd": round(spend_usd, 2),
                "vote_count": vote_count,
                "voting_power": round(vp, 3),
                "cost_per_vote_usd": round(spend_usd / vote_count, 2) if vote_count else None,
                "cost_per_voting_power_usd": round(spend_usd / vp, 6) if vp else None,
            }
        )

    monthly_rows: list[dict[str, Any]] = []
    previous_spend = 0.0
    for month in sorted(by_month):
        row = by_month[month]
        spend = to_float(row.get("executed_spend_usd"))
        votes = int(row.get("vote_count") or 0)
        vp = to_float(row.get("voting_power"))
        velocity = spend - previous_spend
        previous_spend = spend
        monthly_rows.append(
            {
                "month": month,
                "proposal_count": int(row.get("proposal_count") or 0),
                "executed_spend_usd": round(spend, 2),
                "cost_per_vote_usd": round(spend / votes, 2) if votes else None,
                "cost_per_voting_power_usd": round(spend / vp, 6) if vp else None,
                "spend_velocity_usd": round(velocity, 2),
            }
        )

    return {
        "dataset": "efficiency",
        "as_of": utc_now_iso(),
        "version": 1,
        "allocation_by_proposal": proposal_rows,
        "timeseries": monthly_rows,
    }


def build_culture(proposals: dict[str, Any]) -> dict[str, Any]:
    theme_patterns: dict[str, tuple[str, ...]] = {
        "athletes": ("athlete", "sponsor", "skate", "surf", "shred"),
        "media": ("media", "news", "video", "pod", "content"),
        "events": ("event", "devconnect", "tour", "session", "meet"),
        "art": ("art", "artist", "design", "zora", "nft"),
    }

    by_month: dict[str, Counter[str]] = defaultdict(Counter)
    totals = Counter()

    for proposal in proposals.get("records", []):
        title = str(proposal.get("title") or "")
        lower = title.lower()
        month = month_bucket(proposal.get("created_at"))
        matched = False
        for key, words in theme_patterns.items():
            if any(word in lower for word in words):
                by_month[month][key] += 1
                totals[key] += 1
                matched = True
        if not matched:
            by_month[month]["other"] += 1
            totals["other"] += 1

    rows = []
    for month in sorted(by_month):
        row = {"month": month}
        for key in ["athletes", "media", "events", "art", "other"]:
            row[key] = int(by_month[month].get(key, 0))
        rows.append(row)

    return {
        "dataset": "culture",
        "as_of": utc_now_iso(),
        "version": 1,
        "overview": {
            "athlete_related_proposals": int(totals.get("athletes", 0)),
            "media_related_proposals": int(totals.get("media", 0)),
            "event_related_proposals": int(totals.get("events", 0)),
            "art_related_proposals": int(totals.get("art", 0)),
        },
        "timeseries": rows,
    }


def build_sankey(spend_ledger: dict[str, Any], proposals: dict[str, Any]) -> dict[str, Any]:
    labels: list[str] = []
    index: dict[str, int] = {}
    proposal_totals: defaultdict[str, float] = defaultdict(float)
    proposal_labels: dict[str, str] = {}
    proposal_tx_index = build_proposal_tx_index(proposals)

    for row in spend_ledger.get("records", []):
        usd = row.get("usd_value_at_execution")
        if usd is None:
            continue
        value = to_float(usd)
        if value <= 0:
            continue
        archive_id = str(row.get("archive_id") or "")
        if not archive_id:
            continue
        proposal_totals[archive_id] += value
        proposal_number = row.get("proposal_number")
        if proposal_number in (None, ""):
            proposal_labels[archive_id] = f"Proposal: {archive_id}"
        else:
            proposal_labels[archive_id] = f"Proposal: #{int(proposal_number)}"

    top_proposals = {
        archive_id
        for archive_id, _ in sorted(
            proposal_totals.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:24]
    }

    def node(label: str) -> int:
        if label not in index:
            index[label] = len(labels)
            labels.append(label)
        return index[label]

    links_value: defaultdict[tuple[int, int], float] = defaultdict(float)
    decode_match_count = 0
    unmatched_count = 0

    for row in spend_ledger.get("records", []):
        usd = row.get("usd_value_at_execution")
        if usd is None:
            continue
        value = to_float(usd)
        if value <= 0:
            continue
        proposal_number = row.get("proposal_number")
        if proposal_number in (None, ""):
            pn = None
        else:
            pn = int(proposal_number)
        title = str(row.get("title") or "")
        archive_id = str(row.get("archive_id") or "")
        recipient = str(row.get("recipient_display_name") or row.get("recipient_address") or "Unknown")
        funding = infer_funding_source(pn)
        if archive_id and archive_id in top_proposals:
            proposal_label = proposal_labels.get(archive_id, f"Proposal: {archive_id}")
        else:
            proposal_label = f"Proposal type: {infer_proposal_type(title)}"

        proposal_txs = proposal_tx_index.get(archive_id, [])
        tx_match = match_tx_for_spend_row(
            proposal_txs,
            str(row.get("recipient_address") or ""),
            str(row.get("asset_symbol") or ""),
        )
        if tx_match is not None:
            decode_match_count += 1
        else:
            unmatched_count += 1

        route = classify_treasury_route(str(row.get("asset_symbol") or "OTHER"), tx_match)
        cluster = infer_recipient_cluster(recipient, title)

        n1 = node(f"Funding: {funding}")
        n2 = node(proposal_label)
        n3 = node(f"Treasury Route: {route}")
        n4 = node(f"Recipient: {cluster}")
        links_value[(n1, n2)] += value
        links_value[(n2, n3)] += value
        links_value[(n3, n4)] += value

    links = [
        {"source": src, "target": dst, "value": round(val, 2)}
        for (src, dst), val in sorted(links_value.items(), key=lambda item: (item[0][0], item[0][1]))
    ]

    return {
        "dataset": "sankey",
        "as_of": utc_now_iso(),
        "version": 1,
        "track": "Funding source -> Proposal -> Treasury route -> Recipient cluster",
        "nodes": [{"id": i, "label": label} for i, label in enumerate(labels)],
        "links": links,
        "decoding": {
            "matched_routes": decode_match_count,
            "unmatched_routes": unmatched_count,
            "selector_reference": {
                "a9059cbb": "ERC20 transfer",
                "23b872dd": "ERC721 transferFrom",
                "empty": "Native transfer",
            },
        },
    }


def build_delegation_graph(proposals: dict[str, Any]) -> dict[str, Any]:
    voter_power: defaultdict[str, float] = defaultdict(float)
    voter_events: Counter[str] = Counter()
    graph = nx.Graph()

    for proposal in proposals.get("records", []):
        proposal_votes: list[tuple[str, float]] = []
        for vote in proposal.get("votes", []):
            voter = normalize_address(vote.get("voter"))
            amount = to_float(vote.get("votes"))
            if not voter or amount <= 0:
                continue
            proposal_votes.append((voter, amount))
            voter_power[voter] += amount
            voter_events[voter] += 1

        proposal_votes.sort(key=lambda item: item[1], reverse=True)
        capped_votes = proposal_votes[:12]
        for voter, _ in capped_votes:
            graph.add_node(voter)
        for idx in range(len(capped_votes)):
            left_voter, left_power = capped_votes[idx]
            for jdx in range(idx + 1, len(capped_votes)):
                right_voter, right_power = capped_votes[jdx]
                edge = graph.get_edge_data(left_voter, right_voter, default={})
                graph.add_edge(
                    left_voter,
                    right_voter,
                    weight=to_float(edge.get("weight")) + min(left_power, right_power),
                    co_votes=int(edge.get("co_votes") or 0) + 1,
                )

    top_voters = [
        voter
        for voter, _ in sorted(voter_power.items(), key=lambda item: item[1], reverse=True)[:80]
    ]
    subgraph = graph.subgraph(top_voters).copy()
    if subgraph.number_of_nodes() == 0:
        return {
            "dataset": "delegation_graph",
            "as_of": utc_now_iso(),
            "version": 1,
            "overview": {
                "node_count": 0,
                "edge_count": 0,
                "density": 0.0,
                "largest_component_size": 0,
            },
            "nodes": [],
            "links": [],
        }

    positions = nx.spring_layout(subgraph, seed=42, weight="weight")
    betweenness = nx.betweenness_centrality(subgraph, weight="weight", normalized=True)

    nodes = []
    for node in subgraph.nodes():
        x, y = positions.get(node, (0.0, 0.0))
        nodes.append(
            {
                "id": node,
                "label": f"{node[:6]}...{node[-4:]}",
                "x": round(float(x), 6),
                "y": round(float(y), 6),
                "total_votes": round(voter_power.get(node, 0.0), 4),
                "vote_events": int(voter_events.get(node, 0)),
                "degree": int(subgraph.degree(node)),
                "betweenness": round(float(betweenness.get(node, 0.0)), 6),
            }
        )

    links = []
    for source, target, data in subgraph.edges(data=True):
        links.append(
            {
                "source": source,
                "target": target,
                "weight": round(to_float(data.get("weight")), 6),
                "co_votes": int(data.get("co_votes") or 0),
            }
        )

    components = sorted(nx.connected_components(subgraph), key=len, reverse=True)
    largest_component_size = len(components[0]) if components else 0

    return {
        "dataset": "delegation_graph",
        "as_of": utc_now_iso(),
        "version": 1,
        "overview": {
            "node_count": subgraph.number_of_nodes(),
            "edge_count": subgraph.number_of_edges(),
            "density": round(float(nx.density(subgraph)), 6),
            "largest_component_size": largest_component_size,
        },
        "nodes": sorted(nodes, key=lambda item: item["total_votes"], reverse=True),
        "links": sorted(links, key=lambda item: item["weight"], reverse=True),
    }


def build_runway_scenarios(treasury: dict[str, Any], treasury_flows: dict[str, Any]) -> dict[str, Any]:
    treasury_balance = to_float(treasury.get("overview", {}).get("treasury_page_total_value_usd"))
    if treasury_balance <= 0:
        treasury_balance = sum(to_float(row.get("value_usd")) for row in treasury.get("records", []))

    month_spend: defaultdict[str, float] = defaultdict(float)
    for route in treasury_flows.get("routes", []):
        usd = to_float(route.get("usd_value_at_execution"))
        if usd <= 0:
            continue
        month = month_bucket(route.get("event_at") or route.get("valuation_reference_at"))
        if month == "unknown":
            continue
        month_spend[month] += usd

    recent_months = sorted(month_spend.keys())[-6:]
    recent_values = [month_spend[m] for m in recent_months]
    baseline_burn = (sum(recent_values) / len(recent_values)) if recent_values else 0.0

    anchor = datetime.now(timezone.utc).strftime("%Y-%m")

    def project(monthly_burn: float, monthly_inflow: float) -> dict[str, Any]:
        balance = treasury_balance
        rows: list[dict[str, Any]] = []
        runway_months = 0
        for offset in range(0, 25):
            month = add_months(anchor, offset)
            if offset > 0:
                balance = max(0.0, balance + monthly_inflow - monthly_burn)
            if balance > 0:
                runway_months = offset
            rows.append({"month": month, "balance_usd": round(balance, 2)})
        return {
            "runway_months": runway_months,
            "projection": rows,
        }

    scenario_defs = [
        {"scenario_id": "lean", "label": "Lean", "burn_multiplier": 0.75, "monthly_inflow_usd": 0.0},
        {"scenario_id": "baseline", "label": "Baseline", "burn_multiplier": 1.0, "monthly_inflow_usd": 0.0},
        {"scenario_id": "growth", "label": "Growth", "burn_multiplier": 1.25, "monthly_inflow_usd": 0.0},
        {"scenario_id": "expansion", "label": "Expansion", "burn_multiplier": 1.5, "monthly_inflow_usd": 0.0},
        {"scenario_id": "sponsored", "label": "Sponsored", "burn_multiplier": 1.0, "monthly_inflow_usd": 1500.0},
    ]

    scenarios = []
    for item in scenario_defs:
        monthly_burn = baseline_burn * item["burn_multiplier"]
        result = project(monthly_burn, item["monthly_inflow_usd"])
        scenarios.append(
            {
                "scenario_id": item["scenario_id"],
                "label": item["label"],
                "monthly_burn_usd": round(monthly_burn, 2),
                "monthly_inflow_usd": item["monthly_inflow_usd"],
                "runway_months": result["runway_months"],
                "projection": result["projection"],
            }
        )

    return {
        "dataset": "runway_scenarios",
        "as_of": utc_now_iso(),
        "version": 1,
        "overview": {
            "treasury_balance_usd": round(treasury_balance, 2),
            "baseline_monthly_burn_usd": round(baseline_burn, 2),
            "observation_months": recent_months,
        },
        "scenarios": scenarios,
    }


def build_fork_risk(proposals: dict[str, Any]) -> dict[str, Any]:
    month_power: defaultdict[str, defaultdict[str, float]] = defaultdict(lambda: defaultdict(float))

    for proposal in proposals.get("records", []):
        month = month_bucket(proposal.get("created_at"))
        if month == "unknown":
            continue
        for vote in proposal.get("votes", []):
            voter = normalize_address(vote.get("voter"))
            amount = to_float(vote.get("votes"))
            if voter and amount > 0:
                month_power[month][voter] += amount

    rows: list[dict[str, Any]] = []
    alerts: list[dict[str, Any]] = []

    for month in sorted(month_power.keys()):
        values = sorted(month_power[month].values(), reverse=True)
        if not values:
            continue
        total = sum(values)
        top1 = values[0] / total
        top3 = sum(values[:3]) / total
        top5 = sum(values[:5]) / total
        hhi = sum((value / total) ** 2 for value in values)
        gini_value = gini(values)

        if top1 >= 0.35 or top3 >= 0.75 or (gini_value is not None and gini_value >= 0.78):
            level = "high"
        elif top1 >= 0.25 or top3 >= 0.65 or (gini_value is not None and gini_value >= 0.68):
            level = "medium"
        else:
            level = "low"

        row = {
            "month": month,
            "voter_count": len(values),
            "top1_share_pct": round(top1 * 100.0, 4),
            "top3_share_pct": round(top3 * 100.0, 4),
            "top5_share_pct": round(top5 * 100.0, 4),
            "hhi": round(hhi, 6),
            "gini": round(gini_value, 6) if gini_value is not None else None,
            "risk_level": level,
        }
        rows.append(row)
        if level in {"medium", "high"}:
            alerts.append(
                {
                    "month": month,
                    "level": level,
                    "message": (
                        f"Concentration elevated: top1={row['top1_share_pct']:.1f}% "
                        f"top3={row['top3_share_pct']:.1f}% gini={row['gini'] if row['gini'] is not None else 'n/a'}"
                    ),
                }
            )

    latest = rows[-1] if rows else None

    return {
        "dataset": "fork_risk",
        "as_of": utc_now_iso(),
        "version": 1,
        "overview": {
            "latest_month": latest["month"] if latest else None,
            "latest_risk_level": latest["risk_level"] if latest else "unknown",
            "latest_top1_share_pct": latest["top1_share_pct"] if latest else None,
            "latest_top3_share_pct": latest["top3_share_pct"] if latest else None,
            "latest_gini": latest["gini"] if latest else None,
        },
        "timeseries": rows,
        "alerts": alerts[-12:],
    }


def main() -> int:
    proposals = load_json("proposals_archive")
    spend_ledger = load_json("spend_ledger")
    dao_metrics = load_json("dao_metrics")
    treasury = load_json("treasury")
    treasury_flows = load_json("treasury_flows")

    governance = build_governance(proposals, dao_metrics)
    growth = build_growth(proposals, dao_metrics)
    efficiency = build_efficiency(spend_ledger, proposals)
    culture = build_culture(proposals)
    sankey = build_sankey(spend_ledger, proposals)
    delegation_graph = build_delegation_graph(proposals)
    runway_scenarios = build_runway_scenarios(treasury, treasury_flows)
    fork_risk = build_fork_risk(proposals)

    write_json("governance", governance)
    write_json("growth", growth)
    write_json("efficiency", efficiency)
    write_json("culture", culture)
    write_json("sankey", sankey)
    write_json("delegation_graph", delegation_graph)
    write_json("runway_scenarios", runway_scenarios)
    write_json("fork_risk", fork_risk)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

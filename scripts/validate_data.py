from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from product_datasets import PRODUCT_CATEGORIES, normalize_category, slug_label


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SCHEMA_DIR = DATA_DIR / "schemas"

DATASETS = {
    "contracts": "contracts.schema.json",
    "proposals": "proposals.schema.json",
    "proposals_archive": "proposals_archive.schema.json",
    "proposal_tags": "proposal_tags.schema.json",
    "members": "members.schema.json",
    "people_overrides": "people_overrides.schema.json",
    "people": "people.schema.json",
    "treasury": "treasury.schema.json",
    "projects": "projects.schema.json",
    "project_updates": "project_updates.schema.json",
    "project_rollups": "project_rollups.schema.json",
    "spend_ledger": "spend_ledger.schema.json",
    "dao_metrics": "dao_metrics.schema.json",
    "timeline_events": "timeline_events.schema.json",
    "activity_timeseries": "activity_timeseries.schema.json",
    "treasury_flows": "treasury_flows.schema.json",
    "community_signals": "community_signals.schema.json",
    "network_graph": "network_graph.schema.json",
    "proposals_enriched": "proposals_enriched.schema.json",
    "media_proof": "media_proof.schema.json",
    "feed_stream": "feed_stream.schema.json",
    "insights": "insights.schema.json",
    "filter_facets": "filter_facets.schema.json",
    "treasury_snapshots": "treasury_snapshots.schema.json",
    "proposal_reconciliation": "proposal_reconciliation.schema.json",
    "person_reconciliation": "person_reconciliation.schema.json",
    "contract_reconciliation": "contract_reconciliation.schema.json",
    "treasury_reconciliation": "treasury_reconciliation.schema.json",
    "sources": "sources.schema.json",
}


class ValidationError(Exception):
    pass


def type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise ValidationError(f"Unsupported schema type: {expected}")


def validate(instance: Any, schema: dict[str, Any], path: str = "$") -> None:
    if "const" in schema and instance != schema["const"]:
        raise ValidationError(f"{path}: expected constant {schema['const']!r}, got {instance!r}")

    if "enum" in schema and instance not in schema["enum"]:
        raise ValidationError(f"{path}: expected one of {schema['enum']!r}, got {instance!r}")

    expected_type = schema.get("type")
    if expected_type is not None:
        allowed = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(type_matches(instance, item) for item in allowed):
            raise ValidationError(f"{path}: expected type {allowed!r}, got {type(instance).__name__}")

    if isinstance(instance, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                raise ValidationError(f"{path}: missing required key {key!r}")

        properties = schema.get("properties", {})
        additional_properties = schema.get("additionalProperties", True)

        for key, value in instance.items():
            if key in properties:
                validate(value, properties[key], f"{path}.{key}")
            elif additional_properties is False:
                raise ValidationError(f"{path}: unexpected key {key!r}")

    if isinstance(instance, list) and "items" in schema:
        for index, item in enumerate(instance):
            validate(item, schema["items"], f"{path}[{index}]")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_references(datasets: dict[str, Any]) -> list[str]:
    failures: list[str] = []

    people = datasets.get("people", {}).get("records", [])
    projects = datasets.get("project_rollups", {}).get("records", [])
    proposals = datasets.get("proposals_archive", {}).get("records", [])
    proposals_enriched = datasets.get("proposals_enriched", {}).get("records", [])
    timeline = datasets.get("timeline_events", {}).get("records", [])
    media_proof = datasets.get("media_proof", {}).get("records", [])
    feed_stream = datasets.get("feed_stream", {}).get("records", [])
    treasury_flows = datasets.get("treasury_flows", {})
    proposal_reconciliation = datasets.get("proposal_reconciliation", {}).get("records", [])
    person_reconciliation = datasets.get("person_reconciliation", {}).get("records", [])
    contract_reconciliation = datasets.get("contract_reconciliation", {}).get("records", [])
    treasury_reconciliation = datasets.get("treasury_reconciliation", {}).get("records", [])
    contracts = datasets.get("contracts", {}).get("records", [])
    network_graph = datasets.get("network_graph", {})
    filter_facets = datasets.get("filter_facets", {})

    people_by_address = {record["address"]: record for record in people}
    people_slugs = [record["slug"] for record in people]
    project_ids = {record["project_id"] for record in projects}
    project_slugs = [record["slug"] for record in projects]
    archive_ids = {record["archive_id"] for record in proposals}
    enriched_ids = {record["archive_id"] for record in proposals_enriched}
    proof_ids = {record["proof_id"] for record in media_proof}
    contract_ids = {record["contract_id"] for record in contracts}

    if len(people_slugs) != len(set(people_slugs)):
        failures.append("data/people.json: duplicate slugs detected")
    if len(project_slugs) != len(set(project_slugs)):
        failures.append("data/project_rollups.json: duplicate slugs detected")
    if len(archive_ids) != len(proposals):
        failures.append("data/proposals_archive.json: duplicate archive_id detected")
    if archive_ids != enriched_ids:
        failures.append("data/proposals_enriched.json: archive coverage diverges from proposals_archive")

    valid_categories = set(PRODUCT_CATEGORIES)
    for record in proposals_enriched:
        if record["category"] not in valid_categories:
            failures.append(f"data/proposals_enriched.json: invalid category {record['category']!r} on {record['archive_id']}")
    for record in projects:
        category = normalize_category(record.get("category")) or "Other"
        if category not in valid_categories:
            failures.append(f"data/project_rollups.json: invalid category {record.get('category')!r} on {record['project_id']}")

    for record in timeline:
        project_id = record.get("project_id")
        archive_id = record.get("archive_id")
        for address in record.get("people_addresses", []):
            if address not in people_by_address:
                failures.append(f"data/timeline_events.json: unknown person address {address} in {record['event_id']}")
        if project_id and project_id not in project_ids:
            failures.append(f"data/timeline_events.json: unknown project_id {project_id} in {record['event_id']}")
        if archive_id and archive_id not in archive_ids:
            failures.append(f"data/timeline_events.json: unknown archive_id {archive_id} in {record['event_id']}")

    for record in media_proof:
        project_id = record.get("project_id")
        archive_id = record.get("archive_id")
        if project_id and project_id not in project_ids:
            failures.append(f"data/media_proof.json: unknown project_id {project_id} in {record['proof_id']}")
        if archive_id and archive_id not in archive_ids:
            failures.append(f"data/media_proof.json: unknown archive_id {archive_id} in {record['proof_id']}")
        for address in record.get("people_addresses", []):
            if address not in people_by_address:
                failures.append(f"data/media_proof.json: unknown person address {address} in {record['proof_id']}")

    valid_category_slugs = {slug_label(value) for value in PRODUCT_CATEGORIES}
    proposal_index = {record["archive_id"]: record for record in proposals_enriched}
    for record in proposals_enriched:
        related_proofs = record.get("related_proof_ids", [])
        if len(related_proofs) > int(record.get("proof_count", 0)):
            failures.append(
                f"data/proposals_enriched.json: proof_count smaller than related_proof_ids on {record['archive_id']}"
            )
        for proof_id in related_proofs:
            if proof_id not in proof_ids:
                failures.append(
                    f"data/proposals_enriched.json: unknown proof_id {proof_id} on {record['archive_id']}"
                )
        category_slug = slug_label(record.get("category"))
        if category_slug not in valid_category_slugs:
            failures.append(
                f"data/proposals_enriched.json: category {record.get('category')!r} is outside product taxonomy on {record['archive_id']}"
            )
        if record.get("outcome_group") == "closed-passed" and not record.get("successful"):
            failures.append(
                f"data/proposals_enriched.json: closed-passed without successful=true on {record['archive_id']}"
            )
        if record.get("outcome_group") == "closed-not-passed" and record.get("successful"):
            failures.append(
                f"data/proposals_enriched.json: closed-not-passed with successful=true on {record['archive_id']}"
            )

    for record in feed_stream:
        for archive_id in record.get("linked_proposals", []):
            if archive_id not in archive_ids:
                failures.append(f"data/feed_stream.json: unknown linked proposal {archive_id} in {record['item_id']}")
        for project_id in record.get("linked_projects", []):
            if project_id not in project_ids:
                failures.append(f"data/feed_stream.json: unknown linked project {project_id} in {record['item_id']}")
        for address in record.get("linked_people", []):
            if address not in people_by_address:
                failures.append(f"data/feed_stream.json: unknown linked person {address} in {record['item_id']}")
        grouped_labels: set[str] = set()
        for key in (
            "editorial_labels",
            "status_labels",
            "funding_labels",
            "relationship_labels",
            "platform_labels",
            "lifecycle_labels",
            "proof_labels",
        ):
            grouped_labels.update(label for label in (record.get(key) or []) if label not in (None, ""))
        if not grouped_labels.issubset(set(record.get("labels", []))):
            failures.append(f"data/feed_stream.json: labels do not cover grouped labels in {record['item_id']}")

    if {record["archive_id"] for record in proposal_reconciliation} != archive_ids:
        failures.append("data/proposal_reconciliation.json: archive coverage diverges from proposals_archive")
    if {record["address"] for record in person_reconciliation} != set(people_by_address):
        failures.append("data/person_reconciliation.json: address coverage diverges from people")
    if {record["contract_id"] for record in contract_reconciliation} != contract_ids:
        failures.append("data/contract_reconciliation.json: contract coverage diverges from contracts")
    if {record["route_id"] for record in treasury_reconciliation} != {record["ledger_id"] for record in datasets.get("spend_ledger", {}).get("records", [])}:
        failures.append("data/treasury_reconciliation.json: route coverage diverges from spend_ledger")

    for record in proposal_reconciliation:
        if record["archive_id"] not in archive_ids:
            failures.append(f"data/proposal_reconciliation.json: unknown archive_id {record['archive_id']}")
    for record in person_reconciliation:
        if record["address"] not in people_by_address:
            failures.append(f"data/person_reconciliation.json: unknown address {record['address']}")
    for record in contract_reconciliation:
        if record["contract_id"] not in contract_ids:
            failures.append(f"data/contract_reconciliation.json: unknown contract_id {record['contract_id']}")
    for record in treasury_reconciliation:
        if record["archive_id"] not in archive_ids:
            failures.append(f"data/treasury_reconciliation.json: unknown archive_id {record['archive_id']} in {record['route_id']}")
        if record["recipient_address"] not in people_by_address:
            failures.append(f"data/treasury_reconciliation.json: unknown recipient {record['recipient_address']} in {record['route_id']}")

    node_ids = [record["node_id"] for record in network_graph.get("nodes", [])]
    node_id_set = set(node_ids)
    if len(node_ids) != len(node_id_set):
        failures.append("data/network_graph.json: duplicate node_id detected")
    edge_ids = [record["edge_id"] for record in network_graph.get("edges", [])]
    if len(edge_ids) != len(set(edge_ids)):
        failures.append("data/network_graph.json: duplicate edge_id detected")
    for edge in network_graph.get("edges", []):
        if edge["source"] not in node_id_set or edge["target"] not in node_id_set:
            failures.append(f"data/network_graph.json: edge {edge['edge_id']} references missing node")
    homepage = network_graph.get("views", {}).get("homepage", {})
    for node_id in homepage.get("node_ids", []):
        if node_id not in node_id_set:
            failures.append(f"data/network_graph.json: homepage references missing node {node_id}")
    for edge_id in homepage.get("edge_ids", []):
        if edge_id not in set(edge_ids):
            failures.append(f"data/network_graph.json: homepage references missing edge {edge_id}")

    for route in treasury_flows.get("routes", []):
        if route["archive_id"] not in archive_ids:
            failures.append(f"data/treasury_flows.json: route {route['route_id']} references missing proposal")
        if route.get("project_id") and route["project_id"] not in project_ids:
            failures.append(f"data/treasury_flows.json: route {route['route_id']} references missing project")
        if route["recipient_address"] not in people_by_address:
            failures.append(f"data/treasury_flows.json: route {route['route_id']} references missing recipient")
    for route in treasury_flows.get("proposal_routes", []):
        if route["archive_id"] not in archive_ids:
            failures.append(f"data/treasury_flows.json: proposal route references missing proposal {route['archive_id']}")

    surfaces = filter_facets.get("surfaces", {})
    for surface_name, facets in surfaces.items():
        for facet_name, values in facets.items():
            seen_values: set[str] = set()
            for item in values:
                if int(item.get("count", 0)) < 0:
                    failures.append(f"data/filter_facets.json: negative count for {surface_name}.{facet_name}.{item.get('value')}")
                facet_value = str(item.get("value") or "")
                if facet_value in seen_values:
                    failures.append(
                        f"data/filter_facets.json: duplicate facet value {facet_value!r} for {surface_name}.{facet_name}"
                    )
                seen_values.add(facet_value)

    def _facet_counts(values: list[str]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for value in values:
            if value in (None, ""):
                continue
            key = str(value)
            counts[key] = counts.get(key, 0) + 1
        return counts

    expected_facets = {
        "home": {
            "kind": _facet_counts([record.get("kind") for record in feed_stream]),
            "status": _facet_counts([record.get("status") for record in feed_stream]),
            "category": _facet_counts(
                [
                    label
                    for record in feed_stream
                    for label in (record.get("editorial_labels") or [])
                    if label in valid_category_slugs
                ]
            ),
            "asset": _facet_counts(
                [label for record in feed_stream for label in (record.get("linked_assets") or [])]
            ),
        },
        "proposals": {
            "status": _facet_counts([record.get("status") for record in proposals_enriched]),
            "category": _facet_counts([slug_label(record.get("category")) for record in proposals_enriched]),
            "platform": _facet_counts([record.get("platform") for record in proposals_enriched]),
            "chain": _facet_counts([record.get("chain") for record in proposals_enriched]),
        },
        "community": {
            "tribe": _facet_counts(
                [tribe for record in people for tribe in (record.get("tribes") or record.get("tags") or [])]
            ),
            "status": _facet_counts([record.get("status") for record in people]),
        },
        "projects": {
            "category": _facet_counts(
                [slug_label(normalize_category(record.get("category")) or "Other") for record in projects]
            ),
            "status": _facet_counts([record.get("status") for record in projects]),
        },
        "treasury": {
            "asset": _facet_counts([record.get("asset_symbol") for record in treasury_flows.get("routes", [])]),
            "status": _facet_counts([record.get("proposal_status") for record in treasury_flows.get("routes", [])]),
            "category": _facet_counts(
                [
                    slug_label(
                        (proposal_index.get(record["archive_id"]) or {}).get("category") or "Other"
                    )
                    for record in treasury_flows.get("routes", [])
                ]
            ),
        },
        "timeline": {
            "kind": _facet_counts([record.get("kind") for record in timeline]),
            "status": _facet_counts([record.get("status") for record in timeline]),
        },
    }

    def _canonical_facet_value(surface_name: str, facet_name: str, value: Any) -> str:
        text = str(value or "")
        if facet_name == "category":
            return slug_label(text)
        return text

    for surface_name, facet_groups in expected_facets.items():
        actual_groups = surfaces.get(surface_name, {})
        for facet_name, expected_counts in facet_groups.items():
            actual_counts: dict[str, int] = {}
            for item in actual_groups.get(facet_name, []):
                key = _canonical_facet_value(surface_name, facet_name, item.get("value"))
                actual_counts[key] = actual_counts.get(key, 0) + int(item.get("count", 0))
            if actual_counts != expected_counts:
                failures.append(
                    f"data/filter_facets.json: counts mismatch for {surface_name}.{facet_name}"
                )

    return failures


def main() -> int:
    failures: list[str] = []
    loaded_datasets: dict[str, Any] = {}

    for dataset_name, schema_name in DATASETS.items():
        dataset_path = DATA_DIR / f"{dataset_name}.json"
        schema_path = SCHEMA_DIR / schema_name
        try:
            dataset = load_json(dataset_path)
            schema = load_json(schema_path)
            validate(dataset, schema)
            loaded_datasets[dataset_name] = dataset
            print(f"[ok] {dataset_path.relative_to(ROOT)}")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{dataset_path.relative_to(ROOT)}: {exc}")

    if not failures:
        failures.extend(validate_references(loaded_datasets))

    if failures:
        print("\nValidation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nAll datasets validated successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

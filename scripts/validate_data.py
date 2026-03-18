from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SCHEMA_DIR = DATA_DIR / "schemas"

DATASETS = {
    "contracts": "contracts.schema.json",
    "proposals": "proposals.schema.json",
    "proposals_archive": "proposals_archive.schema.json",
    "proposal_tags": "proposal_tags.schema.json",
    "members": "members.schema.json",
    "treasury": "treasury.schema.json",
    "projects": "projects.schema.json",
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


def main() -> int:
    failures: list[str] = []

    for dataset_name, schema_name in DATASETS.items():
        dataset_path = DATA_DIR / f"{dataset_name}.json"
        schema_path = SCHEMA_DIR / schema_name
        try:
            dataset = load_json(dataset_path)
            schema = load_json(schema_path)
            validate(dataset, schema)
            print(f"[ok] {dataset_path.relative_to(ROOT)}")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{dataset_path.relative_to(ROOT)}: {exc}")

    if failures:
        print("\nValidation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nAll datasets validated successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

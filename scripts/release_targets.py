"""Read .github/release-targets.yaml for the publish workflow."""

import argparse
import json
import os
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from ruamel.yaml import YAML


def parse_release_targets(path: Path) -> dict:
    document = YAML().load(path)
    _validate_schema(document, path.with_suffix(".schema.json"))
    registries = [_strings(row) for row in document["registries"]]
    rollouts = [_strings(row) for row in document["rollout"]]
    _validate_names(registries, rollouts)
    return {"registries": registries, "rollout": rollouts}


def _validate_schema(instance: object, schema_path: Path) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(instance), key=lambda error: list(error.absolute_path)
    )
    if not errors:
        return
    error = errors[0]
    location = "/".join(str(part) for part in error.absolute_path)
    prefix = f"{location}: " if location else ""
    raise ValueError(f"{prefix}{error.message}") from error


def _strings(row: dict) -> dict[str, str]:
    return {str(key): str(value) for key, value in row.items()}


def _validate_names(
    registries: list[dict[str, str]], rollouts: list[dict[str, str]]
) -> None:
    registry_names = [row["name"] for row in registries]
    if len(registry_names) != len(set(registry_names)):
        raise ValueError("registry names must be unique")

    rollout_names = [row["name"] for row in rollouts]
    if len(rollout_names) != len(set(rollout_names)):
        raise ValueError("rollout names must be unique")


def write_github_output(name: str, value: str) -> None:
    output = os.environ.get("GITHUB_OUTPUT")
    if not output:
        return
    marker = f"EOF_{name}"
    with open(output, "a", encoding="utf-8") as handle:
        handle.write(f"{name}<<{marker}\n{value}\n{marker}\n")


def plan(path: Path) -> dict[str, str]:
    parsed = parse_release_targets(path)
    payload = {
        "rollouts": json.dumps(parsed["rollout"], separators=(",", ":")),
        "hosts": "\n".join(row["host"] for row in parsed["registries"]),
    }
    for name, value in payload.items():
        write_github_output(name, value)
    return payload


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", type=Path, help="path to release-targets.yaml")
    args = parser.parse_args(argv)
    payload = plan(args.targets)
    if not os.environ.get("GITHUB_OUTPUT"):
        json.dump(payload, sys.stdout)
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()

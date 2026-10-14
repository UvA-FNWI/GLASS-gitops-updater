"""Parse .github/release-targets.yaml for the publish workflow."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REQUIRED_REGISTRY = ("name", "host")
REQUIRED_ROLLOUT = ("name", "registry", "url", "config", "secret")


def parse_release_targets(text: str) -> dict:
    registries: list[dict[str, str]] = []
    rollouts: list[dict[str, str]] = []
    section: str | None = None
    current: dict[str, str] | None = None

    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        content = line.strip()
        if indent == 0:
            if content in ("registries:", "rollout:"):
                section = content[:-1]
                current = None
                continue
            raise ValueError(f"line {line_no}: unknown section {content!r}")
        if section is None:
            raise ValueError(f"line {line_no}: entry outside a section")
        if content.startswith("- "):
            bucket = registries if section == "registries" else rollouts
            current = {}
            bucket.append(current)
            item = content[2:].strip()
            if item:
                _assign(current, item, line_no)
            continue
        if current is None:
            raise ValueError(f"line {line_no}: field before list item")
        _assign(current, content, line_no)

    _validate(registries, rollouts)
    return {"registries": registries, "rollout": rollouts}


def _assign(current: dict[str, str], item: str, line_no: int) -> None:
    if ":" not in item:
        raise ValueError(f"line {line_no}: expected key: value")
    key, value = item.split(":", 1)
    current[key.strip()] = value.strip()


def _validate(registries: list[dict[str, str]], rollouts: list[dict[str, str]]) -> None:
    registry_names = [row.get("name", "") for row in registries]
    if len(registry_names) != len(set(registry_names)):
        raise ValueError("registry names must be unique")
    known = set(registry_names)
    for row in registries:
        for key in REQUIRED_REGISTRY:
            if not row.get(key):
                raise ValueError(f"registry missing {key}")

    rollout_names = [row.get("name", "") for row in rollouts]
    if len(rollout_names) != len(set(rollout_names)):
        raise ValueError("rollout names must be unique")
    for row in rollouts:
        label = row.get("name") or "?"
        for key in REQUIRED_ROLLOUT:
            if not row.get(key):
                raise ValueError(f"rollout {label} missing {key}")
        if row["registry"] not in known:
            raise ValueError(
                f"rollout {label} references unknown registry {row['registry']}"
            )
        if not row["url"].startswith("https://"):
            raise ValueError(f"rollout {label} url must be https")


def write_github_output(name: str, value: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    marker = f"EOF_{name}"
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(f"{name}<<{marker}\n{value}\n{marker}\n")


def plan(path: Path) -> dict[str, str]:
    parsed = parse_release_targets(path.read_text(encoding="utf-8"))
    payload = {
        "registries": json.dumps(parsed["registries"], separators=(",", ":")),
        "rollouts": json.dumps(parsed["rollout"], separators=(",", ":")),
        "hosts": "\n".join(row["host"] for row in parsed["registries"]),
    }
    for name, value in payload.items():
        write_github_output(name, value)
    return payload


def main(argv: list[str]) -> None:
    if len(argv) != 3 or argv[1] != "plan":
        raise SystemExit("usage: release_targets.py plan <file>")
    payload = plan(Path(argv[2]))
    if not os.environ.get("GITHUB_OUTPUT"):
        json.dump(payload, sys.stdout)
        sys.stdout.write("\n")


if __name__ == "__main__":
    main(sys.argv)
